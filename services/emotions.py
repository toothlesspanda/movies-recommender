from transformers import pipeline
from constants import EMOTION_MAP, GENRE_MAP, DEFAULT_SCORES, SYNOPSIS_WEIGHT

# --- Classifier (lazy loaded) ---

_classifier = None

def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=None,
            device=-1,
        )
    return _classifier

# --- Classification ---

def _to_scores(emotions):
    mood = energy = tension = weight = 0.0
    for e in emotions:
        label = e["label"]
        score = e["score"]
        if label in EMOTION_MAP:
            m, en, t, w = EMOTION_MAP[label]
            mood    += score * m
            energy  += score * en
            tension += score * t
            weight  += score * w
    return {
        "mood":    round(min(mood, 100)),
        "energy":  round(min(energy, 100)),
        "tension": round(min(tension, 100)),
        "weight":  round(min(weight, 100)),
    }

def classify_synopsis_batch(texts):
    truncated = [t[:512] for t in texts]
    results = get_classifier()(truncated, batch_size=64, truncation=True)
    return [_to_scores(r) for r in results]

def classify_synopsis(text):
    result = get_classifier()(text[:512], truncation=True)
    return _to_scores(result[0])

def classify_genres(genres_str):
    if not genres_str:
        return dict(DEFAULT_SCORES)
    genres = [g.strip() for g in genres_str.split(",")]
    mood = energy = tension = weight = 0.0
    count = 0
    for g in genres:
        if g in GENRE_MAP:
            m, en, t, w = GENRE_MAP[g]
            mood += m
            energy += en
            tension += t
            weight += w
            count += 1
    if count == 0:
        return dict(DEFAULT_SCORES)
    return {
        "mood":    round(mood / count),
        "energy":  round(energy / count),
        "tension": round(tension / count),
        "weight":  round(weight / count),
    }

# --- Combined scoring ---

def _combine(synopsis_scores, genre_scores):
    genre_weight = 1 - SYNOPSIS_WEIGHT
    return {
        k: round(synopsis_scores[k] * SYNOPSIS_WEIGHT + genre_scores[k] * genre_weight)
        for k in synopsis_scores
    }

def compute_movie_emotions_batch(descriptions, genres_strs):
    synopsis_scores_list = classify_synopsis_batch(descriptions)
    results = []
    for synopsis_scores, genres_str in zip(synopsis_scores_list, genres_strs):
        genre_scores = classify_genres(genres_str)
        results.append(_combine(synopsis_scores, genre_scores))
    return results
