from db import get_connection
from services.embeddings import generate_embeddings_batch, store_embeddings_batch, save_faiss, build_input_text

BATCH_SIZE = 100


def get_pending_ids(conn):
  return [r[0] for r in conn.execute(
      '''
      SELECT m.id FROM movies m
      WHERE m.id NOT IN (SELECT movie_id FROM movie_embeddings)
      AND m.description IS NOT NULL AND m.description != ''
      '''
  ).fetchall()]


def get_movies_by_ids(conn, ids):
  placeholders = ','.join('?' * len(ids))
  return conn.execute(
      f'''
      SELECT m.id, m.title, m.description,
             (SELECT GROUP_CONCAT(g.name) FROM movie_genres mg JOIN genres g ON g.id = mg.genre_id WHERE mg.movie_id = m.id) AS genres,
             (SELECT GROUP_CONCAT(p.name) FROM movie_people mp JOIN people p ON p.id = mp.person_id WHERE mp.movie_id = m.id AND mp.role = 'actor') AS actors,
             (SELECT GROUP_CONCAT(p.name) FROM movie_people mp JOIN people p ON p.id = mp.person_id WHERE mp.movie_id = m.id AND mp.role = 'director') AS directors
      FROM movies m
      WHERE m.id IN ({placeholders})
      ''',
      ids,
  ).fetchall()


def generate_embedding():
  conn = get_connection()
  print("Fetching pending IDs...", flush=True)
  pending_ids = get_pending_ids(conn)
  total_pending = len(pending_ids)
  print(f"{total_pending} movies to process", flush=True)

  count = 0
  for i in range(0, total_pending, BATCH_SIZE):
    batch_ids = pending_ids[i:i + BATCH_SIZE]
    movies = get_movies_by_ids(conn, batch_ids)

    inputs = []
    movie_ids = []
    for movie in movies:
      inputs.append(build_input_text(
          movie['title'], movie['genres'], movie['directors'],
          movie['actors'], movie['description'],
      ))
      movie_ids.append(movie["id"])

    vectors = generate_embeddings_batch(inputs)
    store_embeddings_batch(conn, movie_ids, vectors)
    conn.commit()

    count += len(movie_ids)
    print(f"{count}/{total_pending} embeddings generated", flush=True)

  save_faiss()
  print(f"Done. {count} total embeddings generated.")
  conn.close()

if __name__ == "__main__":
  generate_embedding()
