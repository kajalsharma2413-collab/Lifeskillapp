# app/api/v1/problem_solving.py
import logging
from datetime import date, datetime

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import firestore
from pydantic import BaseModel, Field, field_validator

from app.api.dependencies.ai.problem_solving.models import QuestionResponse
from app.api.dependencies.ai.problem_solving.service import QuestionService
from app.api.dependencies.auth import get_current_user
from app.config.firebase import get_firebase_client
from app.models.user import User
from app.schemas.base import UniformResponse
from app.schemas.skill import ProblemSolvingProgressResponse
from app.services.ai import generate_problem_solving_questions

router = APIRouter(prefix="/problem-solving", tags=["problem-solving"])

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize service — model configured via OLLAMA_* env vars, no API key needed
service = QuestionService()


class GenerateQuestionRequest(BaseModel):
    """Request model for generating problem-solving questions."""

    user_id: str = Field(..., description="User ID for question generation")
    level: str = Field(
        default="beginner", description="Difficulty level: beginner, medium, advanced"
    )
    skill_focus: str = Field(
        default="financial_literacy", description="Skill area focus"
    )

    @field_validator("level")
    def validate_level(cls, v):
        valid_levels = ["beginner", "medium", "advanced"]
        if v not in valid_levels:
            raise ValueError(f"Level must be one of: {', '.join(valid_levels)}")
        return v


class FinancialQuestionResponse(BaseModel):
    """Enhanced question response with financial literacy context."""

    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str
    explanation: str
    skill_area: str = "financial_literacy"
    age_appropriate: bool = True
    difficulty_level: str
    learning_objective: str
    points_awarded: int = 10


class BadgeScoreRequest(BaseModel):
    """Request model for badge score creation."""

    badge_link: str
    user_id: str
    score: int = None
    additional_data: dict = None


@router.post("/generate", response_model=QuestionResponse)
async def generate_question():
    """
    Generate a thought-provoking question to boost mental ability.

    Levels: beginner, medium, advanced
    """
    try:
        # Use dummy data for testing
        user_id = "104"
        level = "beginner"

        # Uncomment to use actual request data:
        # user_id = request.user_id
        # level = request.level

        question = service.generate_question(user_id=user_id, level=level)

        logger.info(f"Generated question for user: {user_id}, level: {level}")
        return question

    except Exception as e:
        logger.error(f"Error generating question: {e}")
        raise HTTPException(
            status_code=500, detail=f"Could not generate question: {str(e)}"
        )


