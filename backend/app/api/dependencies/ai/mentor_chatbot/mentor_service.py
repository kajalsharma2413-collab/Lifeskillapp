import logging
import uuid
from typing import Any

from .database import (
    get_chat_history,
    get_session_context,
    insert_chat_message,
    store_session_context,
)
from .mentor_agent import MentorAgent
from .models import ChildProfile

logger = logging.getLogger(__name__)


class MentorService:
    """
    Service layer for mentor chatbot functionality.
    Handles session management and orchestrates the mentor agent.
    """

    def __init__(self, api_key: str = None):
        """Initialize mentor service with agent."""
        self.agent = MentorAgent(api_key=api_key)
        logger.info("Mentor service initialized")

    def initialize_session(
        self,
        user_name: str,
        age: int,
        current_diary_entry: str,
        past_summaries: list[str] = None,
    ) -> dict[str, str]:
        """
        Initialize a new session with user details, diary entry and past summaries.
        Also saves the initialization exchange to chat history.

        Args:
            user_name: User's name
            age: User's age
            current_diary_entry: Today's diary entry
            past_summaries: List of past conversation summaries

        Returns:
            Dictionary containing session_id and initial_response
        """
        try:
            # Handle default empty list
            if past_summaries is None:
                past_summaries = []

            # Generate unique session ID
            session_id = str(uuid.uuid4())

            # Store session context in database
            store_session_context(
                session_id=session_id,
                user_name=user_name,
                age=age,
                current_diary_entry=current_diary_entry,
                past_summaries=past_summaries,
            )

            # Create child profile
            child_profile = ChildProfile(
                user_name=user_name,
                age=age,
                current_diary_entry=current_diary_entry,
                past_summaries=past_summaries,
            )

            # Generate initial response from mentor based on all user data
            initial_response = self.agent.generate_initial_response(child_profile)

            # Save the initialization exchange to chat history
            # The "user input" for initialization is sharing the diary entry
            initialization_message = (
                f"Here's what I wrote in my diary today:\n\n{current_diary_entry}"
            )

            insert_chat_message(
                session_id=session_id,
                user_query=initialization_message,
                mentor_response=initial_response,
            )

            logger.info(
                f"Initialized session {session_id} for user {user_name} (age {age}) with initial response and saved to chat history"
            )

            return {
                "session_id": session_id,
                "initial_response": initial_response,
            }

        except Exception as e:
            logger.error(f"Error initializing session: {e}")
            raise RuntimeError(f"Session initialization failed: {e}")

    def chat_with_session(self, session_id: str, user_input: str) -> dict[str, Any]:
        """
        Process a chat message using an existing session.

        Args:
            session_id: Existing session ID
            user_input: User's message

        Returns:
            Dictionary with mentor response and session info
        """
        try:
            # Get session context
            context = get_session_context(session_id)
            if not context:
                raise ValueError(f"Session {session_id} not found")

            # Get chat history (now includes initialization exchange)
            chat_history = get_chat_history(session_id)

            # Create child profile from stored context
            child_profile = ChildProfile(
                user_name=context["user_name"],
                age=context["age"],
                current_diary_entry=context["current_diary_entry"],
                past_summaries=context["past_summaries"],
            )

            # Process conversation with agent
            mentor_response = self.agent.process_conversation(
                child_input=user_input,
                child_profile=child_profile,
                chat_history=chat_history,
            )

            # Store the conversation in database
            insert_chat_message(session_id, user_input, mentor_response)

            logger.info(f"Chat completed for session {session_id}")

            return {
                "mentor_response": mentor_response,
                "session_id": session_id,
            }

        except Exception as e:
            logger.error(f"Error in chat with session {session_id}: {e}")
            raise RuntimeError(f"Chat failed: {e}")

    def get_session_info(self, session_id: str) -> dict[str, Any]:
        """
        Get session information without processing a message.

        Args:
            session_id: Session ID to lookup

        Returns:
            Session context information
        """
        context = get_session_context(session_id)
        if not context:
            raise ValueError(f"Session {session_id} not found")

        chat_history = get_chat_history(session_id)

        return {
            "session_id": session_id,
            "user_name": context["user_name"],
            "age": context["age"],
            "has_diary_entry": bool(context["current_diary_entry"]),
            "has_past_summaries": len(context["past_summaries"]) > 0,
            "past_summaries_count": len(context["past_summaries"]),
            "has_chat_history": len(chat_history) > 0,
            "message_count": len(chat_history),
        }
