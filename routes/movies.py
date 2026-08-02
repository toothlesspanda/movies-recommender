import random
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


@bp.route("/api/lucky")
def api_lucky():
    mood = request.args.get("mood", 50, type=int)
    energy = request.args.get("energy", 50, type=int)
    tension = request.args.get("tension", 50, type=int)
    weight = request.args.get("weight", 50, type=int)
    genres_param = request.args.get("genres", "")
    genre_ids = [int(g) for g in genres_param.split(",") if g.strip().isdigit()]
    movie_id = request.args.get("movie_id", type=int)

    db = get_db()
    target_emotions = [mood, energy, tension, weight]

    # With source movie: use embeddings + emotions (like find_related)
    if movie_id:
        me_movie = movie_embeddings_repo.get_embedding_by_movie_id(db, movie_id)
        memo_movie = movie_emotions_repo.get_emotion_by_movie_id(db, movie_id)
        if me_movie and memo_movie:
            source_emotions = [memo_movie["mood"], memo_movie["energy"], memo_movie["tension"], memo_movie["weight"]]
            top_ids = find_related(me_movie["embedding"], movie_id, target_emotions, source_emotions, limit=300, candidates_pool=800)
            if top_ids:
                pick_id = random.choice(top_ids)
                movie = movie_repo.get_movie_detail(db, pick_id)
                if movie:
                    return jsonify(movie)

    # Without source movie: emotion-only search with genre filter
    params = [mood, energy, tension, weight]

    genre_filter = ""
    if genre_ids:
        placeholders = ",".join("?" * len(genre_ids))
        genre_filter = f"""AND EXISTS (SELECT 1 FROM movie_genres mg2
            WHERE mg2.movie_id = m.id AND mg2.genre_id IN ({placeholders}))"""
        params.extend(genre_ids)

    rows = db.execute(f"""
        SELECT m.id,
               ABS(me.mood - ?) + ABS(me.energy - ?) + ABS(me.tension - ?) + ABS(me.weight - ?) AS dist
        FROM movie_emotions me
        JOIN movies m ON m.id = me.movie_id
        WHERE m.vote_count >= 50 AND m.vote_average >= 5
        {genre_filter}
        ORDER BY dist ASC
        LIMIT 200
    """, params).fetchall()
    if not rows:
        return jsonify({"error": "No movies found"}), 404
    pick = random.choice(rows)
    movie = movie_repo.get_movie_detail(db, pick["id"])
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

    source_emotions = [source_profile["mood"], source_profile["energy"], source_profile["tension"], source_profile["weight"]]
    top_movie_ids = find_related(me_movie["embedding"], movie_id, target_emotions, source_emotions, limit=300, candidates_pool=800)
    related_rows = movie_repo.get_movies_by_ids(db, top_movie_ids)
    # Preserve ranking order from find_related
    by_id = {r["id"]: dict(r) for r in related_rows}
    related = [by_id[mid] for mid in top_movie_ids if mid in by_id][:100]

    return jsonify({
        "source": dict(movie),
        "source_emotions": dict(source_profile),
        "related": related,
    })
