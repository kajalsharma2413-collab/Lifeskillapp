import uuid
from typing import Dict, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


def get_or_create_session_id(session_id: Optional[str]) -> str:
    """Return the provided session_id or generate a new one."""
    return session_id or str(uuid.uuid4())


def history_to_lc_messages(history: List[Dict]) -> List[BaseMessage]:
    """Convert chat history from DB to LangChain message objects."""
    messages = []
    for entry in history:
        if entry["role"] == "human":
            messages.append(HumanMessage(content=entry["content"]))
        elif entry["role"] == "ai":
            messages.append(AIMessage(content=entry["content"]))
    return messages


def append_message(
    history: List[BaseMessage], message: BaseMessage
) -> List[BaseMessage]:
    """Return a new list with the message appended."""
    return history + [message]