def get_all(db):
  return db.execute("SELECT * FROM movies").fetchall()

def search(db, query):
  return db.execute(
        """
        SELECT m.*, GROUP_CONCAT(g.name) AS genres,
               CASE
                 WHEN m.title = ? THEN 3
                 WHEN m.title LIKE ? THEN 2
                 ELSE 1
               END AS match_rank
        FROM movies m
        LEFT JOIN movie_genres mg ON mg.movie_id = m.id
        LEFT JOIN genres g ON g.id = mg.genre_id
        WHERE m.title LIKE ?
        GROUP BY m.id
        ORDER BY match_rank DESC, m.popularity DESC
        LIMIT 20
        """,
        (query, f"{query}%", f"%{query}%")).fetchall()

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
        f"""SELECT m.*, GROUP_CONCAT(g.name) AS genres
        FROM movies m
        LEFT JOIN movie_genres mg ON mg.movie_id = m.id
        LEFT JOIN genres g ON g.id = mg.genre_id
        WHERE m.id IN ({placeholder_string})
        GROUP BY m.id""",
        movie_ids,
    ).fetchall()
  
  
def get_movie_detail(db, movie_id):
  movie = db.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()
  if not movie:
    return None
  m = dict(movie)
  genres = db.execute(
    "SELECT g.name FROM movie_genres mg JOIN genres g ON g.id = mg.genre_id WHERE mg.movie_id = ?",
    (movie_id,),
  ).fetchall()
  m["genres"] = ", ".join(r["name"] for r in genres)
  directors = db.execute(
    "SELECT p.name FROM movie_people mp JOIN people p ON p.id = mp.person_id WHERE mp.movie_id = ? AND mp.role = 'director'",
    (movie_id,),
  ).fetchall()
  m["directors"] = ", ".join(r["name"] for r in directors)
  actors = db.execute(
    "SELECT p.name FROM movie_people mp JOIN people p ON p.id = mp.person_id WHERE mp.movie_id = ? AND mp.role = 'actor' ORDER BY mp.display_order LIMIT 5",
    (movie_id,),
  ).fetchall()
  m["actors"] = ", ".join(r["name"] for r in actors)
  return m


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
