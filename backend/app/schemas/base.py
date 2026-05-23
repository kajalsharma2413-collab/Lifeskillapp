# app/schemas/base.py
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


class Base(BaseModel):
    class Config:
        extra = "forbid"
        from_attributes = True
        exclude_none = True


class PaginationParams(BaseModel):
    skip: int | None = Field(None, ge=0, description="Number of items to skip")
    limit: int | None = Field(
        None, ge=1, le=100, description="Maximum number of items to return"
    )


# Valid Roman numerals for grades I-VIII
VALID_GRADES = ["III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

T = TypeVar("T")


class UniformResponse(BaseModel, Generic[T]):
    """Standardized API response format"""

    success: bool = Field(description="Whether the request was successful")
    message: str = Field(description="Human-readable message about the operation")
    data: T | None = Field(default=None, description="Response data payload")
    errors: list[str] | None = Field(default=None, description="List of error messages")
    meta: dict[str, Any] | None = Field(default=None, description="Additional metadata")

    @classmethod
    def success_response(
        cls,
        message: str = "Operation completed successfully",
        data: T | None = None,
        meta: dict[str, Any] | None = None,
    ) -> "UniformResponse[T]":
        """Create a successful response"""
        return cls(success=True, message=message, data=data, errors=None, meta=meta)

    @classmethod
    def error_response(
        cls,
        message: str = "Operation failed",
        errors: list[str] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> "UniformResponse[None]":
        """Create an error response"""
        return cls(
            success=False, message=message, data=None, errors=errors or [], meta=meta
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized paginated response format"""

    success: bool = Field(description="Whether the request was successful")
    message: str = Field(description="Human-readable message about the operation")
    data: list[T] = Field(
        default_factory=list, description="List of response data items"
    )
    pagination: dict[str, Any] = Field(description="Pagination metadata")
    errors: list[str] | None = Field(default=None, description="List of error messages")

    @classmethod
    def success_response(
        cls,
        data: list[T],
        total_count: int,
        page: int = 1,
        page_size: int = 20,
        message: str = "Data retrieved successfully",
    ) -> "PaginatedResponse[T]":
        """Create a successful paginated response"""
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 1

        return cls(
            success=True,
            message=message,
            data=data,
            pagination={
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            },
            errors=None,
        )

    @classmethod
    def error_response(
        cls, message: str = "Failed to retrieve data", errors: list[str] | None = None
    ) -> "PaginatedResponse[T]":
        """Create an error paginated response"""
        return cls(
            success=False,
            message=message,
            data=[],
            pagination={
                "total_count": 0,
                "page": 1,
                "page_size": 0,
                "total_pages": 0,
                "has_next": False,
                "has_previous": False,
            },
            errors=errors or [],
        )
