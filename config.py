# config.py
import os
from dotenv import load_dotenv

load_dotenv()

TMDB_ACCESS_TOKEN = os.environ["TMDB_ACCESS_TOKEN"]