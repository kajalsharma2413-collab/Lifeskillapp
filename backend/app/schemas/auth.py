# app/schemas/auth.py
from pydantic import ValidationInfo, field_validator

from app.models.base import UserRole
from app.schemas.base import VALID_GRADES, Base


# Frontend handles registration via Firebase Auth SDK
# Backend only receives registration completion data
class UserRegistrationComplete(Base):
    """Data sent after Firebase Auth registration is complete"""

    firebase_id_token: str  # Firebase ID token after registration
    username: str
    first_name: str
    last_name: str | None = None
    role: UserRole = UserRole.USER
    # Child-specific fields - Required only for USER role
    age: int | None = None  # Optional, but required for USER role
    grade_level: str | None = None  # Optional, but required for USER role
    # Parent code for linking child to parent - Required only for USER role
    parent_code: str | None = None  # Optional, but required for USER role

    class Config:
        extra = "ignore"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v == UserRole.ADMIN:
            raise ValueError(
                "Admin role registration is not allowed through this endpoint"
            )
        return v

    @field_validator("age")
    @classmethod
    def validate_age(cls, v, info: ValidationInfo):
        if info.data.get("role") == UserRole.USER:
            if v is None:
                raise ValueError("Age is required for child users")
            if v < 8 or v > 14:
                raise ValueError("Age must be between 8 and 14 for student users")
        return v

    @field_validator("grade_level")
    @classmethod
    def validate_grade_level(cls, v, info: ValidationInfo):
        if info.data.get("role") == UserRole.USER:
            if v is None:
                raise ValueError("Grade level is required")
            if v not in VALID_GRADES:
                raise ValueError(f"Grade level must be one of {VALID_GRADES}")
        return v

    @field_validator("parent_code")
    @classmethod
    def validate_parent_code(cls, v, info: ValidationInfo):
        if info.data.get("role") == UserRole.USER:
            if v is None or v.strip() == "":
                raise ValueError("Parent code is required for student users")
        return v


# Frontend handles login via Firebase Auth SDK
# Backend only receives the ID token
class FirebaseAuthToken(Base):
    """Firebase ID token from frontend"""

    firebase_id_token: str


# Firebase user data extracted from ID token
class FirebaseUserData(Base):
    """User data from Firebase ID token"""

    firebase_uid: str
    email: str
    email_verified: bool
    name: str | None = None
    picture: str | None = None


# Account deletion schemas
class AccountDeletionRequest(Base):
    """Base class for account deletion requests"""

    confirmation_text: str  # User must type "DELETE" to confirm

    @field_validator("confirmation_text")
    @classmethod
    def validate_confirmation(cls, v):
        if v != "DELETE":
            raise ValueError("Must type 'DELETE' exactly to confirm account deletion")
        return v


class ChildAccountDeletionRequest(AccountDeletionRequest):
    """Child account deletion request - requires parent code"""

    parent_code: str

    @field_validator("parent_code")
    @classmethod
    def validate_parent_code(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Parent code is required for child account deletion")
        return v
