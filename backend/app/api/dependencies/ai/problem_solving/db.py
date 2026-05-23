import hashlib
import logging
import os
import sqlite3

logger = logging.getLogger(__name__)

# Get the directory of the current script
DB_DIR = os.path.dirname(os.path.abspath(__file__))
# Define the database name
DB_NAME = os.path.join(DB_DIR, "problem_solving.db")


def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def setup_db():
    """Create questions table with enhanced tracking."""
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY,
            user_id TEXT NOT NULL,
            question TEXT NOT NULL,
            question_hash TEXT NOT NULL,
            level TEXT NOT NULL,
            topic TEXT DEFAULT 'general',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(question_hash)
        )
    """
    )

    # Create index for better performance
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_user_level
        ON questions(user_id, level)
    """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_question_hash
        ON questions(question_hash)
    """
    )

    conn.commit()
    conn.close()
    logger.info("Enhanced database setup complete")


def _generate_question_hash(question: str) -> str:
    """Generate a hash for question uniqueness checking."""
    # Normalize the question for better duplicate detection
    normalized = question.lower().strip()
    # Remove common words and punctuation for better matching
    words_to_ignore = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "what",
        "how",
        "why",
        "when",
        "where",
        "which",
        "who",
    }
    words = [word.strip('.,!?;:"()[]{}') for word in normalized.split()]
    significant_words = [
        word for word in words if word not in words_to_ignore and len(word) > 2
    ]
    key_phrase = " ".join(
        sorted(significant_words[:10])
    )  # Use first 10 significant words, sorted
    return hashlib.md5(key_phrase.encode()).hexdigest()


def save_question(user_id: str, question: str, level: str, topic: str = "general"):
    """Save a generated question with duplicate prevention."""
    conn = get_connection()
    try:
        question_hash = _generate_question_hash(question)

        # Check if this question (or very similar) already exists
        cursor = conn.execute(
            "SELECT id FROM questions WHERE question_hash = ?", (question_hash,)
        )

        if cursor.fetchone():
            logger.info(
                f"Similar question already exists (hash: {question_hash}), but saving for user tracking"
            )

        # Save the question for this user
        conn.execute(
            "INSERT OR REPLACE INTO questions (user_id, question, question_hash, level, topic) VALUES (?, ?, ?, ?, ?)",
            (user_id, question, question_hash, level, topic),
        )
        conn.commit()
        logger.info(
            f"Saved question for user: {user_id}, level: {level}, topic: {topic}"
        )
    except Exception as e:
        logger.error(f"Error saving question: {e}")
        raise
    finally:
        conn.close()


def get_user_questions(user_id: str, level: str, limit: int = 20) -> list[str]:
    """Get recent questions asked to this user at this level."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT question FROM questions WHERE user_id = ? AND level = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, level, limit),
        )
        questions = [row["question"] for row in cursor.fetchall()]
        logger.info(
            f"Retrieved {len(questions)} questions for user {user_id} at {level} level"
        )
        return questions
    finally:
        conn.close()


def get_all_question_hashes(level: str, limit: int = 100) -> list[str]:
    """Get hashes of recent questions for a level to avoid global duplicates."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT DISTINCT question_hash FROM questions WHERE level = ? ORDER BY created_at DESC LIMIT ?",
            (level, limit),
        )
        hashes = [row["question_hash"] for row in cursor.fetchall()]
        logger.info(f"Retrieved {len(hashes)} question hashes for {level} level")
        return hashes
    finally:
        conn.close()


def is_question_too_similar(question: str, level: str) -> bool:
    """Check if a question is too similar to existing questions."""
    question_hash = _generate_question_hash(question)
    existing_hashes = get_all_question_hashes(level)

    is_similar = question_hash in existing_hashes
    if is_similar:
        logger.info(
            f"Question too similar to existing question (hash: {question_hash})"
        )

    return is_similar


def get_question_stats(user_id: str = None) -> dict:
    """Get statistics about questions asked."""
    conn = get_connection()
    try:
        if user_id:
            # User-specific stats
            cursor = conn.execute(
                """SELECT
                    level,
                    COUNT(*) as count,
                    MAX(created_at) as last_question
                FROM questions
                WHERE user_id = ?
                GROUP BY level""",
                (user_id,),
            )
            user_stats = {
                row["level"]: {
                    "count": row["count"],
                    "last_question": row["last_question"],
                }
                for row in cursor.fetchall()
            }

            cursor = conn.execute(
                "SELECT COUNT(*) as total FROM questions WHERE user_id = ?", (user_id,)
            )
            total = cursor.fetchone()["total"]

            return {
                "user_id": user_id,
                "total_questions": total,
                "by_level": user_stats,
            }
        else:
            # Global stats
            cursor = conn.execute(
                """SELECT
                    level,
                    COUNT(*) as count,
                    COUNT(DISTINCT user_id) as unique_users
                FROM questions
                GROUP BY level"""
            )
            level_stats = {
                row["level"]: {
                    "count": row["count"],
                    "unique_users": row["unique_users"],
                }
                for row in cursor.fetchall()
            }

            cursor = conn.execute("SELECT COUNT(*) as total FROM questions")
            total = cursor.fetchone()["total"]

            cursor = conn.execute(
                "SELECT COUNT(DISTINCT user_id) as unique_users FROM questions"
            )
            unique_users = cursor.fetchone()["unique_users"]

            cursor = conn.execute(
                "SELECT COUNT(DISTINCT question_hash) as unique_questions FROM questions"
            )
            unique_questions = cursor.fetchone()["unique_questions"]

            return {
                "total_questions": total,
                "unique_questions": unique_questions,
                "unique_users": unique_users,
                "by_level": level_stats,
            }
    finally:
        conn.close()


def clean_old_questions(days_old: int = 30):
    """Clean up old questions to prevent database bloat."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM questions WHERE created_at < datetime('now', '-' || ? || ' days')",
            (days_old,),
        )
        deleted = cursor.rowcount
        conn.commit()
        logger.info(f"Cleaned up {deleted} questions older than {days_old} days")
        return deleted
    except Exception as e:
        logger.error(f"Error cleaning old questions: {e}")
        raise
    finally:
        conn.close()


def get_topic_distribution(level: str = None, limit: int = 20) -> list[dict]:
    """Get distribution of topics for questions."""
    conn = get_connection()
    try:
        if level:
            cursor = conn.execute(
                """SELECT topic, COUNT(*) as count
                FROM questions
                WHERE level = ? AND topic != 'general'
                GROUP BY topic
                ORDER BY count DESC
                LIMIT ?""",
                (level, limit),
            )
        else:
            cursor = conn.execute(
                """SELECT topic, COUNT(*) as count
                FROM questions
                WHERE topic != 'general'
                GROUP BY topic
                ORDER BY count DESC
                LIMIT ?""",
                (limit,),
            )

        topics = [
            {"topic": row["topic"], "count": row["count"]} for row in cursor.fetchall()
        ]
        logger.info(f"Retrieved topic distribution: {len(topics)} topics")
        return topics
    finally:
        conn.close()


# Initialize database
setup_db()
