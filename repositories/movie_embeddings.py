def get_all(db):
  return db.execute("SELECT * FROM movie_embeddings").fetchall()

def get_embedding_by_movie_id(db, movie_id):
  return db.execute("SELECT * FROM movie_embeddings where movie_id = ?", (movie_id,)).fetchone()