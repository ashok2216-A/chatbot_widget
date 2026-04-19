import sqlite3
import json
import os
from datetime import datetime

# Path to the SQLite database
_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "auth.db")

def _get_conn():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if it doesn't exist."""
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_credentials (
                session_id TEXT,
                provider TEXT,
                token_json TEXT,
                updated_at DATETIMEDEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (session_id, provider)
            )
        """)
        conn.commit()

def save_token(session_id: str, provider: str, token_data: dict):
    """Saves or updates a token for a given session and provider."""
    # Ensure nested objects are handled if necessary, but usually token_data is a flat-ish dict
    token_str = json.dumps(token_data)
    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO user_credentials (session_id, provider, token_json, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(session_id, provider) DO UPDATE SET
                token_json = excluded.token_json,
                updated_at = excluded.updated_at
        """, (session_id, provider, token_str, datetime.now().isoformat()))
        conn.commit()

def get_token(session_id: str, provider: str) -> dict:
    """Retrieves the token dict for a given session and provider. Returns None if not found."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT token_json FROM user_credentials WHERE session_id = ? AND provider = ?",
            (session_id, provider)
        ).fetchone()
        if row:
            return json.loads(row["token_json"])
    return None

def delete_tokens(session_id: str):
    """Removes all tokens for a given session (Logout)."""
    with _get_conn() as conn:
        conn.execute("DELETE FROM user_credentials WHERE session_id = ?", (session_id,))
        conn.commit()

# Initialize on import
init_db()
