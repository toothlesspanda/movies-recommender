"""Re-fetch credits from TMDB for movies missing crew data (concurrent version)."""
import time
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_connection
from services.tmdb_client import get_credits, RateLimitError

WORKERS = 10
BATCH_SIZE = 500
RATE_LIMIT_SLEEP = 5
FAILED_IDS_FILE = "failed_credits.txt"


rate_limits = 0


def fetch_credits(row):
    """Fetch credits from TMDB (HTTP only, no DB). Returns (row, credits) or (row, error)."""
    global rate_limits
    try:
        credits = get_credits(row["tmdb_id"])
        return (row, credits)
    except RateLimitError:
        rate_limits += 1
        print(f"  429 rate limited on {row['tmdb_id']}, sleeping {RATE_LIMIT_SLEEP}s...", flush=True)
        time.sleep(RATE_LIMIT_SLEEP)
        try:
            credits = get_credits(row["tmdb_id"])
            return (row, credits)
        except Exception as e:
            return (row, e)
    except Exception as e:
        return (row, e)


def save_credits_from_data(conn, movie_id, credits):
    """Save pre-fetched credits to DB (sequential, no HTTP)."""
    from scripts.seeds_movies import _upsert_person, MAX_CAST

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



def sync_missing_credits():
    conn = get_connection()

    rows = conn.execute("""
        SELECT m.id, m.tmdb_id, m.title
        FROM movies m
        WHERE NOT EXISTS (SELECT 1 FROM movie_people mp WHERE mp.movie_id = m.id)
        ORDER BY m.vote_count DESC
    """).fetchall()

    total = len(rows)
    print(f"Found {total} movies without credits. Using {WORKERS} workers.")

    done = 0
    errors = 0
    rate_limits = 0
    failed_ids = []
    start = time.time()

    # Process in chunks — fetch in parallel, write sequentially
    chunk_size = WORKERS * 4
    for i in range(0, total, chunk_size):
        chunk = rows[i:i + chunk_size]

        # Parallel HTTP fetches
        results = []
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            futures = {executor.submit(fetch_credits, row): row for row in chunk}
            for future in as_completed(futures):
                results.append(future.result())

        # Sequential DB writes (no commit per movie)
        for row, credits_or_error in results:
            if isinstance(credits_or_error, Exception):
                failed_ids.append(f"{row['id']},{row['tmdb_id']}")
                errors += 1
            else:
                try:
                    save_credits_from_data(conn, row["id"], credits_or_error)
                except Exception:
                    failed_ids.append(f"{row['id']},{row['tmdb_id']}")
                    errors += 1
            done += 1

        # Commit once per chunk instead of per movie
        conn.commit()

        if done % BATCH_SIZE < chunk_size:
            elapsed = time.time() - start
            rate = done / elapsed
            remaining = (total - done) / rate / 3600
            print(f"  {done}/{total} ({done*100//total}%) | {rate:.1f} req/s | ~{remaining:.1f}h remaining | {errors} errors | {rate_limits} rate limits", flush=True)

    conn.close()
    elapsed = time.time() - start
    print(f"Done. {done} processed, {errors} errors, {elapsed/3600:.1f}h total.")

    if failed_ids:
        with open(FAILED_IDS_FILE, "w") as f:
            f.write("\n".join(failed_ids))
        print(f"Failed IDs saved to {FAILED_IDS_FILE} ({len(failed_ids)} entries)")


if __name__ == "__main__":
    sync_missing_credits()
