# db.py
import sqlite3
import os
from flask import g

DATABASE = os.environ.get("DATABASE_PATH", "movies.db")

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_db():
    if "db" not in g:
        g.db = get_connection()
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)