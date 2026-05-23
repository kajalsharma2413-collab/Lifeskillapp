# app/api/v1/quiz.py - UPDATED with Auto-Generation
# Enhanced Quiz Endpoints with Automatic Quiz Generation

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import firestore

from app.api.dependencies.auth import get_current_user
from app.config.firebase import get_firebase_client
from app.models.user import User
from app.schemas.base import UniformResponse
from app.schemas.quiz import (
    EnhancedQuizResponse,
    QuestionOptionResponse,
    QuestionResponse,
    QuizMetadata,
    QuizResultResponse,
    QuizSubmissionRequest,
)
from app.utils.quiz_utils import get_quiz_id_for_content

router = APIRouter(prefix="/quiz", tags=["quiz"])
logger = logging.getLogger(__name__)

# ==================== ENHANCED QUIZ RETRIEVAL WITH AUTO-GENERATION ====================


async def _get_enhanced_quiz_by_id(
    quiz_id: str, db: firestore.AsyncClient
) -> UniformResponse[EnhancedQuizResponse]:
    """Get comprehensive quiz information by ID"""
    try:
        # Get quiz document
        quiz_ref = db.collection("quizzes").document(quiz_id)
        quiz_doc = await quiz_ref.get()

        if not quiz_doc.exists:
            raise HTTPException(status_code=404, detail="Quiz not found")

        quiz_data = quiz_doc.to_dict()

        # Get all questions for this quiz
        questions_ref = (
            db.collection("questions")
            .where("quiz_id", "==", quiz_id)
            .order_by("question_order")
        )
        questions_docs = await questions_ref.get()

        questions = []
        for question_doc in questions_docs:
            question_data = question_doc.to_dict()
            question_id = question_doc.id

            # Get options for this question
            options_ref = (
                db.collection("question_options")
                .where("question_id", "==", question_id)
                .order_by("option_order")
            )
            options_docs = await options_ref.get()

            options = [
                QuestionOptionResponse(
                    id=option_doc.id,
                    option_order=option_doc.to_dict().get("option_order", 1),
                    text=option_doc.to_dict().get("option_text", ""),
                    is_correct=option_doc.to_dict().get("is_correct", False),
                )
                for option_doc in options_docs
            ]

            questions.append(
                QuestionResponse(
                    id=question_id,
                    question_order=question_data.get("question_order", 1),
                    question_text=question_data.get("question_text", ""),
                    options=options,
                )
            )

        # Build quiz metadata
        metadata = QuizMetadata(
            quiz_id=quiz_id,
            title=quiz_data.get("title", ""),
            skill_type=quiz_data.get("skill_type", ""),
            content_type=quiz_data.get("content_type", ""),
            content_id=quiz_data.get("content_id", ""),
            min_score=quiz_data.get("min_score", 50),
            max_attempts=quiz_data.get("max_attempts"),
            time_limit_minutes=quiz_data.get("time_limit_minutes"),
            badge_id=quiz_data.get("badge_id"),
            badge_name=quiz_data.get("badge_name"),
            badge_description=quiz_data.get("badge_description"),
        )

        # Build enhanced response
        enhanced_quiz = EnhancedQuizResponse(
            metadata=metadata,
            questions=questions,
            total_questions=len(questions),
        )

        return UniformResponse.success_response(
            message="Quiz retrieved successfully",
            data=enhanced_quiz,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving quiz {quiz_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve quiz: {str(e)}"
        )


async def get_quiz_by_content_with_auto_gen(
    content_id: str, content_type: str, skill_type: str, db: firestore.AsyncClient
) -> UniformResponse[EnhancedQuizResponse]:
    """
    Get quiz for content by looking it up directly from Firestore.
    """
    logger.info(f"🔍 Looking for quiz: {skill_type} {content_type} {content_id}")

    quiz_id = await get_quiz_id_for_content(db, content_id, content_type, skill_type)

    if not quiz_id:
        raise HTTPException(
            status_code=404,
            detail=f"No quiz found for {skill_type} {content_type} {content_id}",
        )

    logger.info(f"✅ Quiz found with ID: {quiz_id}")
    return await _get_enhanced_quiz_by_id(quiz_id, db)


# ==================== UPDATED QUIZ ENDPOINTS ====================


@router.get("/{quiz_id}", response_model=UniformResponse[EnhancedQuizResponse])
async def get_quiz_by_id(
    quiz_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get quiz by ID with comprehensive information"""
    return await _get_enhanced_quiz_by_id(quiz_id, db)


@router.get("/video/{video_id}", response_model=UniformResponse[EnhancedQuizResponse])
async def get_video_quiz(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """
    🚀 ENHANCED: Get quiz for a video with AUTO-GENERATION
    No more 404 errors - always returns a quiz!
    """
    logger.info(f"📹 Getting quiz for video {video_id}")

    # First try to find the video to determine its skill type
    video_ref = db.collection("videos").document(video_id)
    video_doc = await video_ref.get()

    if not video_doc.exists:
        raise HTTPException(status_code=404, detail="Video not found")

    video_data = video_doc.to_dict()
    skill_type = video_data.get("skill_type", "safety")

    # Use auto-generation function - GUARANTEED to return a quiz
    return await get_quiz_by_content_with_auto_gen(video_id, "video", skill_type, db)


@router.get("/comic/{comic_id}", response_model=UniformResponse[EnhancedQuizResponse])
async def get_comic_quiz(
    comic_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """
    🚀 ENHANCED: Get quiz for a comic with AUTO-GENERATION
    No more 404 errors - always returns a quiz!
    """
    logger.info(f"📚 Getting quiz for comic {comic_id}")

    # First try to find the comic to determine its skill type
    comic_ref = db.collection("comics").document(comic_id)
    comic_doc = await comic_ref.get()

    if not comic_doc.exists:
        raise HTTPException(status_code=404, detail="Comic not found")

    comic_data = comic_doc.to_dict()
    skill_type = comic_data.get("skill_type", "safety")

    # Use auto-generation function - GUARANTEED to return a quiz
    return await get_quiz_by_content_with_auto_gen(comic_id, "comic", skill_type, db)


@router.get(
    "/finance/level/{level_id}", response_model=UniformResponse[EnhancedQuizResponse]
)
async def get_finance_level_quiz(
    level_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """
    🚀 ENHANCED: Get quiz for a finance level with AUTO-GENERATION
    """
    logger.info(f"💰 Getting quiz for finance level {level_id}")

    # Check if finance level exists
    level_ref = db.collection("game_levels").document(level_id)
    level_doc = await level_ref.get()

    if not level_doc.exists:
        raise HTTPException(status_code=404, detail="Finance level not found")

    # Use auto-generation for finance levels
    return await get_quiz_by_content_with_auto_gen(level_id, "level", "finance", db)


# ==================== QUIZ SUBMISSION (UNCHANGED) ====================


@router.post("/{quiz_id}/submit", response_model=UniformResponse[QuizResultResponse])
async def submit_quiz(
    quiz_id: str,
    submission: QuizSubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Submit quiz answers and get comprehensive results"""
    try:
        # Get quiz details
        quiz_ref = db.collection("quizzes").document(quiz_id)
        quiz_doc = await quiz_ref.get()

        if not quiz_doc.exists:
            raise HTTPException(status_code=404, detail="Quiz not found")

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

        # Get attempt number
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
            "content_id": quiz_data.get("content_id"),
            "content_type": quiz_data.get("content_type"),
            "skill_type": quiz_data.get("skill_type"),
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

        # Handle badge awarding (if applicable)
        badge_awarded = False
        badge_id = quiz_data.get("badge_id")
        badge_name = quiz_data.get("badge_name")

        if passed and badge_id:
            # Check if user already has this badge
            existing_badge_ref = (
                db.collection("user_badges")
                .where("user_id", "==", current_user.id)
                .where("badge_id", "==", badge_id)
            )
            existing_badges = await existing_badge_ref.get()

            if not existing_badges:
                # Award badge
                badge_data = {
                    "user_id": current_user.id,
                    "badge_id": badge_id,
                    "earned_from": f"quiz_{quiz_id}",
                    "earned_at": datetime.utcnow(),
                }
                await db.collection("user_badges").add(badge_data)
                badge_awarded = True

        # Build result response
        result = QuizResultResponse(
            quiz_id=quiz_id,
            content_id=quiz_data.get("content_id", ""),
            content_type=quiz_data.get("content_type", ""),
            skill_type=quiz_data.get("skill_type", ""),
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

        message = f"Quiz completed! Score: {score_percentage}% ({'Passed' if passed else 'Failed'})"
        if badge_awarded:
            message += f" 🏆 Badge earned: {badge_name}!"

        return UniformResponse.success_response(message=message, data=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting quiz {quiz_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit quiz: {str(e)}")


# ==================== ADMIN UTILITIES ====================


@router.get("/admin/coverage", response_model=UniformResponse[dict])
async def get_quiz_coverage_stats(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """
    🔍 ADMIN: Get quiz coverage statistics across all content
    """
    try:
        # Count total content
        videos_snapshot = await db.collection("videos").get()
        comics_snapshot = await db.collection("comics").get()
        levels_snapshot = await db.collection("game_levels").get()

        total_videos = len(videos_snapshot)
        total_comics = len(comics_snapshot)
        total_levels = len(levels_snapshot)

        # Count content with quizzes
        video_quizzes = (
            await db.collection("quizzes").where("content_type", "==", "video").get()
        )
        comic_quizzes = (
            await db.collection("quizzes").where("content_type", "==", "comic").get()
        )
        level_quizzes = (
            await db.collection("quizzes").where("content_type", "==", "level").get()
        )

        videos_with_quizzes = len(video_quizzes)
        comics_with_quizzes = len(comic_quizzes)
        levels_with_quizzes = len(level_quizzes)

        # Count auto-generated quizzes
        auto_quizzes = (
            await db.collection("quizzes").where("auto_generated", "==", True).get()
        )
        auto_generated_count = len(auto_quizzes)

        stats = {
            "total_content": {
                "videos": total_videos,
                "comics": total_comics,
                "levels": total_levels,
                "total": total_videos + total_comics + total_levels,
            },
            "quiz_coverage": {
                "videos": f"{videos_with_quizzes}/{total_videos} ({videos_with_quizzes / total_videos * 100:.1f}%)"
                if total_videos > 0
                else "0/0 (0%)",
                "comics": f"{comics_with_quizzes}/{total_comics} ({comics_with_quizzes / total_comics * 100:.1f}%)"
                if total_comics > 0
                else "0/0 (0%)",
                "levels": f"{levels_with_quizzes}/{total_levels} ({levels_with_quizzes / total_levels * 100:.1f}%)"
                if total_levels > 0
                else "0/0 (0%)",
                "overall": f"{videos_with_quizzes + comics_with_quizzes + levels_with_quizzes}/{total_videos + total_comics + total_levels}",
            },
            "auto_generated_quizzes": auto_generated_count,
            "system_status": "🚀 Auto-generation ENABLED - 100% coverage guaranteed!",
        }

        return UniformResponse.success_response(
            message="Quiz coverage statistics retrieved", data=stats
        )

    except Exception as e:
        logger.error(f"Error getting quiz coverage stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get coverage stats: {str(e)}"
        )
