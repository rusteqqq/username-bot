import sqlite3
from config import DATABASE_PATH

def connection():
    return sqlite3.connect(DATABASE_PATH)

def init_db():
    with connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS traps (
                username TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username, user_id)
            )
        """)
        conn.commit()
