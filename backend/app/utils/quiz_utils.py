# app/utils/quiz_utils.py
from firebase_admin import firestore

from app.config.logging import log


async def get_quiz_id_for_content(
    db: firestore.AsyncClient, content_id: str, content_type: str, skill_type: str
) -> str | None:
    """Get quiz ID for a given content (video/comic/game)"""
    try:
        quiz_ref = (
            db.collection("quizzes")
            .where("content_id", "==", content_id)
            .where("content_type", "==", content_type)
            .where("skill_type", "==", skill_type)
        )
        quiz_docs = await quiz_ref.get()
        if quiz_docs:
            return quiz_docs[0].id
        return None
    except Exception as e:
        log.warning(f"Failed to get quiz ID for {content_type} {content_id}: {str(e)}")
        return None


async def get_badge_info_for_content(
    db: firestore.AsyncClient, content_id: str, collection: str
) -> dict | None:
    """Get badge information for a content item"""
    try:
        content_ref = db.collection(collection).document(content_id)
        content_doc = await content_ref.get()

        if not content_doc.exists:
            return None

        content_data = content_doc.to_dict()
        badge_id = content_data.get("badge_id")

        if not badge_id:
            return None

        # Get badge details
        badge_ref = db.collection("badges").document(badge_id)
        badge_doc = await badge_ref.get()

        if badge_doc.exists:
            badge_data = badge_doc.to_dict()
            return {
                "badge_id": badge_id,
                "badge_name": badge_data.get("name", ""),
                "badge_url": badge_data.get("image_url", ""),
                "badge_description": badge_data.get("description", ""),
                "badge_points": badge_data.get("points", 5),
            }
        return None
    except Exception as e:
        log.warning(f"Failed to get badge info for {collection} {content_id}: {str(e)}")
        return None
