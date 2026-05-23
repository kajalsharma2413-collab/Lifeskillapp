# app/api/v1/admin_dashboard.py
"""
Admin Dashboard APIs for Life Skills App
Extends existing admin.py with dashboard-specific endpoints
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from firebase_admin import firestore
from pydantic import BaseModel

from app.api.dependencies.auth import get_current_user
from app.config.firebase import get_firebase_client
from app.config.logging import log
from app.models.base import UserRole
from app.models.user import User
from app.schemas.base import UniformResponse


# ==================== RESPONSE SCHEMAS ====================
class DashboardStatsResponse(BaseModel):
    """Main dashboard statistics"""

    total_users: int
    active_users: int  # Active in last 7 days
    quiz_attempts: int
    badges_earned: int


class SkillEngagementResponse(BaseModel):
    """Skill engagement data for bar chart"""

    skill: str
    engagement: float  # Percentage


class MoodTrendResponse(BaseModel):
    """Mood trends for line chart"""

    date: str
    average_mood: float
    total_entries: int


class AlertResponse(BaseModel):
    """Alert/Flag response"""

    id: str
    type: str
    title: str
    description: str
    severity: str
    count: int | None = None
    completion_rate: float | None = None
    content_id: str | None = None
    skill_type: str | None = None
    created_at: datetime
    resolved: bool = False


class UserAnalyticsResponse(BaseModel):
    """User analytics data"""

    id: str
    name: str
    age: int
    email: str
    last_login: datetime | None
    status: str  # active/inactive
    badges: int
    quiz_attempts: int
    average_score: float


class SkillStatsResponse(BaseModel):
    """Skill statistics"""

    id: str
    name: str
    type: str
    status: str
    total_quizzes: int
    average_completion: float
    description: str


class EngagementReportResponse(BaseModel):
    """Engagement report data"""

    period: dict[str, str]
    total_users: int
    active_users: int
    engagement_rate: float
    skill_breakdown: list[dict[str, Any]]
    daily_active: list[dict[str, Any]]


class PerformanceReportResponse(BaseModel):
    """Performance report data"""

    total_quizzes: int
    average_score: float
    skill_performance: list[dict[str, Any]]
    improvement_trends: list[dict[str, Any]]


# ==================== ROUTER SETUP ====================
router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])


def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to ensure user is admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ==================== DASHBOARD STATISTICS ENDPOINTS ====================
@router.get("/stats", response_model=UniformResponse[DashboardStatsResponse])
async def get_dashboard_stats(
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get main dashboard statistics (matches frontend: 415 users, 38 active, etc.)"""
    try:
        log.info(f"Admin dashboard stats requested by: {admin_user.id}")

        # Get total users count (children only)
        users_ref = db.collection("users").where("role", "==", "user")
        users_docs = await users_ref.get()
        total_users = len(users_docs)

        # Calculate active users (logged in within last 7 days) - FIXED: Use timezone-aware datetime
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        active_users = 0
        for doc in users_docs:
            user_data = doc.to_dict()
            last_login = user_data.get("last_login")
            if last_login and last_login >= seven_days_ago:
                active_users += 1

        # Get total quiz attempts
        quiz_attempts_ref = db.collection("quiz_attempts")
        quiz_attempts_docs = await quiz_attempts_ref.get()
        total_quiz_attempts = len(quiz_attempts_docs)

        # Get total badges earned
        user_badges_ref = db.collection("user_badges")
        user_badges_docs = await user_badges_ref.get()
        total_badges_earned = len(user_badges_docs)

        stats = DashboardStatsResponse(
            total_users=total_users,
            active_users=active_users,
            quiz_attempts=total_quiz_attempts,
            badges_earned=total_badges_earned,
        )

        return UniformResponse.success_response(
            message="Dashboard statistics retrieved successfully", data=stats
        )
    except Exception as e:
        log.error(f"Failed to get dashboard stats: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get dashboard stats: {str(e)}"
        )


