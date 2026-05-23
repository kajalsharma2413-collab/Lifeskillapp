from datetime import date, datetime

from pydantic import EmailStr, field_validator

from app.models.base import UserRole
from app.schemas.base import VALID_GRADES, Base


class UserBase(Base):
    email: EmailStr
    username: str
    first_name: str
    last_name: str | None = None
    role: UserRole


class UserUpdate(Base):
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    age: int | None = None
    grade_level: str | None = None
    avatar_url: str | None = None
    preferences: dict | None = None
    date_of_birth: date | None = None

    @field_validator("age")
    @classmethod
    def validate_age(cls, v):
        if v is not None and (v < 8 or v > 14):
            raise ValueError("Age must be between 8 and 14 for student users")
        return v

    @field_validator("grade_level")
    @classmethod
    def validate_grade_level(cls, v):
        if v is not None and v not in VALID_GRADES:
            raise ValueError(f"Grade level must be one of {VALID_GRADES}")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v):
        if v is not None:
            from datetime import date

            today = date.today()
            age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
            if age < 8 or age > 14:
                raise ValueError(
                    "Date of birth must correspond to age between 8 and 14 years"
                )
            if v > today:
                raise ValueError("Date of birth cannot be in the future")
        return v


class UserResponse(UserBase):
    id: str
    firebase_uid: str
    is_active: bool
    is_verified: bool
    age: int | None = None  # Optional at model level, required for children
    date_of_birth: date | None = None
    grade_level: str | None = None  # Optional at model level, required for children
    parent_id: str | None = None
    children_ids: list[str] | None = []
    avatar_url: str | None = None
    current_skills: list[str] | None = []
    completed_skills: list[str] | None = []
    points: int = 0
    badges: list[str] | None = []
    preferences: dict | None = {}
    emergency_contacts: list[dict] | None = []
    last_login: datetime | None = None
    last_activity: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    firebase_synced_at: datetime | None = None


# ==================== SCORING TABLE SCHEMAS ====================


class BadgeDetailResponse(Base):
    """Detailed badge information for scoring table"""

    badge_id: str
    name: str
    description: str
    image_url: str
    skill_type: str | None = None
    points: int
    earned_at: str | None = None
    quiz_score: int | None = None


class SkillBreakdownResponse(Base):
    """Skill-wise scoring breakdown"""

    points: int
    badges: int
    activities: int


class UserSummaryResponse(Base):
    """User summary for scoring table"""

    user_id: str
    name: str
    username: str
    total_points: int
    total_badges: int
    badge_points: int
    activity_points: int
    percentile: float
    rank: int


class ProgressStatsResponse(Base):
    """Progress statistics for user"""

    profile_completion: float
    account_age_days: int
    badges_this_month: int
    average_quiz_score: float


class RecentAchievementResponse(Base):
    """Recent achievement information"""

    badge_id: str
    name: str
    image_url: str
    skill_type: str | None = None
    earned_at: str | None = None
    score: int | None = None
    points: int


# ==================== NEW: COMPLETED SKILLS SCHEMA ====================


class CompletedSkillResponse(Base):
    """Detailed completed skill information for scoring table"""

    skill_id: str
    name: str
    description: str
    skill_type: str | None = None
    completed_at: str | None = None


# ==================== UPDATED: SCORING TABLE RESPONSE ====================


class ScoringTableResponse(Base):
    """Complete scoring table response - UPDATED with completed skills details"""

    user_summary: UserSummaryResponse
    badges_earned: list[BadgeDetailResponse]
    completed_skills_details: list[CompletedSkillResponse]  # ✅ NEW FIELD
    skill_breakdown: dict[str, SkillBreakdownResponse]
    recent_achievements: list[RecentAchievementResponse]
    progress_stats: ProgressStatsResponse


# ==================== LEADERBOARD SCHEMAS ====================


class LeaderboardEntryResponse(Base):
    """Single leaderboard entry"""

    user_id: str
    name: str
    username: str
    total_points: int
    badges_count: int
    badge_points: int
    activity_points: int
    latest_badge_url: str | None = None
    latest_badge_name: str | None = None
    age: int | None = None
    grade: str | None = None
    rank: int
    is_current_user: bool = False


class LeaderboardResponse(Base):
    """Leaderboard response with rankings"""

    leaderboard: list[LeaderboardEntryResponse]
    current_user_entry: LeaderboardEntryResponse | None = None
    total_players: int
    user_rank: int | None = None
