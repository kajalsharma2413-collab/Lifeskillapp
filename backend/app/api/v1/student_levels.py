# app/api/v1/student_levels.py
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import firestore
from pydantic import BaseModel, Field

from app.api.dependencies.auth import get_current_user
from app.config.firebase import get_firebase_client
from app.models.user import User
from app.schemas.base import UniformResponse

router = APIRouter(prefix="/student-levels", tags=["student-levels"])


class UpdateLevelRequest(BaseModel):
    """Request model for updating student level"""

    level: str = Field(..., description="Student level: beginner, medium, or advanced")
    skill_type: str | None = Field(None, description="Specific skill type (optional)")


class StudentLevelResponse(BaseModel):
    """Response model for student level information"""

    user_id: str
    current_level: str
    skill_type: str | None = None
    updated_at: datetime
    previous_level: str | None = None


@router.put("/update", response_model=UniformResponse[StudentLevelResponse])
async def update_student_level(
    request: UpdateLevelRequest,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """
    Update student's skill level

    **Levels:**
    - `beginner`: Ages 8-10, basic concepts and simple tasks
    - `medium`: Ages 10-12, intermediate challenges and multi-step problems
    - `advanced`: Ages 12-14, complex scenarios and critical thinking
    """
    try:
        # Validate level
        valid_levels = ["beginner", "medium", "advanced"]
        if request.level not in valid_levels:
            return UniformResponse.error_response(
                message="Invalid level",
                errors=[f"Level must be one of: {', '.join(valid_levels)}"],
            )

        # Get current user level data
        user_ref = db.collection("users").document(current_user.id)
        user_doc = await user_ref.get()

        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")

        user_data = user_doc.to_dict()
        previous_level = user_data.get("skill_level", "beginner")

        # Prepare update data
        update_data = {
            "skill_level": request.level,
            "level_updated_at": datetime.utcnow(),
        }

        # If specific skill type is provided, update skill-specific level
        if request.skill_type:
            valid_skills = [
                "safety",
                "finance",
                "communication",
                "problem_solving",
                "basic_manners",
            ]
            if request.skill_type not in valid_skills:
                return UniformResponse.error_response(
                    message="Invalid skill type",
                    errors=[f"Skill type must be one of: {', '.join(valid_skills)}"],
                )

            # Update skill-specific level
            skill_levels = user_data.get("skill_levels", {})
            skill_levels[request.skill_type] = request.level
            update_data["skill_levels"] = skill_levels

        # Update user document
        await user_ref.update(update_data)

        # Log level change for analytics
        await db.collection("level_changes").add(
            {
                "user_id": current_user.id,
                "previous_level": previous_level,
                "new_level": request.level,
                "skill_type": request.skill_type,
                "changed_at": datetime.utcnow(),
                "user_age": user_data.get("age"),
                "change_reason": "manual_update",
            }
        )

        response_data = StudentLevelResponse(
            user_id=current_user.id,
            current_level=request.level,
            skill_type=request.skill_type,
            updated_at=datetime.utcnow(),
            previous_level=previous_level,
        )

        return UniformResponse.success_response(
            message="Student level updated successfully", data=response_data
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update student level: {str(e)}"
        )


@router.get("/current", response_model=UniformResponse[dict])
async def get_current_level(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get current student's skill level information"""
    try:
        user_ref = db.collection("users").document(current_user.id)
        user_doc = await user_ref.get()

        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")

        user_data = user_doc.to_dict()

        level_info = {
            "user_id": current_user.id,
            "overall_level": user_data.get("skill_level", "beginner"),
            "skill_levels": user_data.get("skill_levels", {}),
            "age": user_data.get("age"),
            "level_updated_at": user_data.get("level_updated_at"),
            "level_recommendations": _get_level_recommendations(user_data),
        }

        return UniformResponse.success_response(
            message="Current level retrieved successfully", data=level_info
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve current level: {str(e)}"
        )


@router.post("/auto-adjust", response_model=UniformResponse[StudentLevelResponse])
async def auto_adjust_level(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """
    Automatically adjust student level based on performance data
    """
    try:
        # Get user performance data
        user_badges_ref = db.collection("user_badges").where(
            "user_id", "==", current_user.id
        )
        badges_docs = await user_badges_ref.get()

        # Get problem solving progress
        progress_ref = db.collection("problem_solving_progress").where(
            "user_id", "==", current_user.id
        )
        progress_docs = await progress_ref.get()

        # Calculate performance metrics
        total_badges = len(badges_docs)
        correct_answers = 0
        total_questions = 0

        for doc in progress_docs:
            progress_data = doc.to_dict()
            correct_answers += progress_data.get("questions_correct", 0)
            total_questions += progress_data.get("questions_attempted", 0)

        accuracy_rate = (
            (correct_answers / total_questions) if total_questions > 0 else 0
        )

        # Get current user data
        user_ref = db.collection("users").document(current_user.id)
        user_doc = await user_ref.get()
        user_data = user_doc.to_dict()

        current_level = user_data.get("skill_level", "beginner")
        user_age = user_data.get("age", 8)

        # Auto-adjust logic
        recommended_level = _calculate_recommended_level(
            current_level, accuracy_rate, total_badges, user_age
        )

        if recommended_level != current_level:
            # Update level
            await user_ref.update(
                {
                    "skill_level": recommended_level,
                    "level_updated_at": datetime.utcnow(),
                    "auto_adjusted": True,
                }
            )

            # Log auto-adjustment
            await db.collection("level_changes").add(
                {
                    "user_id": current_user.id,
                    "previous_level": current_level,
                    "new_level": recommended_level,
                    "changed_at": datetime.utcnow(),
                    "change_reason": "auto_adjustment",
                    "performance_metrics": {
                        "accuracy_rate": accuracy_rate,
                        "total_badges": total_badges,
                        "total_questions": total_questions,
                    },
                }
            )

            response_data = StudentLevelResponse(
                user_id=current_user.id,
                current_level=recommended_level,
                updated_at=datetime.utcnow(),
                previous_level=current_level,
            )

            return UniformResponse.success_response(
                message=f"Level auto-adjusted from {current_level} to {recommended_level}",
                data=response_data,
            )
        else:
            return UniformResponse.success_response(
                message=f"Current level ({current_level}) is appropriate, no adjustment needed",
                data=StudentLevelResponse(
                    user_id=current_user.id,
                    current_level=current_level,
                    updated_at=datetime.utcnow(),
                ),
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to auto-adjust level: {str(e)}"
        )


@router.get("/recommendations", response_model=UniformResponse[dict])
async def get_level_recommendations(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get level recommendations based on age and performance"""
    try:
        user_ref = db.collection("users").document(current_user.id)
        user_doc = await user_ref.get()
        user_data = user_doc.to_dict()

        recommendations = _get_level_recommendations(user_data)

        return UniformResponse.success_response(
            message="Level recommendations retrieved successfully", data=recommendations
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get recommendations: {str(e)}"
        )


def _calculate_recommended_level(
    current_level: str, accuracy_rate: float, total_badges: int, user_age: int
) -> str:
    """Calculate recommended level based on performance metrics"""

    # Age-based baseline
    if user_age <= 9:
        baseline = "beginner"
    elif user_age <= 11:
        baseline = "medium"
    else:
        baseline = "advanced"

    # Performance adjustments
    if accuracy_rate >= 0.85 and total_badges >= 5:
        # High performance - consider upgrading
        if current_level == "beginner":
            return "medium"
        elif current_level == "medium" and user_age >= 11:
            return "advanced"
    elif accuracy_rate < 0.6 and total_badges < 3:
        # Low performance - consider downgrading
        if current_level == "advanced":
            return "medium"
        elif current_level == "medium" and user_age <= 9:
            return "beginner"

    return baseline


def _get_level_recommendations(user_data: dict) -> dict:
    """Get level recommendations based on user data"""
    age = user_data.get("age", 8)
    current_level = user_data.get("skill_level", "beginner")

    recommendations = {
        "current_level": current_level,
        "age_appropriate_level": "beginner"
        if age <= 9
        else "medium"
        if age <= 11
        else "advanced",
        "level_descriptions": {
            "beginner": {
                "age_range": "8-10 years",
                "description": "Basic concepts, simple tasks, foundational skills",
                "features": [
                    "Simple questions",
                    "Visual aids",
                    "Step-by-step guidance",
                ],
            },
            "medium": {
                "age_range": "10-12 years",
                "description": "Intermediate challenges, multi-step problems",
                "features": [
                    "Complex scenarios",
                    "Multiple choice reasoning",
                    "Practical applications",
                ],
            },
            "advanced": {
                "age_range": "12-14 years",
                "description": "Complex scenarios, critical thinking, real-world applications",
                "features": [
                    "Critical analysis",
                    "Problem solving",
                    "Independent thinking",
                ],
            },
        },
    }

    # Add specific recommendations
    if age < 8:
        recommendations["recommendation"] = (
            "Consider beginner level with adult supervision"
        )
    elif age > 14:
        recommendations["recommendation"] = (
            "Advanced level appropriate, consider teen-focused content"
        )
    else:
        recommendations["recommendation"] = (
            f"Age-appropriate level is {recommendations['age_appropriate_level']}"
        )

    return recommendations
