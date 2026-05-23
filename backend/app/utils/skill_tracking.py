# app/utils/skill_tracking.py
from datetime import datetime

from firebase_admin import firestore

from app.config.logging import log
from app.schemas.base import UniformResponse
from app.schemas.skill import SkillType


async def track_skill_engagement(
    user_id: str,
    skill_type: SkillType,
    action: str,
    db: firestore.AsyncClient,
    content_type: str = "skill",
    content_id: str = None,
):
    """Helper function to track skill engagement"""
    try:
        engagement_data = {
            "user_id": user_id,
            "skill_type": skill_type.value,
            "content_type": content_type,
            "content_id": content_id or f"{skill_type.value}_main",
            "action": action,
            "timestamp": datetime.utcnow(),
        }

        # Add engagement record
        await db.collection("skill_engagements").add(engagement_data)

        # Update skill engagement stats (aggregated counter)
        stats_ref = db.collection("skill_stats").document(
            f"{user_id}_{skill_type.value}"
        )
        stats_doc = await stats_ref.get()

        if stats_doc.exists:
            current_data = stats_doc.to_dict()
            views = current_data.get("views", 0) + 1
            await stats_ref.update({"views": views, "updated_at": datetime.utcnow()})
        else:
            await stats_ref.set(
                {
                    "user_id": user_id,
                    "skill_type": skill_type.value,
                    "views": 1,
                    "quizzes_completed": 0,
                    "avg_score": 0.0,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            )

        log.success(
            f"Skill engagement tracked: {user_id} - {skill_type.value} - {action}"
        )

        return UniformResponse.success_response(
            message=f"{skill_type.value.replace('_', ' ').title()} engagement tracked successfully",
            data={"action": action, "skill_type": skill_type.value},
        )

    except Exception as e:
        log.error(f"Failed to track skill engagement: {str(e)}")
        return UniformResponse.error_response(
            message="Failed to track skill engagement", errors=[str(e)]
        )
