"""
Sync recent movies from TMDB: fetch, save, generate emotions + embeddings, update Faiss.
Usage: python sync_recent.py [--days 21]
"""
import argparse
import time
from datetime import datetime, timedelta
from db import get_connection
from services.tmdb_client import get_movies, get_credits
from services.emotions import compute_movie_emotions_batch
from services.embeddings import (
    build_input_text, generate_embeddings_batch,
    store_embeddings_batch, save_faiss,
)

MAX_CAST = 10
CREDITS_SLEEP = 0.25
CREDITS_MIN_VOTES = 10


def _upsert_person(conn, tmdb_id, name):
    row = conn.execute("SELECT id FROM people WHERE tmdb_id = ?", (tmdb_id,)).fetchone()
    if row:
        return row["id"]
    cursor = conn.execute("INSERT INTO people (tmdb_id, name) VALUES (?, ?)", (tmdb_id, name))
    return cursor.lastrowid


def save_credits(conn, movie_id, movie_tmdb_id):
    try:
        credits = get_credits(movie_tmdb_id)
    except Exception as e:
        print(f"  credits error for tmdb_id {movie_tmdb_id}: {e}")
        return

    for member in credits["cast"][:MAX_CAST]:
        person_id = _upsert_person(conn, member["id"], member["name"])
        conn.execute(
            "INSERT OR IGNORE INTO movie_people (movie_id, person_id, role, character, display_order) VALUES (?, ?, 'actor', ?, ?)",
            (movie_id, person_id, member.get("character", ""), member.get("order", 0)),
        )

    for member in credits["crew"]:
        if member.get("job") == "Director":
            person_id = _upsert_person(conn, member["id"], member["name"])
            conn.execute(
                "INSERT OR IGNORE INTO movie_people (movie_id, person_id, role, character, display_order) VALUES (?, ?, 'director', NULL, 0)",
                (movie_id, person_id),
            )


def save_movie(conn, movie):
    cursor = conn.execute(
        """INSERT OR IGNORE INTO movies
           (tmdb_id, title, description, original_language, poster_path,
            release_date, vote_average, vote_count, popularity)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            movie["id"], movie["title"], movie["overview"],
            movie["original_language"], movie["poster_path"],
            movie["release_date"], movie["vote_average"],
            movie["vote_count"], movie["popularity"],
        ),
    )

    is_new = cursor.rowcount > 0
    if is_new:
        movie_id = cursor.lastrowid
    else:
        row = conn.execute("SELECT id FROM movies WHERE tmdb_id = ?", (movie["id"],)).fetchone()
        movie_id = row["id"]

    for genre_tmdb_id in movie["genre_ids"]:
        genre_row = conn.execute("SELECT id FROM genres WHERE tmdb_id = ?", (genre_tmdb_id,)).fetchone()
        if genre_row:
            conn.execute(
                "INSERT OR IGNORE INTO movie_genres (movie_id, genre_id) VALUES (?, ?)",
                (movie_id, genre_row["id"]),
            )

    if movie.get("vote_count", 0) >= CREDITS_MIN_VOTES:
        has_credits = conn.execute(
            "SELECT 1 FROM movie_people WHERE movie_id = ? LIMIT 1", (movie_id,)
        ).fetchone()
        if not has_credits:
            save_credits(conn, movie_id, movie["id"])
            time.sleep(CREDITS_SLEEP)

    return movie_id, is_new


def enrich_movie(conn, movie_id):
    return conn.execute(
        '''
        SELECT
            (SELECT GROUP_CONCAT(g.name) FROM movie_genres mg JOIN genres g ON g.id = mg.genre_id WHERE mg.movie_id = ?) AS genres,
            (SELECT GROUP_CONCAT(p.name) FROM movie_people mp JOIN people p ON p.id = mp.person_id WHERE mp.movie_id = ? AND mp.role = 'actor') AS actors,
            (SELECT GROUP_CONCAT(p.name) FROM movie_people mp JOIN people p ON p.id = mp.person_id WHERE mp.movie_id = ? AND mp.role = 'director') AS directors
        ''',
        (movie_id, movie_id, movie_id),
    ).fetchone()


def process_enrichments(conn, new_movies):
    """Generate emotions + embeddings for new movies."""
    if not new_movies:
        return

    # Filter movies with descriptions
    valid = [(mid, m) for mid, m in new_movies if m.get("overview")]
    if not valid:
        return

    movie_ids = [mid for mid, _ in valid]

    # Emotions
    descriptions = [m["overview"] for _, m in valid]
    genres_strs = []
    for mid, _ in valid:
        row = conn.execute(
            "SELECT GROUP_CONCAT(g.name) FROM movie_genres mg JOIN genres g ON g.id = mg.genre_id WHERE mg.movie_id = ?",
            (mid,),
        ).fetchone()
        genres_strs.append(row[0] if row else None)

    emotions_list = compute_movie_emotions_batch(descriptions, genres_strs)

    for mid, emotions in zip(movie_ids, emotions_list):
        conn.execute(
            "INSERT OR IGNORE INTO movie_emotions(movie_id, mood, energy, tension, weight, model_name) VALUES (?, ?, ?, ?, ?, 'hf:distilroberta+genres')",
            (mid, emotions["mood"], emotions["energy"], emotions["tension"], emotions["weight"]),
        )

    # Embeddings
    texts = []
    for mid, m in valid:
        extra = enrich_movie(conn, mid)
        texts.append(build_input_text(
            m["title"], extra["genres"], extra["directors"], extra["actors"], m["overview"],
        ))

    vectors = generate_embeddings_batch(texts)
    store_embeddings_batch(conn, movie_ids, vectors)

    conn.commit()
    print(f"  Enriched {len(movie_ids)} movies (emotions + embeddings)")


def sync(days=21):
    date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    date_to = datetime.now().strftime("%Y-%m-%d")
    print(f"Syncing movies from {date_from} to {date_to}...")

    conn = get_connection()
    total_new = 0
    page = 1

    while True:
        data = get_movies(page=page, date_gte=date_from, date_lte=date_to)
        if not data["results"]:
            break

        new_movies = []
        for movie in data["results"]:
            movie_id, is_new = save_movie(conn, movie)
            if is_new:
                new_movies.append((movie_id, movie))

        conn.commit()
        process_enrichments(conn, new_movies)

        total_new += len(new_movies)
        print(f"Page {page}/{data['total_pages']} — {len(new_movies)} new movies")

        if page >= data["total_pages"]:
            break
        page += 1
        time.sleep(1)

    # Save Faiss index
    save_faiss()
    conn.close()
    print(f"Done! {total_new} new movies synced.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=21, help="Number of days to look back")
    args = parser.parse_args()
    sync(days=args.days)
