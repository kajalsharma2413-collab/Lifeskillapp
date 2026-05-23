import logging

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException

from app.api.dependencies.ai.mentor_chatbot.mentor_service import MentorService
from app.api.dependencies.ai.mentor_chatbot.models import (
    InitializeResponse,
    MentorInitialize,
    QueryInput,
    QueryResponse,
)

load_dotenv()

# No API key needed — model configured via OLLAMA_BASE_URL and OLLAMA_MODEL env vars
mentor_service = MentorService()
router = APIRouter(prefix="/mentor", tags=["mentor"])

logger = logging.getLogger(__name__)


@router.post("/initialize", response_model=InitializeResponse)
async def mentor_initialize(
    request: MentorInitialize,
    # current_user: User = Depends(get_current_user)
):
    """
    Initialize a new mentor session with user details and diary entry.
    Returns session ID and initial mentor response.
    """
    try:
        result = mentor_service.initialize_session(
            user_name=request.user_name,
            age=request.age,
            current_diary_entry=request.current_diary_entry,
            past_summaries=request.past_summaries,
        )

        logger.info(f"Session initialized: {result['session_id']}")

        return InitializeResponse(
            session_id=result["session_id"],
            initial_response=result["initial_response"],
        )

    except Exception as e:
        logger.error(f"Error initializing session: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to initialize session: {str(e)}"
        )


@router.post("/chat", response_model=QueryResponse)
async def mentor_chat(request: QueryInput):
    """
    Chat with the mentor using an existing session ID.
    """
    try:
        result = mentor_service.chat_with_session(
            session_id=request.session_id, user_input=request.question
        )

        return QueryResponse(
            answer=result["mentor_response"],
            session_id=result["session_id"],
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")