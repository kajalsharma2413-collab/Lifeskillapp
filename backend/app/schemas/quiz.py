# app/schemas/quiz.py - Enhanced Quiz Response Models
from datetime import datetime

from app.schemas.base import Base


# Enhanced Question Option Response
class QuestionOptionResponse(Base):
    id: str  # question_option document ID for tracking
    option_order: int  # order of the option (1, 2, 3, 4)
    text: str
    is_correct: bool


class QuestionResponse(Base):
    id: str  # question document ID for tracking
    question_order: int  # order of the question in the quiz
    question_text: str
    options: list[QuestionOptionResponse]  # standardized to "options"


class QuizMetadata(Base):
    quiz_id: str
    title: str
    skill_type: str  # "safety", "finance", "problem_solving", etc.
    content_type: str  # "video", "comic", "game", "lesson", etc.
    content_id: str  # ID of the associated content
    min_score: int
    max_attempts: int | None = None
    time_limit_minutes: int | None = None
    badge_id: str | None = None
    badge_name: str | None = None
    badge_description: str | None = None


class EnhancedQuizResponse(Base):
    """Comprehensive quiz response with all information frontend needs"""

    metadata: QuizMetadata
    questions: list[QuestionResponse]
    total_questions: int

    def model_post_init(self, __context) -> None:
        """Auto-calculate total_questions"""
        if not hasattr(self, "total_questions") or self.total_questions is None:
            self.total_questions = len(self.questions)


# Quiz Submission Models
class QuizAnswerSubmission(Base):
    question_id: str
    selected_option_id: str  # option document ID or option_order


class QuizSubmissionRequest(Base):
    answers: list[QuizAnswerSubmission]
    time_taken_seconds: int | None = None


class QuizResultResponse(Base):
    quiz_id: str
    content_id: str
    content_type: str
    skill_type: str
    score_percentage: int
    correct_answers: int
    total_questions: int
    passed: bool
    min_score_required: int
    badge_awarded: bool = False
    badge_id: str | None = None
    badge_name: str | None = None
    attempt_number: int
    time_taken_seconds: int | None = None
    completed_at: datetime
    detailed_results: list[dict] | None = None  # Question-by-question breakdown
