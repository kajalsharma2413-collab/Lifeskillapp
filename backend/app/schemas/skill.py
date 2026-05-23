# app/schemas/skill.py
from datetime import datetime

from pydantic import Field, field_validator

from app.models.skill import ContentType, SkillType
from app.schemas.base import Base


# Badge schemas
class BadgeResponse(Base):
    id: str
    name: str
    image_url: str = Field(alias="image")
    description: str | None = None
    skill_type: SkillType | None = None
    points: int = 5


class UserBadgeResponse(Base):
    id: str
    badge_id: str
    earned_at: datetime
    quiz_id: str | None = None
    score: int | None = None


# Video schemas
class VideoResponse(Base):
    id: str
    title: str
    description: str
    video_url: str = Field(alias="videoUrl")
    thumbnail_url: str | None = Field(alias="thumbnail", default=None)
    likes: int = 0
    dislikes: int = 0
    view_count: int = 0
    user_liked: bool | None = Field(default=None, alias="userLiked")
    user_disliked: bool | None = Field(default=None, alias="userDisliked")


class VideoCreateRequest(Base):
    title: str
    description: str
    video_url: str
    thumbnail_url: str | None = None
    skill_type: SkillType
    badge_id: str | None = None


class VideoUpdateRequest(Base):
    title: str | None = None
    description: str | None = None
    video_url: str | None = None
    thumbnail_url: str | None = None


# Comic schemas
class ComicResponse(Base):
    id: str
    title: str
    description: str
    pdf_url: str = Field(alias="pdfUrl")
    thumbnail_url: str | None = Field(alias="thumbnail", default=None)
    likes: int = 0
    dislikes: int = 0
    view_count: int = 0
    user_liked: bool | None = Field(default=None, alias="userLiked")
    user_disliked: bool | None = Field(default=None, alias="userDisliked")


class ComicCreateRequest(Base):
    title: str
    description: str
    pdf_url: str
    thumbnail_url: str | None = None
    skill_type: SkillType
    badge_id: str | None = None


# Quiz schemas
class QuestionOptionResponse(Base):
    id: int
    text: str
    is_true: bool


class QuestionResponse(Base):
    question: str
    answers: list[QuestionOptionResponse]


class QuizResponse(Base):
    questions: list[QuestionResponse]
    min_score: int
    badge_link: str | None = Field(alias="badge_link")


class QuizSubmissionRequest(Base):
    user_id: str
    username: str
    quiz_id: str
    score: int
    attempt: int = 1
    badge_link: str | None = None


class GameItemResponse(Base):
    name: str
    cost: int
    type: str = Field(alias="item_type")
    description: str | None = None


class GameLevelResponse(Base):
    success: bool = True
    income: int
    items: list[GameItemResponse]
    quiz_id: str | None = None  # NEW: Include quiz ID


class GameSubmissionRequest(Base):
    user_id: str
    username: str
    level: int
    score: int
    needs: int
    wants: int


# Skill engagement schemas
class SkillResponse(Base):
    title: str
    usage: int


class SkillsUsageResponse(Base):
    success: bool = True
    skills: list[SkillResponse]


class SkillViewRequest(Base):
    skill_id: str = Field(alias="skill_engagement")


# Diary schemas
class DiaryEntryResponse(Base):
    id: str
    text: str
    mood: int | None = None
    date: str


class DiaryAnalysisRequest(Base):
    entry: str


class DiaryAnalysisResponse(Base):
    mood: str
    emoji: str
    response: str


class DiaryEntryCreateRequest(Base):
    user_id: str
    entry: str
    mood: str
    emoji: str
    timestamp: str


class SupportiveTipsRequest(Base):
    entries: list[DiaryEntryResponse]


class SupportiveTipsResponse(Base):
    tip: str


# Parent dashboard schemas
class ChildResponse(Base):
    id: int | str
    first_name: str
    username: str
    age: int


class ParentChildrenResponse(Base):
    success: bool = True
    children: list[ChildResponse]


