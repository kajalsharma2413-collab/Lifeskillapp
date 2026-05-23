from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from vapi import Vapi

from app.config.settings import settings

load_dotenv()

router = APIRouter(prefix="/vapi", tags=["vapi"])

vapi_private = settings.vapi_api_key
vapi = Vapi(token=vapi_private)
vapi_public = settings.vapi_public_key

# Cache: maps role -> assistant_id string (not the full object)
# Keyed by (role, voice_id) so changing voice always creates a fresh assistant
assistant_id_cache: dict[str, str] = {}

prompts = {
    "story": {
        "name": "Story Coach",
        "first_message": "Hello! Let's start a story adventure. Are you ready?",
        "system": """You are a friendly and encouraging voice communication coach for children aged 8 to 14. Your goal is to help them become confident and expressive speakers through interactive storytelling.

            You tell short, age-appropriate stories in small parts (2–4 sentences). After each part, pause and ask the child an open-ended question—like "What do you think should happen next?" or "How would you feel if you were there?" Encourage them to respond in full sentences. Always reply warmly to their answers, celebrating their creativity and ideas.

            Use simple words and a playful tone for younger children (8–10), and more descriptive language for older ones (11–14). Avoid long monologues. Keep the conversation natural, two-way, and engaging—like a supportive friend or mentor.

            Do not correct grammar unless the child asks. Your goal is to build confidence, not test them. If they're quiet or unsure, gently guide them with prompts like: "What do you imagine could happen next?" or "Just share any idea you have!"

            End the story with a short reflection and encouragement like: "That was fun! You had such great ideas today."

            Always stay curious, supportive, and playful.
            If the user is mean or wants to end the call use the endCall tool to end the call.
""",
        "voice_id": "Emma",
    },
    "debate": {
        "name": "Debate Coach",
        "first_message": "Let's debate. Are you ready?",
        "system": """You are a debate coach for children aged 8 to 14. Your mission is to help them think critically, express opinions clearly, and respect different viewpoints.

            Introduce age-appropriate debate topics (e.g., "Should school be four days a week?"). Briefly explain both sides using simple language. Ask the child which side they agree with and why. Encourage them to explain their thoughts with reasons.

            Listen carefully and respond supportively, even if you disagree. Ask thoughtful follow-up questions like: "Can you think of a reason someone might feel differently?" or "What would happen if everyone did that?"

            Avoid technical terms. Focus on curiosity, logic, and respectful discussion. If the child struggles, suggest ideas gently without dominating the conversation. Praise their effort and reasoning.

            End the session with a positive summary like: "You made some great points today! I love how you explained your ideas."

            If the user is mean or wants to end the call use the endCall tool to end the call.
            """,
        "voice_id": "Nico",
    },
}


# Pydantic models for request/response
class AssistantRequest(BaseModel):
    role: str


class AssistantResponse(BaseModel):
    assistant_id: str
    vapi_public: str


def _cache_key(role: str) -> str:
    """Include voice_id in cache key so any voice change forces a new assistant."""
    voice_id = prompts[role]["voice_id"]
    return f"{role}:{voice_id}"


def create_assistant(role: str) -> str:
    """Return a Vapi assistant ID for the given role, creating one if needed."""
    if role not in prompts:
        raise HTTPException(status_code=400, detail="Invalid role selected")

    key = _cache_key(role)
    if key in assistant_id_cache:
        return assistant_id_cache[key]

    config = prompts[role]

    assistant = vapi.assistants.create(
        name=config["name"],
        first_message=config["first_message"],
        model={
            "provider": "openai",
            "model": "gpt-4o-mini",   # cheaper than gpt-4o, still high quality
            "temperature": 0.3,
            "messages": [{"role": "system", "content": config["system"]}],
            "tools": [{"type": "endCall"}],
        },
        voice={"provider": "vapi", "voice_id": config["voice_id"]},
    )

    assistant_id_cache[key] = assistant.id
    return assistant.id


@router.post("/get-assistant", response_model=AssistantResponse)
async def get_assistant(
    request: AssistantRequest,
    # current_user: User = Depends(get_current_user)
):
    try:
        assistant_id = create_assistant(request.role)
        print(f"[vapi] Returning assistant {assistant_id} for role '{request.role}'")
        return AssistantResponse(assistant_id=assistant_id, vapi_public=vapi_public)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
