from flask import Blueprint, request, jsonify
from db import get_db
import repositories.movies as movie_repo
import repositories.movie_embeddings as movie_embeddings_repo
import repositories.movie_emotions as movie_emotions_repo
from services.recommendation import find_related

bp = Blueprint("movies", __name__)


@bp.route("/movies")
def movies():
    db = get_db()
    result = movie_repo.get_all(db)
    return {"movies": [dict(m) for m in result]}


@bp.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    db = get_db()
    rows = movie_repo.search(db, q)
    return jsonify([dict(r) for r in rows])


@bp.route("/api/movies/<int:movie_id>")
def api_movie_detail(movie_id):
    db = get_db()
    movie = movie_repo.get_movie_detail(db, movie_id)
    if not movie:
        return jsonify({"error": "Movie not found"}), 404
    return jsonify(movie)


@bp.route("/api/related/<int:movie_id>")
def api_related(movie_id):
    db = get_db()
    movie = movie_repo.get_movie_by_id(db, movie_id)
    if not movie:
        return jsonify({"error": "Movie not found"}), 404

    me_movie = movie_embeddings_repo.get_embedding_by_movie_id(db, movie_id)
    if not me_movie:
        return jsonify({"error": "Embedding not found"}), 404

    memo_movie = movie_emotions_repo.get_emotion_by_movie_id(db, movie_id)
    source_profile = memo_movie

    target_emotions = [
        request.args.get("mood", source_profile["mood"], type=int),
        request.args.get("energy", source_profile["energy"], type=int),
        request.args.get("tension", source_profile["tension"], type=int),
        request.args.get("weight", source_profile["weight"], type=int),
    ]

    top_movie_ids = find_related(me_movie["embedding"], movie_id, target_emotions, limit=100, candidates_pool=400)
    related_rows = movie_repo.get_movies_by_ids(db, top_movie_ids)
    # Preserve ranking order from find_related
    by_id = {r["id"]: dict(r) for r in related_rows}
    related = [by_id[mid] for mid in top_movie_ids if mid in by_id]

    return jsonify({
        "source": dict(movie),
        "source_emotions": dict(source_profile),
        "related": related,
    })
