# app/utils/auto_quiz_generator.py
# Auto Quiz Generation System - Connects AI generator to content quizzes

import logging
import os
from datetime import datetime
from typing import Optional

from firebase_admin import firestore

from app.api.dependencies.ai.problem_solving.service import QuestionService

logger = logging.getLogger(__name__)


class AutoQuizGenerator:
    """
    Automatically generates quizzes for content using AI when missing.
    Uses Ollama (cloud or local) — no Google API key required.
    """

    def __init__(self):
        """Initialize the auto quiz generator with Ollama-backed QuestionService."""
        ollama_model = os.getenv("OLLAMA_MODEL", "gemma3:4b")
        ollama_api_key = os.getenv("OLLAMA_API_KEY", "")
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "")

        try:
            # Pass Ollama config to QuestionService.
            # QuestionService should accept these kwargs and build its own
            # ChatOllama instance internally (same pattern as ai.py).
            self.question_service = QuestionService(
                model=ollama_model,
                api_key=ollama_api_key,
                base_url=ollama_base_url,
            )
            logger.info(
                f"AutoQuizGenerator initialized with model={ollama_model}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize QuestionService: {e}")
            raise

    async def auto_generate_quiz_for_content(
        self,
        content_id: str,
        content_type: str,  # "video" or "comic"
        skill_type: str,    # "safety", "finance", etc.
        db: firestore.AsyncClient,
        num_questions: int = 4,
    ) -> str:
        """
        Auto-generate a complete quiz for content that doesn't have one.

        Returns:
            str: The quiz_id of the created quiz.
        """
        logger.info(
            f"🤖 Auto-generating quiz for {skill_type} {content_type} {content_id}"
        )

        try:
            # 1. Create the quiz document
            quiz_data = {
                "title": f"Quiz for {content_type.title()} {content_id}",
                "skill_type": skill_type,
                "content_type": content_type,
                "content_id": content_id,
                "min_score": 50,
                "badge_id": None,
                "auto_generated": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            quiz_doc_ref = await db.collection("quizzes").add(quiz_data)
            quiz_id = quiz_doc_ref[1].id
            logger.info(f"✅ Created quiz document with ID: {quiz_id}")

            # 2. Generate AI questions for this content
            questions_created = 0
            for question_order in range(1, num_questions + 1):
                try:
                    ai_question = self.question_service.generate_question(
                        user_id=f"auto_gen_{content_type}_{content_id}",
                        level=self._get_difficulty_level(skill_type),
                    )

                    # Create question document
                    question_data = {
                        "quiz_id": quiz_id,
                        "question_text": ai_question.question,
                        "question_order": question_order,
                        "auto_generated": True,
                        "explanation": ai_question.explanation,
                        "created_at": datetime.utcnow(),
                    }

                    question_ref = await db.collection("questions").add(question_data)
                    question_id = question_ref[1].id

                    # Create option documents
                    options = [
                        {
                            "text": ai_question.option_a,
                            "order": 1,
                            "correct": ai_question.correct_answer == "A",
                        },
                        {
                            "text": ai_question.option_b,
                            "order": 2,
                            "correct": ai_question.correct_answer == "B",
                        },
                        {
                            "text": ai_question.option_c,
                            "order": 3,
                            "correct": ai_question.correct_answer == "C",
                        },
                        {
                            "text": ai_question.option_d,
                            "order": 4,
                            "correct": ai_question.correct_answer == "D",
                        },
                    ]

                    for option in options:
                        option_data = {
                            "question_id": question_id,
                            "option_text": option["text"],
                            "is_correct": option["correct"],
                            "option_order": option["order"],
                            "auto_generated": True,
                            "created_at": datetime.utcnow(),
                        }
                        await db.collection("question_options").add(option_data)

                    questions_created += 1
                    logger.info(
                        f"✅ Created question {question_order}/{num_questions} for quiz {quiz_id}"
                    )

                except Exception as e:
                    logger.error(f"❌ Failed to create question {question_order}: {e}")
                    continue  # Keep going even if one question fails

            if questions_created == 0:
                logger.error(f"❌ No questions were created for quiz {quiz_id}")
                await db.collection("quizzes").document(quiz_id).delete()
                raise RuntimeError("Failed to generate any questions for the quiz")

            # Update quiz with actual question count
            await (
                db.collection("quizzes")
                .document(quiz_id)
                .update(
                    {
                        "total_questions": questions_created,
                        "updated_at": datetime.utcnow(),
                    }
                )
            )

            logger.info(
                f"🎉 Successfully auto-generated quiz {quiz_id} with {questions_created} questions"
            )
            return quiz_id

        except Exception as e:
            logger.error(
                f"❌ Failed to auto-generate quiz for {content_type} {content_id}: {e}"
            )
            raise RuntimeError(f"Auto quiz generation failed: {str(e)}")

    def _get_difficulty_level(self, skill_type: str) -> str:
        """Map skill types to appropriate difficulty levels for AI generation."""
        difficulty_mapping = {
            "safety": "beginner",
            "finance": "medium",
            "communication": "medium",
            "problem_solving": "advanced",
        }
        return difficulty_mapping.get(skill_type, "medium")

    async def check_quiz_exists(
        self,
        content_id: str,
        content_type: str,
        skill_type: str,
        db: firestore.AsyncClient,
    ) -> Optional[str]:
        """
        Check if a quiz already exists for the given content.

        Returns:
            Optional[str]: quiz_id if exists, None if not found.
        """
        quiz_ref = (
            db.collection("quizzes")
            .where("content_id", "==", content_id)
            .where("content_type", "==", content_type)
            .where("skill_type", "==", skill_type)
        )

        quiz_docs = await quiz_ref.get()

        if quiz_docs:
            return quiz_docs[0].id
        return None

    async def get_or_create_quiz(
        self,
        content_id: str,
        content_type: str,
        skill_type: str,
        db: firestore.AsyncClient,
    ) -> str:
        """
        Get existing quiz or auto-generate one if missing.

        Returns:
            str: quiz_id
        """
        existing_quiz_id = await self.check_quiz_exists(
            content_id, content_type, skill_type, db
        )

        if existing_quiz_id:
            logger.info(
                f"📋 Found existing quiz {existing_quiz_id} for {content_type} {content_id}"
            )
            return existing_quiz_id

        logger.info(
            f"🔄 No quiz found for {content_type} {content_id}, auto-generating..."
        )
        return await self.auto_generate_quiz_for_content(
            content_id, content_type, skill_type, db
        )


# ---------------------------------------------------------------------------
# Lazy singleton — instantiated on first use, not at import time.
# This prevents startup crashes if env vars are missing or Ollama is
# temporarily unreachable when the module is first imported.
# ---------------------------------------------------------------------------

_auto_quiz_generator: Optional[AutoQuizGenerator] = None


def get_auto_quiz_generator() -> AutoQuizGenerator:
    """Return the shared AutoQuizGenerator instance, creating it on first call."""
    global _auto_quiz_generator
    if _auto_quiz_generator is None:
        _auto_quiz_generator = AutoQuizGenerator()
    return _auto_quiz_generator


# Back-compat alias so existing callers (`from ... import auto_quiz_generator`)
# continue to work without any changes elsewhere.
# The object is a module-level proxy; it resolves lazily on first attribute access.
class _LazyProxy:
    """Thin proxy that forwards all attribute access to the real instance."""

    def __getattr__(self, name: str):
        return getattr(get_auto_quiz_generator(), name)


auto_quiz_generator = _LazyProxy()
