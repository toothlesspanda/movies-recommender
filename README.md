# Movies Recommender

Movie recommendation system that finds similar movies based on factual similarity (plot, cast, genres) and emotional profile (mood, energy, tension, weight).

## How it works

1. User searches for a movie
2. System finds similar movies using two layers:
   - **Factual similarity** — embeddings of title, synopsis, genres, cast, director (via sentence-transformers)
   - **Emotional similarity** — mood/energy/tension/weight scores derived from synopsis (HuggingFace) + genres
3. User can adjust emotion sliders (mixer) to shift recommendations towards a different vibe

## Tech Stack

- **Backend:** Python, Flask, Gunicorn
- **Database:** SQLite
- **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`)
- **Emotion classification:** HuggingFace (`j-hartmann/emotion-english-distilroberta-base`)
- **Vector search:** Faiss
- **Data source:** TMDB API

## Project Structure

```
app.py                  # Flask app setup
db.py                   # SQLite connection
config.py               # Environment variables
constants.py            # Emotion/genre mappings
init_db.py              # Schema creation
routes/
  movies.py             # API endpoints (search, related)
services/
  recommendation.py     # Faiss + emotion scoring logic
  emotions.py           # Synopsis + genre emotion classification
  embeddings.py         # Embedding generation + Faiss index management
  similarity.py         # Cosine similarity
repositories/
  movies.py             # Movie queries
  movie_embeddings.py   # Embedding queries
  movie_emotions.py     # Emotion queries
scripts/
  seeds_movies.py       # Seed movies from TMDB
  seeds_emotions.py     # Generate emotion scores
  seeds_embeddings.py   # Generate embeddings + Faiss index
  sync_recent.py        # Sync recent movies (fetch + emotions + embeddings)
templates/              # HTML templates
static/                 # CSS, JS
```

## Setup

### Requirements

- Python 3.14
- TMDB API token

### Install

```bash
pip install -r requirements.txt
```

### Environment

Create a `.env` file:

```
TMDB_ACCESS_TOKEN=your_token_here
```

### Initialize database

```bash
python init_db.py
```

### Seed data

```bash
python scripts/seeds_movies.py        # Fetch movies from TMDB
python scripts/seeds_emotions.py      # Generate emotion profiles
python scripts/seeds_embeddings.py    # Generate embeddings + Faiss index
```

### Run

```bash
# Development
flask run

# Production
gunicorn app:app -w 2 -b 0.0.0.0:5000
```

### Docker

```bash
docker build -t movies-recommender .
docker run -p 8080:5000 -v $(pwd):/app/data movies-recommender
```

### Sync recent movies

```bash
python scripts/sync_recent.py           # Last 21 days
python scripts/sync_recent.py --days 7  # Last 7 days
```

## API

### `GET /api/search?q=<query>`
Search movies by title.

### `GET /api/related/<movie_id>?mood=50&energy=50&tension=50&weight=50`
Get similar movies. Optional emotion parameters override the source movie's profile.