class ChildDiaryResponse(Base):
    success: bool = True
    entries: list[DiaryEntryResponse]


# User reaction schemas
class UserReactionResponse(Base):
    liked: bool
    disliked: bool


# Problem solving schemas
class ProblemSolvingProgressResponse(Base):
    date: str
    attempted: int
    correct: int
    badge_earned: bool


# Admin schemas
class QuestionCreateRequest(Base):
    question_text: str
    question_order: int = 1


class QuestionOptionCreateRequest(Base):
    option_text: str
    is_correct: bool = False
    option_order: int = 1


class QuizCreateRequest(Base):
    title: str
    skill_type: SkillType
    content_type: ContentType
    content_id: str
    min_score: int = 50
    badge_id: str | None = None


# Life skills response
class LifeSkillResponse(Base):
    title: str
    image: str
    description: str
    route: str | None


class FinanceLevelCreateRequest(Base):
    level_number: int = Field(ge=1, le=50, description="Level number from 1-50")
    title: str = Field(min_length=3, max_length=100, description="Level title")
    description: str = Field(
        min_length=10, max_length=500, description="Level description"
    )
    income: int = Field(ge=100, le=50000, description="Player income for this level")
    difficulty: str = Field(default="easy", description="Difficulty level")

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v):
        if v not in ["easy", "medium", "hard"]:
            raise ValueError("Difficulty must be 'easy', 'medium', or 'hard'")
        return v


class FinanceLevelUpdateRequest(Base):
    level_number: int | None = Field(
        None, ge=1, le=50, description="Level number from 1-50"
    )
    title: str | None = Field(
        None, min_length=3, max_length=100, description="Level title"
    )
    description: str | None = Field(
        None, min_length=10, max_length=500, description="Level description"
    )
    income: int | None = Field(
        None, ge=100, le=50000, description="Player income for this level"
    )
    difficulty: str | None = Field(None, description="Difficulty level")

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v):
        if v is not None and v not in ["easy", "medium", "hard"]:
            raise ValueError("Difficulty must be 'easy', 'medium', or 'hard'")
        return v


class GameItemCreateRequest(Base):
    name: str = Field(min_length=2, max_length=50, description="Item name")
    cost: int = Field(ge=1, le=10000, description="Item cost")
    item_type: str = Field(description="Item type: 'need' or 'want'")
    description: str | None = Field(
        None, max_length=200, description="Item description"
    )

    @field_validator("item_type")
    @classmethod
    def validate_item_type(cls, v):
        if v not in ["need", "want"]:
            raise ValueError("Item type must be 'need' or 'want'")
        return v


class GameItemUpdateRequest(Base):
    name: str | None = Field(None, min_length=2, max_length=50, description="Item name")
    cost: int | None = Field(None, ge=1, le=10000, description="Item cost")
    item_type: str | None = Field(None, description="Item type: 'need' or 'want'")
    description: str | None = Field(
        None, max_length=200, description="Item description"
    )

    @field_validator("item_type")
    @classmethod
    def validate_item_type(cls, v):
        if v is not None and v not in ["need", "want"]:
            raise ValueError("Item type must be 'need' or 'want'")
        return v


class FinanceQuizCreateRequest(Base):
    title: str = Field(min_length=5, max_length=100, description="Quiz title")
    min_score: int = Field(
        default=50, ge=0, le=100, description="Minimum passing score"
    )
    badge_id: str | None = Field(None, description="Badge ID to award on completion")


class FinanceGameAttemptResponse(Base):
    id: str
    level_id: str
    score: int
    needs_selected: int
    wants_selected: int
    completed_at: datetime
    level_title: str | None = None
    level_income: int | None = None


class FinanceProgressResponse(Base):
    total_levels: int
    levels_completed: int
    highest_level: int
    total_attempts: int
    average_score: float
    total_points_earned: int
    badges_earned: int
    recent_attempts: list[FinanceGameAttemptResponse]
