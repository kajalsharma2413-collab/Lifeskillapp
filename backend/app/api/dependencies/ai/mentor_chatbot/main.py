import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from .mentor_service import MentorService
from .models import InitializeResponse, MentorInitialize, QueryInput, QueryResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Mentor Chatbot API", version="1.0.0")

# Initialize mentor service (no API key needed — Ollama is configured via env vars)
mentor_service = MentorService()


@app.post("/mentor/initialize", response_model=InitializeResponse)
async def mentor_initialize(request: MentorInitialize):
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


@app.post("/mentor/chat", response_model=QueryResponse)
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


@app.get("/mentor/session/{session_id}")
async def get_session_info(session_id: str):
    """
    Get information about a session.
    """
    try:
        info = mentor_service.get_session_info(session_id)
        return info

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "mentor-chatbot"}


def main():
    """Example usage demonstrating the simplified workflow."""
    print("=== MENTOR CHATBOT DEMO ===\n")

    diary_entry = """Today was challenging but rewarding. I was scared to give my book report
    in front of the class, but I practiced at home and did it! My voice was shaky at first, but I got
    more confident. Mrs. Johnson said I did great and my classmates clapped. I'm proud of myself."""

    try:
        result = mentor_service.initialize_session(
            user_name="Alex",
            age=11,
            current_diary_entry=diary_entry,
        )
        session_id = result["session_id"]
        initial_response = result["initial_response"]

        print(f"✅ Session created: {session_id}")
        print(f"🤖 Initial Mentor Response: {initial_response}")
        print("-" * 80)

    except Exception as e:
        print(f"❌ Error initializing session: {e}")
        return

    conversations = [
        "Hi! I'm feeling nervous about my presentation tomorrow at school.",
        "Thanks for the encouragement! What if I forget what to say?",
        "You're right, I did handle the book report well. Maybe I can do this too!",
        "I think I'm ready now. Thank you for helping me feel better!",
    ]

    print("2. Starting conversation...\n")

    for user_input in conversations:
        print(f"👦 User: {user_input}")

        try:
            result = mentor_service.chat_with_session(session_id, user_input)
            print(f"🤖 Mentor: {result['mentor_response']}")
            print("-" * 80)
        except Exception as e:
            print(f"❌ Error: {e}")
            print("-" * 80)


if __name__ == "__main__":
    main()
