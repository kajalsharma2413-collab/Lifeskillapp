# app/schemas/diary.py
from pydantic import BaseModel, Field


class DiaryEntryRequest(BaseModel):
    """Request model for diary analysis endpoint."""

    diary_entry: str = Field(..., min_length=60, description="The diary entry text")


class DiaryAnalysisResponse(BaseModel):
    """Response model for successful diary analysis."""

    summary: str = Field(description="Summary of the diary entry")
    score: int = Field(ge=1, le=10, description="Well-being score from 1-10")