@router.get("/progress", response_model=UniformResponse[ProblemSolvingProgressResponse])
async def get_problem_solving_progress(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get user's financial literacy problem-solving progress for today."""
    try:
        today = date.today().isoformat()
        progress_ref = db.collection("problem_solving_progress").document(
            f"{current_user.id}_{today}"
        )
        progress_doc = await progress_ref.get()

        if progress_doc.exists:
            progress_data = progress_doc.to_dict()
            response = ProblemSolvingProgressResponse(
                date=today,
                attempted=progress_data.get("questions_attempted", 0),
                correct=progress_data.get("questions_correct", 0),
                badge_earned=progress_data.get("badge_earned", False),
            )
        else:
            response = ProblemSolvingProgressResponse(
                date=today, attempted=0, correct=0, badge_earned=False
            )

        return UniformResponse.success_response(
            message="Problem-solving progress retrieved successfully", data=response
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get problem-solving progress: {str(e)}"
        )


@router.get("/questions", response_model=UniformResponse[dict])
async def get_daily_questions(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get 6 daily AI-generated problem-solving questions."""
    try:
        today = date.today().isoformat()

        progress_ref = (
            db.collection("problem_solving_progress")
            .where("user_id", "==", current_user.id)
            .where("date", "==", today)
        )
        progress_docs = await progress_ref.get()

        if progress_docs:
            progress_data = progress_docs[0].to_dict()
            if progress_data.get("questions_attempted", 0) >= 6:
                return UniformResponse.error_response(
                    message="Daily question limit reached",
                    errors=[
                        "You have already completed today's 6 questions. Come back tomorrow!"
                    ],
                )

        questions_ref = db.collection("daily_questions").document(
            f"{current_user.id}_{today}"
        )
        questions_doc = await questions_ref.get()

        if questions_doc.exists:
            questions_data = questions_doc.to_dict()
            questions = questions_data.get("questions", [])
        else:
            questions = await generate_problem_solving_questions()

            await questions_ref.set(
                {
                    "user_id": current_user.id,
                    "date": today,
                    "questions": questions,
                    "created_at": datetime.utcnow(),
                }
            )

        return UniformResponse.success_response(
            message="Daily questions retrieved successfully",
            data={"questions": questions},
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get daily questions: {str(e)}"
        )


@router.get("/recommendations", response_model=UniformResponse[dict])
async def get_learning_recommendations(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """
    Get personalized financial literacy learning recommendations based on:
    - User's age and current skill level
    - Recent performance and progress
    - Areas needing improvement
    - Engaging next steps for continued learning
    """
    try:
        user_ref = db.collection("users").document(current_user.id)
        user_doc = await user_ref.get()
        user_data = user_doc.to_dict() if user_doc.exists else {}

        age = user_data.get("age", 10)
        current_level = user_data.get("skill_level", "beginner")

        recommendations = {
            "current_level": current_level,
            "age_appropriate_level": "beginner"
            if age <= 9
            else "medium"
            if age <= 11
            else "advanced",
            "recommended_activities": [],
            "focus_areas": [],
            "next_skills": [],
        }

        if age <= 9:
            recommendations["recommended_activities"] = [
                "Practice identifying needs vs wants",
                "Learn about different coins and bills",
                "Simple saving goals (toy, game)",
                "Understanding 'expensive' vs 'cheap'",
            ]
            recommendations["focus_areas"] = ["basic_money_concepts", "needs_vs_wants"]
            recommendations["next_skills"] = ["counting_money", "simple_saving"]

        elif age <= 11:
            recommendations["recommended_activities"] = [
                "Set and track a savings goal",
                "Practice making smart spending choices",
                "Learn about earning money through chores",
                "Budget a small allowance",
            ]
            recommendations["focus_areas"] = ["saving_strategies", "spending_decisions"]
            recommendations["next_skills"] = ["goal_setting", "basic_budgeting"]

        else:
            recommendations["recommended_activities"] = [
                "Create a monthly budget plan",
                "Compare prices before purchasing",
                "Learn about bank accounts and interest",
                "Plan for larger financial goals",
            ]
            recommendations["focus_areas"] = [
                "financial_planning",
                "comparison_shopping",
            ]
            recommendations["next_skills"] = ["banking_basics", "investment_concepts"]

        return UniformResponse.success_response(
            message="Learning recommendations generated successfully",
            data=recommendations,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get recommendations: {str(e)}"
        )


@router.post("/badges/problem-solving", response_model=UniformResponse[dict])
async def award_problem_solving_badge(
    request: BadgeScoreRequest,
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Award badge for problem-solving completion and create score database entry."""
    try:
        today = date.today().isoformat()

        progress_ref = (
            db.collection("problem_solving_progress")
            .where("user_id", "==", request.user_id)
            .where("date", "==", today)
        )
        progress_docs = await progress_ref.get()

        if not progress_docs:
            raise HTTPException(status_code=400, detail="No progress found for today")

        progress_data = progress_docs[0].to_dict()
        attempted = progress_data.get("questions_attempted", 0)
        correct = progress_data.get("questions_correct", 0)

        if (
            attempted >= 6
            and correct >= 4
            and not progress_data.get("badge_earned", False)
        ):
            badge_id = "problem_solving_daily"

            user_ref = db.collection("users").document(request.user_id)
            user_doc = await user_ref.get()

            if user_doc.exists:
                user_data = user_doc.to_dict()
                current_badges = user_data.get("badges", [])
                if badge_id not in current_badges:
                    current_badges.append(badge_id)
                    await user_ref.update(
                        {
                            "badges": current_badges,
                            "points": user_data.get("points", 0) + 5,
                        }
                    )

            await progress_docs[0].reference.update({"badge_earned": True})

            score_data = {
                "user_id": request.user_id,
                "badge_id": badge_id,
                "badge_link": request.badge_link,
                "score": request.score if request.score is not None else correct,
                "max_score": 6,
                "questions_attempted": attempted,
                "questions_correct": correct,
                "success_rate": round((correct / attempted) * 100, 2)
                if attempted > 0
                else 0,
                "earned_at": datetime.utcnow(),
                "date": today,
                "quiz_id": None,
                "skill_type": "problem_solving",
                "activity_type": "daily_challenge",
                "additional_data": request.additional_data or {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            await db.collection("user_badges").add(score_data)
            await db.collection("score_database").add(score_data)

            return UniformResponse.success_response(
                message="Problem-solving badge awarded and score recorded successfully",
                data={
                    "badge_earned": True,
                    "badge_id": badge_id,
                    "badge_link": request.badge_link,
                    "score": score_data["score"],
                    "success_rate": score_data["success_rate"],
                    "score_database_id": "created",
                },
            )
        else:
            score_data = {
                "user_id": request.user_id,
                "badge_id": None,
                "badge_link": request.badge_link,
                "score": request.score if request.score is not None else correct,
                "max_score": 6,
                "questions_attempted": attempted,
                "questions_correct": correct,
                "success_rate": round((correct / attempted) * 100, 2)
                if attempted > 0
                else 0,
                "earned_at": None,
                "date": today,
                "quiz_id": None,
                "skill_type": "problem_solving",
                "activity_type": "daily_challenge",
                "badge_earned": False,
                "additional_data": request.additional_data or {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            await db.collection("score_database").add(score_data)

            return UniformResponse.error_response(
                message="Badge criteria not met, but score recorded",
                errors=[
                    f"Need 4+ correct answers out of 6. Current: {correct}/{attempted}"
                ],
                data={
                    "badge_earned": False,
                    "score": score_data["score"],
                    "success_rate": score_data["success_rate"],
                    "score_database_id": "created",
                },
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process problem-solving badge: {str(e)}"
        )


@router.post("/submit-answer", response_model=UniformResponse[dict])
async def submit_answer(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """
    Submit answer for a financial literacy question and get immediate feedback.

    Tracks progress and awards points based on correct answers and consistency.
    """
    try:
        question_id = request.get("question_id")
        selected_answer = request.get("selected_answer")
        user_id = request.get("user_id", current_user.id)

        if user_id != current_user.id and current_user.role.value not in [
            "parent",
            "admin",
        ]:
            raise HTTPException(status_code=403, detail="Access denied")

        question_ref = db.collection("problem_solving_questions").document(question_id)
        question_doc = await question_ref.get()

        if not question_doc.exists:
            raise HTTPException(status_code=404, detail="Question not found")

        question_data = question_doc.to_dict()
        correct_answer = question_data.get("correct_answer")
        level = question_data.get("level", "beginner")

        is_correct = selected_answer.upper() == correct_answer.upper()
        points_earned = (
            (10 if level == "beginner" else 15 if level == "medium" else 20)
            if is_correct
            else 0
        )

        submission_data = {
            "user_id": user_id,
            "question_id": question_id,
            "selected_answer": selected_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "points_earned": points_earned,
            "skill_area": "financial_literacy",
            "level": level,
            "submitted_at": datetime.utcnow(),
        }

        await db.collection("answer_submissions").add(submission_data)

        today = date.today().isoformat()
        progress_ref = db.collection("problem_solving_progress").document(
            f"{user_id}_{today}"
        )

        progress_doc = await progress_ref.get()
        if progress_doc.exists:
            progress_data = progress_doc.to_dict()
            new_attempted = progress_data.get("questions_attempted", 0) + 1
            new_correct = progress_data.get("questions_correct", 0) + (
                1 if is_correct else 0
            )
            new_points = progress_data.get("points_earned", 0) + points_earned
        else:
            new_attempted = 1
            new_correct = 1 if is_correct else 0
            new_points = points_earned

        await progress_ref.set(
            {
                "user_id": user_id,
                "date": today,
                "questions_attempted": new_attempted,
                "questions_correct": new_correct,
                "points_earned": new_points,
                "skill_area": "financial_literacy",
                "badge_earned": new_correct >= 5,
                "updated_at": datetime.utcnow(),
            }
        )

        feedback_message = (
            "Great job! You're learning important money skills!"
            if is_correct
            else "Good try! Check the explanation to learn more."
        )

        return UniformResponse.success_response(
            message="Answer submitted successfully",
            data={
                "is_correct": is_correct,
                "points_earned": points_earned,
                "total_attempted_today": new_attempted,
                "total_correct_today": new_correct,
                "feedback": feedback_message,
                "progress_towards_badge": f"{new_correct}/5 correct answers",
            },
        )

    except Exception as e:
        logger.error(f"Error submitting answer: {e}")
        raise HTTPException(
            status_code=500, detail=f"Could not submit answer: {str(e)}"
        )