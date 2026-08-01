from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
import os

DATA_DIR = os.environ.get("DATA_DIR", ".")
FAISS_INDEX_PATH = os.path.join(DATA_DIR, "movies.faiss")
FAISS_IDS_PATH = os.path.join(DATA_DIR, "movies_faiss_ids.npy")
MODEL_NAME = "all-MiniLM-L6-v2"
DIMS = 384

_model = None
_faiss_index = None
_faiss_ids = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _load_faiss():
    global _faiss_index, _faiss_ids
    if _faiss_index is None:
        if os.path.exists(FAISS_INDEX_PATH):
            _faiss_index = faiss.read_index(FAISS_INDEX_PATH)
            _faiss_ids = list(np.load(FAISS_IDS_PATH))
        else:
            _faiss_index = faiss.IndexFlatIP(DIMS)
            _faiss_ids = []
    return _faiss_index, _faiss_ids


def save_faiss():
    index, ids = _load_faiss()
    faiss.write_index(index, FAISS_INDEX_PATH)
    np.save(FAISS_IDS_PATH, np.array(ids))


def build_input_text(title, genres, directors, actors, description):
    return f"""Title: {title}
Genres: {genres or ''}
Directors: {directors or ''}
Cast: {actors or ''}
Synopsis: {description or ''}"""


def generate_embeddings_batch(texts):
    return get_model().encode(texts, batch_size=64).astype(np.float32)


def store_embeddings_batch(conn, movie_ids, vectors):
    for movie_id, vector in zip(movie_ids, vectors):
        blob = vector.tobytes()
        conn.execute(
            "INSERT OR IGNORE INTO movie_embeddings (movie_id, embedding, model_name) VALUES (?, ?, ?)",
            (movie_id, blob, f"hf:{MODEL_NAME}"),
        )
    # Add to Faiss
    index, ids = _load_faiss()
    v = vectors.copy()
    faiss.normalize_L2(v)
    index.add(v)
    ids.extend(movie_ids)
