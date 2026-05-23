# app/api/v1/ai.py
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.auth import get_current_user
from app.models.base import UserRole
from app.models.user import User
from app.schemas.base import UniformResponse
from app.schemas.skill import SupportiveTipsRequest, SupportiveTipsResponse
from app.services.ai import get_supportive_tips

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/supportive-tips", response_model=UniformResponse[SupportiveTipsResponse])
async def get_ai_supportive_tips(
    request: SupportiveTipsRequest,
    current_user: User = Depends(get_current_user),
):
    """Get AI-generated supportive tips based on diary entries"""
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=403, detail="Only parents can access this endpoint"
        )

    if not request.entries:
        raise HTTPException(status_code=400, detail="No diary entries provided")

    tips_response = await get_supportive_tips(request.entries)

    return UniformResponse.success_response(
        message="Supportive tips generated successfully", data=tips_response
    )