# app/schemas/safety.py - Updated with badge support
from pydantic import Field

from app.schemas.base import Base


# View Tracking Schemas
class ViewTrackingRequest(Base):
    """Request to track content view"""

    content_type: str = Field(description="Type of content: 'video' or 'comic'")
    content_id: str = Field(description="ID of the content being viewed")


class ViewTrackingResponse(Base):
    """Response for view tracking"""

    success: bool = True
    video_id: str | None = None
    comic_id: str | None = None
    message: str = "View tracked successfully"


# Reaction Schemas
class ReactionResponse(Base):
    """Response for like/dislike actions"""

    success: bool = True
    action: str = Field(
        description="Action taken: 'like', 'dislike', 'remove_like', etc."
    )
    message: str = Field(description="Human readable message about the action")


class UserReactionStatus(Base):
    """Current user's reaction status for content"""

    liked: bool = False
    disliked: bool = False


# Safety Video Schemas
class SafetyVideoBasic(Base):
    """Basic safety video information for lists"""

    id: str
    title: str
    description: str
    thumbnail: str
    quiz_id: str | None = None  # ✅ FIXED: Include quiz ID
    # ✅ FIXED: Add badge fields
    badge_id: str | None = None
    badge_name: str | None = None
    badge_url: str | None = None
    badge_points: int | None = None


class SafetyVideoList(Base):
    """Response for safety videos list"""

    videos: list[SafetyVideoBasic]


# Safety Comic Schemas
class SafetyComicBasic(Base):
    """Basic safety comic information for lists"""

    id: str
    title: str
    description: str
    thumbnail: str
    quiz_id: str | None = None  # ✅ FIXED: Include quiz ID
    # ✅ FIXED: Add badge fields
    badge_id: str | None = None
    badge_name: str | None = None
    badge_url: str | None = None
    badge_points: int | None = None


class SafetyComicList(Base):
    """Response for safety comics list"""

    comics: list[SafetyComicBasic]


class SafetyVideoDetail(Base):
    """Detailed safety video information"""

    id: str
    title: str
    description: str
    video_url: str = Field(alias="videoUrl")
    likes: int = 0
    dislikes: int = 0
    user_liked: bool = Field(alias="userLiked")
    user_disliked: bool = Field(alias="userDisliked")
    # ✅ FIXED: Add badge fields for detailed view
    badge_id: str | None = None
    badge_name: str | None = None
    badge_url: str | None = None
    badge_points: int | None = None


class SafetyVideoResponse(Base):
    """Response wrapper for single video"""

    video: SafetyVideoDetail


class SafetyComicDetail(Base):
    """Detailed safety comic information"""

    id: str
    title: str
    description: str
    pdf_url: str = Field(alias="pdfUrl")
    likes: int = 0
    dislikes: int = 0
    user_liked: bool = Field(alias="userLiked")
    user_disliked: bool = Field(alias="userDisliked")
    # ✅ FIXED: Add badge fields for detailed view
    badge_id: str | None = None
    badge_name: str | None = None
    badge_url: str | None = None
    badge_points: int | None = None


class SafetyComicResponse(Base):
    """Response wrapper for single comic"""

    comic: SafetyComicDetail
