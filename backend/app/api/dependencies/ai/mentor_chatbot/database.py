import json
import logging
import os
import sqlite3
from typing import Any

logger = logging.getLogger(__name__)

# Get the directory of the current script
DB_DIR = os.path.dirname(os.path.abspath(__file__))
# Define the database name
DB_NAME = os.path.join(DB_DIR, "mentor_app.db")


def get_db_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    """Create required database tables."""
    conn = get_db_connection()

    # Chat history table
    conn.execute(
        """CREATE TABLE IF NOT EXISTS chat_history
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     session_id TEXT,
                     user_query TEXT,
                     mentor_response TEXT,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
    )

    # Session context table - updated to include user details
    conn.execute(
        """CREATE TABLE IF NOT EXISTS session_context
                    (session_id TEXT PRIMARY KEY,
                     user_name TEXT,
                     age INTEGER,
                     current_diary_entry TEXT,
                     past_summaries TEXT,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
    )

    conn.commit()
    conn.close()
    logger.info("Database tables created successfully")


def store_session_context(
    session_id: str,
    user_name: str,
    age: int,
    current_diary_entry: str,
    past_summaries: list[str],
):
    """Store session context in database."""
    conn = get_db_connection()
    # Convert past_summaries list to JSON string for storage
    past_summaries_json = json.dumps(past_summaries)

    conn.execute(
        """INSERT OR REPLACE INTO session_context
           (session_id, user_name, age, current_diary_entry, past_summaries)
           VALUES (?, ?, ?, ?, ?)""",
        (session_id, user_name, age, current_diary_entry, past_summaries_json),
    )
    conn.commit()
    conn.close()
    logger.info(f"Session context stored for session: {session_id}")


def get_session_context(session_id: str) -> dict[str, Any] | None:
    """Get session context from database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT user_name, age, current_diary_entry, past_summaries
           FROM session_context WHERE session_id = ?""",
        (session_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        # Convert JSON string back to list
        past_summaries = (
            json.loads(row["past_summaries"]) if row["past_summaries"] else []
        )

        return {
            "user_name": row["user_name"],
            "age": row["age"],
            "current_diary_entry": row["current_diary_entry"],
            "past_summaries": past_summaries,
        }
    return None


def insert_chat_message(session_id: str, user_query: str, mentor_response: str):
    """Insert chat message into database."""
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO chat_history (session_id, user_query, mentor_response) VALUES (?, ?, ?)",
        (session_id, user_query, mentor_response),
    )
    conn.commit()
    conn.close()
    logger.info(f"Chat message stored for session: {session_id}")


def get_chat_history(session_id: str, limit: int = 10) -> list[dict[str, str]]:
    """Get chat history for a session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_query, mentor_response FROM chat_history WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
        (session_id, limit),
    )

    messages = []
    rows = cursor.fetchall()

    # Reverse to get chronological order
    for row in reversed(rows):
        messages.append({"role": "user", "content": row["user_query"]})
        if row["mentor_response"]:
            messages.append({"role": "mentor", "content": row["mentor_response"]})

    conn.close()
    return messages


# Initialize database on import
create_tables()
