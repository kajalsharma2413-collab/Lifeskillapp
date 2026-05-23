# app/api/v1/finance.py - Updated to use shared quiz utils and include badge info
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from firebase_admin import firestore

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
from app.schemas.skill import (
    FinanceGameAttemptResponse,
    FinanceProgressResponse,
    GameItemResponse,
    GameLevelResponse,
    GameSubmissionRequest,
    UserReactionResponse,
)
from app.utils.quiz_utils import get_badge_info_for_content, get_quiz_id_for_content

router = APIRouter(prefix="/finance", tags=["finance"])


@router.post("/video/{video_id}/view", response_model=UniformResponse[dict])
async def track_finance_video_view(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Track finance video view for analytics"""
    try:
        # Record engagement
        from app.utils.skill_tracking import track_skill_engagement

        await track_skill_engagement(
            user_id=current_user.id,
            skill_type=SkillType.FINANCE,
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

        return UniformResponse.success_response(
            message="Finance video view tracked successfully",
            data={"video_id": video_id},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to track finance video view: {str(e)}"
        )


@router.post("/game/level/{level}/score", response_model=UniformResponse[dict])
async def submit_game_score(
    level: int,
    submission: GameSubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Submit game score for a level"""
    try:
        # Find the level
        level_ref = (
            db.collection("game_levels")
            .where("level_number", "==", level)
            .where("skill_type", "==", "finance")
        )
        level_docs = await level_ref.get()

        if not level_docs:
            raise HTTPException(status_code=404, detail="Game level not found")

        level_doc = level_docs[0]

        # Record game attempt
        attempt_data = {
            "user_id": submission.user_id,
            "level_id": level_doc.id,
            "score": submission.score,
            "needs_selected": submission.needs,
            "wants_selected": submission.wants,
            "completed_at": datetime.utcnow(),
        }
        attempt_ref = await db.collection("game_attempts").add(attempt_data)

        # Track skill engagement
        from app.utils.skill_tracking import track_skill_engagement

        await track_skill_engagement(
            user_id=current_user.id,
            skill_type=SkillType.FINANCE,
            action="game_complete",
            db=db,
            content_type="game",
            content_id=level_doc.id,
        )

        return UniformResponse.success_response(
            message="Game score submitted successfully",
            data={
                "attempt_id": attempt_ref[1].id,
                "score": submission.score,
                "level": level,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to submit game score: {str(e)}"
        )


@router.get("/comic/{comic_id}", response_model=UniformResponse[dict])
async def get_finance_comic(
    comic_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get finance comic by ID with user reaction status and badge information"""
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

        comic_response = {
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
            comic_response.update(
                {
                    "badge_id": badge_info["badge_id"],
                    "badge_name": badge_info["badge_name"],
                    "badge_url": badge_info["badge_url"],
                    "badge_points": badge_info["badge_points"],
                }
            )

        return UniformResponse.success_response(
            message="Finance comic retrieved successfully",
            data={"comic": comic_response},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve finance comic: {str(e)}"
        )


@router.post("/comic/{comic_id}/view", response_model=UniformResponse[dict])
async def track_finance_comic_view(
    comic_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Track finance comic view for analytics"""
    try:
        # Record engagement
        from app.utils.skill_tracking import track_skill_engagement

        await track_skill_engagement(
            user_id=current_user.id,
            skill_type=SkillType.FINANCE,
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

        return UniformResponse.success_response(
            message="Finance comic view tracked successfully",
            data={"comic_id": comic_id},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to track finance comic view: {str(e)}"
        )


# Finance Comic Reactions (like safety comics)
@router.post("/comic/{comic_id}/like", response_model=UniformResponse[dict])
async def like_finance_comic(
    comic_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Like a finance comic"""
    return await _handle_finance_comic_reaction(comic_id, current_user.id, "like", db)


@router.post("/comic/{comic_id}/dislike", response_model=UniformResponse[dict])
async def dislike_finance_comic(
    comic_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Dislike a finance comic"""
    return await _handle_finance_comic_reaction(
        comic_id, current_user.id, "dislike", db
    )


@router.post("/comic/{comic_id}/remove-like", response_model=UniformResponse[dict])
async def remove_finance_comic_like(
    comic_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Remove like from a finance comic"""
    return await _remove_finance_comic_reaction(comic_id, current_user.id, "like", db)


@router.post("/comic/{comic_id}/remove-dislike", response_model=UniformResponse[dict])
async def remove_finance_comic_dislike(
    comic_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Remove dislike from a finance comic"""
    return await _remove_finance_comic_reaction(
        comic_id, current_user.id, "dislike", db
    )


# Finance Video Reactions (missing - add to match safety videos)
@router.post("/video/{video_id}/like", response_model=UniformResponse[dict])
async def like_finance_video(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Like a finance video"""
    return await _handle_finance_video_reaction(video_id, current_user.id, "like", db)


@router.post("/video/{video_id}/dislike", response_model=UniformResponse[dict])
async def dislike_finance_video(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Dislike a finance video"""
    return await _handle_finance_video_reaction(
        video_id, current_user.id, "dislike", db
    )


@router.post("/video/{video_id}/remove-like", response_model=UniformResponse[dict])
async def remove_finance_video_like(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Remove like from a finance video"""
    return await _remove_finance_video_reaction(video_id, current_user.id, "like", db)


@router.post("/video/{video_id}/remove-dislike", response_model=UniformResponse[dict])
async def remove_finance_video_dislike(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Remove dislike from a finance video"""
    return await _remove_finance_video_reaction(
        video_id, current_user.id, "dislike", db
    )


@router.get("/video/{video_id}", response_model=UniformResponse[dict])
async def get_finance_video(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get finance video by ID with user reaction status and badge information"""
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

        video_response = {
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
            video_response.update(
                {
                    "badge_id": badge_info["badge_id"],
                    "badge_name": badge_info["badge_name"],
                    "badge_url": badge_info["badge_url"],
                    "badge_points": badge_info["badge_points"],
                }
            )

        return UniformResponse.success_response(
            message="Finance video retrieved successfully",
            data={"video": video_response},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve finance video: {str(e)}"
        )


# Helper functions for finance reactions (same pattern as safety)
async def _handle_finance_video_reaction(
    video_id: str, user_id: str, reaction_type: str, db: firestore.AsyncClient
):
    """Handle finance video like/dislike"""
    try:
        # Remove existing opposite reaction
        opposite_reaction = "dislike" if reaction_type == "like" else "like"
        await _remove_finance_video_reaction(video_id, user_id, opposite_reaction, db)

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
            return UniformResponse.success_response(
                message=f"Video already {reaction_type}d",
                data={"action": f"{reaction_type}_exists"},
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

        return UniformResponse.success_response(
            message=f"Video {reaction_type}d successfully",
            data={"action": reaction_type},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to {reaction_type} video: {str(e)}"
        )


async def _remove_finance_video_reaction(
    video_id: str, user_id: str, reaction_type: str, db: firestore.AsyncClient
):
    """Remove finance video reaction"""
    try:
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

        return UniformResponse.success_response(
            message=f"Video {reaction_type} removed successfully",
            data={"action": f"remove_{reaction_type}"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to remove video {reaction_type}: {str(e)}"
        )


async def _handle_finance_comic_reaction(
    comic_id: str, user_id: str, reaction_type: str, db: firestore.AsyncClient
):
    """Handle finance comic like/dislike"""
    try:
        # Remove existing opposite reaction
        opposite_reaction = "dislike" if reaction_type == "like" else "like"
        await _remove_finance_comic_reaction(comic_id, user_id, opposite_reaction, db)

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
            return UniformResponse.success_response(
                message=f"Comic already {reaction_type}d",
                data={"action": f"{reaction_type}_exists"},
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

        return UniformResponse.success_response(
            message=f"Comic {reaction_type}d successfully",
            data={"action": reaction_type},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to {reaction_type} comic: {str(e)}"
        )


async def _remove_finance_comic_reaction(
    comic_id: str, user_id: str, reaction_type: str, db: firestore.AsyncClient
):
    """Remove finance comic reaction"""
    try:
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

        return UniformResponse.success_response(
            message=f"Comic {reaction_type} removed successfully",
            data={"action": f"remove_{reaction_type}"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to remove comic {reaction_type}: {str(e)}"
        )


@router.get("/progress", response_model=UniformResponse[FinanceProgressResponse])
async def get_finance_progress(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get comprehensive finance learning progress for user"""
    try:
        # Get all finance levels
        levels_ref = db.collection("game_levels").where("skill_type", "==", "finance")
        levels_docs = await levels_ref.get()
        total_levels = len(levels_docs)

        # Get user's finance game attempts
        attempts_ref = db.collection("game_attempts").where(
            "user_id", "==", current_user.id
        )
        attempts_docs = await attempts_ref.get()

        # Filter finance attempts and gather stats
        finance_attempts = []
        levels_completed = set()
        total_score = 0
        highest_level = 0

        for doc in attempts_docs:
            data = doc.to_dict()
            level_id = data.get("level_id", "")

            # Check if this is a finance level
            level_ref = db.collection("game_levels").document(level_id)
            level_doc = await level_ref.get()
            if level_doc.exists and level_doc.to_dict().get("skill_type") == "finance":
                level_data = level_doc.to_dict()
                attempt_data = {
                    "id": doc.id,
                    "level_id": level_id,
                    "score": data.get("score", 0),
                    "needs_selected": data.get("needs_selected", 0),
                    "wants_selected": data.get("wants_selected", 0),
                    "completed_at": data.get("completed_at"),
                    "level_title": level_data.get("title"),
                    "level_income": level_data.get("income"),
                }
                finance_attempts.append(attempt_data)
                levels_completed.add(level_id)
                total_score += data.get("score", 0)

                # Track highest level (by level number)
                level_number = level_data.get("level_number", 0)
                if level_number > highest_level:
                    highest_level = level_number

        # Calculate stats
        total_attempts = len(finance_attempts)
        average_score = (
            round(total_score / total_attempts, 1) if total_attempts > 0 else 0
        )

        # Get recent attempts (last 5)
        recent_attempts = sorted(
            finance_attempts,
            key=lambda x: x["completed_at"] or datetime.min,
            reverse=True,
        )[:5]

        # Get finance badges earned
        finance_badges = 0
        user_badges_ref = db.collection("user_badges").where(
            "user_id", "==", current_user.id
        )
        user_badges_docs = await user_badges_ref.get()

        for user_badge_doc in user_badges_docs:
            user_badge_data = user_badge_doc.to_dict()
            badge_id = user_badge_data.get("badge_id")
            if badge_id:
                try:
                    badge_ref = db.collection("badges").document(badge_id)
                    badge_doc = await badge_ref.get()
                    if badge_doc.exists:
                        badge_data = badge_doc.to_dict()
                        if badge_data.get("skill_type") == "finance":
                            finance_badges += 1
                except Exception:
                    continue

        # Calculate points earned from finance activities
        points_per_attempt = 2
        points_per_completion = 5
        bonus_points = 0
        total_points_earned = (
            total_attempts * points_per_attempt
            + len(levels_completed) * points_per_completion
            + finance_badges * 10
            + bonus_points
        )

        progress = FinanceProgressResponse(
            total_levels=total_levels,
            levels_completed=len(levels_completed),
            highest_level=highest_level,
            total_attempts=total_attempts,
            average_score=average_score,
            total_points_earned=total_points_earned,
            badges_earned=finance_badges,
            recent_attempts=[
                FinanceGameAttemptResponse(**attempt) for attempt in recent_attempts
            ],
        )

        return UniformResponse.success_response(
            message="Finance progress retrieved successfully",
            data=progress,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve finance progress: {str(e)}"
        )


@router.get("/leaderboard", response_model=UniformResponse[dict])
async def get_finance_leaderboard(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
    limit: int = Query(
        default=10, ge=5, le=50, description="Number of top players to show"
    ),
):
    """Get finance game leaderboard"""
    try:
        # Get all users' finance performance
        attempts_ref = db.collection("game_attempts")
        attempts_docs = await attempts_ref.get()

        # Group by user and calculate stats
        user_stats = {}
        for doc in attempts_docs:
            data = doc.to_dict()
            user_id = data.get("user_id")
            level_id = data.get("level_id", "")

            # Check if this is a finance level
            level_ref = db.collection("game_levels").document(level_id)
            level_doc = await level_ref.get()
            if level_doc.exists and level_doc.to_dict().get("skill_type") == "finance":
                if user_id not in user_stats:
                    user_stats[user_id] = {
                        "user_id": user_id,
                        "total_attempts": 0,
                        "total_score": 0,
                        "levels_completed": set(),
                        "highest_score": 0,
                    }

                user_stats[user_id]["total_attempts"] += 1
                user_stats[user_id]["total_score"] += data.get("score", 0)
                user_stats[user_id]["levels_completed"].add(level_id)
                score = data.get("score", 0)
                if score > user_stats[user_id]["highest_score"]:
                    user_stats[user_id]["highest_score"] = score

        # Calculate final scores and get user info
        leaderboard = []
        for user_id, stats in user_stats.items():
            try:
                # Get user info
                user_ref = db.collection("users").document(user_id)
                user_doc = await user_ref.get()
                if user_doc.exists:
                    user_data = user_doc.to_dict()

                    # Calculate composite score
                    avg_score = (
                        stats["total_score"] / stats["total_attempts"]
                        if stats["total_attempts"] > 0
                        else 0
                    )
                    composite_score = (
                        avg_score * 0.4
                        + len(stats["levels_completed"]) * 10
                        + stats["highest_score"] * 0.3
                        + stats["total_attempts"] * 0.1
                    )

                    leaderboard.append(
                        {
                            "user_id": user_id,
                            "username": user_data.get("username", "Unknown"),
                            "first_name": user_data.get("first_name", ""),
                            "total_attempts": stats["total_attempts"],
                            "levels_completed": len(stats["levels_completed"]),
                            "average_score": round(avg_score, 1),
                            "highest_score": stats["highest_score"],
                            "composite_score": round(composite_score, 1),
                            "is_current_user": user_id == current_user.id,
                        }
                    )
            except Exception:
                continue

        # Sort by composite score
        leaderboard.sort(key=lambda x: x["composite_score"], reverse=True)

        # Add rankings
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1

        # Limit results
        top_leaderboard = leaderboard[:limit]

        # Find current user's position if not in top
        current_user_entry = None
        if not any(entry["is_current_user"] for entry in top_leaderboard):
            for entry in leaderboard:
                if entry["is_current_user"]:
                    current_user_entry = entry
                    break

        return UniformResponse.success_response(
            message="Finance leaderboard retrieved successfully",
            data={
                "leaderboard": top_leaderboard,
                "current_user_entry": current_user_entry,
                "total_players": len(leaderboard),
                "user_rank": current_user_entry["rank"] if current_user_entry else None,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve finance leaderboard: {str(e)}"
        )


@router.get("/levels/recommendations", response_model=UniformResponse[dict])
async def get_finance_level_recommendations(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get recommended finance levels for user based on their progress"""
    try:
        # Get user's completed levels
        attempts_ref = db.collection("game_attempts").where(
            "user_id", "==", current_user.id
        )
        attempts_docs = await attempts_ref.get()

        completed_levels = set()
        user_average_score = 0
        total_attempts = 0
        total_score = 0

        for doc in attempts_docs:
            data = doc.to_dict()
            level_id = data.get("level_id", "")

            # Check if this is a finance level
            level_ref = db.collection("game_levels").document(level_id)
            level_doc = await level_ref.get()
            if level_doc.exists and level_doc.to_dict().get("skill_type") == "finance":
                completed_levels.add(level_id)
                total_attempts += 1
                total_score += data.get("score", 0)

        user_average_score = total_score / total_attempts if total_attempts > 0 else 0

        # Get all finance levels
        levels_ref = db.collection("game_levels").where("skill_type", "==", "finance")
        levels_docs = await levels_ref.get()

        # Find recommendations
        recommendations = []
        for doc in levels_docs:
            level_data = doc.to_dict()
            level_id = doc.id

            if level_id not in completed_levels:
                # Determine recommendation score based on user performance
                difficulty = level_data.get("difficulty", "easy")
                level_number = level_data.get("level_number", 1)
                recommendation_score = 0

                # Beginner recommendations
                if total_attempts == 0:
                    if difficulty == "easy" and level_number <= 3:
                        recommendation_score = 10
                elif user_average_score < 60:
                    if difficulty == "easy":
                        recommendation_score = 8
                elif user_average_score < 80:
                    if difficulty in ["easy", "medium"]:
                        recommendation_score = 7
                else:
                    recommendation_score = 5

                # Boost score for sequential levels
                max_completed_level = 0
                for completed_level_id in completed_levels:
                    try:
                        comp_level_ref = db.collection("game_levels").document(
                            completed_level_id
                        )
                        comp_level_doc = await comp_level_ref.get()
                        if comp_level_doc.exists:
                            comp_level_data = comp_level_doc.to_dict()
                            comp_level_number = comp_level_data.get("level_number", 0)
                            if comp_level_number > max_completed_level:
                                max_completed_level = comp_level_number
                    except Exception:
                        continue

                if level_number == max_completed_level + 1:
                    recommendation_score += 5  # Next sequential level

                if recommendation_score > 0:
                    recommendations.append(
                        {
                            "level_id": level_id,
                            "level_number": level_number,
                            "title": level_data.get("title", ""),
                            "description": level_data.get("description", ""),
                            "difficulty": difficulty,
                            "income": level_data.get("income", 0),
                            "recommendation_score": recommendation_score,
                            "reason": _get_recommendation_reason(
                                difficulty,
                                level_number,
                                max_completed_level,
                                user_average_score,
                                total_attempts,
                            ),
                        }
                    )

        # Sort by recommendation score
        recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)

        return UniformResponse.success_response(
            message="Finance level recommendations retrieved successfully",
            data={
                "recommendations": recommendations[:5],  # Top 5 recommendations
                "user_stats": {
                    "levels_completed": len(completed_levels),
                    "total_attempts": total_attempts,
                    "average_score": round(user_average_score, 1),
                },
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get finance level recommendations: {str(e)}",
        )


def _get_recommendation_reason(
    difficulty, level_number, max_completed_level, avg_score, total_attempts
):
    """Generate recommendation reason based on user performance"""
    if total_attempts == 0:
        return f"Perfect starting level for beginners (Level {level_number})"
    elif level_number == max_completed_level + 1:
        return "Next sequential level in your progression"
    elif avg_score < 60 and difficulty == "easy":
        return "Easy level to build confidence"
    elif avg_score >= 80 and difficulty == "hard":
        return "Challenge level for advanced learners"
    else:
        return f"Recommended based on your {difficulty} skill level"


@router.get(
    "/comic/{comic_id}/reaction", response_model=UniformResponse[UserReactionResponse]
)
async def get_finance_comic_reaction(
    comic_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get user's reaction status for a finance comic"""
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

        return UniformResponse.success_response(
            message="Finance comic reaction status retrieved successfully",
            data=UserReactionResponse(liked=liked, disliked=disliked),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get finance comic reaction: {str(e)}"
        )


@router.get(
    "/video/{video_id}/reaction", response_model=UniformResponse[UserReactionResponse]
)
async def get_finance_video_reaction(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get user's reaction status for a finance video"""
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

        return UniformResponse.success_response(
            message="Finance video reaction status retrieved successfully",
            data=UserReactionResponse(liked=liked, disliked=disliked),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get finance video reaction: {str(e)}"
        )


# Finance Game Stats endpoint
@router.get("/game/stats", response_model=UniformResponse[dict])
async def get_finance_game_stats(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get user's finance game statistics"""
    try:
        # Get all finance game attempts for this user
        attempts_ref = db.collection("game_attempts").where(
            "user_id", "==", current_user.id
        )
        attempts_docs = await attempts_ref.get()

        finance_attempts = []
        for doc in attempts_docs:
            data = doc.to_dict()
            # Check if this is a finance game attempt
            level_ref = db.collection("game_levels").document(data.get("level_id", ""))
            level_doc = await level_ref.get()
            if level_doc.exists and level_doc.to_dict().get("skill_type") == "finance":
                finance_attempts.append(data)

        # Calculate stats
        total_attempts = len(finance_attempts)
        total_score = sum(attempt.get("score", 0) for attempt in finance_attempts)
        average_score = (
            round(total_score / total_attempts, 1) if total_attempts > 0 else 0
        )
        levels_completed = len(
            {attempt.get("level_id") for attempt in finance_attempts}
        )

        # Get highest score
        highest_score = max(
            (attempt.get("score", 0) for attempt in finance_attempts), default=0
        )

        stats = {
            "total_attempts": total_attempts,
            "levels_completed": levels_completed,
            "average_score": average_score,
            "highest_score": highest_score,
            "total_score": total_score,
        }

        return UniformResponse.success_response(
            message="Finance game stats retrieved successfully",
            data={"stats": stats},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve finance game stats: {str(e)}"
        )


@router.get("/game/level/{level}", response_model=UniformResponse[GameLevelResponse])
async def get_game_level(
    level: int,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get finance game level data with quiz ID"""
    try:
        # Get level details
        level_ref = (
            db.collection("game_levels")
            .where("level_number", "==", level)
            .where("skill_type", "==", "finance")
        )
        level_docs = await level_ref.get()

        if not level_docs:
            raise HTTPException(status_code=404, detail="Game level not found")

        level_doc = level_docs[0]
        level_data = level_doc.to_dict()

        # Get quiz ID for this game level using shared utility
        quiz_id = await get_quiz_id_for_content(db, level_doc.id, "game", "finance")

        # Get items for this level
        items_ref = db.collection("game_items").where("level_id", "==", level_doc.id)
        items_docs = await items_ref.get()

        items = []
        for item_doc in items_docs:
            item_data = item_doc.to_dict()
            items.append(
                GameItemResponse(
                    name=item_data.get("name", ""),
                    cost=item_data.get("cost", 0),
                    item_type=item_data.get("item_type", ""),
                    description=item_data.get("description", ""),
                )
            )

        game_response = GameLevelResponse(
            success=True,
            income=level_data.get("income", 1000),
            items=items,
            quiz_id=quiz_id,  # ✅ FIXED: Include quiz ID using shared utility
        )

        return UniformResponse.success_response(
            message="Game level retrieved successfully", data=game_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve game level: {str(e)}"
        )


@router.get("/videos", response_model=UniformResponse[dict])
async def get_finance_videos(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get all finance videos with quiz IDs and badge information"""
    try:
        videos_ref = db.collection("videos").where("skill_type", "==", "finance")
        videos_docs = await videos_ref.get()

        videos = []
        for doc in videos_docs:
            data = doc.to_dict()
            video_id = doc.id

            # Get quiz ID for this video using shared utility
            quiz_id = await get_quiz_id_for_content(db, video_id, "video", "finance")

            # Get badge information
            badge_info = await get_badge_info_for_content(db, video_id, "videos")

            video_data = {
                "id": video_id,
                "title": data.get("title", ""),
                "description": data.get("description", ""),
                "thumbnail": data.get("thumbnail_url", ""),
                "quiz_id": quiz_id,  # ✅ FIXED: Include quiz ID using shared utility
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

        return UniformResponse.success_response(
            message="Finance videos retrieved successfully", data={"videos": videos}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve finance videos: {str(e)}"
        )


@router.get("/comics", response_model=UniformResponse[dict])
async def get_finance_comics(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get all finance comics with quiz IDs and badge information"""
    try:
        comics_ref = db.collection("comics").where("skill_type", "==", "finance")
        comics_docs = await comics_ref.get()

        comics = []
        for doc in comics_docs:
            data = doc.to_dict()
            comic_id = doc.id

            # Get quiz ID for this comic using shared utility
            quiz_id = await get_quiz_id_for_content(db, comic_id, "comic", "finance")

            # Get badge information
            badge_info = await get_badge_info_for_content(db, comic_id, "comics")

            comic_data = {
                "id": comic_id,
                "title": data.get("title", ""),
                "description": data.get("description", ""),
                "thumbnail": data.get("thumbnail_url", ""),
                "quiz_id": quiz_id,  # ✅ FIXED: Include quiz ID using shared utility
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

        return UniformResponse.success_response(
            message="Finance comics retrieved successfully", data={"comics": comics}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve finance comics: {str(e)}"
        )


@router.get(
    "/level/{level_id}/quiz", response_model=UniformResponse[EnhancedQuizResponse]
)
async def get_finance_level_quiz(
    level_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get quiz questions for a finance game level with comprehensive information"""
    try:
        # Verify the level exists
        level_ref = db.collection("game_levels").document(level_id)
        level_doc = await level_ref.get()
        if not level_doc.exists:
            raise HTTPException(status_code=404, detail="Finance level not found")

        level_data = level_doc.to_dict()
        if level_data.get("skill_type") != "finance":
            raise HTTPException(status_code=400, detail="This is not a finance level")

        # Use the standardized quiz retrieval function
        from app.api.v1.quiz import get_quiz_by_content

        return await get_quiz_by_content(level_id, "game", "finance", db)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve finance level quiz: {str(e)}"
        )


@router.post(
    "/level/{level_id}/quiz/submit", response_model=UniformResponse[QuizResultResponse]
)
async def submit_finance_level_quiz(
    level_id: str,
    submission: QuizSubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Submit quiz answers for a finance game level"""
    try:
        # Get quiz for this finance level
        quiz_ref = (
            db.collection("quizzes")
            .where("content_id", "==", level_id)
            .where("content_type", "==", "game")
            .where("skill_type", "==", "finance")
        )
        quiz_docs = await quiz_ref.get()
        if not quiz_docs:
            raise HTTPException(
                status_code=404, detail="No quiz found for this finance level"
            )

        quiz_id = quiz_docs[0].id
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
            "content_id": level_id,
            "content_type": "game",
            "skill_type": "finance",
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
            content_id=level_id,
            content_type="game",
            skill_type="finance",
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
            message="Finance level quiz submitted successfully", data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to submit finance level quiz: {str(e)}"
        )


@router.get(
    "/video/{video_id}/quiz", response_model=UniformResponse[EnhancedQuizResponse]
)
async def get_finance_video_quiz(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """
    🚀 NEW: Get quiz for a finance video with AUTO-GENERATION
    Guarantees quiz availability for all finance videos!
    """
    try:
        # Verify video exists and is a finance video
        video_ref = db.collection("videos").document(video_id)
        video_doc = await video_ref.get()
        if not video_doc.exists:
            raise HTTPException(status_code=404, detail="Finance video not found")

        video_data = video_doc.to_dict()
        if video_data.get("skill_type") != "finance":
            raise HTTPException(status_code=400, detail="This is not a finance video")

        # Use the enhanced auto-generation function
        return await get_quiz_by_content_with_auto_gen(video_id, "video", "finance", db)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve finance video quiz: {str(e)}"
        )


@router.get(
    "/comic/{comic_id}/quiz", response_model=UniformResponse[EnhancedQuizResponse]
)
async def get_finance_comic_quiz(
    comic_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """
    🚀 NEW: Get quiz for a finance comic with AUTO-GENERATION
    Guarantees quiz availability for all finance comics!
    """
    try:
        # Verify comic exists and is a finance comic
        comic_ref = db.collection("comics").document(comic_id)
        comic_doc = await comic_ref.get()
        if not comic_doc.exists:
            raise HTTPException(status_code=404, detail="Finance comic not found")

        comic_data = comic_doc.to_dict()
        if comic_data.get("skill_type") != "finance":
            raise HTTPException(status_code=400, detail="This is not a finance comic")

        # Use the enhanced auto-generation function
        return await get_quiz_by_content_with_auto_gen(comic_id, "comic", "finance", db)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve finance comic quiz: {str(e)}"
        )


@router.post(
    "/video/{video_id}/quiz/submit", response_model=UniformResponse[QuizResultResponse]
)
async def submit_finance_video_quiz(
    video_id: str,
    submission: QuizSubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Submit quiz answers for a finance video"""
    try:
        # Get quiz for this video (guaranteed to exist with auto-generation)
        quiz_ref = (
            db.collection("quizzes")
            .where("content_id", "==", video_id)
            .where("content_type", "==", "video")
            .where("skill_type", "==", "finance")
        )
        quiz_docs = await quiz_ref.get()

        if not quiz_docs:
            # This should never happen with auto-generation, but just in case
            raise HTTPException(
                status_code=404, detail="No quiz found for this finance video"
            )

        quiz_id = quiz_docs[0].id

        # Use the centralized quiz submission from quiz.py
        from app.api.v1.quiz import submit_quiz

        # Create a mock request object with quiz_id
        class MockRequest:
            def __init__(self, quiz_id):
                self.path_params = {"quiz_id": quiz_id}

        _mock_request = MockRequest(quiz_id)

        # Forward to the main quiz submission handler
        return await submit_quiz(quiz_id, submission, current_user, db)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to submit finance video quiz: {str(e)}"
        )


@router.post(
    "/comic/{comic_id}/quiz/submit", response_model=UniformResponse[QuizResultResponse]
)
async def submit_finance_comic_quiz(
    comic_id: str,
    submission: QuizSubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Submit quiz answers for a finance comic"""
    try:
        # Get quiz for this comic (guaranteed to exist with auto-generation)
        quiz_ref = (
            db.collection("quizzes")
            .where("content_id", "==", comic_id)
            .where("content_type", "==", "comic")
            .where("skill_type", "==", "finance")
        )
        quiz_docs = await quiz_ref.get()

        if not quiz_docs:
            # This should never happen with auto-generation, but just in case
            raise HTTPException(
                status_code=404, detail="No quiz found for this finance comic"
            )

        quiz_id = quiz_docs[0].id

        # Forward to the main quiz submission handler
        from app.api.v1.quiz import submit_quiz

        return await submit_quiz(quiz_id, submission, current_user, db)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to submit finance comic quiz: {str(e)}"
        )