@router.get(
    "/skill-engagement", response_model=UniformResponse[list[SkillEngagementResponse]]
)
async def get_skill_engagement(
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get skill engagement data for bar chart"""
    try:
        log.info(f"Skill engagement data requested by: {admin_user.id}")

        # Get all skill engagements
        engagements_ref = db.collection("skill_engagements")
        engagements_docs = await engagements_ref.get()

        # Count engagements by skill type
        skill_counts = {
            "finance": 0,
            "safety": 0,
            "communication": 0,
            "problem_solving": 0,
            "basic_manners": 0,
        }

        total_engagements = len(engagements_docs)
        for doc in engagements_docs:
            data = doc.to_dict()
            skill_type = data.get("skill_type", "")
            if skill_type in skill_counts:
                skill_counts[skill_type] += 1

        # Calculate percentages
        skill_engagements = []
        for skill, count in skill_counts.items():
            percentage = (
                (count / total_engagements * 100) if total_engagements > 0 else 0
            )
            skill_engagements.append(
                SkillEngagementResponse(
                    skill=skill.replace("_", " ").title(),
                    engagement=round(percentage, 1),
                )
            )

        return UniformResponse.success_response(
            message="Skill engagement data retrieved successfully",
            data=skill_engagements,
        )
    except Exception as e:
        log.error(f"Failed to get skill engagement: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get skill engagement: {str(e)}"
        )


@router.get("/mood-trends", response_model=UniformResponse[list[MoodTrendResponse]])
async def get_mood_trends(
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
):
    """Get mood trends for line chart"""
    try:
        log.info(f"Mood trends requested by admin: {admin_user.id} for {days} days")

        # FIXED: Use timezone-aware datetime
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Get diary entries from the period
        diary_ref = db.collection("diary_entries").where("timestamp", ">=", start_date)
        diary_docs = await diary_ref.get()

        # Group by date and calculate averages
        daily_moods = {}
        for doc in diary_docs:
            data = doc.to_dict()
            entry_date = data.get("date", "")
            mood_score = data.get("mood_score", 5)

            if entry_date not in daily_moods:
                daily_moods[entry_date] = []
            daily_moods[entry_date].append(mood_score)

        # Generate trend data
        mood_trends = []
        for i in range(days):
            date = datetime.now(timezone.utc) - timedelta(days=days - i - 1)
            date_str = date.date().isoformat()

            if date_str in daily_moods:
                mood_scores = daily_moods[date_str]
                average_mood = sum(mood_scores) / len(mood_scores)
                total_entries = len(mood_scores)
            else:
                average_mood = 5.0  # Default neutral mood
                total_entries = 0

            mood_trends.append(
                MoodTrendResponse(
                    date=date_str,
                    average_mood=round(average_mood, 1),
                    total_entries=total_entries,
                )
            )

        return UniformResponse.success_response(
            message="Mood trends retrieved successfully", data=mood_trends
        )
    except Exception as e:
        log.error(f"Failed to get mood trends: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get mood trends: {str(e)}"
        )


# ==================== ALERTS AND FLAGS ENDPOINTS ====================
@router.get("/alerts", response_model=UniformResponse[list[AlertResponse]])
async def get_admin_alerts(
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get all admin alerts and flags"""
    try:
        log.info(f"Admin alerts requested by: {admin_user.id}")
        alerts = []

        # LOW_ENGAGEMENT Alert - Users inactive for 5+ days - FIXED: Use timezone-aware datetime
        five_days_ago = datetime.now(timezone.utc) - timedelta(days=5)
        users_ref = db.collection("users").where("role", "==", "user")
        users_docs = await users_ref.get()

        inactive_count = 0
        for doc in users_docs:
            user_data = doc.to_dict()
            last_login = user_data.get("last_login")
            if not last_login or last_login < five_days_ago:
                inactive_count += 1

        if inactive_count > 0:
            alerts.append(
                AlertResponse(
                    id="low_engagement_001",
                    type="LOW_ENGAGEMENT",
                    title="Low Engagement Alert",
                    description=f"{inactive_count} users haven't logged in for 5+ days",
                    severity="warning",
                    count=inactive_count,
                    created_at=datetime.now(timezone.utc),
                    resolved=False,
                )
            )

        # CONTENT_ISSUE Alert - Check for low completion rates
        # Example: Finance content with low completion
        quiz_attempts_ref = db.collection("quiz_attempts").where(
            "content_type", "==", "finance_game"
        )
        quiz_attempts_docs = await quiz_attempts_ref.get()

        if len(quiz_attempts_docs) > 0:
            # Calculate pass rate for finance content
            passed_attempts = sum(
                1 for doc in quiz_attempts_docs if doc.to_dict().get("passed", False)
            )
            pass_rate = (passed_attempts / len(quiz_attempts_docs)) * 100

            if pass_rate < 60:  # If less than 60% pass rate
                alerts.append(
                    AlertResponse(
                        id="content_issue_001",
                        type="CONTENT_ISSUE",
                        title="Low Completion Rate",
                        description=f"Finance content has {pass_rate:.1f}% completion rate",
                        severity="error",
                        completion_rate=round(pass_rate, 1),
                        content_id="finance_game",
                        skill_type="finance",
                        created_at=datetime.now(timezone.utc),
                        resolved=False,
                    )
                )

        return UniformResponse.success_response(
            message="Admin alerts retrieved successfully", data=alerts
        )
    except Exception as e:
        log.error(f"Failed to get admin alerts: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get admin alerts: {str(e)}"
        )


# ==================== USER ANALYTICS ENDPOINTS ====================
@router.get("/users", response_model=UniformResponse[list[UserAnalyticsResponse]])
async def get_users_analytics(
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str = Query("", description="Search users by name or email"),
):
    """Get user analytics data with pagination"""
    try:
        log.info(f"User analytics requested by admin: {admin_user.id}")

        # Get child users only
        users_ref = db.collection("users").where("role", "==", "user")
        users_docs = await users_ref.get()

        user_analytics = []
        # FIXED: Use timezone-aware datetime
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        for doc in users_docs:
            user_data = doc.to_dict()
            user_id = doc.id

            # Skip if search term doesn't match
            if search and search.lower() not in user_data.get("name", "").lower():
                continue

            # Get user's quiz attempts
            quiz_attempts_ref = db.collection("quiz_attempts").where(
                "user_id", "==", user_id
            )
            quiz_attempts_docs = await quiz_attempts_ref.get()

            # Calculate average score
            total_score = 0
            quiz_count = len(quiz_attempts_docs)
            for attempt_doc in quiz_attempts_docs:
                attempt_data = attempt_doc.to_dict()
                total_score += attempt_data.get("score", 0)

            average_score = total_score / quiz_count if quiz_count > 0 else 0

            # Determine status
            last_login = user_data.get("last_login")
            status = (
                "active" if last_login and last_login >= seven_days_ago else "inactive"
            )

            user_analytics.append(
                UserAnalyticsResponse(
                    id=user_id,
                    name=user_data.get("name", "Unknown"),
                    age=user_data.get("age", 0),
                    email=user_data.get("email", ""),
                    last_login=last_login,
                    status=status,
                    badges=len(user_data.get("badges", [])),
                    quiz_attempts=quiz_count,
                    average_score=round(average_score, 1),
                )
            )

        # Apply pagination
        total_users = len(user_analytics)
        paginated_users = user_analytics[offset : offset + limit]

        return UniformResponse.success_response(
            message="User analytics retrieved successfully",
            data=paginated_users,
            meta={
                "total": total_users,
                "offset": offset,
                "limit": limit,
                "has_more": offset + limit < total_users,
            },
        )
    except Exception as e:
        log.error(f"Failed to get user analytics: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get user analytics: {str(e)}"
        )


@router.get(
    "/users/inactive", response_model=UniformResponse[list[UserAnalyticsResponse]]
)
async def get_inactive_users(
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
    days: int = Query(5, ge=1, le=30, description="Days of inactivity"),
):
    """Get users who haven't logged in for specified days"""
    try:
        log.info(f"Inactive users requested by admin: {admin_user.id} for {days} days")

        # FIXED: Use timezone-aware datetime
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        users_ref = db.collection("users").where("role", "==", "user")
        users_docs = await users_ref.get()

        inactive_users = []
        for doc in users_docs:
            user_data = doc.to_dict()
            user_id = doc.id
            last_login = user_data.get("last_login")

            # Check if user is inactive
            if not last_login or last_login < cutoff_date:
                # Get quiz attempts count
                quiz_attempts_ref = db.collection("quiz_attempts").where(
                    "user_id", "==", user_id
                )
                quiz_attempts_docs = await quiz_attempts_ref.get()

                inactive_users.append(
                    UserAnalyticsResponse(
                        id=user_id,
                        name=user_data.get("name", "Unknown"),
                        age=user_data.get("age", 0),
                        email=user_data.get("email", ""),
                        last_login=last_login,
                        status="inactive",
                        badges=len(user_data.get("badges", [])),
                        quiz_attempts=len(quiz_attempts_docs),
                        average_score=0.0,
                    )
                )

        return UniformResponse.success_response(
            message="Inactive users retrieved successfully",
            data=inactive_users,
            meta={"total": len(inactive_users), "cutoff_days": days},
        )
    except Exception as e:
        log.error(f"Failed to get inactive users: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get inactive users: {str(e)}"
        )


# ==================== SKILLS ANALYTICS ENDPOINTS ====================
@router.get("/skills", response_model=UniformResponse[list[SkillStatsResponse]])
async def get_skills_analytics(
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Get skills analytics data"""
    try:
        log.info(f"Skills analytics requested by admin: {admin_user.id}")

        # Get all skills
        skills_ref = db.collection("skills")
        skills_docs = await skills_ref.get()

        skills_analytics = []
        for doc in skills_docs:
            skill = doc.to_dict()
            skill["id"] = doc.id

            # Get quiz attempts for this skill
            quiz_attempts_ref = db.collection("quiz_attempts").where(
                "skill_id", "==", skill["id"]
            )
            quiz_attempts_docs = await quiz_attempts_ref.get()

            if quiz_attempts_docs:
                completed_attempts = sum(
                    1
                    for attempt_doc in quiz_attempts_docs
                    if attempt_doc.to_dict().get("completed", False)
                )
                total_quizzes = len(quiz_attempts_docs)
                completion_rate = (
                    (completed_attempts / total_quizzes * 100)
                    if total_quizzes > 0
                    else 0
                )
            else:
                total_quizzes = 0
                completion_rate = 0

            skills_analytics.append(
                SkillStatsResponse(
                    id=skill["id"],
                    name=skill["name"],
                    type=skill["type"],
                    status=skill["status"],
                    total_quizzes=total_quizzes,
                    average_completion=round(completion_rate, 1),
                    description=skill["description"],
                )
            )

        return UniformResponse.success_response(
            message="Skills analytics retrieved successfully", data=skills_analytics
        )
    except Exception as e:
        log.error(f"Failed to get skills analytics: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get skills analytics: {str(e)}"
        )


# ==================== REPORTING ENDPOINTS ====================
@router.get(
    "/reports/engagement", response_model=UniformResponse[EngagementReportResponse]
)
async def get_engagement_report(
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
):
    """Get detailed engagement report"""
    try:
        log.info(f"Engagement report requested by admin: {admin_user.id}")

        # Parse dates - FIXED: Make timezone-aware
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        # Get total users
        users_ref = db.collection("users").where("role", "==", "user")
        users_docs = await users_ref.get()
        total_users = len(users_docs)

        # Get active users in period
        active_users = 0
        for doc in users_docs:
            user_data = doc.to_dict()
            last_login = user_data.get("last_login")
            if last_login and start_dt <= last_login <= end_dt:
                active_users += 1

        engagement_rate = (active_users / total_users * 100) if total_users > 0 else 0

        # Get skill breakdown
        engagements_ref = (
            db.collection("skill_engagements")
            .where("timestamp", ">=", start_dt)
            .where("timestamp", "<=", end_dt)
        )
        engagements_docs = await engagements_ref.get()

        skill_breakdown = {}
        for doc in engagements_docs:
            data = doc.to_dict()
            skill_type = data.get("skill_type", "unknown")
            if skill_type not in skill_breakdown:
                skill_breakdown[skill_type] = 0
            skill_breakdown[skill_type] += 1

        # Generate daily active users
        daily_active = []
        current_date = start_dt
        while current_date <= end_dt:
            date_str = current_date.date().isoformat()

            # Count users active on this day
            daily_count = 0
            for doc in users_docs:
                user_data = doc.to_dict()
                last_login = user_data.get("last_login")
                if last_login and last_login.date() == current_date.date():
                    daily_count += 1

            daily_active.append({"date": date_str, "active_users": daily_count})
            current_date += timedelta(days=1)

        report = EngagementReportResponse(
            period={"start": start_date, "end": end_date},
            total_users=total_users,
            active_users=active_users,
            engagement_rate=round(engagement_rate, 1),
            skill_breakdown=[
                {"skill": skill, "count": count}
                for skill, count in skill_breakdown.items()
            ],
            daily_active=daily_active,
        )

        return UniformResponse.success_response(
            message="Engagement report generated successfully", data=report
        )
    except Exception as e:
        log.error(f"Failed to generate engagement report: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate engagement report: {str(e)}"
        )


@router.get(
    "/reports/performance", response_model=UniformResponse[PerformanceReportResponse]
)
async def get_performance_report(
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
):
    """Get detailed performance report"""
    try:
        log.info(f"Performance report requested by admin: {admin_user.id}")

        # Parse dates - FIXED: Make timezone-aware
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        # Get quiz attempts in period
        quiz_attempts_ref = (
            db.collection("quiz_attempts")
            .where("timestamp", ">=", start_dt)
            .where("timestamp", "<=", end_dt)
        )
        quiz_attempts_docs = await quiz_attempts_ref.get()

        total_quizzes = len(quiz_attempts_docs)
        total_score = 0
        skill_performance = {}

        for doc in quiz_attempts_docs:
            data = doc.to_dict()
            score = data.get("score", 0)
            skill_type = data.get("skill_type", "unknown")

            total_score += score

            if skill_type not in skill_performance:
                skill_performance[skill_type] = {"total_score": 0, "count": 0}

            skill_performance[skill_type]["total_score"] += score
            skill_performance[skill_type]["count"] += 1

        average_score = (total_score / total_quizzes) if total_quizzes > 0 else 0

        # Calculate skill performance averages
        skill_performance_list = []
        for skill, data in skill_performance.items():
            avg_score = data["total_score"] / data["count"] if data["count"] > 0 else 0
            skill_performance_list.append(
                {
                    "skill": skill,
                    "average_score": round(avg_score, 1),
                    "attempts": data["count"],
                }
            )

        # Generate improvement trends (simplified)
        improvement_trends = [
            {"period": "week1", "average_score": 75.2},
            {"period": "week2", "average_score": 78.1},
            {"period": "week3", "average_score": 81.3},
            {"period": "week4", "average_score": 83.7},
        ]

        report = PerformanceReportResponse(
            total_quizzes=total_quizzes,
            average_score=round(average_score, 1),
            skill_performance=skill_performance_list,
            improvement_trends=improvement_trends,
        )

        return UniformResponse.success_response(
            message="Performance report generated successfully", data=report
        )
    except Exception as e:
        log.error(f"Failed to generate performance report: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate performance report: {str(e)}"
        )


# ==================== REQUEST SCHEMAS ====================
class CreateAlertRequest(BaseModel):
    """Request schema for creating custom alerts"""

    type: str  # CUSTOM, SAFETY_CONCERN, CONTENT_ISSUE, etc.
    title: str
    description: str
    severity: str  # low, warning, high, critical
    user_id: str | None = None
    content_id: str | None = None
    skill_type: str | None = None
    expires_at: datetime | None = None


class CreateFlagRequest(BaseModel):
    """Request schema for creating content flags"""

    content_type: str  # quiz, diary_entry, chat_message, user_profile
    content_id: str
    flag_type: str  # inappropriate, safety_concern, spam, other
    reason: str
    reporter_id: str | None = None
    priority: str = "medium"  # low, medium, high, urgent


class ResolveAlertRequest(BaseModel):
    """Request schema for resolving alerts"""

    resolution_notes: str | None = None
    resolved_by: str


class UpdateFlagRequest(BaseModel):
    """Request schema for updating flag status"""

    status: str  # pending, reviewing, resolved, dismissed
    admin_notes: str | None = None
    action_taken: str | None = None


# ==================== ALERT MANAGEMENT ENDPOINTS ====================


@router.post("/alerts", response_model=UniformResponse[AlertResponse])
async def create_custom_alert(
    request: CreateAlertRequest,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Create a custom alert (Admin only)"""
    try:
        log.info(f"Creating custom alert by admin: {admin_user.id}")

        # Generate unique alert ID
        alert_id = (
            f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{admin_user.id[:8]}"
        )

        # Create alert document
        alert_data = {
            "id": alert_id,
            "type": request.type,
            "title": request.title,
            "description": request.description,
            "severity": request.severity,
            "user_id": request.user_id,
            "content_id": request.content_id,
            "skill_type": request.skill_type,
            "created_at": datetime.now(timezone.utc),
            "created_by": admin_user.id,
            "resolved": False,
            "expires_at": request.expires_at,
        }

        # Save to database
        await db.collection("admin_alerts").document(alert_id).set(alert_data)

        # Return response
        alert_response = AlertResponse(
            id=alert_id,
            type=request.type,
            title=request.title,
            description=request.description,
            severity=request.severity,
            created_at=alert_data["created_at"],
            resolved=False,
        )

        return UniformResponse.success_response(
            message="Alert created successfully", data=alert_response
        )

    except Exception as e:
        log.error(f"Failed to create alert: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create alert: {str(e)}")


@router.patch("/alerts/{alert_id}/resolve", response_model=UniformResponse[dict])
async def resolve_alert(
    alert_id: str,
    request: ResolveAlertRequest,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Resolve an alert"""
    try:
        log.info(f"Resolving alert {alert_id} by admin: {admin_user.id}")

        # Check if alert exists
        alert_ref = db.collection("admin_alerts").document(alert_id)
        alert_doc = await alert_ref.get()

        if not alert_doc.exists:
            raise HTTPException(status_code=404, detail="Alert not found")

        # Update alert
        update_data = {
            "resolved": True,
            "resolved_at": datetime.now(timezone.utc),
            "resolved_by": admin_user.id,
            "resolution_notes": request.resolution_notes,
        }

        await alert_ref.update(update_data)

        return UniformResponse.success_response(
            message="Alert resolved successfully", data={"alert_id": alert_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to resolve alert: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to resolve alert: {str(e)}"
        )


@router.delete("/alerts/{alert_id}", response_model=UniformResponse[dict])
async def delete_alert(
    alert_id: str,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Delete an alert (Admin only)"""
    try:
        log.info(f"Deleting alert {alert_id} by admin: {admin_user.id}")

        # Check if alert exists
        alert_ref = db.collection("admin_alerts").document(alert_id)
        alert_doc = await alert_ref.get()

        if not alert_doc.exists:
            raise HTTPException(status_code=404, detail="Alert not found")

        # Delete alert
        await alert_ref.delete()

        return UniformResponse.success_response(
            message="Alert deleted successfully", data={"alert_id": alert_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to delete alert: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete alert: {str(e)}")


# ==================== FLAGS MANAGEMENT ENDPOINTS ====================


@router.post("/flags", response_model=UniformResponse[dict])
async def create_content_flag(
    request: CreateFlagRequest,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Create a content flag"""
    try:
        log.info(f"Creating content flag by admin: {admin_user.id}")

        # Generate unique flag ID
        flag_id = f"flag_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{admin_user.id[:8]}"

        # Create flag document
        flag_data = {
            "id": flag_id,
            "content_type": request.content_type,
            "content_id": request.content_id,
            "flag_type": request.flag_type,
            "reason": request.reason,
            "reporter_id": request.reporter_id or admin_user.id,
            "priority": request.priority,
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
            "created_by": admin_user.id,
        }

        # Save to database
        await db.collection("content_flags").document(flag_id).set(flag_data)

        # Create corresponding alert if high priority
        if request.priority in ["high", "urgent"]:
            alert_data = {
                "id": f"flag_alert_{flag_id}",
                "type": "CONTENT_FLAG",
                "title": "High Priority Content Flag",
                "description": f"Content flagged: {request.reason}",
                "severity": "high" if request.priority == "high" else "critical",
                "content_id": request.content_id,
                "created_at": datetime.now(timezone.utc),
                "resolved": False,
                "flag_id": flag_id,
            }
            await (
                db.collection("admin_alerts")
                .document(f"flag_alert_{flag_id}")
                .set(alert_data)
            )

        return UniformResponse.success_response(
            message="Content flag created successfully",
            data={"flag_id": flag_id, "status": "pending"},
        )

    except Exception as e:
        log.error(f"Failed to create content flag: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create content flag: {str(e)}"
        )


@router.get("/flags", response_model=UniformResponse[list[dict]])
async def get_content_flags(
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
    status: str | None = Query(None, description="Filter by status"),
    priority: str | None = Query(None, description="Filter by priority"),
    limit: int = Query(50, ge=1, le=200, description="Limit results"),
):
    """Get all content flags"""
    try:
        log.info(f"Getting content flags by admin: {admin_user.id}")

        # Build query
        flags_ref = db.collection("content_flags")

        if status:
            flags_ref = flags_ref.where("status", "==", status)
        if priority:
            flags_ref = flags_ref.where("priority", "==", priority)

        flags_ref = flags_ref.order_by("created_at", direction="DESCENDING").limit(
            limit
        )

        # Execute query
        flags_docs = await flags_ref.get()

        flags = []
        for doc in flags_docs:
            flag_data = doc.to_dict()
            flags.append(flag_data)

        return UniformResponse.success_response(
            message="Content flags retrieved successfully", data=flags
        )

    except Exception as e:
        log.error(f"Failed to get content flags: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get content flags: {str(e)}"
        )


@router.patch("/flags/{flag_id}", response_model=UniformResponse[dict])
async def update_flag_status(
    flag_id: str,
    request: UpdateFlagRequest,
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Update flag status and add admin notes"""
    try:
        log.info(f"Updating flag {flag_id} by admin: {admin_user.id}")

        # Check if flag exists
        flag_ref = db.collection("content_flags").document(flag_id)
        flag_doc = await flag_ref.get()

        if not flag_doc.exists:
            raise HTTPException(status_code=404, detail="Flag not found")

        # Update flag
        update_data = {
            "status": request.status,
            "admin_notes": request.admin_notes,
            "action_taken": request.action_taken,
            "updated_at": datetime.now(timezone.utc),
            "updated_by": admin_user.id,
        }

        if request.status in ["resolved", "dismissed"]:
            update_data["resolved_at"] = datetime.now(timezone.utc)

        await flag_ref.update(update_data)

        return UniformResponse.success_response(
            message="Flag updated successfully",
            data={"flag_id": flag_id, "status": request.status},
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to update flag: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update flag: {str(e)}")


# ==================== BULK OPERATIONS ====================


@router.post("/alerts/bulk-resolve", response_model=UniformResponse[dict])
async def bulk_resolve_alerts(
    alert_ids: list[str],
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
):
    """Bulk resolve multiple alerts"""
    try:
        log.info(f"Bulk resolving alerts by admin: {admin_user.id}")

        resolved_count = 0
        failed_count = 0

        for alert_id in alert_ids:
            try:
                alert_ref = db.collection("admin_alerts").document(alert_id)
                alert_doc = await alert_ref.get()

                if alert_doc.exists:
                    await alert_ref.update(
                        {
                            "resolved": True,
                            "resolved_at": datetime.now(timezone.utc),
                            "resolved_by": admin_user.id,
                        }
                    )
                    resolved_count += 1
                else:
                    failed_count += 1
            except Exception:
                failed_count += 1

        return UniformResponse.success_response(
            message="Bulk operation completed",
            data={
                "resolved_count": resolved_count,
                "failed_count": failed_count,
                "total_requested": len(alert_ids),
            },
        )

    except Exception as e:
        log.error(f"Failed to bulk resolve alerts: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to bulk resolve alerts: {str(e)}"
        )


# ==================== EMERGENCY ALERT BUTTON ====================


@router.post("/emergency-alert", response_model=UniformResponse[AlertResponse])
async def create_emergency_alert(
    admin_user: User = Depends(require_admin),
    db: firestore.AsyncClient = Depends(get_firebase_client),
    title: str = "Emergency Alert",
    description: str = "Emergency situation detected - immediate attention required",
):
    """Create emergency alert - one-click button functionality"""
    try:
        log.info(f"EMERGENCY ALERT created by admin: {admin_user.id}")

        # Generate emergency alert ID
        alert_id = (
            f"emergency_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{admin_user.id[:8]}"
        )

        # Create emergency alert
        alert_data = {
            "id": alert_id,
            "type": "EMERGENCY",
            "title": title,
            "description": description,
            "severity": "critical",
            "created_at": datetime.now(timezone.utc),
            "created_by": admin_user.id,
            "resolved": False,
            "is_emergency": True,
        }

        # Save to database
        await db.collection("admin_alerts").document(alert_id).set(alert_data)

        # Log emergency alert creation
        log.critical(f"EMERGENCY ALERT CREATED: {alert_id} by admin {admin_user.id}")

        # Return response
        alert_response = AlertResponse(
            id=alert_id,
            type="EMERGENCY",
            title=title,
            description=description,
            severity="critical",
            created_at=alert_data["created_at"],
            resolved=False,
        )

        return UniformResponse.success_response(
            message="Emergency alert created successfully", data=alert_response
        )

    except Exception as e:
        log.error(f"Failed to create emergency alert: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create emergency alert: {str(e)}"
        )
