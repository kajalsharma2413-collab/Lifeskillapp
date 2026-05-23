# app/api/v1/safety.py - Updated with quiz_id and badge information support
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import firestore
from pydantic import BaseModel

from app.api.dependencies.auth import get_current_user
from app.api.v1.quiz import get_quiz_by_content_with_auto_gen
from app.config.firebase import get_firebase_client
from app.models.skill import SkillType
from app.models.user import User
from app.schemas.base import UniformResponse
from app.schemas.quiz import (
    EnhancedQuizResponse,
    QuizResultResponse,
    QuizSubmissionRequest,
)
from app.schemas.safety import (
    ReactionResponse,
    SafetyComicList,
    SafetyComicResponse,
    SafetyVideoList,
    SafetyVideoResponse,
    UserReactionStatus,
    ViewTrackingResponse,
)
from app.utils.quiz_utils import get_badge_info_for_content, get_quiz_id_for_content

router = APIRouter(prefix="/safety", tags=["safety"])


# ==================== QUIZ SCHEMAS ====================
class SafetyQuizQuestion(BaseModel):
    id: str
    question: str
    options: list[dict]  # [{"id": 1, "text": "Option text", "is_correct": bool}]


class SafetyQuizResponse(BaseModel):
    quiz_id: str
    content_id: str
    content_type: str  # "video" or "comic"
    questions: list[SafetyQuizQuestion]
    min_score: int
    badge_id: str | None = None


class SafetyQuizSubmission(BaseModel):
    answers: list[dict]  # [{"question_id": "string", "selected_option_id": int}]


class SafetyQuizResult(BaseModel):
    quiz_id: str
    content_id: str
    content_type: str
    score: int
    total_questions: int
    passed: bool
    badge_awarded: bool = False
    badge_id: str | None = None


