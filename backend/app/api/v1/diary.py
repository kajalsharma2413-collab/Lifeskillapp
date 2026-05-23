# app/api/v1/diary.py - FIXED integration of AI analysis with diary entry creation
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import firestore
from pydantic import BaseModel

from app.api.dependencies.ai.diary_summarizer import (
    ContentFilterError,
    DiaryAnalysisWorkflow,
)
from app.api.dependencies.auth import get_current_user
from app.config.firebase import get_firebase_client
from app.models.user import User
from app.schemas.base import UniformResponse
from app.schemas.diary import DiaryAnalysisResponse, DiaryEntryRequest

router = APIRouter(prefix="/diary", tags=["diary"])


# NEW: Simplified request model for diary creation (only needs entry text)
class DiaryCreateRequest(BaseModel):
    entry_text: str
    timestamp: str | None = None


@router.post("/analyze")
async def analyze_diary_entry_ai(
    request: DiaryEntryRequest,
    current_user: User = Depends(get_current_user),
):
    """Analyze diary entry using AI - standalone endpoint"""
    try:
        workflow = DiaryAnalysisWorkflow()
        result = workflow.analyze_diary(request.diary_entry)
        return DiaryAnalysisResponse(**result)
    except ContentFilterError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/entry", response_model=UniformResponse[dict])
async def create_diary_entry(
    request: DiaryCreateRequest,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Create diary entry with automatic AI analysis integration"""
    try:
        # STEP 1: Analyze the diary entry using AI
        workflow = DiaryAnalysisWorkflow()
        analysis_result = workflow.analyze_diary(request.entry_text)

        # Extract AI analysis results
        ai_summary = analysis_result["summary"]
        ai_wellbeing_score = analysis_result["score"]

        # STEP 2: Convert AI score to mood categories and emoji
        mood_data = _convert_ai_score_to_mood(ai_wellbeing_score)

        # STEP 3: Prepare timestamp
        if request.timestamp:
            try:
                entry_timestamp = datetime.fromisoformat(
                    request.timestamp.replace("Z", "+00:00")
                )
            except Exception:
                entry_timestamp = datetime.utcnow()
        else:
            entry_timestamp = datetime.utcnow()

        entry_date = entry_timestamp.date().isoformat()

        # STEP 4: Save diary entry with AI-analyzed data
        diary_entry_data = {
            "user_id": current_user.id,
            "entry_text": request.entry_text,
            "mood": mood_data["mood"],
            "emoji": mood_data["emoji"],
            "ai_response": ai_summary,  # Store AI summary as response
            "mood_score": ai_wellbeing_score,  # Store original AI score (1-10)
            "date": entry_date,
            "timestamp": entry_timestamp,
        }

        # Save to Firebase
        diary_ref = await db.collection("diary_entries").add(diary_entry_data)

        return UniformResponse.success_response(
            message="Diary entry created and analyzed successfully",
            data={
                "entry_id": diary_ref[1].id,
                "date": entry_date,
                "mood": mood_data["mood"],
                "emoji": mood_data["emoji"],
                "ai_summary": ai_summary,
                "wellbeing_score": ai_wellbeing_score,
                "mood_category": mood_data["category"],
            },
        )

    except ContentFilterError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create diary entry: {str(e)}"
        )


@router.get("/entries", response_model=UniformResponse[dict])
async def get_user_diary_entries(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
    limit: int = 7,
):
    """Get user's recent diary entries"""
    try:
        # Query using authenticated user ID
        diary_ref = db.collection("diary_entries").where(
            "user_id", "==", current_user.id
        )
        diary_docs = await diary_ref.get()

        # Convert to list and sort in Python
        entries_data = []
        for doc in diary_docs:
            data = doc.to_dict()
            data["id"] = doc.id
            entries_data.append(data)

        # Sort by timestamp in descending order (most recent first)
        entries_data.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)

        # Limit to requested number
        entries_data = entries_data[:limit]

        # Format response with AI analysis data
        entries = []
        for data in entries_data:
            entries.append(
                {
                    "id": data["id"],
                    "text": data.get("entry_text", ""),
                    "mood": data.get("mood_score", 5),  # Use AI score (1-10)
                    "mood_category": data.get("mood", "Content"),  # Mood category
                    "date": data.get("date", ""),
                    "emoji": data.get("emoji", "😊"),
                    "ai_summary": data.get("ai_response", ""),
                    "wellbeing_score": data.get("mood_score", 5),
                }
            )

        return UniformResponse.success_response(
            message="Diary entries retrieved successfully", data={"entries": entries}
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve diary entries: {str(e)}"
        )


