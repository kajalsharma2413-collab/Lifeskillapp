import uuid

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


def get_or_create_session_id(session_id: str | None) -> str:
    """Return the provided session_id or generate a new one."""
    return session_id or str(uuid.uuid4())


def history_to_lc_messages(history: list[dict]) -> list[BaseMessage]:
    """Convert chat history from DB to LangChain message objects."""
    messages = []
    for entry in history:
        if entry["role"] == "user":
            messages.append(HumanMessage(content=entry["content"]))
        elif entry["role"] == "mentor":
            messages.append(AIMessage(content=entry["content"]))
    return messages


def append_message(
    history: list[BaseMessage], message: BaseMessage
) -> list[BaseMessage]:
    """Return a new list with the message appended."""
    return history + [message]


def validate_diary_entry(diary_entry: str) -> bool:
    """Basic validation for diary entry."""
    if not diary_entry or not diary_entry.strip():
        return False

    # Check minimum length (at least 10 characters)
    return not len(diary_entry.strip()) < 10


def validate_user_name(user_name: str) -> bool:
    """Basic validation for user name."""
    if not user_name or not user_name.strip():
        return False

    # Check reasonable length (2-50 characters)
    return not (len(user_name.strip()) < 2 or len(user_name.strip()) > 50)


def validate_age(age: int) -> bool:
    """Basic validation for age."""
    return 7 <= age <= 14


def validate_past_summaries(past_summaries: list[str]) -> bool:
    """Basic validation for past summaries."""
    if not isinstance(past_summaries, list):
        return False

    # Check each summary is a non-empty string and reasonable length
    for summary in past_summaries:
        if not isinstance(summary, str) or not summary.strip():
            return False
        if len(summary.strip()) > 500:  # Each summary should be concise
            return False

    # Limit total number of summaries
    return not len(past_summaries) > 10


def clean_user_input(user_input: str) -> str:
    """Clean and validate user input."""
    if not user_input:
        return ""

    # Strip whitespace and limit length
    cleaned = user_input.strip()

    # Limit to reasonable length (1000 characters)
    if len(cleaned) > 1000:
        cleaned = cleaned[:1000]

    return cleaned


def clean_user_name(user_name: str) -> str:
    """Clean and validate user name."""
    if not user_name:
        return ""

    # Strip whitespace and limit length
    cleaned = user_name.strip()

    # Limit to reasonable length (50 characters)
    if len(cleaned) > 50:
        cleaned = cleaned[:50]

    return cleaned