# ==================== SAFETY VIDEOS ====================
@router.get("/videos", response_model=UniformResponse[SafetyVideoList])
async def get_safety_videos(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get all safety videos with quiz_id and badge information"""
    try:
        videos_ref = db.collection("videos").where("skill_type", "==", "safety")
        videos_docs = await videos_ref.get()

        videos = []
        for doc in videos_docs:
            data = doc.to_dict()
            video_id = doc.id

            # Get quiz ID for this video
            quiz_id = await get_quiz_id_for_content(db, video_id, "video", "safety")

            # Get badge information
            badge_info = await get_badge_info_for_content(db, video_id, "videos")

            video_data = {
                "id": video_id,
                "title": data.get("title", ""),
                "description": data.get("description", ""),
                "thumbnail": data.get("thumbnail_url", ""),
                "quiz_id": quiz_id,  # ✅ FIXED: Include quiz ID
            }

            # ✅ FIXED: Include badge information if available
            if badge_info:
                video_data.update(
                    {
                        "badge_id": badge_info["badge_id"],
                        "badge_name": badge_info["badge_name"],
                        "badge_url": badge_info["badge_url"],
                        "badge_points": badge_info["badge_points"],
                    }
                )

            videos.append(video_data)

        response_data = SafetyVideoList(videos=videos)
        return UniformResponse.success_response(
            message="Safety videos retrieved successfully", data=response_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve safety videos: {str(e)}"
        )


@router.get("/video/{video_id}", response_model=UniformResponse[SafetyVideoResponse])
async def get_safety_video(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get safety video by ID with user reaction status and badge information"""
    try:
        # Get video details
        video_ref = db.collection("videos").document(video_id)
        video_doc = await video_ref.get()
        if not video_doc.exists:
            raise HTTPException(status_code=404, detail="Video not found")

        video_data = video_doc.to_dict()

        # Get user reaction status
        reaction_ref = (
            db.collection("user_reactions")
            .where("user_id", "==", current_user.id)
            .where("content_id", "==", video_id)
            .where("content_type", "==", "video")
        )
        reaction_docs = await reaction_ref.get()

        user_liked = False
        user_disliked = False
        for reaction_doc in reaction_docs:
            reaction_data = reaction_doc.to_dict()
            if reaction_data.get("reaction_type") == "like":
                user_liked = True
            elif reaction_data.get("reaction_type") == "dislike":
                user_disliked = True

        # Get badge information
        badge_info = await get_badge_info_for_content(db, video_id, "videos")

        video_detail = {
            "id": video_id,
            "title": video_data.get("title", ""),
            "description": video_data.get("description", ""),
            "videoUrl": video_data.get("video_url", ""),
            "likes": video_data.get("likes", 0),
            "dislikes": video_data.get("dislikes", 0),
            "userLiked": user_liked,
            "userDisliked": user_disliked,
        }

        # ✅ FIXED: Include badge information if available
        if badge_info:
            video_detail.update(
                {
                    "badge_id": badge_info["badge_id"],
                    "badge_name": badge_info["badge_name"],
                    "badge_url": badge_info["badge_url"],
                    "badge_points": badge_info["badge_points"],
                }
            )

        response_data = SafetyVideoResponse(video=video_detail)
        return UniformResponse.success_response(
            message="Safety video retrieved successfully",
            data=response_data,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve safety video: {str(e)}"
        )


# ==================== SAFETY COMICS ====================
@router.get("/comics", response_model=UniformResponse[SafetyComicList])
async def get_safety_comics(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get all safety comics with quiz_id and badge information"""
    try:
        comics_ref = db.collection("comics").where("skill_type", "==", "safety")
        comics_docs = await comics_ref.get()

        comics = []
        for doc in comics_docs:
            data = doc.to_dict()
            comic_id = doc.id

            # Get quiz ID for this comic
            quiz_id = await get_quiz_id_for_content(db, comic_id, "comic", "safety")

            # Get badge information
            badge_info = await get_badge_info_for_content(db, comic_id, "comics")

            comic_data = {
                "id": comic_id,
                "title": data.get("title", ""),
                "description": data.get("description", ""),
                "thumbnail": data.get("thumbnail_url", ""),
                "quiz_id": quiz_id,  # ✅ FIXED: Include quiz ID
            }

            # ✅ FIXED: Include badge information if available
            if badge_info:
                comic_data.update(
                    {
                        "badge_id": badge_info["badge_id"],
                        "badge_name": badge_info["badge_name"],
                        "badge_url": badge_info["badge_url"],
                        "badge_points": badge_info["badge_points"],
                    }
                )

            comics.append(comic_data)

        response_data = SafetyComicList(comics=comics)
        return UniformResponse.success_response(
            message="Safety comics retrieved successfully", data=response_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve safety comics: {str(e)}"
        )


@router.get("/comic/{comic_id}", response_model=UniformResponse[SafetyComicResponse])
async def get_safety_comic(
    comic_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get safety comic by ID with user reaction status and badge information"""
    try:
        # Get comic details
        comic_ref = db.collection("comics").document(comic_id)
        comic_doc = await comic_ref.get()
        if not comic_doc.exists:
            raise HTTPException(status_code=404, detail="Comic not found")

        comic_data = comic_doc.to_dict()

        # Get user reaction status
        reaction_ref = (
            db.collection("user_reactions")
            .where("user_id", "==", current_user.id)
            .where("content_id", "==", comic_id)
            .where("content_type", "==", "comic")
        )
        reaction_docs = await reaction_ref.get()

        user_liked = False
        user_disliked = False
        for reaction_doc in reaction_docs:
            reaction_data = reaction_doc.to_dict()
            if reaction_data.get("reaction_type") == "like":
                user_liked = True
            elif reaction_data.get("reaction_type") == "dislike":
                user_disliked = True

        # Get badge information
        badge_info = await get_badge_info_for_content(db, comic_id, "comics")

        comic_detail = {
            "id": comic_id,
            "title": comic_data.get("title", ""),
            "description": comic_data.get("description", ""),
            "pdfUrl": comic_data.get("pdf_url", ""),
            "likes": comic_data.get("likes", 0),
            "dislikes": comic_data.get("dislikes", 0),
            "userLiked": user_liked,
            "userDisliked": user_disliked,
        }

        # ✅ FIXED: Include badge information if available
        if badge_info:
            comic_detail.update(
                {
                    "badge_id": badge_info["badge_id"],
                    "badge_name": badge_info["badge_name"],
                    "badge_url": badge_info["badge_url"],
                    "badge_points": badge_info["badge_points"],
                }
            )

        response_data = SafetyComicResponse(comic=comic_detail)
        return UniformResponse.success_response(
            message="Safety comic retrieved successfully",
            data=response_data,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve safety comic: {str(e)}"
        )


# ==================== EXISTING ENDPOINTS (View tracking, reactions, etc.) ====================
@router.post(
    "/video/{video_id}/view", response_model=UniformResponse[ViewTrackingResponse]
)
async def track_video_view(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Track video view for analytics"""
    try:
        # Record engagement
        from app.utils.skill_tracking import track_skill_engagement

        await track_skill_engagement(
            user_id=current_user.id,
            skill_type=SkillType.SAFETY,
            action="view",
            db=db,
            content_type="video",
            content_id=video_id,
        )

        # Increment view count
        video_ref = db.collection("videos").document(video_id)
        video_doc = await video_ref.get()
        if video_doc.exists:
            current_views = video_doc.to_dict().get("view_count", 0)
            await video_ref.update({"view_count": current_views + 1})

        response_data = ViewTrackingResponse(
            video_id=video_id, message="Video view tracked successfully"
        )
        return UniformResponse.success_response(
            message="Video view tracked successfully", data=response_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to track video view: {str(e)}"
        )


@router.post(
    "/comic/{comic_id}/view", response_model=UniformResponse[ViewTrackingResponse]
)
async def track_comic_view(
    comic_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Track comic view for analytics"""
    try:
        # Record engagement
        from app.utils.skill_tracking import track_skill_engagement

        await track_skill_engagement(
            user_id=current_user.id,
            skill_type=SkillType.SAFETY,
            action="view",
            db=db,
            content_type="comic",
            content_id=comic_id,
        )

        # Increment view count
        comic_ref = db.collection("comics").document(comic_id)
        comic_doc = await comic_ref.get()
        if comic_doc.exists:
            current_views = comic_doc.to_dict().get("view_count", 0)
            await comic_ref.update({"view_count": current_views + 1})

        response_data = ViewTrackingResponse(
            comic_id=comic_id, message="Comic view tracked successfully"
        )
        return UniformResponse.success_response(
            message="Comic view tracked successfully", data=response_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to track comic view: {str(e)}"
        )


# ==================== REACTION ENDPOINTS ====================
@router.post("/video/{video_id}/like", response_model=UniformResponse[ReactionResponse])
async def like_video(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Like a safety video"""
    try:
        response_data = await _handle_video_reaction(
            video_id, current_user.id, "like", db
        )
        return UniformResponse.success_response(
            message="Video liked successfully", data=response_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to like video: {str(e)}")


@router.post(
    "/video/{video_id}/dislike", response_model=UniformResponse[ReactionResponse]
)
async def dislike_video(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Dislike a safety video"""
    try:
        response_data = await _handle_video_reaction(
            video_id, current_user.id, "dislike", db
        )
        return UniformResponse.success_response(
            message="Video disliked successfully", data=response_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to dislike video: {str(e)}"
        )


@router.post("/comic/{comic_id}/like", response_model=UniformResponse[ReactionResponse])
async def like_comic(
    comic_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Like a safety comic"""
    try:
        response_data = await _handle_comic_reaction(
            comic_id, current_user.id, "like", db
        )
        return UniformResponse.success_response(
            message="Comic liked successfully", data=response_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to like comic: {str(e)}")


@router.post(
    "/comic/{comic_id}/dislike", response_model=UniformResponse[ReactionResponse]
)
async def dislike_comic(
    comic_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Dislike a safety comic"""
    try:
        response_data = await _handle_comic_reaction(
            comic_id, current_user.id, "dislike", db
        )
        return UniformResponse.success_response(
            message="Comic disliked successfully", data=response_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to dislike comic: {str(e)}"
        )


@router.get(
    "/video/{video_id}/reaction", response_model=UniformResponse[UserReactionStatus]
)
async def get_video_reaction(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get user's reaction status for a video"""
    try:
        reaction_ref = (
            db.collection("user_reactions")
            .where("user_id", "==", current_user.id)
            .where("content_id", "==", video_id)
            .where("content_type", "==", "video")
        )
        reaction_docs = await reaction_ref.get()

        liked = False
        disliked = False
        for reaction_doc in reaction_docs:
            reaction_data = reaction_doc.to_dict()
            if reaction_data.get("reaction_type") == "like":
                liked = True
            elif reaction_data.get("reaction_type") == "dislike":
                disliked = True

        response_data = UserReactionStatus(liked=liked, disliked=disliked)
        return UniformResponse.success_response(
            message="Video reaction status retrieved successfully",
            data=response_data,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get video reaction: {str(e)}"
        )


@router.get(
    "/comic/{comic_id}/reaction", response_model=UniformResponse[UserReactionStatus]
)
async def get_comic_reaction(
    comic_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get user's reaction status for a comic"""
    try:
        reaction_ref = (
            db.collection("user_reactions")
            .where("user_id", "==", current_user.id)
            .where("content_id", "==", comic_id)
            .where("content_type", "==", "comic")
        )
        reaction_docs = await reaction_ref.get()

        liked = False
        disliked = False
        for reaction_doc in reaction_docs:
            reaction_data = reaction_doc.to_dict()
            if reaction_data.get("reaction_type") == "like":
                liked = True
            elif reaction_data.get("reaction_type") == "dislike":
                disliked = True

        response_data = UserReactionStatus(liked=liked, disliked=disliked)
        return UniformResponse.success_response(
            message="Comic reaction status retrieved successfully",
            data=response_data,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get comic reaction: {str(e)}"
        )


# ==================== HELPER FUNCTIONS ====================
async def _handle_video_reaction(
    video_id: str, user_id: str, reaction_type: str, db: firestore.AsyncClient
) -> ReactionResponse:
    """Handle video like/dislike"""
    # Remove existing opposite reaction
    opposite_reaction = "dislike" if reaction_type == "like" else "like"
    await _remove_video_reaction(video_id, user_id, opposite_reaction, db)

    # Check if reaction already exists
    reaction_ref = (
        db.collection("user_reactions")
        .where("user_id", "==", user_id)
        .where("content_id", "==", video_id)
        .where("content_type", "==", "video")
        .where("reaction_type", "==", reaction_type)
    )
    existing_reactions = await reaction_ref.get()

    if existing_reactions:
        return ReactionResponse(
            action=f"{reaction_type}_exists", message=f"Video already {reaction_type}d"
        )

    # Add new reaction
    reaction_data = {
        "user_id": user_id,
        "content_type": "video",
        "content_id": video_id,
        "reaction_type": reaction_type,
        "timestamp": datetime.utcnow(),
    }
    await db.collection("user_reactions").add(reaction_data)

    # Update video counts
    video_ref = db.collection("videos").document(video_id)
    video_doc = await video_ref.get()
    if video_doc.exists:
        video_data = video_doc.to_dict()
        current_count = video_data.get(f"{reaction_type}s", 0)
        await video_ref.update({f"{reaction_type}s": current_count + 1})

    return ReactionResponse(
        action=reaction_type, message=f"Video {reaction_type}d successfully"
    )


async def _remove_video_reaction(
    video_id: str, user_id: str, reaction_type: str, db: firestore.AsyncClient
) -> ReactionResponse:
    """Remove video reaction"""
    # Find and remove existing reaction
    reaction_ref = (
        db.collection("user_reactions")
        .where("user_id", "==", user_id)
        .where("content_id", "==", video_id)
        .where("content_type", "==", "video")
        .where("reaction_type", "==", reaction_type)
    )
    existing_reactions = await reaction_ref.get()

    for reaction_doc in existing_reactions:
        await reaction_doc.reference.delete()

        # Update video counts
        video_ref = db.collection("videos").document(video_id)
        video_doc = await video_ref.get()
        if video_doc.exists:
            video_data = video_doc.to_dict()
            current_count = max(0, video_data.get(f"{reaction_type}s", 0) - 1)
            await video_ref.update({f"{reaction_type}s": current_count})

    return ReactionResponse(
        action=f"remove_{reaction_type}",
        message=f"Video {reaction_type} removed successfully",
    )


async def _handle_comic_reaction(
    comic_id: str, user_id: str, reaction_type: str, db: firestore.AsyncClient
) -> ReactionResponse:
    """Handle comic like/dislike"""
    # Remove existing opposite reaction
    opposite_reaction = "dislike" if reaction_type == "like" else "like"
    await _remove_comic_reaction(comic_id, user_id, opposite_reaction, db)

    # Check if reaction already exists
    reaction_ref = (
        db.collection("user_reactions")
        .where("user_id", "==", user_id)
        .where("content_id", "==", comic_id)
        .where("content_type", "==", "comic")
        .where("reaction_type", "==", reaction_type)
    )
    existing_reactions = await reaction_ref.get()

    if existing_reactions:
        return ReactionResponse(
            action=f"{reaction_type}_exists", message=f"Comic already {reaction_type}d"
        )

    # Add new reaction
    reaction_data = {
        "user_id": user_id,
        "content_type": "comic",
        "content_id": comic_id,
        "reaction_type": reaction_type,
        "timestamp": datetime.utcnow(),
    }
    await db.collection("user_reactions").add(reaction_data)

    # Update comic counts
    comic_ref = db.collection("comics").document(comic_id)
    comic_doc = await comic_ref.get()
    if comic_doc.exists:
        comic_data = comic_doc.to_dict()
        current_count = comic_data.get(f"{reaction_type}s", 0)
        await comic_ref.update({f"{reaction_type}s": current_count + 1})

    return ReactionResponse(
        action=reaction_type, message=f"Comic {reaction_type}d successfully"
    )


async def _remove_comic_reaction(
    comic_id: str, user_id: str, reaction_type: str, db: firestore.AsyncClient
) -> ReactionResponse:
    """Remove comic reaction"""
    # Find and remove existing reaction
    reaction_ref = (
        db.collection("user_reactions")
        .where("user_id", "==", user_id)
        .where("content_id", "==", comic_id)
        .where("content_type", "==", "comic")
        .where("reaction_type", "==", reaction_type)
    )
    existing_reactions = await reaction_ref.get()

    for reaction_doc in existing_reactions:
        await reaction_doc.reference.delete()

        # Update comic counts
        comic_ref = db.collection("comics").document(comic_id)
        comic_doc = await comic_ref.get()
        if comic_doc.exists:
            comic_data = comic_doc.to_dict()
            current_count = max(0, comic_data.get(f"{reaction_type}s", 0) - 1)
            await comic_ref.update({f"{reaction_type}s": current_count})

    return ReactionResponse(
        action=f"remove_{reaction_type}",
        message=f"Comic {reaction_type} removed successfully",
    )


@router.post(
    "/video/{video_id}/quiz/submit", response_model=UniformResponse[QuizResultResponse]
)
async def submit_safety_video_quiz(
    video_id: str,
    submission: QuizSubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Submit quiz answers for a safety video"""
    try:
        # Get quiz for this video
        quiz_ref = (
            db.collection("quizzes")
            .where("content_id", "==", video_id)
            .where("content_type", "==", "video")
            .where("skill_type", "==", "safety")
        )
        quiz_docs = await quiz_ref.get()
        if not quiz_docs:
            raise HTTPException(
                status_code=404, detail="No quiz found for this safety video"
            )

        quiz_id = quiz_docs[0].id

        # Use the standardized quiz submission function

        # Call the submit_quiz function directly with the quiz_id
        _request = type("MockRequest", (), {"path_params": {"quiz_id": quiz_id}})()

        # We need to recreate the submission call manually since we can't redirect FastAPI routes
        # This is a bit of a workaround - we'll duplicate the submission logic here
        # but use the same comprehensive result format

        # Get quiz details
        quiz_doc = quiz_docs[0]
        quiz_data = quiz_doc.to_dict()

        # Calculate score and detailed results
        total_questions = 0
        correct_answers = 0
        detailed_results = []

        for answer in submission.answers:
            question_id = answer.question_id
            selected_option_id = answer.selected_option_id

            # Get the selected option
            option_ref = db.collection("question_options").document(selected_option_id)
            option_doc = await option_ref.get()

            if option_doc.exists:
                option_data = option_doc.to_dict()
                is_correct = option_data.get("is_correct", False)

                total_questions += 1
                if is_correct:
                    correct_answers += 1

                # Get question text for detailed results
                question_ref = db.collection("questions").document(question_id)
                question_doc = await question_ref.get()
                question_text = ""
                if question_doc.exists:
                    question_text = question_doc.to_dict().get("question_text", "")

                detailed_results.append(
                    {
                        "question_id": question_id,
                        "question_text": question_text,
                        "selected_option_id": selected_option_id,
                        "selected_option_text": option_data.get("option_text", ""),
                        "is_correct": is_correct,
                    }
                )

        # Calculate percentage score
        score_percentage = (
            int((correct_answers / total_questions * 100)) if total_questions > 0 else 0
        )

        min_score = quiz_data.get("min_score", 50)
        passed = score_percentage >= min_score

        # Get attempt number for this user
        attempts_ref = (
            db.collection("quiz_attempts")
            .where("user_id", "==", current_user.id)
            .where("quiz_id", "==", quiz_id)
        )
        previous_attempts = await attempts_ref.get()
        attempt_number = len(previous_attempts) + 1

        # Record quiz attempt
        attempt_data = {
            "user_id": current_user.id,
            "quiz_id": quiz_id,
            "content_id": video_id,
            "content_type": "video",
            "skill_type": "safety",
            "score_percentage": score_percentage,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "passed": passed,
            "attempt_number": attempt_number,
            "time_taken_seconds": submission.time_taken_seconds,
            "answers": [answer.model_dump() for answer in submission.answers],
            "detailed_results": detailed_results,
            "completed_at": datetime.utcnow(),
        }

        await db.collection("quiz_attempts").add(attempt_data)

        # Handle badge awarding
        badge_awarded = False
        badge_id = None
        badge_name = None

        if passed and quiz_data.get("badge_id"):
            badge_id = quiz_data["badge_id"]

            # Check if user already has this badge
            existing_badge_ref = (
                db.collection("user_badges")
                .where("user_id", "==", current_user.id)
                .where("badge_id", "==", badge_id)
            )
            existing_badges = await existing_badge_ref.get()

            if not existing_badges:
                # Award the badge
                badge_data = {
                    "user_id": current_user.id,
                    "badge_id": badge_id,
                    "quiz_id": quiz_id,
                    "score_percentage": score_percentage,
                    "earned_at": datetime.utcnow(),
                }
                await db.collection("user_badges").add(badge_data)
                badge_awarded = True

                # Get badge name
                badge_ref = db.collection("badges").document(badge_id)
                badge_doc = await badge_ref.get()
                if badge_doc.exists:
                    badge_name = badge_doc.to_dict().get("name")

        # Build comprehensive result response
        result = QuizResultResponse(
            quiz_id=quiz_id,
            content_id=video_id,
            content_type="video",
            skill_type="safety",
            score_percentage=score_percentage,
            correct_answers=correct_answers,
            total_questions=total_questions,
            passed=passed,
            min_score_required=min_score,
            badge_awarded=badge_awarded,
            badge_id=badge_id,
            badge_name=badge_name,
            attempt_number=attempt_number,
            time_taken_seconds=submission.time_taken_seconds,
            completed_at=datetime.utcnow(),
            detailed_results=detailed_results,
        )

        return UniformResponse.success_response(
            message="Safety video quiz submitted successfully", data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to submit safety video quiz: {str(e)}"
        )


@router.post(
    "/comic/{comic_id}/quiz/submit", response_model=UniformResponse[QuizResultResponse]
)
async def submit_safety_comic_quiz(
    comic_id: str,
    submission: QuizSubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Submit quiz answers for a safety comic"""
    # Similar implementation as video quiz submission, just replace video_id with comic_id
    # and content_type "video" with "comic"
    # [Implementation follows the same pattern as submit_safety_video_quiz above]
    try:
        # Get quiz for this video
        quiz_ref = (
            db.collection("quizzes")
            .where("content_id", "==", comic_id)
            .where("content_type", "==", "comic")
            .where("skill_type", "==", "safety")
        )
        quiz_docs = await quiz_ref.get()
        if not quiz_docs:
            raise HTTPException(
                status_code=404, detail="No quiz found for this safety video"
            )

        quiz_id = quiz_docs[0].id

        # Use the standardized quiz submission function

        # Call the submit_quiz function directly with the quiz_id
        _request = type("MockRequest", (), {"path_params": {"quiz_id": quiz_id}})()

        # We need to recreate the submission call manually since we can't redirect FastAPI routes
        # This is a bit of a workaround - we'll duplicate the submission logic here
        # but use the same comprehensive result format

        # Get quiz details
        quiz_doc = quiz_docs[0]
        quiz_data = quiz_doc.to_dict()

        # Calculate score and detailed results
        total_questions = 0
        correct_answers = 0
        detailed_results = []

        for answer in submission.answers:
            question_id = answer.question_id
            selected_option_id = answer.selected_option_id

            # Get the selected option
            option_ref = db.collection("question_options").document(selected_option_id)
            option_doc = await option_ref.get()

            if option_doc.exists:
                option_data = option_doc.to_dict()
                is_correct = option_data.get("is_correct", False)

                total_questions += 1
                if is_correct:
                    correct_answers += 1

                # Get question text for detailed results
                question_ref = db.collection("questions").document(question_id)
                question_doc = await question_ref.get()
                question_text = ""
                if question_doc.exists:
                    question_text = question_doc.to_dict().get("question_text", "")

                detailed_results.append(
                    {
                        "question_id": question_id,
                        "question_text": question_text,
                        "selected_option_id": selected_option_id,
                        "selected_option_text": option_data.get("option_text", ""),
                        "is_correct": is_correct,
                    }
                )

        # Calculate percentage score
        score_percentage = (
            int((correct_answers / total_questions * 100)) if total_questions > 0 else 0
        )

        min_score = quiz_data.get("min_score", 50)
        passed = score_percentage >= min_score

        # Get attempt number for this user
        attempts_ref = (
            db.collection("quiz_attempts")
            .where("user_id", "==", current_user.id)
            .where("quiz_id", "==", quiz_id)
        )
        previous_attempts = await attempts_ref.get()
        attempt_number = len(previous_attempts) + 1

        # Record quiz attempt
        attempt_data = {
            "user_id": current_user.id,
            "quiz_id": quiz_id,
            "content_id": comic_id,
            "content_type": "comic",
            "skill_type": "safety",
            "score_percentage": score_percentage,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "passed": passed,
            "attempt_number": attempt_number,
            "time_taken_seconds": submission.time_taken_seconds,
            "answers": [answer.model_dump() for answer in submission.answers],
            "detailed_results": detailed_results,
            "completed_at": datetime.utcnow(),
        }

        await db.collection("quiz_attempts").add(attempt_data)

        # Handle badge awarding
        badge_awarded = False
        badge_id = None
        badge_name = None

        if passed and quiz_data.get("badge_id"):
            badge_id = quiz_data["badge_id"]

            # Check if user already has this badge
            existing_badge_ref = (
                db.collection("user_badges")
                .where("user_id", "==", current_user.id)
                .where("badge_id", "==", badge_id)
            )
            existing_badges = await existing_badge_ref.get()

            if not existing_badges:
                # Award the badge
                badge_data = {
                    "user_id": current_user.id,
                    "badge_id": badge_id,
                    "quiz_id": quiz_id,
                    "score_percentage": score_percentage,
                    "earned_at": datetime.utcnow(),
                }
                await db.collection("user_badges").add(badge_data)
                badge_awarded = True

                # Get badge name
                badge_ref = db.collection("badges").document(badge_id)
                badge_doc = await badge_ref.get()
                if badge_doc.exists:
                    badge_name = badge_doc.to_dict().get("name")

        # Build comprehensive result response
        result = QuizResultResponse(
            quiz_id=quiz_id,
            content_id=comic_id,
            content_type="comic",
            skill_type="safety",
            score_percentage=score_percentage,
            correct_answers=correct_answers,
            total_questions=total_questions,
            passed=passed,
            min_score_required=min_score,
            badge_awarded=badge_awarded,
            badge_id=badge_id,
            badge_name=badge_name,
            attempt_number=attempt_number,
            time_taken_seconds=submission.time_taken_seconds,
            completed_at=datetime.utcnow(),
            detailed_results=detailed_results,
        )

        return UniformResponse.success_response(
            message="Safety video quiz submitted successfully", data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to submit safety video quiz: {str(e)}"
        )


@router.get(
    "/video/{video_id}/quiz", response_model=UniformResponse[EnhancedQuizResponse]
)
async def get_safety_video_quiz(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """
    🚀 ENHANCED: Get quiz for a safety video with AUTO-GENERATION
    No more 404 errors - always returns a quiz!
    """
    try:
        # Verify video exists and is a safety video
        video_ref = db.collection("videos").document(video_id)
        video_doc = await video_ref.get()
        if not video_doc.exists:
            raise HTTPException(status_code=404, detail="Safety video not found")

        video_data = video_doc.to_dict()
        if video_data.get("skill_type") != "safety":
            raise HTTPException(status_code=400, detail="This is not a safety video")

        # Use the enhanced auto-generation function
        return await get_quiz_by_content_with_auto_gen(video_id, "video", "safety", db)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve safety video quiz: {str(e)}"
        )


# REPLACE the existing get_safety_comic_quiz function with this:
@router.get(
    "/comic/{comic_id}/quiz", response_model=UniformResponse[EnhancedQuizResponse]
)
async def get_safety_comic_quiz(
    comic_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """
    🚀 ENHANCED: Get quiz for a safety comic with AUTO-GENERATION
    No more 404 errors - always returns a quiz!
    """
    try:
        # Verify comic exists and is a safety comic
        comic_ref = db.collection("comics").document(comic_id)
        comic_doc = await comic_ref.get()
        if not comic_doc.exists:
            raise HTTPException(status_code=404, detail="Safety comic not found")

        comic_data = comic_doc.to_dict()
        if comic_data.get("skill_type") != "safety":
            raise HTTPException(status_code=400, detail="This is not a safety comic")

        # Use the enhanced auto-generation function
        return await get_quiz_by_content_with_auto_gen(comic_id, "comic", "safety", db)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve safety comic quiz: {str(e)}"
        )
