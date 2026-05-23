# app/api/v1/chatbot.py
from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import firestore
from pydantic import BaseModel

from app.api.dependencies.auth import get_current_user
from app.config.firebase import get_firebase_client
from app.models.user import User
from app.schemas.base import UniformResponse
from app.services.ai import ChatbotService

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


class ChatMessage(BaseModel):
    message: str
    context: str | None = None  # Optional context (e.g., "safety", "finance", "general")


class ChatResponse(BaseModel):
    response: str
    context: str | None = None


@router.post("/chat", response_model=UniformResponse[ChatResponse])
async def chat_with_ai(
    chat_request: ChatMessage,
    current_user: User = Depends(get_current_user),
):
    """General AI chatbot for encouragement, support, and guidance"""
    try:
        chatbot_service = ChatbotService()

        ai_response = await chatbot_service.get_chat_response(
            message=chat_request.message,
            context=chat_request.context,
            user_age=current_user.age,
            user_name=current_user.first_name,
        )

        response = ChatResponse(response=ai_response, context=chat_request.context)

        return UniformResponse.success_response(
            message="Chat response generated successfully", data=response
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get chat response: {str(e)}"
        )


@router.post("/safety-comic-chat", response_model=UniformResponse[ChatResponse])
async def safety_comic_chat(
    chat_request: ChatMessage,
    current_user: User = Depends(get_current_user),
):
    """AI chatbot specifically for safety comic discussions"""
    try:
        chatbot_service = ChatbotService()

        ai_response = await chatbot_service.get_safety_comic_response(
            message=chat_request.message,
            user_age=current_user.age,
            user_name=current_user.first_name,
        )

        response = ChatResponse(response=ai_response, context="safety_comic")

        return UniformResponse.success_response(
            message="Safety comic chat response generated successfully", data=response
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get safety comic chat response: {str(e)}",
        )


@router.post("/encouragement", response_model=UniformResponse[ChatResponse])
async def get_encouragement(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get an encouraging message for the user"""
    try:
        chatbot_service = ChatbotService()

        user_badges_ref = db.collection("user_badges").where(
            "user_id", "==", current_user.id
        )
        user_badges_docs = await user_badges_ref.get()
        actual_badges_count = len(user_badges_docs)

        ai_response = await chatbot_service.get_encouragement(
            user_name=current_user.first_name,
            user_age=current_user.age,
            user_points=current_user.points,
            user_badges_count=actual_badges_count,
        )

        response = ChatResponse(response=ai_response, context="encouragement")

        return UniformResponse.success_response(
            message="Encouragement generated successfully", data=response
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get encouragement: {str(e)}"
        )