@router.get("/mood-trend", response_model=UniformResponse[dict])
async def get_mood_trend(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
    days: int = 7,
):
    """Get user's mood trend over the specified number of days"""
    try:
        # Query using authenticated user ID
        diary_ref = db.collection("diary_entries").where(
            "user_id", "==", current_user.id
        )
        diary_docs = await diary_ref.get()

        # Convert to list and sort in Python
        all_entries = []
        for doc in diary_docs:
            data = doc.to_dict()
            all_entries.append(data)

        # Sort by timestamp in descending order (most recent first)
        all_entries.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)

        # Limit to requested number of days
        mood_data = []
        for data in all_entries[:days]:
            mood_data.append(
                {
                    "date": data.get("date", ""),
                    "mood_score": data.get(
                        "mood_score", 5
                    ),  # AI wellbeing score (1-10)
                    "mood_category": data.get("mood", "Content"),
                    "emoji": data.get("emoji", "😊"),
                    "has_ai_analysis": bool(data.get("ai_response")),
                }
            )

        # Calculate average mood using AI scores
        if mood_data:
            avg_mood = sum(entry["mood_score"] for entry in mood_data) / len(mood_data)
        else:
            avg_mood = 5.0

        return UniformResponse.success_response(
            message="Mood trend retrieved successfully",
            data={
                "mood_data": mood_data,
                "average_wellbeing": round(avg_mood, 1),
                "total_entries": len(mood_data),
                "trend_analysis": _analyze_mood_trend(mood_data),
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve mood trend: {str(e)}"
        )


def _convert_ai_score_to_mood(wellbeing_score: int) -> dict:
    """Convert AI wellbeing score (1-10) to mood category and emoji"""
    if wellbeing_score <= 2:
        return {"mood": "Very Difficult", "emoji": "😢", "category": "struggling"}
    elif wellbeing_score <= 4:
        return {"mood": "Challenging", "emoji": "😟", "category": "difficult"}
    elif wellbeing_score <= 6:
        return {"mood": "Mixed", "emoji": "😐", "category": "neutral"}
    elif wellbeing_score <= 8:
        return {"mood": "Positive", "emoji": "😊", "category": "good"}
    else:  # 9-10
        return {"mood": "Excellent", "emoji": "😄", "category": "great"}


def _analyze_mood_trend(mood_data: list) -> dict:
    """Analyze mood trend over time"""
    if len(mood_data) < 2:
        return {"trend": "insufficient_data", "direction": "stable"}

    # Get last 3 days vs previous days for trend
    recent_avg = sum(entry["mood_score"] for entry in mood_data[:3]) / min(
        3, len(mood_data)
    )
    if len(mood_data) > 3:
        older_avg = sum(entry["mood_score"] for entry in mood_data[3:]) / len(
            mood_data[3:]
        )

        diff = recent_avg - older_avg
        if diff > 1:
            direction = "improving"
        elif diff < -1:
            direction = "declining"
        else:
            direction = "stable"
    else:
        direction = "stable"

    return {
        "trend": "analyzed",
        "direction": direction,
        "recent_average": round(recent_avg, 1),
        "overall_average": round(
            sum(entry["mood_score"] for entry in mood_data) / len(mood_data), 1
        ),
    }
