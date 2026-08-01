# Project Context — Movies Recommender

## Overview

A movie and TV series recommendation system inspired by the
[Chosic Playlist Generator](https://www.chosic.com/playlist-generator/), but for
audiovisual content instead of music.

**Core idea:** the user provides a starting point (a movie, via an IMDb link or
name search) and the system returns similar recommendations that can be fine-tuned
through criteria such as:

- Genres (include / exclude)
- Release year (how old / recent)
- Popularity (how mainstream vs. niche)
- Other criteria TBD (original language, rating, etc.)

**Secondary goals:**

- **Brush up on Python** — the project also serves as a language relearning exercise.
- **Go online** — it should end up published and accessible on the web.
- **Explore ML / LLMs** — the recommendation engine will use machine learning
  techniques and/or LLMs (see Recommendation Engine section).

## Target Architecture

```
┌──────────────────┐      ┌─────────────────────┐      ┌──────────────────┐
│  TMDB API        │──────▶  Ingestion (batch)  │──────▶  Database        │
│  (data source)   │      │  collects movies    │      │  SQLite → Supabase│
└──────────────────┘      └─────────────────────┘      └────────┬─────────┘
                                                                 │
                          ┌─────────────────────┐                │
                          │  Recommendation     │◀───────────────┘
                          │  engine (ML)        │
                          └──────────┬──────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  API / Web UI       │
                          │  (Flask + frontend) │
                          └─────────────────────┘
```

## Components

### Data Ingestion (batch backend)

A process that runs periodically, collecting all movies (and later TV series) from
the [TMDB API](https://developer.themoviedb.org/docs) and storing them in the
database. Populates movies, genres, and the movie-genre relationship.

### Database

Starts with **SQLite3** (fast to prototype, zero setup). Should migrate to
**Supabase** (Postgres) when the project goes to production / online, mainly
because of: concurrent access, managed hosting, and potential use of **pgvector**
for embedding-based search.

### Recommendation Engine

Given a starting movie + criteria, returns similar movies. Approaches to explore
(from simplest to most advanced):

1. **Metadata filtering** (shared genres, year, popularity).
2. **Embedding similarity** on synopses / metadata (semantic search).
3. **LLM usage** to re-rank or explain recommendations.

### Web Interface + API

Flask backend exposing endpoints (e.g. `/movies`). Simple frontend for:

- Adding a movie via IMDb link or name search;
- Adjusting sliders/filters (genres, release year, popularity);
- Viewing the resulting recommendations.

## Tech Stack

| Layer         | Current              | Future / TBD                       |
|---------------|----------------------|------------------------------------|
| Language      | Python               | —                                  |
| Web framework | Flask                | —                                  |
| Database      | SQLite3              | Supabase (Postgres + pgvector)     |
| Data source   | TMDB API             | + IMDb (for input links)           |
| Embeddings/ML | (TBD)                | sentence-transformers / LLM        |
| Hosting       | (TBD)                | Cloud platform + Supabase          |
| Config        | .env + python-dotenv | —                                  |

## Current Code State

An initial skeleton already exists:

- **app.py** — Minimal Flask app with a `GET /movies` endpoint that lists movies
  from the DB.
- **db.py** — SQLite connection using Flask's context pattern (`get_db`,
  `close_db`, `init_app`).
- **init_db.py** — Creates the schema: tables `movies`, `genres`, and the
  junction table `movie_genres`.
- **config.py** — Loads `TMDB_ACCESS_TOKEN` from `.env`.
- **services/tmdb_client.py** — TMDB client (draft: `get_genres`, `get_movies`).
- **models/movie.py** — `Movie` model with `create`, `find_by_tmdb_id`, `all`.
- **models/genre.py** — Empty (not yet implemented).
- **seeds_movies.py** — Seeding draft (incomplete / broken).
- **movies.db** — Existing SQLite file.

### Current Schema (init_db.py)

- **movies:** `id`, `title`, `description`, `original_language`, `poster_path`,
  `release_date`, `vote_average`, `vote_count`, `popularity`.
- **genres:** `id`, `name` (unique), `tmdb_id`.
- **movie_genres:** `movie_id`, `genre_id` (composite key, FKs).

## Known Issues / Things to Fix

- **services/tmdb_client.py:** methods call `requests.get(...)` but have no
  `return`; also missing `self` or `@staticmethod`. The `get_movies` endpoint uses
  `/movie?page=` which doesn't exist — the correct path is `/movie/popular` or
  `/discover/movie`.
- **models/movie.py:** `create` only inserts `tmdb_id`, `title`, `description`,
  but the schema has no `tmdb_id` column; there's a mismatch between the model and
  the schema.
- **seeds_movies.py:** broken (invalid SQL, imports of non-existent modules like
  `services.embeddings`, `@app.route` out of context). Needs a rewrite.
- **models/genre.py** is empty.
- No `requirements.txt` / dependency management.

## Suggested Next Steps

1. **Stabilize the schema and models** — decide on `tmdb_id` in `movies`, align
   `Movie.create` with the actual columns, implement `models/genre.py`.
2. **Finish the TMDB client** — add `return` statements, fix endpoints, handle
   pagination and errors.
3. **Write a working seed script** — fetch genres and a first page of popular
   movies into the DB.
4. **Add `requirements.txt`** (flask, requests, python-dotenv, ...).
5. **Recommendation v0** — simple filter by genres + popularity + year.
6. **Recommendation v1** — synopsis embeddings and similarity search.
7. **Minimal frontend** — movie search + criteria sliders.
8. **Migrate to Supabase** and deploy online.

## UI Design

**Single-page application** (no detail pages, no multi-page navigation):

- **Search bar** centered on the page — the user types a movie name and picks from
  an autocomplete dropdown.
- **Source movie banner** — shows the selected movie (poster, title, genres).
- **Recommendation mixer** — a set of sliders/controls that allow the user to
  fine-tune the recommendations. Parameters TBD but may include: popularity
  (niche vs mainstream), release year (classic vs recent), rating threshold,
  genre weight, actor/thematic similarity, etc.
- **Related movies grid** — displays recommended movies based on shared genres
  and (later) other criteria from the mixer.

Clicking a related movie re-runs the recommendation from that movie, keeping the
user on the same page.

## Recommendation Engine (future)

The mixer sliders will eventually drive a recommendation engine that combines:

1. **Metadata filtering** — shared genres, year range, popularity band.
2. **Embedding similarity** — semantic search on synopses / metadata using
   sentence-transformers or similar.
3. **LLM re-ranking** — an LLM layer to re-rank or explain recommendations
   based on thematic/tonal similarity, actor overlap, director style, etc.

This is exploratory — the goal is to experiment with ML/LLM-backed
recommendations, not to build a production-grade engine from day one.

## References

- Inspiration: https://www.chosic.com/playlist-generator/
- TMDB API: https://developer.themoviedb.org/docs
- Supabase: https://supabase.com/docs
- pgvector: https://github.com/pgvector/pgvector
