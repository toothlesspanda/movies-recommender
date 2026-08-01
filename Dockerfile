FROM python:3.14-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Download HuggingFace models at build time (cached in image)
RUN python -c "from transformers import pipeline; pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base')"
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

ENV DATA_DIR=/app/data
ENV DATABASE_PATH=/app/data/movies.db

EXPOSE 5000

CMD ["gunicorn", "app:app", "-w", "2", "-b", "0.0.0.0:5000"]
