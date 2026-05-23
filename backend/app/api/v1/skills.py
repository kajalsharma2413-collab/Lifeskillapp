# app/api/v1/skills.py
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from firebase_admin import firestore
from pydantic import BaseModel

from app.api.dependencies.auth import get_current_user
from app.config.firebase import get_firebase_client
from app.models.skill import SkillType
from app.models.user import User
from app.schemas.base import UniformResponse
from app.schemas.skill import LifeSkillResponse
from app.utils.skill_tracking import track_skill_engagement

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=UniformResponse[list[LifeSkillResponse]])
async def get_life_skills():
    """Get all available life skills"""
    skills = [
        LifeSkillResponse(
            title="Safety Skills",
            image="safety_img",  # Frontend will handle image paths
            description="Learn how to handle emergencies safely and effectively.",
            route="/safetyskills",
        ),
        LifeSkillResponse(
            title="Financial Literacy",
            image="finance_img",
            description="Understand money management, saving, and budgeting.",
            route="/financeskills",
        ),
        LifeSkillResponse(
            title="Communication Skills",
            image="communication_img",
            description="Improve your ability to express yourself and listen to others.",
            route="/conversation",
        ),
        LifeSkillResponse(
            title="Problem Solving",
            image="problem_img",
            description="Develop strategies to solve problems creatively and logically.",
            route="/problem-solving",
        ),
        LifeSkillResponse(
            title="Coming Soon: Basic Manners",
            image="manners_img",
            description="Practice kindness, empathy, hygiene, and respectful behavior.",
            route=None,
        ),
    ]

    return UniformResponse.success_response(
        message="Life skills retrieved successfully", data=skills
    )


