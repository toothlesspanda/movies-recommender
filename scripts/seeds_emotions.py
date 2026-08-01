from db import get_connection
from services.emotions import compute_movie_emotions_batch

BATCH_SIZE = 32


def get_movies_batch(conn, limit):
    return conn.execute(
        '''
        SELECT m.id, m.description,
               (SELECT GROUP_CONCAT(g.name) FROM movie_genres mg JOIN genres g ON g.id = mg.genre_id WHERE mg.movie_id = m.id) AS genres
        FROM movies m
        LEFT JOIN movie_emotions me ON m.id = me.movie_id
        WHERE me.movie_id IS NULL
        AND m.description IS NOT NULL AND m.description != ''
        LIMIT ?
        ''',
        (limit,),
    ).fetchall()


def generate_emotions():
    print("Loading model...", flush=True)
    conn = get_connection()
    total = 0

    while True:
        movies = get_movies_batch(conn, BATCH_SIZE)
        if not movies:
            break

        descriptions = [m["description"] for m in movies]
        genres_strs = [m["genres"] for m in movies]
        scores_list = compute_movie_emotions_batch(descriptions, genres_strs)

        insert_values = []
        for movie, scores in zip(movies, scores_list):
            insert_values.append((
                movie["id"],
                scores["mood"],
                scores["energy"],
                scores["tension"],
                scores["weight"],
            ))

        conn.executemany(
            "INSERT OR IGNORE INTO movie_emotions(movie_id, mood, energy, tension, weight, model_name) VALUES (?, ?, ?, ?, ?, 'hf:distilroberta+genres')",
            insert_values,
        )
        conn.commit()

        total += len(insert_values)
        print(f"Processados: {total}", flush=True)

    conn.close()
    print(f"Done! Total: {total}")


if __name__ == "__main__":
    generate_emotions()
