# app/api/v1/admin.py
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import firestore
from pydantic import BaseModel

from app.api.dependencies.auth import get_current_user
from app.config.firebase import get_firebase_client
from app.models.base import UserRole
from app.models.user import User
from app.schemas.base import UniformResponse
from app.schemas.skill import (
    ComicCreateRequest,
    FinanceLevelCreateRequest,
    FinanceLevelUpdateRequest,
    GameItemCreateRequest,
    GameItemUpdateRequest,
    QuestionCreateRequest,
    QuestionOptionCreateRequest,
    VideoCreateRequest,
)
from app.utils.quiz_utils import get_badge_info_for_content

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to ensure user is admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# Finance Video Question Management
@router.post("/finance/video/{video_id}/question", response_model=UniformResponse[dict])
async def add_finance_video_question(
    video_id: str,
    request: QuestionCreateRequest,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Add a question to a finance video"""
    try:
        # First, get or create a quiz for this video
        quiz_ref = (
            db.collection("quizzes")
            .where("content_id", "==", video_id)
            .where("content_type", "==", "video")
        )
        quiz_docs = await quiz_ref.get()

        if quiz_docs:
            quiz_id = quiz_docs[0].id
        else:
            # Create a new quiz for this video
            quiz_data = {
                "title": f"Quiz for Finance Video {video_id}",
                "skill_type": "finance",
                "content_type": "video",
                "content_id": video_id,
                "min_score": 50,
                "badge_id": None,
                "created_at": datetime.utcnow(),
            }
            quiz_doc_ref = await db.collection("quizzes").add(quiz_data)
            quiz_id = quiz_doc_ref[1].id

        # Add the question
        question_data = {
            "quiz_id": quiz_id,
            "question_text": request.question_text,
            "question_order": request.question_order,
            "created_at": datetime.utcnow(),
        }
        question_ref = await db.collection("questions").add(question_data)

        return UniformResponse.success_response(
            message="Question added successfully",
            data={"question_id": question_ref[1].id, "quiz_id": quiz_id},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add question: {str(e)}")


@router.post(
    "/finance/video/question/{question_id}/option", response_model=UniformResponse[dict]
)
async def add_finance_question_option(
    question_id: str,
    request: QuestionOptionCreateRequest,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Add an option to a finance video question"""
    try:
        option_data = {
            "question_id": question_id,
            "option_text": request.option_text,
            "is_correct": request.is_correct,
            "option_order": request.option_order,
            "created_at": datetime.utcnow(),
        }
        option_ref = await db.collection("question_options").add(option_data)
        return UniformResponse.success_response(
            message="Question option added successfully",
            data={"option_id": option_ref[1].id},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to add question option: {str(e)}"
        )


# Safety Comic Question Management
@router.post("/safety/comic/{comic_id}/question", response_model=UniformResponse[dict])
async def add_safety_comic_question(
    comic_id: str,
    request: QuestionCreateRequest,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Add a question to a safety comic"""
    try:
        # First, get or create a quiz for this comic
        quiz_ref = (
            db.collection("quizzes")
            .where("content_id", "==", comic_id)
            .where("content_type", "==", "comic")
        )
        quiz_docs = await quiz_ref.get()
        if quiz_docs:
            quiz_id = quiz_docs[0].id
        else:
            # Create a new quiz for this comic
            quiz_data = {
                "title": f"Quiz for Safety Comic {comic_id}",
                "skill_type": "safety",
                "content_type": "comic",
                "content_id": comic_id,
                "min_score": 50,
                "badge_id": None,
                "created_at": datetime.utcnow(),
            }
            quiz_doc_ref = await db.collection("quizzes").add(quiz_data)
            quiz_id = quiz_doc_ref[1].id
        # Add the question
        question_data = {
            "quiz_id": quiz_id,
            "question_text": request.question_text,
            "question_order": request.question_order,
            "created_at": datetime.utcnow(),
        }
        question_ref = await db.collection("questions").add(question_data)
        return UniformResponse.success_response(
            message="Question added successfully",
            data={"question_id": question_ref[1].id, "quiz_id": quiz_id},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add question: {str(e)}")


@router.post(
    "/safety/comic/question/{question_id}/option", response_model=UniformResponse[dict]
)
async def add_safety_comic_question_option(
    question_id: str,
    request: QuestionOptionCreateRequest,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Add an option to a safety comic question"""
    try:
        option_data = {
            "question_id": question_id,
            "option_text": request.option_text,
            "is_correct": request.is_correct,
            "option_order": request.option_order,
            "created_at": datetime.utcnow(),
        }
        option_ref = await db.collection("question_options").add(option_data)
        return UniformResponse.success_response(
            message="Question option added successfully",
            data={"option_id": option_ref[1].id},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to add question option: {str(e)}"
        )


# Finance Comic Question Management
@router.post("/finance/comic/{comic_id}/question", response_model=UniformResponse[dict])
async def add_finance_comic_question(
    comic_id: str,
    request: QuestionCreateRequest,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Add a question to a finance comic"""
    try:
        # First, get or create a quiz for this comic
        quiz_ref = (
            db.collection("quizzes")
            .where("content_id", "==", comic_id)
            .where("content_type", "==", "comic")
        )
        quiz_docs = await quiz_ref.get()
        if quiz_docs:
            quiz_id = quiz_docs[0].id
        else:
            # Create a new quiz for this comic
            quiz_data = {
                "title": f"Quiz for Finance Comic {comic_id}",
                "skill_type": "finance",
                "content_type": "comic",
                "content_id": comic_id,
                "min_score": 50,
                "badge_id": None,
                "created_at": datetime.utcnow(),
            }
            quiz_doc_ref = await db.collection("quizzes").add(quiz_data)
            quiz_id = quiz_doc_ref[1].id
        # Add the question
        question_data = {
            "quiz_id": quiz_id,
            "question_text": request.question_text,
            "question_order": request.question_order,
            "created_at": datetime.utcnow(),
        }
        question_ref = await db.collection("questions").add(question_data)
        return UniformResponse.success_response(
            message="Question added successfully",
            data={"question_id": question_ref[1].id, "quiz_id": quiz_id},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add question: {str(e)}")


@router.post(
    "/finance/comic/question/{question_id}/option", response_model=UniformResponse[dict]
)
async def add_finance_comic_question_option(
    question_id: str,
    request: QuestionOptionCreateRequest,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Add an option to a finance comic question"""
    try:
        option_data = {
            "question_id": question_id,
            "option_text": request.option_text,
            "is_correct": request.is_correct,
            "option_order": request.option_order,
            "created_at": datetime.utcnow(),
        }
        option_ref = await db.collection("question_options").add(option_data)
        return UniformResponse.success_response(
            message="Question option added successfully",
            data={"option_id": option_ref[1].id},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to add question option: {str(e)}"
        )


@router.put("/finance/level/{level_id}", response_model=UniformResponse[dict])
async def update_finance_level(
    level_id: str,
    request: FinanceLevelUpdateRequest,  # Use proper model instead of dict
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Update a finance game level"""
    try:
        # Check if level exists
        level_ref = db.collection("game_levels").document(level_id)
        level_doc = await level_ref.get()
        if not level_doc.exists:
            raise HTTPException(status_code=404, detail="Level not found")

        # Prepare update data - only include non-None values
        update_data = {}
        if request.level_number is not None:
            update_data["level_number"] = request.level_number
        if request.title is not None:
            update_data["title"] = request.title
        if request.description is not None:
            update_data["description"] = request.description
        if request.income is not None:
            update_data["income"] = request.income
        if request.difficulty is not None:
            update_data["difficulty"] = request.difficulty

        update_data["updated_at"] = datetime.utcnow()

        await level_ref.update(update_data)

        return UniformResponse.success_response(
            message="Finance level updated successfully",
            data={"level_id": level_id},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update finance level: {str(e)}"
        )


@router.put(
    "/finance/level/{level_id}/item/{item_id}", response_model=UniformResponse[dict]
)
async def update_finance_level_item(
    level_id: str,
    item_id: str,
    request: GameItemUpdateRequest,  # Use proper model instead of dict
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Update an item in a finance game level"""
    try:
        # Check if item exists
        item_ref = db.collection("game_items").document(item_id)
        item_doc = await item_ref.get()
        if not item_doc.exists:
            raise HTTPException(status_code=404, detail="Item not found")

        # Validate item_type if provided
        if request.item_type is not None and request.item_type not in ["need", "want"]:
            raise HTTPException(
                status_code=400, detail="item_type must be 'need' or 'want'"
            )

        # Prepare update data - only include non-None values
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.cost is not None:
            update_data["cost"] = request.cost
        if request.item_type is not None:
            update_data["item_type"] = request.item_type
        if request.description is not None:
            update_data["description"] = request.description

        update_data["updated_at"] = datetime.utcnow()

        await item_ref.update(update_data)

        return UniformResponse.success_response(
            message="Finance level item updated successfully",
            data={"item_id": item_id, "level_id": level_id},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update finance level item: {str(e)}"
        )


# Add comprehensive finance level validation endpoint
@router.post("/finance/level/{level_id}/validate", response_model=UniformResponse[dict])
async def validate_finance_level(
    level_id: str,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Validate a finance level is complete and ready for students"""
    try:
        # Check if level exists
        level_ref = db.collection("game_levels").document(level_id)
        level_doc = await level_ref.get()
        if not level_doc.exists:
            raise HTTPException(status_code=404, detail="Level not found")

        level_data = level_doc.to_dict()
        validation_results = {
            "level_id": level_id,
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": [],
        }

        # Check basic level data
        if not level_data.get("title"):
            validation_results["errors"].append("Level title is required")
            validation_results["valid"] = False

        if not level_data.get("description"):
            validation_results["warnings"].append("Level description is recommended")

        if level_data.get("income", 0) <= 0:
            validation_results["errors"].append("Level income must be greater than 0")
            validation_results["valid"] = False

        # Check if level has items
        items_ref = db.collection("game_items").where("level_id", "==", level_id)
        items_docs = await items_ref.get()

        if not items_docs:
            validation_results["errors"].append("Level must have at least one item")
            validation_results["valid"] = False
        else:
            needs_count = 0
            wants_count = 0
            total_cost = 0

            for item_doc in items_docs:
                item_data = item_doc.to_dict()
                item_type = item_data.get("item_type", "")
                item_cost = item_data.get("cost", 0)

                if item_type == "need":
                    needs_count += 1
                elif item_type == "want":
                    wants_count += 1

                total_cost += item_cost

            # Validation rules for finance game balance
            if needs_count == 0:
                validation_results["errors"].append(
                    "Level must have at least one 'need' item"
                )
                validation_results["valid"] = False

            if wants_count == 0:
                validation_results["warnings"].append(
                    "Level should have at least one 'want' item for better learning"
                )

            income = level_data.get("income", 0)
            if total_cost <= income:
                validation_results["warnings"].append(
                    "Total item cost should exceed income to create financial decision-making scenarios"
                )

            if total_cost < income * 0.8:
                validation_results["suggestions"].append(
                    "Consider adding more items to create challenging financial decisions"
                )

        # Check if level has a quiz
        quiz_ref = (
            db.collection("quizzes")
            .where("content_id", "==", level_id)
            .where("content_type", "==", "game")
            .where("skill_type", "==", "finance")
        )
        quiz_docs = await quiz_ref.get()

        if not quiz_docs:
            validation_results["warnings"].append(
                "Level should have a quiz for knowledge assessment"
            )
        else:
            # Check quiz has questions
            quiz_id = quiz_docs[0].id
            questions_ref = db.collection("questions").where("quiz_id", "==", quiz_id)
            questions_docs = await questions_ref.get()

            if not questions_docs:
                validation_results["warnings"].append("Quiz should have questions")
            elif len(questions_docs) < 3:
                validation_results["suggestions"].append(
                    "Quiz should have at least 3-5 questions for comprehensive assessment"
                )

        return UniformResponse.success_response(
            message="Finance level validation completed",
            data=validation_results,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to validate finance level: {str(e)}"
        )


# Add bulk operations for finance management
@router.post("/finance/levels/bulk-create", response_model=UniformResponse[dict])
async def bulk_create_finance_levels(
    levels: list[FinanceLevelCreateRequest],
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Create multiple finance levels at once"""
    try:
        created_levels = []
        errors = []

        for i, level_request in enumerate(levels):
            try:
                level_data = {
                    "level_number": level_request.level_number,
                    "title": level_request.title,
                    "description": level_request.description,
                    "income": level_request.income,
                    "difficulty": level_request.difficulty,
                    "skill_type": "finance",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
                level_ref = await db.collection("game_levels").add(level_data)
                created_levels.append(
                    {
                        "index": i,
                        "level_id": level_ref[1].id,
                        "level_number": level_request.level_number,
                        "title": level_request.title,
                    }
                )
            except Exception as e:
                errors.append(
                    {
                        "index": i,
                        "title": level_request.title,
                        "error": str(e),
                    }
                )

        return UniformResponse.success_response(
            message=f"Bulk creation completed: {len(created_levels)} levels created, {len(errors)} errors",
            data={
                "created_levels": created_levels,
                "errors": errors,
                "total_requested": len(levels),
                "total_created": len(created_levels),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to bulk create finance levels: {str(e)}"
        )


def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to ensure user is admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ==================== SAFETY VIDEO ADMIN APIs ====================
@router.get("/safety/videos", response_model=UniformResponse[dict])
async def get_all_safety_videos_admin(
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get all safety videos for admin management with badge information"""
    try:
        videos_ref = db.collection("videos").where("skill_type", "==", "safety")
        videos_docs = await videos_ref.get()

        videos = []
        for doc in videos_docs:
            data = doc.to_dict()
            video_id = doc.id

            # Get badge information
            badge_info = await get_badge_info_for_content(db, video_id, "videos")

            video_data = {
                "id": video_id,
                "title": data.get("title", ""),
                "description": data.get("description", ""),
                "video_url": data.get("video_url", ""),
                "thumbnail_url": data.get("thumbnail_url", ""),
                "likes": data.get("likes", 0),
                "dislikes": data.get("dislikes", 0),
                "view_count": data.get("view_count", 0),
                "created_at": data.get("created_at"),
                "badge_id": data.get(
                    "badge_id"
                ),  # ✅ FIXED: Include badge_id from content
            }

            # ✅ FIXED: Add resolved badge information
            if badge_info:
                video_data.update(
                    {
                        "badge_name": badge_info["badge_name"],
                        "badge_url": badge_info["badge_url"],
                        "badge_points": badge_info["badge_points"],
                        "badge_description": badge_info["badge_description"],
                    }
                )

            videos.append(video_data)

        return UniformResponse.success_response(
            message="Safety videos retrieved successfully", data={"videos": videos}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve safety videos: {str(e)}"
        )


@router.post("/safety/video", response_model=UniformResponse[dict])
async def create_safety_video(
    request: VideoCreateRequest,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Create a new safety video"""
    try:
        video_data = {
            "title": request.title,
            "description": request.description,
            "video_url": request.video_url,
            "thumbnail_url": request.thumbnail_url,
            "skill_type": request.skill_type.value,
            "likes": 0,
            "dislikes": 0,
            "view_count": 0,
            "badge_id": request.badge_id,  # ✅ This should work now
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        video_ref = await db.collection("videos").add(video_data)
        return UniformResponse.success_response(
            message="Safety video created successfully",
            data={
                "video_id": video_ref[1].id,
                "badge_id": request.badge_id,  # ✅ FIXED: Include badge_id in response
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create safety video: {str(e)}"
        )


@router.delete("/safety/video/{video_id}", response_model=UniformResponse[dict])
async def delete_safety_video(
    video_id: str,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Delete a safety video"""
    try:
        video_ref = db.collection("videos").document(video_id)
        video_doc = await video_ref.get()
        if not video_doc.exists:
            raise HTTPException(status_code=404, detail="Video not found")

        await video_ref.delete()
        return UniformResponse.success_response(
            message="Safety video deleted successfully", data={"video_id": video_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete safety video: {str(e)}"
        )


# ==================== SAFETY COMIC ADMIN APIs ====================
@router.get("/safety/comics", response_model=UniformResponse[dict])
async def get_all_safety_comics_admin(
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get all safety comics for admin management with badge information"""
    try:
        comics_ref = db.collection("comics").where("skill_type", "==", "safety")
        comics_docs = await comics_ref.get()

        comics = []
        for doc in comics_docs:
            data = doc.to_dict()
            comic_id = doc.id

            # Get badge information
            badge_info = await get_badge_info_for_content(db, comic_id, "comics")

            comic_data = {
                "id": comic_id,
                "title": data.get("title", ""),
                "description": data.get("description", ""),
                "pdf_url": data.get("pdf_url", ""),
                "thumbnail_url": data.get("thumbnail_url", ""),
                "likes": data.get("likes", 0),
                "dislikes": data.get("dislikes", 0),
                "view_count": data.get("view_count", 0),
                "created_at": data.get("created_at"),
                "badge_id": data.get(
                    "badge_id"
                ),  # ✅ FIXED: Include badge_id from content
            }

            # ✅ FIXED: Add resolved badge information
            if badge_info:
                comic_data.update(
                    {
                        "badge_name": badge_info["badge_name"],
                        "badge_url": badge_info["badge_url"],
                        "badge_points": badge_info["badge_points"],
                        "badge_description": badge_info["badge_description"],
                    }
                )

            comics.append(comic_data)

        return UniformResponse.success_response(
            message="Safety comics retrieved successfully", data={"comics": comics}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve safety comics: {str(e)}"
        )


@router.post("/safety/comic", response_model=UniformResponse[dict])
async def create_safety_comic(
    request: ComicCreateRequest,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Create a new safety comic"""
    try:
        comic_data = {
            "title": request.title,
            "description": request.description,
            "pdf_url": request.pdf_url,
            "thumbnail_url": request.thumbnail_url,
            "skill_type": request.skill_type.value,
            "likes": 0,
            "dislikes": 0,
            "view_count": 0,
            "badge_id": request.badge_id,  # ✅ This should work now
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        comic_ref = await db.collection("comics").add(comic_data)
        return UniformResponse.success_response(
            message="Safety comic created successfully",
            data={
                "comic_id": comic_ref[1].id,
                "badge_id": request.badge_id,  # ✅ FIXED: Include badge_id in response
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create safety comic: {str(e)}"
        )


@router.delete("/safety/comic/{comic_id}", response_model=UniformResponse[dict])
async def delete_safety_comic(
    comic_id: str,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Delete a safety comic"""
    try:
        comic_ref = db.collection("comics").document(comic_id)
        comic_doc = await comic_ref.get()
        if not comic_doc.exists:
            raise HTTPException(status_code=404, detail="Comic not found")

        await comic_ref.delete()
        return UniformResponse.success_response(
            message="Safety comic deleted successfully", data={"comic_id": comic_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete safety comic: {str(e)}"
        )


# ==================== FINANCE VIDEO ADMIN APIs ====================
@router.get("/finance/videos", response_model=UniformResponse[dict])
async def get_all_finance_videos_admin(
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get all finance videos for admin management with badge information"""
    try:
        videos_ref = db.collection("videos").where("skill_type", "==", "finance")
        videos_docs = await videos_ref.get()

        videos = []
        for doc in videos_docs:
            data = doc.to_dict()
            video_id = doc.id

            # Get badge information
            badge_info = await get_badge_info_for_content(db, video_id, "videos")

            video_data = {
                "id": video_id,
                "title": data.get("title", ""),
                "description": data.get("description", ""),
                "video_url": data.get("video_url", ""),
                "thumbnail_url": data.get("thumbnail_url", ""),
                "likes": data.get("likes", 0),
                "dislikes": data.get("dislikes", 0),
                "view_count": data.get("view_count", 0),
                "created_at": data.get("created_at"),
                "badge_id": data.get(
                    "badge_id"
                ),  # ✅ FIXED: Include badge_id from content
            }

            # ✅ FIXED: Add resolved badge information
            if badge_info:
                video_data.update(
                    {
                        "badge_name": badge_info["badge_name"],
                        "badge_url": badge_info["badge_url"],
                        "badge_points": badge_info["badge_points"],
                        "badge_description": badge_info["badge_description"],
                    }
                )

            videos.append(video_data)

        return UniformResponse.success_response(
            message="Finance videos retrieved successfully", data={"videos": videos}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve finance videos: {str(e)}"
        )


@router.post("/finance/video", response_model=UniformResponse[dict])
async def create_finance_video(
    request: VideoCreateRequest,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Create a new finance video"""
    try:
        video_data = {
            "title": request.title,
            "description": request.description,
            "video_url": request.video_url,
            "thumbnail_url": request.thumbnail_url,
            "skill_type": request.skill_type.value,
            "likes": 0,
            "dislikes": 0,
            "view_count": 0,
            "badge_id": request.badge_id,  # ✅ This should work now
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        video_ref = await db.collection("videos").add(video_data)
        return UniformResponse.success_response(
            message="Finance video created successfully",
            data={
                "video_id": video_ref[1].id,
                "badge_id": request.badge_id,  # ✅ FIXED: Include badge_id in response
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create finance video: {str(e)}"
        )


@router.delete("/finance/video/{video_id}", response_model=UniformResponse[dict])
async def delete_finance_video(
    video_id: str,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Delete a finance video"""
    try:
        video_ref = db.collection("videos").document(video_id)
        video_doc = await video_ref.get()
        if not video_doc.exists:
            raise HTTPException(status_code=404, detail="Video not found")

        await video_ref.delete()
        return UniformResponse.success_response(
            message="Finance video deleted successfully", data={"video_id": video_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete finance video: {str(e)}"
        )


# ==================== FINANCE COMIC ADMIN APIs ====================
@router.get("/finance/comics", response_model=UniformResponse[dict])
async def get_all_finance_comics_admin(
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get all finance comics for admin management with badge information"""
    try:
        comics_ref = db.collection("comics").where("skill_type", "==", "finance")
        comics_docs = await comics_ref.get()

        comics = []
        for doc in comics_docs:
            data = doc.to_dict()
            comic_id = doc.id

            # Get badge information
            badge_info = await get_badge_info_for_content(db, comic_id, "comics")

            comic_data = {
                "id": comic_id,
                "title": data.get("title", ""),
                "description": data.get("description", ""),
                "pdf_url": data.get("pdf_url", ""),
                "thumbnail_url": data.get("thumbnail_url", ""),
                "likes": data.get("likes", 0),
                "dislikes": data.get("dislikes", 0),
                "view_count": data.get("view_count", 0),
                "created_at": data.get("created_at"),
                "badge_id": data.get(
                    "badge_id"
                ),  # ✅ FIXED: Include badge_id from content
            }

            # ✅ FIXED: Add resolved badge information
            if badge_info:
                comic_data.update(
                    {
                        "badge_name": badge_info["badge_name"],
                        "badge_url": badge_info["badge_url"],
                        "badge_points": badge_info["badge_points"],
                        "badge_description": badge_info["badge_description"],
                    }
                )

            comics.append(comic_data)

        return UniformResponse.success_response(
            message="Finance comics retrieved successfully", data={"comics": comics}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve finance comics: {str(e)}"
        )


@router.post("/finance/comic", response_model=UniformResponse[dict])
async def create_finance_comic(
    request: ComicCreateRequest,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Create a new finance comic"""
    try:
        comic_data = {
            "title": request.title,
            "description": request.description,
            "pdf_url": request.pdf_url,
            "thumbnail_url": request.thumbnail_url,
            "skill_type": request.skill_type.value,
            "likes": 0,
            "dislikes": 0,
            "view_count": 0,
            "badge_id": request.badge_id,  # ✅ This should work now
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        comic_ref = await db.collection("comics").add(comic_data)
        return UniformResponse.success_response(
            message="Finance comic created successfully",
            data={
                "comic_id": comic_ref[1].id,
                "badge_id": request.badge_id,  # ✅ FIXED: Include badge_id in response
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create finance comic: {str(e)}"
        )


@router.delete("/finance/comic/{comic_id}", response_model=UniformResponse[dict])
async def delete_finance_comic(
    comic_id: str,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Delete a finance comic"""
    try:
        comic_ref = db.collection("comics").document(comic_id)
        comic_doc = await comic_ref.get()
        if not comic_doc.exists:
            raise HTTPException(status_code=404, detail="Comic not found")

        await comic_ref.delete()
        return UniformResponse.success_response(
            message="Finance comic deleted successfully", data={"comic_id": comic_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete finance comic: {str(e)}"
        )


# ==================== QUESTION AND QUIZ MANAGEMENT ====================
@router.post("/safety/video/{video_id}/question", response_model=UniformResponse[dict])
async def add_video_question(
    video_id: str,
    request: QuestionCreateRequest,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Add a question to a safety video"""
    try:
        # First, get or create a quiz for this video
        quiz_ref = (
            db.collection("quizzes")
            .where("content_id", "==", video_id)
            .where("content_type", "==", "video")
        )
        quiz_docs = await quiz_ref.get()

        if quiz_docs:
            quiz_id = quiz_docs[0].id
        else:
            # Create a new quiz for this video
            quiz_data = {
                "title": f"Quiz for Video {video_id}",
                "skill_type": "safety",
                "content_type": "video",
                "content_id": video_id,
                "min_score": 50,
                "badge_id": None,
                "created_at": datetime.utcnow(),
            }
            quiz_doc_ref = await db.collection("quizzes").add(quiz_data)
            quiz_id = quiz_doc_ref[1].id

        # Add the question
        question_data = {
            "quiz_id": quiz_id,
            "question_text": request.question_text,
            "question_order": request.question_order,
            "created_at": datetime.utcnow(),
        }
        question_ref = await db.collection("questions").add(question_data)

        return UniformResponse.success_response(
            message="Question added successfully",
            data={"question_id": question_ref[1].id, "quiz_id": quiz_id},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add question: {str(e)}")


@router.post(
    "/safety/video/question/{question_id}/option", response_model=UniformResponse[dict]
)
async def add_question_option(
    question_id: str,
    request: QuestionOptionCreateRequest,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Add an option to a question"""
    try:
        option_data = {
            "question_id": question_id,
            "option_text": request.option_text,
            "is_correct": request.is_correct,
            "option_order": request.option_order,
            "created_at": datetime.utcnow(),
        }
        option_ref = await db.collection("question_options").add(option_data)

        return UniformResponse.success_response(
            message="Question option added successfully",
            data={"option_id": option_ref[1].id},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to add question option: {str(e)}"
        )


# ==================== FINANCE GAME LEVEL ADMIN APIs ====================
@router.get("/finance/levels", response_model=UniformResponse[dict])
async def get_all_finance_levels_admin(
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get all finance game levels for admin management"""
    try:
        levels_ref = db.collection("game_levels").where("skill_type", "==", "finance")
        levels_docs = await levels_ref.get()

        levels = []
        for doc in levels_docs:
            data = doc.to_dict()
            levels.append(
                {
                    "id": doc.id,
                    "level_number": data.get("level_number", 1),
                    "title": data.get("title", ""),
                    "description": data.get("description", ""),
                    "income": data.get("income", 1000),
                    "difficulty": data.get("difficulty", "easy"),
                    "created_at": data.get("created_at"),
                }
            )

        return UniformResponse.success_response(
            message="Finance levels retrieved successfully", data={"levels": levels}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve finance levels: {str(e)}"
        )


@router.post("/finance/level", response_model=UniformResponse[dict])
async def create_finance_level(
    request: FinanceLevelCreateRequest,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Create a new finance game level with proper validation"""
    try:
        level_data = {
            "level_number": request.level_number,
            "title": request.title,
            "description": request.description,
            "income": request.income,
            "difficulty": request.difficulty,
            "skill_type": "finance",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        level_ref = await db.collection("game_levels").add(level_data)
        return UniformResponse.success_response(
            message="Finance level created successfully",
            data={"level_id": level_ref[1].id, "level_number": request.level_number},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create finance level: {str(e)}"
        )


@router.delete("/finance/level/{level_id}", response_model=UniformResponse[dict])
async def delete_finance_level(
    level_id: str,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Delete a finance game level"""
    try:
        level_ref = db.collection("game_levels").document(level_id)
        level_doc = await level_ref.get()
        if not level_doc.exists:
            raise HTTPException(status_code=404, detail="Level not found")

        # Also delete associated items
        items_ref = db.collection("game_items").where("level_id", "==", level_id)
        items_docs = await items_ref.get()
        for item_doc in items_docs:
            await item_doc.reference.delete()

        await level_ref.delete()
        return UniformResponse.success_response(
            message="Finance level deleted successfully", data={"level_id": level_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete finance level: {str(e)}"
        )


@router.post("/finance/level/{level_id}/item", response_model=UniformResponse[dict])
async def add_finance_level_item(
    level_id: str,
    request: GameItemCreateRequest,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Add an item to a finance game level"""
    try:
        # Validate item_type
        if request.item_type not in ["need", "want"]:
            raise HTTPException(
                status_code=400, detail="item_type must be 'need' or 'want'"
            )

        item_data = {
            "level_id": level_id,
            "name": request.name,
            "cost": request.cost,
            "item_type": request.item_type,
            "description": request.description,
            "created_at": datetime.utcnow(),
        }

        item_ref = await db.collection("game_items").add(item_data)
        return UniformResponse.success_response(
            message="Finance level item added successfully",
            data={"item_id": item_ref[1].id, "level_id": level_id},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to add finance level item: {str(e)}"
        )


# Request/Response schemas for badges
class BadgeCreateRequest(BaseModel):
    badge_name: str
    badge_url: str
    description: str = ""
    skill_type: str = ""
    points: int = 5


class BadgeResponse(BaseModel):
    id: str
    badge_name: str
    badge_url: str
    description: str
    skill_type: str
    points: int
    created_at: str


def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to ensure user is admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ==================== BADGE MANAGEMENT APIs ====================


@router.post("/badges", response_model=UniformResponse[dict])
async def create_badge(
    request: BadgeCreateRequest,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Create a new badge with badge_url and badge_name"""
    try:
        badge_data = {
            "name": request.badge_name,  # Map badge_name to name field
            "image_url": request.badge_url,  # Map badge_url to image_url field
            "description": request.description,
            "skill_type": request.skill_type,
            "points": request.points,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        badge_ref = await db.collection("badges").add(badge_data)
        badge_id = badge_ref[1].id

        return UniformResponse.success_response(
            message="Badge created successfully",
            data={
                "badge_id": badge_id,
                "badge_name": request.badge_name,
                "badge_url": request.badge_url,
                "description": request.description,
                "skill_type": request.skill_type,
                "points": request.points,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create badge: {str(e)}")


@router.delete("/badges/{badge_id}", response_model=UniformResponse[dict])
async def delete_badge(
    badge_id: str,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Delete a badge by ID"""
    try:
        badge_ref = db.collection("badges").document(badge_id)
        badge_doc = await badge_ref.get()

        if not badge_doc.exists:
            raise HTTPException(status_code=404, detail="Badge not found")

        await badge_ref.delete()

        return UniformResponse.success_response(
            message="Badge deleted successfully", data={"badge_id": badge_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete badge: {str(e)}")


@router.get("/badges/{badge_id}", response_model=UniformResponse[BadgeResponse])
async def get_badge_by_id(
    badge_id: str,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get badge by ID (for admin to add badge to skills)"""
    try:
        badge_ref = db.collection("badges").document(badge_id)
        badge_doc = await badge_ref.get()

        if not badge_doc.exists:
            raise HTTPException(status_code=404, detail="Badge not found")

        badge_data = badge_doc.to_dict()

        badge_response = BadgeResponse(
            id=badge_id,
            badge_name=badge_data.get("name", ""),
            badge_url=badge_data.get("image_url", ""),
            description=badge_data.get("description", ""),
            skill_type=badge_data.get("skill_type", ""),
            points=badge_data.get("points", 5),
            created_at=badge_data.get("created_at", "").isoformat()
            if badge_data.get("created_at")
            else "",
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


@router.patch("/admin/quiz/{quiz_id}/badge", response_model=UniformResponse[dict])
async def update_quiz_badge(
    quiz_id: str,
    badge_id: str,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Update badge assignment for a quiz"""
    try:
        quiz_ref = db.collection("quizzes").document(quiz_id)
        quiz_doc = await quiz_ref.get()

        if not quiz_doc.exists:
            raise HTTPException(status_code=404, detail="Quiz not found")

        # Validate badge exists
        badge_ref = db.collection("badges").document(badge_id)
        badge_doc = await badge_ref.get()
        if not badge_doc.exists:
            raise HTTPException(status_code=404, detail="Badge not found")

        # Update quiz
        await quiz_ref.update({"badge_id": badge_id, "updated_at": datetime.utcnow()})

        return UniformResponse.success_response(
            message="Quiz badge updated successfully",
            data={"quiz_id": quiz_id, "badge_id": badge_id},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update quiz badge: {str(e)}"
        )
