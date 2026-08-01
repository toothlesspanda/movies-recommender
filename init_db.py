import sqlite3

def init_db(db_path="movies.db"):
    conn = sqlite3.connect(db_path)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tmdb_id INTEGER UNIQUE,
            title TEXT,
            description TEXT,
            original_language TEXT,
            poster_path TEXT,
            release_date DATETIME,
            vote_average FLOAT,
            vote_count INTEGER,
            popularity FLOAT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS genres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            tmdb_id INTEGER
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS movie_genres (
            movie_id INTEGER NOT NULL,
            genre_id INTEGER NOT NULL,
            PRIMARY KEY (movie_id, genre_id),
            FOREIGN KEY (movie_id) REFERENCES movies(id),
            FOREIGN KEY (genre_id) REFERENCES genres(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tmdb_id INTEGER UNIQUE,
            name TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS movie_people (
            movie_id INTEGER NOT NULL,
            person_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            character TEXT,
            display_order INTEGER,
            PRIMARY KEY (movie_id, person_id, role),
            FOREIGN KEY (movie_id) REFERENCES movies(id),
            FOREIGN KEY (person_id) REFERENCES people(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS movie_embeddings (
            movie_id INTEGER PRIMARY KEY,
            embedding BLOB NOT NULL,
            model_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (movie_id) REFERENCES movies(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS movie_emotions (
            movie_id INTEGER PRIMARY KEY,
            mood INTEGER NOT NULL,
            energy INTEGER NOT NULL,
            tension INTEGER NOT NULL,
            weight INTEGER NOT NULL,
            model_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (movie_id) REFERENCES movies(id)
        )
    """)

    # Indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_movie_genres_movie ON movie_genres(movie_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_movie_genres_genre ON movie_genres(genre_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_movie_people_movie ON movie_people(movie_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_movie_people_person ON movie_people(person_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_movie_people_role ON movie_people(role)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_movies_tmdb ON movies(tmdb_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_movies_title ON movies(title)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_people_tmdb ON people(tmdb_id)")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS sync_state (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("Base de dados inicializada.")


if __name__ == "__main__":
    init_db()