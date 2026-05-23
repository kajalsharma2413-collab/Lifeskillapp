# app/models/skill.py
from datetime import datetime
from enum import Enum

from app.models.base import BaseDocument


class SkillType(str, Enum):
    SAFETY = "safety"
    FINANCE = "finance"
    COMMUNICATION = "communication"
    PROBLEM_SOLVING = "problem_solving"
    BASIC_MANNERS = "basic_manners"


class ContentType(str, Enum):
    VIDEO = "video"
    COMIC = "comic"
    GAME = "game"
    QUIZ = "quiz"


class SkillEngagement(BaseDocument):
    user_id: str
    skill_type: SkillType
    content_type: ContentType
    content_id: str
    action: str  # "view", "like", "dislike", "complete"
    timestamp: datetime
    metadata: dict | None = {}


class Badge(BaseDocument):
    name: str
    description: str
    image_url: str
    skill_type: SkillType | None = None
    requirements: dict | None = {}  # Criteria for earning the badge
    points: int = 5  # Default 5 points per badge


class UserBadge(BaseDocument):
    user_id: str
    badge_id: str
    earned_at: datetime
    quiz_id: str | None = None  # If earned through quiz
    score: int | None = None  # Quiz score when earned


class DiaryEntry(BaseDocument):
    user_id: str
    entry_text: str
    mood: str | None = None
    emoji: str | None = None
    ai_response: str | None = None
    mood_score: int | None = None  # 1-5 scale
    date: str  # YYYY-MM-DD format
    timestamp: datetime


class Video(BaseDocument):
    title: str
    description: str
    video_url: str
    thumbnail_url: str | None = None
    skill_type: SkillType
    likes: int = 0
    dislikes: int = 0
    view_count: int = 0
    duration: int | None = None  # in seconds
    badge_id: str | None = None  # Badge earned after watching


class Comic(BaseDocument):
    title: str
    description: str
    pdf_url: str
    thumbnail_url: str | None = None
    skill_type: SkillType
    likes: int = 0
    dislikes: int = 0
    view_count: int = 0
    badge_id: str | None = None


class Quiz(BaseDocument):
    title: str
    skill_type: SkillType
    content_type: ContentType  # video, comic, game
    content_id: str  # ID of related video/comic/game
    min_score: int = 50  # Minimum score to pass
    badge_id: str | None = None  # Badge earned on passing


class Question(BaseDocument):
    quiz_id: str
    question_text: str
    question_order: int = 1


class QuestionOption(BaseDocument):
    question_id: str
    option_text: str
    is_correct: bool = False
    option_order: int = 1


class QuizAttempt(BaseDocument):
    user_id: str
    quiz_id: str
    score: int
    attempt_number: int = 1
    answers: list[dict] | None = []  # User's answers
    completed_at: datetime
    passed: bool = False


class GameLevel(BaseDocument):
    level_number: int
    skill_type: SkillType
    title: str
    description: str
    income: int
    difficulty: str = "easy"  # easy, medium, hard


class GameItem(BaseDocument):
    level_id: str
    name: str
    cost: int
    item_type: str  # "need" or "want"
    description: str | None = None


class GameAttempt(BaseDocument):
    user_id: str
    level_id: str
    score: int
    needs_selected: int = 0
    wants_selected: int = 0
    completed_at: datetime
    items_selected: list[str] | None = []  # Item IDs


class UserReaction(BaseDocument):
    user_id: str
    content_type: ContentType  # video, comic
    content_id: str
    reaction_type: str  # "like", "dislike"
    timestamp: datetime


class ProblemSolvingProgress(BaseDocument):
    user_id: str
    date: str  # YYYY-MM-DD
    questions_attempted: int = 0
    questions_correct: int = 0
    badge_earned: bool = False
    completed_at: datetime | None = None
