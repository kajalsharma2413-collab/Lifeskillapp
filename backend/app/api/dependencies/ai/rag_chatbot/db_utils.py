import os
import sqlite3

# Get the directory of the current script
DB_DIR = os.path.dirname(os.path.abspath(__file__))
# Define the database name
DB_NAME = os.path.join(DB_DIR, "rag_app.db")


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_chat_history():
    conn = get_db_connection()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS chat_history
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     session_id TEXT,
                     user_query TEXT,
                     gpt_response TEXT,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
    )
    conn.close()


def insert_chat_history(session_id, user_query, gpt_response):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO chat_history (session_id, user_query, gpt_response ) VALUES (?, ?, ? )",
        (session_id, user_query, gpt_response),
    )
    conn.commit()
    conn.close()


def get_chat_history(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_query, gpt_response FROM chat_history WHERE session_id = ? ORDER BY created_at",
        (session_id,),
    )
    messages = []
    for row in cursor.fetchall():
        messages.append({"role": "human", "content": row["user_query"]})
        if row["gpt_response"] is not None:
            messages.append({"role": "ai", "content": row["gpt_response"]})
    conn.close()
    return messages


# Initialize the database tables
create_chat_history()