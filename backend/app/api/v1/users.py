# app/api/v1/users.py - Simplified meta responses
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from firebase_admin import firestore

from app.api.dependencies.auth import (
    get_current_active_user,
    get_parent_user,
)
from app.config.firebase import get_firebase_client
from app.config.logging import log
from app.models.base import UserRole
from app.models.user import User
from app.schemas.auth import AccountDeletionRequest, ChildAccountDeletionRequest
from app.schemas.base import PaginatedResponse, UniformResponse
from app.schemas.skill import BadgeResponse
from app.schemas.user import (
    BadgeDetailResponse,
    CompletedSkillResponse,  # NEW SCHEMA
    LeaderboardEntryResponse,
    LeaderboardResponse,
    ProgressStatsResponse,
    RecentAchievementResponse,
    ScoringTableResponse,
    SkillBreakdownResponse,
    UserResponse,
    UserSummaryResponse,
    UserUpdate,
)
from app.services.auth import AuthService
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])
user_service = UserService()
auth_service = AuthService()


@router.get("/me", response_model=UniformResponse[dict])
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),  # ADD THIS
):
    """Get current user's information for dashboard"""
    log.info(f"User info request by user: {current_user.id}")
    try:
        # 🔥 FIX: Query actual badges count
        user_badges_ref = db.collection("user_badges").where(
            "user_id", "==", current_user.id
        )
        user_badges_docs = await user_badges_ref.get()
        actual_badges_count = len(user_badges_docs)

        user_data = {
            "id": current_user.id,
            "name": f"{current_user.first_name} {current_user.last_name or ''}".strip(),
            "role": current_user.role,
            "email": current_user.email,
            "grade": current_user.grade_level,
            "age": current_user.age,
            "username": current_user.username,
            "points": current_user.points,
            "badges_count": actual_badges_count,  # 🔥 FIXED
            "avatar_url": current_user.avatar_url,
        }
        return UniformResponse.success_response(
            message="User information retrieved successfully",
            data={"user": user_data},
        )
    except Exception as e:
        log.error(f"User info retrieval failed for user {current_user.id}: {str(e)}")
        return UniformResponse.error_response(
            message="Failed to retrieve user information", errors=[str(e)]
        )


