# app/api/v1/router.py
from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.admin_dashboard import router as admin_dashboard_router
from app.api.v1.ai import router as ai_router
from app.api.v1.auth import router as auth_router
from app.api.v1.chatbot import router as chatbot_router
from app.api.v1.diary import router as diary_router
from app.api.v1.finance import router as finance_router
from app.api.v1.mentor_chatbot import router as mentor_router
from app.api.v1.parent import router as parent_router
from app.api.v1.problem_solving import router as problem_solving_router
from app.api.v1.public import public_router  # Import the new public router
from app.api.v1.quiz import router as quiz_router
from app.api.v1.rag_chat import router as rag_chat_router
from app.api.v1.safety import router as safety_router
from app.api.v1.skills import router as skills_router
from app.api.v1.users import router as users_router
from app.api.v1.vapi import router as vapi_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(admin_router)
api_router.include_router(mentor_router)
api_router.include_router(vapi_router)
api_router.include_router(rag_chat_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(parent_router)
api_router.include_router(ai_router)
api_router.include_router(skills_router)
api_router.include_router(safety_router)
api_router.include_router(finance_router)
api_router.include_router(quiz_router)
api_router.include_router(problem_solving_router)
api_router.include_router(diary_router)
api_router.include_router(chatbot_router)
api_router.include_router(admin_dashboard_router)  # NEW
api_router.include_router(public_router)  # NEW
