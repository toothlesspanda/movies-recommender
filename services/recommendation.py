import os
import numpy as np
import faiss
from db import get_connection
import repositories.movie_emotions as movie_emotions_repo
import services.similarity as similar

DATA_DIR = os.environ.get("DATA_DIR", ".")
FAISS_INDEX_PATH = os.path.join(DATA_DIR, "movies.faiss")
FAISS_IDS_PATH = os.path.join(DATA_DIR, "movies_faiss_ids.npy")

_faiss_index = None
_faiss_ids = None
_emotions_matrix = None
_emotions_id_map = None


def _load():
    global _faiss_index, _faiss_ids, _emotions_matrix, _emotions_id_map

    if _faiss_index is not None:
        return

    _faiss_index = faiss.read_index(FAISS_INDEX_PATH)
    _faiss_ids = np.load(FAISS_IDS_PATH)

    conn = get_connection()
    rows = movie_emotions_repo.get_all(conn)
    conn.close()

    ids = []
    vectors = []
    for row in rows:
        ids.append(row["movie_id"])
        vectors.append([row["mood"], row["energy"], row["tension"], row["weight"]])

    _emotions_matrix = np.array(vectors, dtype=np.float32)
    _emotions_id_map = {mid: i for i, mid in enumerate(ids)}
    print(f"Loaded Faiss index ({_faiss_index.ntotal} vectors) + {len(ids)} emotions.")


def find_related(source_embedding, movie_id, target_emotions, source_emotions=None, limit=50, candidates_pool=200):
    _load()

    # Dynamic weighting: more slider movement = more emotional weight
    # No change: 50/50, max change: 20/80
    if source_emotions:
        diff = np.mean(np.abs(np.array(target_emotions) - np.array(source_emotions))) / 100.0
        emo_weight = 0.5 + diff * 0.6  # 0.5 to 0.8
        emo_weight = min(emo_weight, 0.8)
    else:
        emo_weight = 0.5
    fact_weight = 1.0 - emo_weight

    # Normalise source for cosine similarity
    source_vector = np.frombuffer(source_embedding, dtype=np.float32).reshape(1, -1).copy()
    faiss.normalize_L2(source_vector)

    # Factual similarity via Faiss
    factual_scores, factual_indices = _faiss_index.search(source_vector, candidates_pool)
    candidates = {}
    for score, idx in zip(factual_scores[0], factual_indices[0]):
        mid = int(_faiss_ids[idx])
        if mid != movie_id:
            candidates[mid] = score * fact_weight

    # Emotional similarity on candidates
    target_vec = np.array(target_emotions, dtype=np.float32)
    for mid in candidates:
        if mid in _emotions_id_map:
            emo_idx = _emotions_id_map[mid]
            emo_score = similar.cosine_similarity(target_vec, _emotions_matrix[emo_idx:emo_idx+1])[0]
            candidates[mid] += emo_score * emo_weight

    return sorted(candidates, key=candidates.get, reverse=True)[:limit]