@router.get("/badges", response_model=UniformResponse[dict])
async def get_user_badges(
    current_user: User = Depends(get_current_active_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get user's earned badges"""
    log.info(f"User badges request by user: {current_user.id}")
    try:
        badges = []

        # 🔥 SIMPLE FIX: Query user_badges collection instead of current_user.badges
        user_badges_ref = db.collection("user_badges").where(
            "user_id", "==", current_user.id
        )
        user_badges_docs = await user_badges_ref.get()

        # Get badge details from Firebase
        for user_badge_doc in user_badges_docs:
            user_badge_data = user_badge_doc.to_dict()
            badge_id = user_badge_data.get("badge_id")

            if badge_id:
                try:
                    badge_ref = db.collection("badges").document(badge_id)
                    badge_doc = await badge_ref.get()
                    if badge_doc.exists:
                        badge_data = badge_doc.to_dict()
                        badges.append(
                            BadgeResponse(
                                id=badge_id,
                                name=badge_data.get("name", "Unknown Badge"),
                                image=badge_data.get(
                                    "image_url",
                                    "https://cdn-icons-png.flaticon.com/128/16846/16846979.png",
                                ),
                                description=badge_data.get("description", ""),
                                skill_type=badge_data.get("skill_type"),
                                points=badge_data.get("points", 5),
                            )
                        )
                except Exception:
                    continue  # Skip invalid badge records

        return UniformResponse.success_response(
            message="User badges retrieved successfully",
            data={"badges": badges},
        )

    except Exception as e:
        log.error(f"User badges retrieval failed for user {current_user.id}: {str(e)}")
        return UniformResponse.error_response(
            message="Failed to retrieve user badges", errors=[str(e)]
        )


@router.get("/profile/{user_id}", response_model=UniformResponse[dict])
async def get_user_profile(
    user_id: str, current_user: User = Depends(get_current_active_user)
):
    """Get user profile by ID"""
    log.info(f"Profile access request for user {user_id} by {current_user.id}")

    try:
        user = await user_service.get_user_profile(
            user_id, current_user.id, current_user.role
        )
        user_data = UserResponse.model_validate(user.model_dump()).model_dump()

        return UniformResponse.success_response(
            message="User profile retrieved successfully",
            data={"user": user_data},
        )

    except Exception as e:
        log.error(f"Profile access failed for user {user_id}: {str(e)}")
        return UniformResponse.error_response(
            message="Failed to retrieve user profile", errors=[str(e)]
        )


@router.put("/profile/{user_id}", response_model=UniformResponse[dict])
async def update_user_profile(
    user_id: str,
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
):
    """Update user profile"""
    log.info(f"Profile update request for user {user_id} by {current_user.id}")

    # Prevent admin profile updates
    if user_id == current_user.id and current_user.role == UserRole.ADMIN:
        log.warning(f"Admin user attempted to update own profile: {current_user.id}")
        return UniformResponse.error_response(
            message="Admin profiles cannot be updated",
            errors=["Admin accounts have fixed profiles that cannot be modified"],
            meta={"error_type": "admin_restriction"},
        )

    # Check if target user is admin
    try:
        target_user = await user_service.get_user_by_id(user_id)
        if target_user.role == UserRole.ADMIN:
            log.warning(f"Attempted to update admin profile: {user_id}")
            return UniformResponse.error_response(
                message="Admin profiles cannot be updated",
                errors=["Admin accounts have fixed profiles that cannot be modified"],
                meta={"error_type": "admin_restriction"},
            )
    except Exception as e:
        log.error(f"Failed to check target user role: {str(e)}")
        return UniformResponse.error_response(
            message="Failed to verify user permissions", errors=[str(e)]
        )

    try:
        user = await user_service.update_user_profile(
            user_id, update_data, current_user.id, current_user.role
        )
        user_data = UserResponse.model_validate(user.model_dump()).model_dump()

        return UniformResponse.success_response(
            message="Profile updated successfully",
            data={"user": user_data},
        )

    except Exception as e:
        log.error(f"Profile update failed for user {user_id}: {str(e)}")
        return UniformResponse.error_response(
            message="Failed to update profile", errors=[str(e)]
        )


@router.delete("/delete-child-account", response_model=UniformResponse[dict])
async def delete_child_account(
    deletion_request: ChildAccountDeletionRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Delete child account - requires parent code validation"""
    log.info(f"Child account deletion request by user: {current_user.id}")

    # Ensure only child users can use this endpoint
    if current_user.role != UserRole.USER:
        log.warning(
            f"Non-child user attempted child account deletion: {current_user.id}"
        )
        return UniformResponse.error_response(
            message="This endpoint is only for child users",
            errors=["Only children can delete accounts using this method"],
            meta={"error_type": "role_restriction"},
        )

    try:
        success = await auth_service.delete_child_account(
            current_user.id, deletion_request, current_user.id
        )

        if success:
            log.success(f"Child account deleted successfully: {current_user.id}")
            return UniformResponse.success_response(
                message="Child account deleted successfully",
                data={"deleted_user_id": current_user.id},
            )
        else:
            return UniformResponse.error_response(
                message="Failed to delete child account",
                errors=["Account deletion was not completed"],
            )

    except Exception as e:
        log.error(f"Child account deletion failed for user {current_user.id}: {str(e)}")
        return UniformResponse.error_response(
            message="Failed to delete child account", errors=[str(e)]
        )


@router.delete("/delete-parent-account", response_model=UniformResponse[dict])
async def delete_parent_account(
    deletion_request: AccountDeletionRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Delete parent account - only if no children are linked"""
    log.info(f"Parent account deletion request by user: {current_user.id}")

    # Ensure only parent users can use this endpoint
    if current_user.role != UserRole.PARENT:
        log.warning(
            f"Non-parent user attempted parent account deletion: {current_user.id}"
        )
        return UniformResponse.error_response(
            message="This endpoint is only for parent users",
            errors=["Only parents can delete accounts using this method"],
            meta={"error_type": "role_restriction"},
        )

    try:
        success = await auth_service.delete_parent_account(
            current_user.id, deletion_request, current_user.id
        )

        if success:
            log.success(f"Parent account deleted successfully: {current_user.id}")
            return UniformResponse.success_response(
                message="Parent account deleted successfully",
                data={"deleted_user_id": current_user.id},
            )
        else:
            return UniformResponse.error_response(
                message="Failed to delete parent account",
                errors=["Account deletion was not completed"],
            )

    except Exception as e:
        log.error(
            f"Parent account deletion failed for user {current_user.id}: {str(e)}"
        )
        return UniformResponse.error_response(
            message="Failed to delete parent account", errors=[str(e)]
        )


@router.get("/children", response_model=PaginatedResponse[UserResponse])
async def get_user_children(
    current_user: User = Depends(get_parent_user),
    include_inactive: bool = Query(False, description="Include inactive children"),
):
    """Get all children for the current parent"""
    log.info(f"Children list request by parent: {current_user.id}")

    try:
        children = await user_service.get_user_children(current_user.id)

        # Filter inactive children if requested
        if not include_inactive:
            children = [child for child in children if child.is_active]

        children_data = [
            UserResponse.model_validate(child.model_dump()) for child in children
        ]

        return PaginatedResponse.success_response(
            data=children_data,
            total_count=len(children_data),
            page=1,
            page_size=len(children_data),
            message=f"Retrieved {len(children_data)} children successfully",
        )

    except Exception as e:
        log.error(f"Failed to get children for parent {current_user.id}: {str(e)}")
        return PaginatedResponse.error_response(
            message="Failed to retrieve children", errors=[str(e)]
        )


@router.get("/parent", response_model=UniformResponse[dict])
async def get_my_parent(current_user: User = Depends(get_current_active_user)):
    """Get parent information for the current child user"""
    log.info(f"Parent info request by child: {current_user.id}")

    # Check if user is a child
    if current_user.role != UserRole.USER:
        log.warning(f"Non-child user attempted parent access: {current_user.id}")
        return UniformResponse.error_response(
            message="This endpoint is only available for child users",
            errors=["Only children can access parent information"],
        )

    # Check if child has a parent_id
    if not current_user.parent_id:
        log.warning(f"Child user has no parent linked: {current_user.id}")
        return UniformResponse.error_response(
            message="No parent found",
            errors=["This child account is not linked to a parent"],
        )

    try:
        parent = await user_service.get_user_by_id(current_user.parent_id)
        parent_data = UserResponse.model_validate(parent.model_dump()).model_dump()

        # Remove sensitive parent information for child safety
        safe_parent_data = {
            "id": parent_data["id"],
            "first_name": parent_data["first_name"],
            "last_name": parent_data["last_name"],
            "email": parent_data["email"],
            "username": parent_data["username"],
            "role": parent_data["role"],
            "is_active": parent_data["is_active"],
        }

        return UniformResponse.success_response(
            message="Parent information retrieved successfully",
            data={
                "parent": safe_parent_data,
                "emergency_contact": {
                    "name": f"{parent.first_name} {parent.last_name or ''}".strip(),
                    "email": parent.email,
                    "relationship": "Parent/Guardian",
                },
            },
        )

    except Exception as e:
        log.error(f"Parent info retrieval failed for child {current_user.id}: {str(e)}")
        return UniformResponse.error_response(
            message="Failed to retrieve parent information", errors=[str(e)]
        )


# MINIMAL FIX: Update the get_my_stats function in app/api/v1/users.py


@router.get("/my-stats", response_model=UniformResponse[dict])
async def get_my_stats(
    current_user: User = Depends(get_current_active_user),
    db: firestore.AsyncClient = Depends(
        get_firebase_client
    ),  # 🔥 ADD: Firebase dependency
):
    """Get current user's own statistics and progress"""
    log.info(f"My stats request by user: {current_user.id}")
    try:
        # 🔥 FIX: Query user_badges collection to get actual badge count
        user_badges_ref = db.collection("user_badges").where(
            "user_id", "==", current_user.id
        )
        user_badges_docs = await user_badges_ref.get()
        actual_badges_count = len(user_badges_docs)

        stats = {
            "points": current_user.points,
            "badges_count": actual_badges_count,  # 🔥 FIXED: Use actual count from collection
            "current_skills_count": len(current_user.current_skills or []),
            "completed_skills_count": len(current_user.completed_skills or []),
            "profile_completion": _calculate_profile_completeness(current_user),
            "account_age_days": _calculate_account_age(current_user),
            "last_activity": (
                current_user.last_activity.isoformat()
                if current_user.last_activity
                else None
            ),
        }
        return UniformResponse.success_response(
            message="Your statistics retrieved successfully",
            data={"stats": stats},
        )
    except Exception as e:
        log.error(f"My stats retrieval failed for user {current_user.id}: {str(e)}")
        return UniformResponse.error_response(
            message="Failed to retrieve your statistics", errors=[str(e)]
        )


@router.get("/stats/{user_id}", response_model=UniformResponse[dict])
async def get_user_stats(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: firestore.AsyncClient = Depends(
        get_firebase_client
    ),  # 🔥 ADD: Firebase dependency
):
    """Get user statistics and progress"""
    log.info(f"Stats request for user {user_id} by {current_user.id}")

    try:
        user = await user_service.get_user_profile(
            user_id, current_user.id, current_user.role
        )
        user_badges_ref = db.collection("user_badges").where(
            "user_id", "==", current_user.id
        )
        user_badges_docs = await user_badges_ref.get()
        actual_badges_count = len(user_badges_docs)

        stats = {
            "points": user.points,
            "badges_count": actual_badges_count,
            "current_skills_count": len(user.current_skills or []),
            "completed_skills_count": len(user.completed_skills or []),
            "profile_completion": _calculate_profile_completeness(user),
            "account_age_days": _calculate_account_age(user),
            "last_activity": (
                user.last_activity.isoformat() if user.last_activity else None
            ),
        }

        return UniformResponse.success_response(
            message="User statistics retrieved successfully",
            data={"stats": stats},
        )

    except Exception as e:
        log.error(f"Stats retrieval failed for user {user_id}: {str(e)}")
        return UniformResponse.error_response(
            message="Failed to retrieve user statistics", errors=[str(e)]
        )


def _calculate_profile_completeness(user: User) -> float:
    """Calculate profile completion percentage"""
    total_fields = 9
    completed_fields = 0

    if user.first_name:
        completed_fields += 1
    if user.last_name:
        completed_fields += 1
    if user.username:
        completed_fields += 1
    if user.email:
        completed_fields += 1
    if user.age:
        completed_fields += 1
    if user.grade_level:
        completed_fields += 1
    if user.avatar_url:
        completed_fields += 1
    if user.preferences:
        completed_fields += 1
    if user.current_skills:
        completed_fields += 1

    return round((completed_fields / total_fields) * 100, 1)


def _calculate_account_age(user: User) -> int:
    """Calculate account age in days"""
    if user.created_at:
        from datetime import datetime, timezone

        return (datetime.now(timezone.utc) - user.created_at).days
    return 0


@router.get("/leaderboard", response_model=UniformResponse[LeaderboardResponse])
async def get_leaderboard(
    current_user: User = Depends(get_current_active_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
    limit: int = Query(
        default=10, ge=5, le=50, description="Number of top users to show"
    ),
):
    """Get leaderboard with user scores and badge information"""
    log.info(f"Leaderboard request by user: {current_user.id}")
    try:
        # Get all child users
        users_ref = db.collection("users").where("role", "==", "user")
        users_docs = await users_ref.get()
        leaderboard_data = []

        for doc in users_docs:
            user_data = doc.to_dict()
            user_id = doc.id

            # 🔥 FIX: Query user_badges collection for each user
            user_badges_ref = db.collection("user_badges").where(
                "user_id", "==", user_id
            )
            user_badges_docs = await user_badges_ref.get()

            # Calculate badge points from actual earned badges
            badge_points = 0
            for user_badge_doc in user_badges_docs:
                user_badge_data = user_badge_doc.to_dict()
                badge_id = user_badge_data.get("badge_id")
                if badge_id:
                    try:
                        badge_ref = db.collection("badges").document(badge_id)
                        badge_doc = await badge_ref.get()
                        if badge_doc.exists:
                            badge_data = badge_doc.to_dict()
                            badge_points += badge_data.get("points", 5)
                    except Exception:
                        continue

            # Get latest badge earned (for badge URL display) - this part is already correct
            latest_badge_ref = (
                db.collection("user_badges")
                .where("user_id", "==", user_id)
                .order_by("earned_at", direction=firestore.Query.DESCENDING)
                .limit(1)
            )
            latest_badge_docs = await latest_badge_ref.get()
            latest_badge_url = None
            latest_badge_name = None
            if latest_badge_docs:
                latest_badge_data = latest_badge_docs[0].to_dict()
                badge_id = latest_badge_data.get("badge_id")
                if badge_id:
                    badge_ref = db.collection("badges").document(badge_id)
                    badge_doc = await badge_ref.get()
                    if badge_doc.exists:
                        badge_data = badge_doc.to_dict()
                        latest_badge_url = badge_data.get("image_url")
                        latest_badge_name = badge_data.get("name")

            leaderboard_data.append(
                {
                    "user_id": user_id,
                    "name": f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip(),
                    "username": user_data.get("username", ""),
                    "total_points": user_data.get("points", 0),
                    "badges_count": len(user_badges_docs),  # 🔥 FIXED: Use actual count
                    "badge_points": badge_points,
                    "activity_points": user_data.get("points", 0) - badge_points,
                    "latest_badge_url": latest_badge_url,
                    "latest_badge_name": latest_badge_name,
                    "age": user_data.get("age"),
                    "grade": user_data.get("grade_level"),
                    "is_current_user": user_id == current_user.id,
                }
            )

        # Sort by total points
        leaderboard_data.sort(key=lambda x: x["total_points"], reverse=True)

        # Add rankings
        for i, entry in enumerate(leaderboard_data):
            entry["rank"] = i + 1

        # Limit results
        top_leaderboard = leaderboard_data[:limit]

        # Find current user's position if not in top
        current_user_entry = None
        if not any(entry["is_current_user"] for entry in top_leaderboard):
            for entry in leaderboard_data:
                if entry["is_current_user"]:
                    current_user_entry = entry
                    break

        # Convert to proper schema objects
        leaderboard_entries = [
            LeaderboardEntryResponse(**entry) for entry in top_leaderboard
        ]
        current_user_entry_obj = (
            LeaderboardEntryResponse(**current_user_entry)
            if current_user_entry
            else None
        )

        leaderboard_response = LeaderboardResponse(
            leaderboard=leaderboard_entries,
            current_user_entry=current_user_entry_obj,
            total_players=len(leaderboard_data),
            user_rank=current_user_entry["rank"] if current_user_entry else None,
        )

        return UniformResponse.success_response(
            message="Leaderboard retrieved successfully", data=leaderboard_response
        )

    except Exception as e:
        log.error(f"Leaderboard retrieval failed: {str(e)}")
        return UniformResponse.error_response(
            message="Failed to retrieve leaderboard", errors=[str(e)]
        )

    # Add this to app/api/v1/users.py (after existing badge endpoint)


@router.get("/badge/{badge_id}", response_model=UniformResponse[dict])
async def get_badge_public(
    badge_id: str,
    current_user: User = Depends(get_current_active_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get badge by ID - accessible to all authenticated users for frontend display"""
    log.info(f"Public badge request for badge {badge_id} by user: {current_user.id}")
    try:
        badge_ref = db.collection("badges").document(badge_id)
        badge_doc = await badge_ref.get()

        if not badge_doc.exists:
            return UniformResponse.error_response(
                message="Badge not found",
                errors=[f"Badge with ID {badge_id} does not exist"],
            )

        badge_data = badge_doc.to_dict()

        # Return badge data in format frontend expects
        badge_info = {
            "id": badge_id,
            "name": badge_data.get("name", "Unknown Badge"),
            "image_url": badge_data.get("image_url", ""),
            "badge_url": badge_data.get("image_url", ""),  # Alias for compatibility
            "description": badge_data.get("description", ""),
            "skill_type": badge_data.get("skill_type", ""),
            "points": badge_data.get("points", 5),
        }

        return UniformResponse.success_response(
            message="Badge retrieved successfully", data={"badge": badge_info}
        )

    except Exception as e:
        log.error(f"Public badge retrieval failed for badge {badge_id}: {str(e)}")
        return UniformResponse.error_response(
            message="Failed to retrieve badge", errors=[str(e)]
        )


# ==================== FIXED SCORING TABLE ENDPOINT ====================


@router.get("/scoring-table", response_model=UniformResponse[ScoringTableResponse])
async def get_user_scoring_table(
    current_user: User = Depends(get_current_active_user),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get comprehensive user scoring information including badges, points, and achievements"""
    log.info(f"User scoring table request by user: {current_user.id}")
    try:
        # 🔥 FIX: Get ALL user badge completion data in one query
        user_badges_ref = db.collection("user_badges").where(
            "user_id", "==", current_user.id
        )
        user_badges_docs = await user_badges_ref.get()

        # Create lookup map for badge completion data
        badge_completion_map = {}
        badges_details = []
        total_badge_points = 0

        for doc in user_badges_docs:
            data = doc.to_dict()
            badge_id = data.get("badge_id")
            if badge_id:
                badge_completion_map[badge_id] = {
                    "earned_at": data.get("earned_at"),
                    "score": data.get("score") or data.get("score_percentage"),
                    "quiz_id": data.get("quiz_id"),
                    "doc_id": doc.id,
                }

                # 🔥 FIX: Get badge details from each badge_id in collection
                try:
                    badge_ref = db.collection("badges").document(badge_id)
                    badge_doc = await badge_ref.get()
                    if badge_doc.exists:
                        badge_data = badge_doc.to_dict()
                        badge_points = badge_data.get("points", 5)
                        total_badge_points += badge_points

                        completion_data = badge_completion_map.get(badge_id, {})
                        earned_at = completion_data.get("earned_at")
                        quiz_score = completion_data.get("score")

                        badges_details.append(
                            {
                                "badge_id": badge_id,
                                "name": badge_data.get("name", "Unknown Badge"),
                                "description": badge_data.get("description", ""),
                                "image_url": badge_data.get(
                                    "image_url",
                                    "https://cdn-icons-png.flaticon.com/128/16846/16846979.png",
                                ),
                                "skill_type": badge_data.get("skill_type"),
                                "points": badge_points,
                                "earned_at": earned_at.isoformat()
                                if earned_at
                                else None,
                                "quiz_score": quiz_score,
                            }
                        )
                except Exception:
                    continue

        # ==================== NEW: GET COMPLETED SKILLS DETAILS ====================
        completed_skills_details = []
        if current_user.completed_skills:
            for skill_id in current_user.completed_skills:
                try:
                    # Get skill metadata from skills collection
                    skill_ref = db.collection("skills").document(skill_id)
                    skill_doc = await skill_ref.get()

                    if skill_doc.exists:
                        skill_data = skill_doc.to_dict()

                        # Try to find completion timestamp from various sources
                        completion_timestamp = None

                        # Option 1: Check if there's a badge for this skill
                        skill_type = skill_data.get("type") or skill_data.get(
                            "skill_type"
                        )
                        for badge in badges_details:
                            if badge.get("skill_type") == skill_type and badge.get(
                                "earned_at"
                            ):
                                completion_timestamp = badge.get("earned_at")
                                break

                        # Option 2: Check quiz attempts for this skill
                        if not completion_timestamp:
                            quiz_attempts_ref = (
                                db.collection("quiz_attempts")
                                .where("user_id", "==", current_user.id)
                                .where("skill_type", "==", skill_type)
                                .where("passed", "==", True)
                                .order_by(
                                    "completed_at", direction=firestore.Query.DESCENDING
                                )
                                .limit(1)
                            )
                            quiz_attempts_docs = await quiz_attempts_ref.get()
                            if quiz_attempts_docs:
                                latest_attempt = quiz_attempts_docs[0].to_dict()
                                completed_at = latest_attempt.get("completed_at")
                                if completed_at:
                                    completion_timestamp = completed_at.isoformat()

                        completed_skills_details.append(
                            {
                                "skill_id": skill_id,
                                "name": skill_data.get("name", "Unknown Skill"),
                                "description": skill_data.get("description", ""),
                                "skill_type": skill_type,
                                "completed_at": completion_timestamp,
                            }
                        )
                except Exception as e:
                    log.warning(
                        f"Failed to process completed skill {skill_id}: {str(e)}"
                    )
                    continue

        # Get skill-wise scoring breakdown
        skill_scores = {
            "safety": {"points": 0, "badges": 0, "activities": 0},
            "finance": {"points": 0, "badges": 0, "activities": 0},
            "communication": {"points": 0, "badges": 0, "activities": 0},
            "problem_solving": {"points": 0, "badges": 0, "activities": 0},
            "basic_manners": {"points": 0, "badges": 0, "activities": 0},
        }

        # Calculate skill-wise breakdown from badges
        for badge in badges_details:
            skill_type = badge.get("skill_type")
            if skill_type and skill_type in skill_scores:
                skill_scores[skill_type]["badges"] += 1
                skill_scores[skill_type]["points"] += badge.get("points", 5)

        # Get activity counts from engagements
        engagement_ref = db.collection("skill_engagements").where(
            "user_id", "==", current_user.id
        )
        engagement_docs = await engagement_ref.get()
        for doc in engagement_docs:
            data = doc.to_dict()
            skill_type = data.get("skill_type", "")
            if skill_type in skill_scores:
                skill_scores[skill_type]["activities"] += 1

        # Get recent achievements (optimized)
        recent_achievements = []
        if user_badges_docs:  # Reuse the badges we already fetched
            # Sort by earned_at descending and take first 10
            user_badges_list = []
            for doc in user_badges_docs:
                data = doc.to_dict()
                earned_at = data.get("earned_at")
                if earned_at:  # Only include badges with earned_at timestamp
                    user_badges_list.append(data)

            user_badges_list.sort(
                key=lambda x: x.get("earned_at", datetime.min), reverse=True
            )
            recent_badges_limited = user_badges_list[:10]

            for data in recent_badges_limited:
                badge_id = data.get("badge_id")
                # Get badge details
                badge_ref = db.collection("badges").document(badge_id)
                badge_doc = await badge_ref.get()
                if badge_doc.exists:
                    badge_data = badge_doc.to_dict()
                    recent_achievements.append(
                        {
                            "badge_id": badge_id,
                            "name": badge_data.get("name", "Unknown Badge"),
                            "image_url": badge_data.get("image_url", ""),
                            "skill_type": badge_data.get("skill_type"),
                            "earned_at": data.get("earned_at").isoformat()
                            if data.get("earned_at")
                            else None,
                            # Handle both score field variations
                            "score": data.get("score") or data.get("score_percentage"),
                            "points": badge_data.get("points", 5),
                        }
                    )

        # Calculate ranking/percentile
        all_users_ref = db.collection("users").where("role", "==", "user")
        all_users_docs = await all_users_ref.get()
        user_points = current_user.points
        users_with_lower_points = 0
        total_users = 0

        for doc in all_users_docs:
            user_data = doc.to_dict()
            if user_data.get("points", 0) < user_points:
                users_with_lower_points += 1
            total_users += 1

        percentile = (
            (users_with_lower_points / total_users * 100) if total_users > 0 else 0
        )

        # Build response
        scoring_data = ScoringTableResponse(
            user_summary=UserSummaryResponse(
                user_id=current_user.id,
                name=f"{current_user.first_name} {current_user.last_name or ''}".strip(),
                username=current_user.username,
                total_points=current_user.points,
                total_badges=len(user_badges_docs),
                badge_points=total_badge_points,
                activity_points=current_user.points - total_badge_points,
                percentile=round(percentile, 1),
                rank=total_users - users_with_lower_points if total_users > 0 else 1,
            ),
            badges_earned=[BadgeDetailResponse(**badge) for badge in badges_details],
            completed_skills_details=[  # NEW FIELD
                CompletedSkillResponse(**skill) for skill in completed_skills_details
            ],
            skill_breakdown={
                skill: SkillBreakdownResponse(**data)
                for skill, data in skill_scores.items()
            },
            recent_achievements=[
                RecentAchievementResponse(**achievement)
                for achievement in recent_achievements
            ],
            progress_stats=ProgressStatsResponse(
                profile_completion=_calculate_profile_completeness(current_user),
                account_age_days=_calculate_account_age(current_user),
                badges_this_month=len(
                    [
                        b
                        for b in recent_achievements
                        if b.get("earned_at")
                        and datetime.fromisoformat(
                            b["earned_at"].replace("Z", "+00:00")
                        ).month
                        == datetime.utcnow().month
                    ]
                ),
                average_quiz_score=round(
                    sum(
                        b.get("quiz_score", 0)
                        for b in badges_details
                        if b.get("quiz_score")
                    )
                    / len([b for b in badges_details if b.get("quiz_score")]),
                    1,
                )
                if any(b.get("quiz_score") for b in badges_details)
                else 0,
            ),
        )

        return UniformResponse.success_response(
            message="User scoring table retrieved successfully", data=scoring_data
        )

    except Exception as e:
        log.error(
            f"Scoring table retrieval failed for user {current_user.id}: {str(e)}"
        )
        return UniformResponse.error_response(
            message="Failed to retrieve scoring information", errors=[str(e)]
        )


# ==================== FIXED HELPER FUNCTIONS ====================


def _calculate_profile_completeness(user: User) -> float:
    """Calculate profile completion percentage - FIXED to include completed_skills"""
    total_fields = 10  # INCREASED from 9 to 10
    completed_fields = 0

    if user.first_name:
        completed_fields += 1
    if user.last_name:
        completed_fields += 1
    if user.username:
        completed_fields += 1
    if user.email:
        completed_fields += 1
    if user.age:
        completed_fields += 1
    if user.grade_level:
        completed_fields += 1
    if user.avatar_url:
        completed_fields += 1
    if user.preferences:
        completed_fields += 1
    if user.current_skills:
        completed_fields += 1
    if user.completed_skills:  # ✅ FIXED: Added this missing check
        completed_fields += 1

    return round((completed_fields / total_fields) * 100, 1)


def _calculate_account_age(user: User) -> int:
    """Calculate account age in days"""
    if user.created_at:
        from datetime import datetime, timezone

        return (datetime.now(timezone.utc) - user.created_at).days
    return 0
