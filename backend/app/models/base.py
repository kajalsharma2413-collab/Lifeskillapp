from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class UserRole(str, Enum):
    USER = "user"  # Children (8-14)
    PARENT = "parent"  # Parents/Guardians
    ADMIN = "admin"  # System administrators


class BaseDocument(BaseModel):
    id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
        extra = "forbid"
        exclude_none = True
        json_encoders = {datetime: lambda v: v.isoformat()}
