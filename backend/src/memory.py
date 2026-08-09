import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Database file will be created in the backend folder
DB_PATH = Path(__file__).parent.parent / "kisan_memory.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create the users table if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT DEFAULT 'hinglish',
            facts TEXT,
            last_interaction TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Database ready:", DB_PATH)

def get_user(user_id: str):
    """Look up a user by ID. Returns a dict or None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "language_preference": row["language_preference"],
        "facts": json.loads(row["facts"]) if row["facts"] else {},
        "last_interaction": row["last_interaction"],
    }

def save_user(user_id: str, name: str = None, language_preference: str = "hinglish", facts: dict = None):
    """Save or update a user. Asks nothing – the agent will handle permission."""
    conn = get_connection()
    cursor = conn.cursor()

    existing = get_user(user_id)
    now = datetime.utcnow().isoformat()

    if existing:
        # Update existing user
        new_name = name or existing["name"]
        new_lang = language_preference or existing["language_preference"]
        new_facts = {**existing["facts"], **(facts or {})}

        cursor.execute("""
            UPDATE users
            SET name = ?, language_preference = ?, facts = ?, last_interaction = ?
            WHERE user_id = ?
        """, (new_name, new_lang, json.dumps(new_facts), now, user_id))
    else:
        # Insert new user
        cursor.execute("""
            INSERT INTO users (user_id, name, language_preference, facts, last_interaction)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, language_preference, json.dumps(facts or {}), now))

    conn.commit()
    conn.close()
    return get_user(user_id)

# Create the table when this file is imported
init_db()