# app/models/user.py
from datetime import date, datetime

from app.models.base import BaseDocument, UserRole


class User(BaseDocument):
    # Basic Information - Firebase Auth handles email/password
    email: str
    firebase_uid: str  # Primary identifier from Firebase Auth
    username: str
    first_name: str
    last_name: str | None = None
    # NO password_hash - Firebase Auth handles this completely!

    # Role and Status
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False  # Can sync from Firebase Auth email verification

    # Child-specific fields (for USER role) - Required only for children
    age: int | None = (
        None  # Optional at model level, required for USER role in validation
    )
    date_of_birth: date | None = None
    grade_level: str | None = (
        None  # Optional at model level, required for USER role in validation
    )

    # Parent-child relationship
    parent_id: str | None = None  # For children - links to Firestore doc ID
    children_ids: list[str] | None = []  # For parents - links to Firestore doc IDs

    # Profile Information
    avatar_url: str | None = None
    preferences: dict | None = {}

    # App-specific fields
    current_skills: list[str] | None = []  # Skills currently learning
    completed_skills: list[str] | None = []  # Skills completed
    points: int = 0
    badges: list[str] | None = []

    # Emergency contacts (for children)
    emergency_contacts: list[dict] | None = []

    # Last activity
    last_login: datetime | None = None
    last_activity: datetime | None = None

    # Firebase sync tracking
    firebase_synced_at: datetime | None = None
