def get_all(db):
  return db.execute("SELECT * FROM movies").fetchall()

def search(db, query):
  return db.execute(
        """
        SELECT m.*, GROUP_CONCAT(g.name) AS genres
        FROM movies m
        LEFT JOIN movie_genres mg ON mg.movie_id = m.id
        LEFT JOIN genres g ON g.id = mg.genre_id
        WHERE m.title LIKE ?
        GROUP BY m.id
        ORDER BY m.popularity DESC
        LIMIT 20
        """,
        (f"%{query}%",)).fetchall()

def get_movie_by_id(db, movie_id):
  return db.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()

def get_movie_genres_by_id(db, movie_id):
  return db.execute(
        "SELECT GROUP_CONCAT(g.name) AS genres FROM movie_genres mg JOIN genres g ON g.id = mg.genre_id WHERE mg.movie_id = ?",
        (movie_id,),
    ).fetchone()
  
def get_movies_by_ids(db, movie_ids):
  placeholder_string = ",".join("?" * len(movie_ids))
  return db.execute(
        f"SELECT * FROM movies WHERE id IN ({placeholder_string})",
        movie_ids,
    ).fetchall()
  
  
def get_candidates_for_movie(db, movie_id):
  return db.execute(
        """
        SELECT m.*, GROUP_CONCAT(g.name) AS genres,
               COUNT(mg2.genre_id) AS shared_genres
        FROM movies m
        JOIN movie_genres mg ON mg.movie_id = m.id
        JOIN movie_genres mg2 ON mg2.genre_id = mg.genre_id AND mg2.movie_id = ?
        LEFT JOIN genres g ON g.id = mg.genre_id
        WHERE m.id != ?
        GROUP BY m.id
        ORDER BY shared_genres DESC, m.popularity DESC
        LIMIT 100
        """,
        (movie_id, movie_id),
    ).fetchall()
