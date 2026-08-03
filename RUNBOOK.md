# Runbook

## Local Development

```bash
flask run --debug
```

## Database

```bash
# VACUUM (reclaim disk space after deletes)
sqlite3 movies.db "VACUUM;"

# Stats
sqlite3 movies.db "SELECT COUNT(*) FROM movies;"
sqlite3 movies.db "SELECT COUNT(*) FROM movie_embeddings;"
sqlite3 movies.db "SELECT COUNT(*) FROM movie_emotions;"
sqlite3 movies.db "SELECT COUNT(*) FROM movie_people;"
```

## Seeding

### Movies (from TMDB)

```bash
python scripts/seeds_movies.py
```

### Emotions (HuggingFace distilroberta)

```bash
python scripts/seeds_emotions.py
```

### Embeddings (sentence-transformers all-mpnet-base-v2)

```bash
# Full regeneration (delete old + generate new + rebuild Faiss)
sqlite3 movies.db "DELETE FROM movie_embeddings;"
rm -f movies.faiss movies_faiss_ids.npy
python scripts/seeds_embeddings.py
```

### Credits (from TMDB, concurrent)

```bash
python scripts/sync_credits.py
```

## Sync

### Sync recent movies (weekly cron)

```bash
python scripts/sync_recent.py
```

## Cron (server)

```bash
# Sync recent movies every Monday at 3am
0 3 * * 1 docker exec app python scripts/sync_recent.py --days 7 >> /root/data/sync.log 2>&1
```

## Upload data to server

```bash
# Upload DB
rsync -avP movies.db root@YOUR_SERVER_IP:/root/data/

# Upload Faiss index
rsync -avP movies.faiss movies_faiss_ids.npy root@YOUR_SERVER_IP:/root/data/

# Upload all data files at once
rsync -avP movies.db movies.faiss movies_faiss_ids.npy root@YOUR_SERVER_IP:/root/data/
```

## Docker

```bash
# Build
docker build -t movies-recommender .

# Run locally
docker run -p 5000:5000 -v $(pwd):/app/data movies-recommender

# Production (behind Caddy)
docker run -d --name app -p 127.0.0.1:5000:5000 -v /root/data:/app/data --restart unless-stopped ghcr.io/toothlesspanda/movies-recommender:latest
```

## Deploy

Tag-triggered via GitHub Actions:

```bash
git tag v1.x.x
git push origin v1.x.x
```

## Server (Hetzner)

```bash
# Caddy config: /etc/caddy/Caddyfile
# Domain: luckymovie.link
# Container logs
docker logs -f app
```
