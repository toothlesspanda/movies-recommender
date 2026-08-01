import time
from db import get_connection
from services.tmdb_client import get_genres, get_movies, get_credits

CREDITS_SLEEP = 0.25
CREDITS_MIN_VOTES = 10
MAX_CAST = 10


def seed_genres():
    conn = get_connection()
    genres = get_genres()

    for genre in genres:
        conn.execute(
            "INSERT OR IGNORE INTO genres (tmdb_id, name) VALUES (?, ?)",
            (genre["id"], genre["name"]),
        )

    conn.commit()
    conn.close()
    print(f"Seeded {len(genres)} genres.")


def get_sync_state(conn):
    row = conn.execute(
        "SELECT value FROM sync_state WHERE key = 'movies_sync'"
    ).fetchone()
    if row:
        parts = row["value"].split(",")
        return int(parts[0]), int(parts[1]), int(parts[2])
    return None, None, 0


def set_sync_state(conn, year, month, page):
    conn.execute(
        "INSERT OR REPLACE INTO sync_state (key, value) VALUES ('movies_sync', ?)",
        (f"{year},{month},{page}",),
    )
    conn.commit()


def save_movies(conn, movies, fetch_credits=True):
    for movie in movies:
        cursor = conn.execute(
            """INSERT OR IGNORE INTO movies
               (tmdb_id, title, description, original_language, poster_path,
                release_date, vote_average, vote_count, popularity)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                movie["id"],
                movie["title"],
                movie["overview"],
                movie["original_language"],
                movie["poster_path"],
                movie["release_date"],
                movie["vote_average"],
                movie["vote_count"],
                movie["popularity"],
            ),
        )

        is_new = cursor.rowcount > 0
        if is_new:
            movie_id = cursor.lastrowid
        else:
            row = conn.execute("SELECT id FROM movies WHERE tmdb_id = ?", (movie["id"],)).fetchone()
            movie_id = row["id"]

        for genre_tmdb_id in movie["genre_ids"]:
            genre_row = conn.execute(
                "SELECT id FROM genres WHERE tmdb_id = ?", (genre_tmdb_id,)
            ).fetchone()
            if genre_row:
                conn.execute(
                    "INSERT OR IGNORE INTO movie_genres (movie_id, genre_id) VALUES (?, ?)",
                    (movie_id, genre_row["id"]),
                )

        # Fetch credits only for movies with enough votes
        if fetch_credits and movie.get("vote_count", 0) >= CREDITS_MIN_VOTES:
            has_credits = conn.execute(
                "SELECT 1 FROM movie_people WHERE movie_id = ? LIMIT 1", (movie_id,)
            ).fetchone()
            if not has_credits:
                save_credits(conn, movie_id, movie["id"])
                time.sleep(CREDITS_SLEEP)


    conn.commit()


def save_credits(conn, movie_id, movie_tmdb_id):
    try:
        credits = get_credits(movie_tmdb_id)
    except Exception as e:
        print(f"  credits error for tmdb_id {movie_tmdb_id}: {e}")
        return

    # Top cast
    for member in credits["cast"][:MAX_CAST]:
        person_id = _upsert_person(conn, member["id"], member["name"])
        conn.execute(
            "INSERT OR IGNORE INTO movie_people (movie_id, person_id, role, character, display_order) VALUES (?, ?, 'actor', ?, ?)",
            (movie_id, person_id, member.get("character", ""), member.get("order", 0)),
        )

    # Director(s)
    for member in credits["crew"]:
        if member.get("job") == "Director":
            person_id = _upsert_person(conn, member["id"], member["name"])
            conn.execute(
                "INSERT OR IGNORE INTO movie_people (movie_id, person_id, role, character, display_order) VALUES (?, ?, 'director', NULL, 0)",
                (movie_id, person_id),
            )

    conn.commit()


def _upsert_person(conn, tmdb_id, name):
    row = conn.execute("SELECT id FROM people WHERE tmdb_id = ?", (tmdb_id,)).fetchone()
    if row:
        return row["id"]
    cursor = conn.execute(
        "INSERT INTO people (tmdb_id, name) VALUES (?, ?)", (tmdb_id, name)
    )
    return cursor.lastrowid


import calendar

START_YEAR = 2000
END_YEAR = 1975


def date_range_for_month(year, month):
    last_day = calendar.monthrange(year, month)[1]
    return f"{year}-{month:02d}-01", f"{year}-{month:02d}-{last_day:02d}"


def fetch_movies_loop(interval=1):
    """Fetches movies year by year, month by month (newest first). Ctrl+C to stop and resume later."""
    print(f"Starting movie fetch loop (1 page every {interval}s)...")

    try:
        conn = get_connection()
        last_year, last_month, last_page = get_sync_state(conn)
        conn.close()

        year = last_year or START_YEAR
        month = last_month or 12
        page = last_page + 1

        while year >= END_YEAR:
            date_gte, date_lte = date_range_for_month(year, month)
            data = get_movies(page=page, date_gte=date_gte, date_lte=date_lte)
            total_pages = data["total_pages"]

            if total_pages == 0 or page > total_pages:
                if month == 1:
                    print(f"{year} done.", flush=True)
                month -= 1
                if month < 1:
                    month = 12
                    year -= 1
                page = 1
                conn = get_connection()
                set_sync_state(conn, year, month, 0)
                conn.close()
                continue

            conn = get_connection()
            save_movies(conn, data["results"])
            set_sync_state(conn, year, month, page)
            conn.close()

            page += 1
            time.sleep(interval)

        print("All years fetched!")
    except KeyboardInterrupt:
        print("\nStopped. Will resume from where it left off.")


if __name__ == "__main__":
    seed_genres()
    fetch_movies_loop()