@router.post("/safety/view", response_model=UniformResponse[dict])
async def track_safety_skill_view(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Track that user viewed safety skills"""
    return await track_skill_engagement(
        user_id=current_user.id, skill_type=SkillType.SAFETY, action="view", db=db
    )


@router.post("/finance/view", response_model=UniformResponse[dict])
async def track_finance_skill_view(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Track that user viewed finance skills"""
    return await track_skill_engagement(
        user_id=current_user.id, skill_type=SkillType.FINANCE, action="view", db=db
    )


@router.post("/communication/view", response_model=UniformResponse[dict])
async def track_communication_skill_view(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Track that user viewed communication skills"""
    return await track_skill_engagement(
        user_id=current_user.id,
        skill_type=SkillType.COMMUNICATION,
        action="view",
        db=db,
    )


@router.post("/problem-solving/view", response_model=UniformResponse[dict])
async def track_problem_solving_skill_view(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Track that user viewed problem solving skills"""
    return await track_skill_engagement(
        user_id=current_user.id,
        skill_type=SkillType.PROBLEM_SOLVING,
        action="view",
        db=db,
    )


class PublicBadgeResponse(BaseModel):
    """Public badge response schema"""

    id: str
    name: str
    description: str
    image_url: str
    skill_type: str
    points: int
    created_at: str


class AllBadgesResponse(BaseModel):
    """Response for all badges endpoint"""

    badges: list[PublicBadgeResponse]
    total_count: int
    skill_types: list[str]


# Add this new endpoint to your existing router
@router.get("/badges/all", response_model=UniformResponse[AllBadgesResponse])
async def get_all_badges_public(
    skill_type: str | None = Query(None, description="Filter by skill type"),
    limit: int | None = Query(
        None, ge=1, le=100, description="Limit number of results"
    ),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """
    Get all available badges - PUBLIC ENDPOINT (no authentication required)

    This endpoint allows anyone to fetch all badges in the system.
    Can be filtered by skill_type and limited in results.
    """
    try:
        # Base query to get all badges
        badges_ref = db.collection("badges")

        # Apply skill_type filter if provided
        if skill_type:
            badges_ref = badges_ref.where("skill_type", "==", skill_type)

        # Order by creation date (newest first)
        badges_ref = badges_ref.order_by(
            "created_at", direction=firestore.Query.DESCENDING
        )

        # Apply limit if provided
        if limit:
            badges_ref = badges_ref.limit(limit)

        # Execute query
        badges_docs = await badges_ref.get()

        # Process badge data
        badges_list = []
        skill_types_set = set()

        for doc in badges_docs:
            badge_data = doc.to_dict()
            skill_type_value = badge_data.get("skill_type", "")

            # Add to skill types set for response metadata
            if skill_type_value:
                skill_types_set.add(skill_type_value)

            # Create badge response object
            badge_response = PublicBadgeResponse(
                id=doc.id,
                name=badge_data.get("name", "Unknown Badge"),
                description=badge_data.get("description", ""),
                image_url=badge_data.get("image_url", ""),
                skill_type=skill_type_value,
                points=badge_data.get("points", 5),
                created_at=badge_data.get("created_at").isoformat()
                if badge_data.get("created_at")
                else datetime.utcnow().isoformat(),
            )
            badges_list.append(badge_response)

        # Prepare response data
        response_data = AllBadgesResponse(
            badges=badges_list,
            total_count=len(badges_list),
            skill_types=sorted(skill_types_set),
        )

        return UniformResponse.success_response(
            message=f"Successfully retrieved {len(badges_list)} badges",
            data=response_data,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve badges: {str(e)}"
        )


@router.get(
    "/badges/skills/{skill_type}",
    response_model=UniformResponse[list[PublicBadgeResponse]],
)
async def get_badges_by_skill_public(
    skill_type: str,
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """
    Get all badges for a specific skill type - PUBLIC ENDPOINT

    Available skill types: safety, finance, communication, problem_solving, basic_manners
    """
    try:
        # Validate skill type
        valid_skills = [
            "safety",
            "finance",
            "communication",
            "problem_solving",
            "basic_manners",
        ]
        if skill_type not in valid_skills:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid skill type. Must be one of: {', '.join(valid_skills)}",
            )

        # Query badges for specific skill type
        badges_ref = db.collection("badges").where("skill_type", "==", skill_type)
        badges_docs = await badges_ref.get()

        badges_list = []
        for doc in badges_docs:
            badge_data = doc.to_dict()
            badge_response = PublicBadgeResponse(
                id=doc.id,
                name=badge_data.get("name", "Unknown Badge"),
                description=badge_data.get("description", ""),
                image_url=badge_data.get("image_url", ""),
                skill_type=badge_data.get("skill_type", ""),
                points=badge_data.get("points", 5),
                created_at=badge_data.get("created_at").isoformat()
                if badge_data.get("created_at")
                else datetime.utcnow().isoformat(),
            )
            badges_list.append(badge_response)

        return UniformResponse.success_response(
            message=f"Successfully retrieved {len(badges_list)} badges for {skill_type}",
            data=badges_list,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve badges for skill type {skill_type}: {str(e)}",
        )


@router.get("/badges/stats", response_model=UniformResponse[dict])
async def get_badge_statistics_public(
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """
    Get badge statistics - PUBLIC ENDPOINT

    Returns general statistics about badges in the system
    """
    try:
        # Get all badges
        badges_ref = db.collection("badges")
        badges_docs = await badges_ref.get()

        # Calculate statistics
        total_badges = len(badges_docs)
        skill_type_counts = {}
        total_points_available = 0

        for doc in badges_docs:
            badge_data = doc.to_dict()
            skill_type = badge_data.get("skill_type", "unknown")
            points = badge_data.get("points", 5)

            # Count by skill type
            skill_type_counts[skill_type] = skill_type_counts.get(skill_type, 0) + 1
            total_points_available += points

        # Get total users who have earned badges
        user_badges_ref = db.collection("user_badges")
        user_badges_docs = await user_badges_ref.get()

        unique_badge_earners = set()
        total_badges_earned = len(user_badges_docs)

        for doc in user_badges_docs:
            user_badge_data = doc.to_dict()
            user_id = user_badge_data.get("user_id")
            if user_id:
                unique_badge_earners.add(user_id)

        stats = {
            "total_badges_available": total_badges,
            "total_badges_earned": total_badges_earned,
            "total_points_available": total_points_available,
            "unique_badge_earners": len(unique_badge_earners),
            "skill_type_distribution": skill_type_counts,
            "average_points_per_badge": round(total_points_available / total_badges, 2)
            if total_badges > 0
            else 0,
        }

        return UniformResponse.success_response(
            message="Badge statistics retrieved successfully", data=stats
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve badge statistics: {str(e)}"
        )
