# models.py - Enhanced models with more flexible validation
from typing import Literal

from pydantic import BaseModel, Field, validator


class QuestionResponse(BaseModel):
    """Generated question response with validation."""

    question: str = Field(..., min_length=50, description="The main question")
    option_a: str = Field(
        ..., min_length=10, description="Option A"
    )  # Reduced from 10 to be more flexible
    option_b: str = Field(..., min_length=10, description="Option B")
    option_c: str = Field(..., min_length=10, description="Option C")
    option_d: str = Field(..., min_length=10, description="Option D")
    correct_answer: Literal["A", "B", "C", "D"] = Field(
        ..., description="Correct answer"
    )
    explanation: str = Field(
        ..., min_length=80, description="Explanation of the answer"
    )

    @validator(
        "question", "option_a", "option_b", "option_c", "option_d", "explanation"
    )
    def strip_whitespace(cls, v):
        return v.strip() if isinstance(v, str) else v


class GeneratedQuestion(BaseModel):
    """Internal model for LLM output with more flexible validation."""

    question: str = Field(..., min_length=50)
    option_a: str = Field(..., min_length=10)  # Reduced from previous requirement
    option_b: str = Field(..., min_length=10)
    option_c: str = Field(..., min_length=10)
    option_d: str = Field(..., min_length=10)
    correct_answer: Literal["A", "B", "C", "D"]
    explanation: str = Field(..., min_length=80)

    @validator(
        "question", "option_a", "option_b", "option_c", "option_d", "explanation"
    )
    def strip_whitespace(cls, v):
        return v.strip() if isinstance(v, str) else v
