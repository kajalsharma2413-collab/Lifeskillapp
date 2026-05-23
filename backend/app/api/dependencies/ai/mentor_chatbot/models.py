from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import TypedDict


# API Models
class MentorInitialize(BaseModel):
    """Initialize mentor session with user details and diary entry."""

    user_name: str = Field(description="Child's name")
    age: int = Field(description="Child's age", ge=7, le=14)
    current_diary_entry: str = Field(description="Today's diary entry")
    past_summaries: list[str] = Field(
        default=[], description="List of past conversation summaries"
    )


class QueryInput(BaseModel):
    """Chat query with session ID."""

    question: str = Field(description="User's question or message")
    session_id: str = Field(description="Session identifier")


class QueryResponse(BaseModel):
    """Response from mentor."""

    answer: str = Field(description="Mentor's response")
    session_id: str = Field(description="Session identifier")


class InitializeResponse(BaseModel):
    """Response after session initialization with initial mentor response."""

    session_id: str = Field(description="New session identifier")
    initial_response: str = Field(
        description="Initial response from mentor based on diary"
    )


# Internal Models
class ChildProfile(BaseModel):
    """Child profile with name, age, diary entry and past summaries."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    user_name: str = Field(description="User's name")
    age: int = Field(description="User's age")
    current_diary_entry: str = Field(description="Current diary entry")
    past_summaries: list[str] = Field(
        default=[], description="Past conversation summaries"
    )


class MentorResponse(BaseModel):
    """Structured response from the mentor chatbot."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    response: str = Field(description="Main response to the child")


# LangGraph State
class ChatState(TypedDict):
    """State for the mentor chatbot conversation."""

    child_input: str
    child_profile: ChildProfile
    current_context: str
    mentor_response: str
    chat_history: list[dict[str, str]]
