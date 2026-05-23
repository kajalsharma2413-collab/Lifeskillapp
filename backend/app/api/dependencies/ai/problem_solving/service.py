# service.py - Enhanced service with better uniqueness tracking
import logging
from typing import Optional

from .db import get_question_stats, get_topic_distribution, get_user_questions, is_question_too_similar, save_question
from .generator import SmartQuestionGenerator
from .models import QuestionResponse

logger = logging.getLogger(__name__)


class QuestionService:
    """Service for generating unique, mind-expanding questions for children aged 7-14."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the service.

        api_key is accepted but ignored — the Ollama model is configured via
        OLLAMA_BASE_URL and OLLAMA_MODEL environment variables.
        """
        try:
            self.generator = SmartQuestionGenerator()
            logger.info(
                "Question service initialized for children 7-14 with enhanced uniqueness tracking"
            )
        except Exception as e:
            logger.error(f"Failed to initialize QuestionService: {e}")
            raise RuntimeError(f"Service initialization failed: {e}")

    def generate_question(self, user_id: str, level: str) -> QuestionResponse:
        """Generate a unique, thought-provoking question for children."""
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")

        valid_levels = ["beginner", "medium", "advanced"]
        if level not in valid_levels:
            raise ValueError(f"Invalid level '{level}'. Must be one of: {valid_levels}")

        max_attempts = 5

        for attempt in range(max_attempts):
            try:
                previous_questions = get_user_questions(user_id, level, limit=30)
                logger.info(
                    f"User {user_id} has {len(previous_questions)} previous questions "
                    f"at {level} level (attempt {attempt + 1})"
                )

                generated = self.generator.generate_question(
                    user_id=user_id, level=level, previous_questions=previous_questions
                )

                if not generated:
                    raise RuntimeError("Generator returned None")

                if not self.generator.validate_question(generated):
                    logger.warning(
                        f"Generated question failed validation on attempt {attempt + 1}"
                    )
                    continue

                if is_question_too_similar(generated.question, level):
                    logger.info(
                        f"Question too similar to existing questions, retrying... (attempt {attempt + 1})"
                    )
                    continue

                logger.info(
                    f"Successfully generated unique question on attempt {attempt + 1}"
                )

                topic = self._extract_topic(generated.question)

                try:
                    save_question(
                        user_id=user_id,
                        question=generated.question,
                        level=level,
                        topic=topic,
                    )
                except Exception as save_error:
                    logger.warning(f"Failed to save question to database: {save_error}")

                logger.info(
                    f"Generated and processed unique {level} question for user {user_id}"
                )

                return QuestionResponse(
                    question=generated.question,
                    option_a=generated.option_a,
                    option_b=generated.option_b,
                    option_c=generated.option_c,
                    option_d=generated.option_d,
                    correct_answer=generated.correct_answer,
                    explanation=generated.explanation,
                )

            except ValueError as ve:
                logger.error(f"Validation error for user {user_id}: {ve}")
                raise

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for user {user_id}: {e}")
                if attempt == max_attempts - 1:
                    logger.error(
                        f"All {max_attempts} attempts failed for user {user_id}"
                    )
                    raise RuntimeError(
                        f"Could not generate unique question after {max_attempts} attempts: {e}"
                    )
                continue

        raise RuntimeError(
            f"Unexpected error: failed to generate question after {max_attempts} attempts"
        )

    def _extract_topic(self, question: str) -> str:
        """Extract topic from question text for better categorization."""
        question_lower = question.lower()

        topic_keywords = {
            "animals": [
                "animal", "cat", "dog", "bird", "fish", "elephant", "lion", "tiger",
                "bear", "rabbit", "mouse", "insect", "butterfly", "bee", "ant",
            ],
            "space": [
                "space", "planet", "star", "moon", "sun", "solar", "galaxy",
                "universe", "astronaut", "rocket", "satellite",
            ],
            "nature": [
                "tree", "plant", "flower", "leaf", "forest", "ocean", "river",
                "mountain", "weather", "rain", "wind", "storm",
            ],
            "human_body": [
                "body", "heart", "brain", "eye", "ear", "hand", "foot", "blood",
                "bone", "muscle", "skin",
            ],
            "physics": [
                "gravity", "force", "energy", "light", "sound", "heat",
                "temperature", "speed", "motion", "electricity",
            ],
            "chemistry": [
                "water", "chemical", "reaction", "gas", "liquid", "solid",
                "molecule", "atom", "oxygen", "carbon",
            ],
            "mathematics": [
                "number", "count", "calculate", "multiply", "divide", "add",
                "subtract", "pattern", "sequence", "geometry",
            ],
            "technology": [
                "computer", "robot", "machine", "invention", "technology",
                "internet", "phone", "car", "airplane", "engine",
            ],
            "food": [
                "food", "eat", "nutrition", "vitamin", "protein", "fruit",
                "vegetable", "meat", "grain", "sugar",
            ],
            "earth": [
                "earth", "geology", "rock", "mineral", "volcano", "earthquake",
                "continent", "country", "map", "geography",
            ],
        }

        topic_scores = {}
        for topic, keywords in topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in question_lower)
            if score > 0:
                topic_scores[topic] = score

        if topic_scores:
            best_topic = max(topic_scores, key=topic_scores.get)
            logger.info(f"Identified topic: {best_topic} for question")
            return best_topic

        return "general"

    def get_user_stats(self, user_id: str) -> dict:
        """Get statistics for a specific user."""
        try:
            stats = get_question_stats(user_id)
            logger.info(f"Retrieved stats for user {user_id}")
            return stats
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {"error": "Could not retrieve stats"}

    def get_global_stats(self) -> dict:
        """Get global statistics about question generation."""
        try:
            stats = get_question_stats()
            topics = get_topic_distribution()
            result = {**stats, "popular_topics": topics[:10]}
            logger.info("Retrieved global statistics")
            return result
        except Exception as e:
            logger.error(f"Error getting global stats: {e}")
            return {"error": "Could not retrieve global stats"}