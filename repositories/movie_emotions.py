def get_all(db):
  return db.execute("SELECT * FROM movie_emotions ORDER BY movie_id").fetchall()

def get_emotion_by_movie_id(db, movie_id):
  return db.execute("SELECT * FROM movie_emotions where movie_id = ?", (movie_id,)).fetchone()