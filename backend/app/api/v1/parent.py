# app/api/v1/parent.py
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import firestore

from app.api.dependencies.auth import get_current_user
from app.config.firebase import get_firebase_client
from app.models.base import UserRole
from app.models.user import User
from app.schemas.base import UniformResponse
from app.schemas.skill import (
    ChildDiaryResponse,
    ChildResponse,
    DiaryEntryResponse,
    ParentChildrenResponse,
    SkillResponse,
    SkillsUsageResponse,
)

router = APIRouter(prefix="/parent", tags=["parent"])


@router.get("/children", response_model=UniformResponse[ParentChildrenResponse])
async def get_parent_children(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get all children linked to a parent"""
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=403, detail="Only parents can access this endpoint"
        )

    if not current_user.children_ids:
        return UniformResponse.success_response(
            message="No children found",
            data=ParentChildrenResponse(success=True, children=[]),
        )

    children = []
    for child_id in current_user.children_ids:
        try:
            child_ref = db.collection("users").document(child_id)
            child_doc = await child_ref.get()

            if child_doc.exists:
                child_data = child_doc.to_dict()
                children.append(
                    ChildResponse(
                        id=child_id,
                        first_name=child_data.get("first_name", ""),
                        username=child_data.get("username", ""),
                        age=child_data.get("age", 0),
                    )
                )
        except Exception:
            continue  # Skip invalid child records

    return UniformResponse.success_response(
        message="Children retrieved successfully",
        data=ParentChildrenResponse(success=True, children=children),
    )


@router.get(
    "/child/{child_id}/diary", response_model=UniformResponse[ChildDiaryResponse]
)
async def get_child_diary_entries(
    child_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get child's diary entries for the last 7 days"""
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=403, detail="Only parents can access this endpoint"
        )
    if not current_user.children_ids or child_id not in current_user.children_ids:
        raise HTTPException(
            status_code=404, detail="Child not found or not linked to parent"
        )

    try:
        # Get all diary entries for the child (without ordering in query)
        diary_ref = db.collection("diary_entries").where("user_id", "==", child_id)
        diary_docs = await diary_ref.get()

        # Convert to list and sort in Python
        entries_data = []
        for doc in diary_docs:
            data = doc.to_dict()
            data["id"] = doc.id
            entries_data.append(data)

        # Sort by timestamp in descending order (most recent first)
        entries_data.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)

        # Limit to 7 entries
        entries_data = entries_data[:7]

        # Format entries
        entries = []
        for data in entries_data:
            entries.append(
                DiaryEntryResponse(
                    id=data["id"],
                    text=data.get("entry_text", ""),
                    mood=data.get("mood_score", 3),
                    date=data.get("date", ""),
                )
            )

        return UniformResponse.success_response(
            message="Diary entries retrieved successfully",
            data=ChildDiaryResponse(success=True, entries=entries),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve diary entries: {str(e)}"
        )


@router.get(
    "/child/{child_id}/skills", response_model=UniformResponse[SkillsUsageResponse]
)
async def get_child_skill_usage(
    child_id: str,
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get skill usage statistics for a child"""
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=403, detail="Only parents can access this endpoint"
        )

    if not current_user.children_ids or child_id not in current_user.children_ids:
        raise HTTPException(
            status_code=404, detail="Child not found or not linked to parent"
        )

    # Get skill engagement data for the child
    engagement_ref = db.collection("skill_engagements").where("user_id", "==", child_id)
    engagement_docs = await engagement_ref.get()

    # Count usage by skill type
    skill_usage = {
        "Safety Skills": 0,
        "Financial Literacy": 0,
        "Communication Skills": 0,
        "Problem Solving": 0,
        "Basic Manners": 0,
    }

    for doc in engagement_docs:
        data = doc.to_dict()
        skill_type = data.get("skill_type", "")

        if skill_type == "safety":
            skill_usage["Safety Skills"] += 1
        elif skill_type == "finance":
            skill_usage["Financial Literacy"] += 1
        elif skill_type == "communication":
            skill_usage["Communication Skills"] += 1
        elif skill_type == "problem_solving":
            skill_usage["Problem Solving"] += 1
        elif skill_type == "basic_manners":
            skill_usage["Basic Manners"] += 1

    skills = [
        SkillResponse(title=title, usage=usage) for title, usage in skill_usage.items()
    ]

    return UniformResponse.success_response(
        message="Skill usage retrieved successfully",
        data=SkillsUsageResponse(success=True, skills=skills),
    )


@router.post("/generate-code", response_model=UniformResponse[dict])
async def generate_parent_code(
    current_user: User = Depends(get_current_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Generate a unique code for parents to link children"""
    if current_user.role != UserRole.PARENT:
        raise HTTPException(status_code=403, detail="Only parents can generate codes")

    import random
    import string

    # Generate a 6-character alphanumeric code
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    # Store the code in Firebase with expiration (24 hours)
    from datetime import datetime, timedelta

    parent_code_data = {
        "parent_id": current_user.id,
        "code": code,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24),
        "used": False,
    }

    await db.collection("parent_codes").document(code).set(parent_code_data)

    return UniformResponse.success_response(
        message="Parent code generated successfully",
        data={"code": code, "expires_in_hours": 24},
    )
