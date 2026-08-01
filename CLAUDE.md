# CLAUDE.md — Movies Recommender

## Project Summary

Movie/series recommendation system. User provides a movie (IMDb link or name search), system returns similar movies filtered by genres, year, popularity, etc. Inspired by Chosic Playlist Generator.

## Tech Stack

- **Language:** Python
- **Web framework:** Flask
- **Database:** SQLite3 (will migrate to Supabase/Postgres + pgvector)
- **Data source:** TMDB API
- **Config:** `.env` + `python-dotenv`

## Project Structure

```
app.py                  # Flask app, GET /movies endpoint
db.py                   # SQLite connection (get_db, close_db, init_app)
init_db.py              # Schema creation (movies, genres, movie_genres)
config.py               # Loads TMDB_ACCESS_TOKEN from .env
seeds_movies.py         # DB seeding script (needs rewrite)
movies.db               # SQLite database file
models/
  movie.py              # Movie model (create, find_by_tmdb_id, all)
  genre.py              # Genre model (empty, needs implementation)
services/
  tmdb_client.py        # TMDB API client (get_genres, get_movies)
context.md              # Full project context and architecture docs
```

## Database Schema

- **movies:** id, title, description, original_language, poster_path, release_date, vote_average, vote_count, popularity
- **genres:** id, name (unique), tmdb_id
- **movie_genres:** movie_id, genre_id (composite PK, FKs)

## Known Issues

- `tmdb_client.py`: missing return statements, wrong API endpoints, missing self/@staticmethod
- `movie.py`: model/schema mismatch (create uses tmdb_id but schema lacks it)
- `seeds_movies.py`: broken, needs full rewrite
- `genre.py`: empty
- No `requirements.txt`

## Commands

```bash
# Run the Flask app
flask run

# Initialize the database
python init_db.py

# Seed movies (currently broken)
python seeds_movies.py
```

## Environment Variables

- `TMDB_ACCESS_TOKEN` — required, loaded from `.env`

## Conventions

- Use raw SQL with SQLite (no ORM)
- Models go in `models/`, services in `services/`
- Context pattern for DB connections (Flask's g object)
