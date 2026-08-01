FROM python:3.14-slim

WORKDIR /app

# Install dependencies + download models (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "from transformers import pipeline; pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base')"
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy app code (changes here don't invalidate model cache)
COPY . .

ENV DATA_DIR=/app/data
ENV DATABASE_PATH=/app/data/movies.db

EXPOSE 5000

CMD ["gunicorn", "app:app", "-w", "2", "-b", "0.0.0.0:5000"]
