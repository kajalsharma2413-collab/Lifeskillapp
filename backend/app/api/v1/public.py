from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from firebase_admin import firestore
from pydantic import BaseModel

from app.config.firebase import get_firebase_client
from app.schemas.base import UniformResponse

# Public router - NO AUTHENTICATION REQUIRED
public_router = APIRouter(prefix="/public", tags=["public"])


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


class PublicSkillResponse(BaseModel):
    """Public skill information"""

    title: str
    description: str
    image: str
    skill_type: str
    badge_count: int


@public_router.get("/badges", response_model=UniformResponse[AllBadgesResponse])
async def get_all_badges_public(
    skill_type: str | None = Query(
        None,
        description="Filter by skill type (safety, finance, communication, problem_solving, basic_manners)",
    ),
    limit: int | None = Query(
        None, ge=1, le=100, description="Limit number of results"
    ),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """
    **PUBLIC ENDPOINT** - Get all available badges (no authentication required)

    Query Parameters:
    - skill_type: Filter badges by skill type
    - limit: Maximum number of badges to return

    Returns all badges with their details, total count, and available skill types.
    """
    try:
        badges_ref = db.collection("badges")

        if skill_type:
            badges_ref = badges_ref.where("skill_type", "==", skill_type)

        badges_ref = badges_ref.order_by(
            "created_at", direction=firestore.Query.DESCENDING
        )

        if limit:
            badges_ref = badges_ref.limit(limit)

        badges_docs = await badges_ref.get()

        badges_list = []
        skill_types_set = set()

        for doc in badges_docs:
            badge_data = doc.to_dict()
            skill_type_value = badge_data.get("skill_type", "")

            if skill_type_value:
                skill_types_set.add(skill_type_value)

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


@public_router.get(
    "/badges/{badge_id}", response_model=UniformResponse[PublicBadgeResponse]
)
async def get_badge_by_id_public(
    badge_id: str,
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """
    **PUBLIC ENDPOINT** - Get a specific badge by ID (no authentication required)
    """
    try:
        badge_ref = db.collection("badges").document(badge_id)
        badge_doc = await badge_ref.get()

        if not badge_doc.exists:
            raise HTTPException(status_code=404, detail="Badge not found")

        badge_data = badge_doc.to_dict()
        badge_response = PublicBadgeResponse(
            id=badge_id,
            name=badge_data.get("name", "Unknown Badge"),
            description=badge_data.get("description", ""),
            image_url=badge_data.get("image_url", ""),
            skill_type=badge_data.get("skill_type", ""),
            points=badge_data.get("points", 5),
            created_at=badge_data.get("created_at").isoformat()
            if badge_data.get("created_at")
            else datetime.utcnow().isoformat(),
        )

        return UniformResponse.success_response(
            message="Badge retrieved successfully", data=badge_response
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve badge: {str(e)}"
        )


@public_router.get("/skills", response_model=UniformResponse[list[PublicSkillResponse]])
async def get_life_skills_public(
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """
    **PUBLIC ENDPOINT** - Get all available life skills with badge counts (no authentication required)
    """
    try:
        # Get badge counts for each skill type
        badges_ref = db.collection("badges")
        badges_docs = await badges_ref.get()

        skill_badge_counts = {}
        for doc in badges_docs:
            badge_data = doc.to_dict()
            skill_type = badge_data.get("skill_type", "")
            skill_badge_counts[skill_type] = skill_badge_counts.get(skill_type, 0) + 1

        skills = [
            PublicSkillResponse(
                title="Safety Skills",
                description="Learn how to handle emergencies safely and effectively.",
                image="safety_img",
                skill_type="safety",
                badge_count=skill_badge_counts.get("safety", 0),
            ),
            PublicSkillResponse(
                title="Financial Literacy",
                description="Understand money management, saving, and budgeting.",
                image="finance_img",
                skill_type="finance",
                badge_count=skill_badge_counts.get("finance", 0),
            ),
            PublicSkillResponse(
                title="Communication Skills",
                description="Improve your ability to express yourself and listen to others.",
                image="communication_img",
                skill_type="communication",
                badge_count=skill_badge_counts.get("communication", 0),
            ),
            PublicSkillResponse(
                title="Problem Solving",
                description="Develop strategies to solve problems creatively and logically.",
                image="problem_img",
                skill_type="problem_solving",
                badge_count=skill_badge_counts.get("problem_solving", 0),
            ),
            PublicSkillResponse(
                title="Basic Manners",
                description="Practice kindness, empathy, hygiene, and respectful behavior.",
                image="manners_img",
                skill_type="basic_manners",
                badge_count=skill_badge_counts.get("basic_manners", 0),
            ),
        ]

        return UniformResponse.success_response(
            message="Life skills retrieved successfully", data=skills
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve skills: {str(e)}"
        )


@public_router.get("/stats", response_model=UniformResponse[dict])
async def get_app_statistics_public(
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """
    **PUBLIC ENDPOINT** - Get general app statistics (no authentication required)
    """
    try:
        # Get badge statistics
        badges_ref = db.collection("badges")
        badges_docs = await badges_ref.get()

        total_badges = len(badges_docs)
        skill_type_counts = {}
        total_points_available = 0

        for doc in badges_docs:
            badge_data = doc.to_dict()
            skill_type = badge_data.get("skill_type", "unknown")
            points = badge_data.get("points", 5)

            skill_type_counts[skill_type] = skill_type_counts.get(skill_type, 0) + 1
            total_points_available += points

        # Get user statistics (public counts only)
        users_ref = db.collection("users").where("role", "==", "user")
        users_docs = await users_ref.get()
        total_users = len(users_docs)

        # Get total badges earned
        user_badges_ref = db.collection("user_badges")
        user_badges_docs = await user_badges_ref.get()
        total_badges_earned = len(user_badges_docs)

        unique_badge_earners = set()
        for doc in user_badges_docs:
            user_badge_data = doc.to_dict()
            user_id = user_badge_data.get("user_id")
            if user_id:
                unique_badge_earners.add(user_id)

        stats = {
            "app_info": {
                "name": "Life Skills Learning App",
                "target_age": "8-14 years",
                "skills_available": 5,
                "total_badges": total_badges,
                "total_points_available": total_points_available,
            },
            "user_engagement": {
                "total_users": total_users,
                "total_badges_earned": total_badges_earned,
                "active_badge_earners": len(unique_badge_earners),
                "average_badges_per_active_user": round(
                    total_badges_earned / len(unique_badge_earners), 2
                )
                if unique_badge_earners
                else 0,
            },
            "skill_distribution": skill_type_counts,
            "learning_metrics": {
                "average_points_per_badge": round(
                    total_points_available / total_badges, 2
                )
                if total_badges > 0
                else 0,
                "badge_completion_rate": round(
                    (total_badges_earned / (total_badges * total_users)) * 100, 2
                )
                if total_badges > 0 and total_users > 0
                else 0,
            },
        }

        return UniformResponse.success_response(
            message="App statistics retrieved successfully", data=stats
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve statistics: {str(e)}"
        )
