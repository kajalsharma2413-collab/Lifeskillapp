# app/api/v1/auth.py - Simplified meta responses
import json

from fastapi import APIRouter, Depends, Request
from pydantic import ValidationError

from app.api.dependencies.auth import get_current_active_user, get_parent_user
from app.config.logging import log
from app.models.base import UserRole
from app.models.user import User
from app.schemas.auth import (
    FirebaseAuthToken,
    UserRegistrationComplete,
)
from app.schemas.base import UniformResponse
from app.schemas.user import UserResponse, UserUpdate
from app.services.auth import AuthService
from app.utils.exceptions import ValidationError as CustomValidationError
from app.utils.security import verify_firebase_token

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()


@router.post("/complete-registration", response_model=UniformResponse[dict])
async def complete_registration(request: Request):
    """Complete user registration after Firebase Auth signup"""
    firebase_uid = None
    firebase_email = None

    try:
        log.info("🚀 Registration completion endpoint called")

        # Extract raw request body
        try:
            raw_body = await request.body()
            request_data = json.loads(raw_body)
            log.debug("✅ Request body parsed successfully")
        except Exception as e:
            log.error(f"❌ Failed to parse request body: {str(e)}")
            return UniformResponse.error_response(
                message="Invalid request format",
                errors=[f"Failed to parse request: {str(e)}"],
            )

        # Extract and verify Firebase token
        firebase_id_token = request_data.get("firebase_id_token")
        if not firebase_id_token:
            log.error("❌ No firebase_id_token in request")
            return UniformResponse.error_response(
                message="Missing Firebase ID token",
                errors=["firebase_id_token is required"],
            )

        log.debug("🔍 Verifying Firebase ID token...")
        firebase_user_data = verify_firebase_token(firebase_id_token)
        if not firebase_user_data:
            log.error("❌ Invalid Firebase ID token")
            return UniformResponse.error_response(
                message="Invalid Firebase ID token",
                errors=["Token verification failed"],
            )

        firebase_uid = firebase_user_data.firebase_uid
        firebase_email = firebase_user_data.email
        log.info(f"✅ Firebase user identified: {firebase_email}")

        # Parse and validate registration data
        try:
            registration_data = UserRegistrationComplete.model_validate(request_data)

            # Block admin role registration
            if registration_data.role == UserRole.ADMIN:
                log.error(f"❌ Admin role registration blocked for: {firebase_email}")
                raise CustomValidationError("Admin role registration is not allowed")

        except ValidationError as e:
            log.error(f"❌ Registration data validation failed: {e.errors()}")
            # Cleanup Firebase user
            cleanup_success = await auth_service.cleanup_firebase_auth_user(
                firebase_uid
            )

            validation_errors = []
            for error in e.errors():
                field = " -> ".join(str(x) for x in error["loc"])
                message = error["msg"]
                validation_errors.append(f"{field}: {message}")

            return UniformResponse.error_response(
                message="Registration validation failed - Firebase user cleaned up",
                errors=validation_errors,
                meta={"cleanup_success": cleanup_success}
                if not cleanup_success
                else None,
            )

        except CustomValidationError as e:
            log.error(f"❌ Custom validation failed: {str(e)}")
            cleanup_success = await auth_service.cleanup_firebase_auth_user(
                firebase_uid
            )

            return UniformResponse.error_response(
                message="Registration validation failed - Firebase user cleaned up",
                errors=[str(e)],
                meta={"cleanup_success": cleanup_success}
                if not cleanup_success
                else None,
            )

        # Complete registration
        try:
            user = await auth_service.complete_registration(registration_data)
            log.success(f"✅ User registration completed successfully: {user.email}")

            user_response = UserResponse.model_validate(user.model_dump()).model_dump()
            return UniformResponse.success_response(
                message="Registration completed successfully",
                data={"user": user_response},
            )

        except Exception as service_error:
            log.error(f"❌ Service registration failed: {str(service_error)}")
            cleanup_success = await auth_service.cleanup_firebase_auth_user(
                firebase_uid
            )

            return UniformResponse.error_response(
                message="Registration completion failed - Firebase user cleaned up",
                errors=[str(service_error)],
                meta={"cleanup_success": cleanup_success}
                if not cleanup_success
                else None,
            )

    except Exception as unexpected_error:
        log.error(f"❌ Unexpected error in registration: {str(unexpected_error)}")

        if firebase_uid:
            cleanup_success = await auth_service.cleanup_firebase_auth_user(
                firebase_uid
            )
        else:
            cleanup_success = False

        return UniformResponse.error_response(
            message="Unexpected registration error - Firebase user cleaned up",
            errors=[str(unexpected_error)],
            meta={"cleanup_success": cleanup_success}
            if firebase_uid and not cleanup_success
            else None,
        )


@router.post("/verify", response_model=UniformResponse[dict])
async def verify_auth_token(auth_token: FirebaseAuthToken):
    """Verify Firebase ID token and return user data"""
    log.info("Auth token verification endpoint called")

    try:
        user = await auth_service.authenticate_user(auth_token)
        log.success(f"Auth token verified for user: {user.email}")

        user_response = UserResponse.model_validate(user.model_dump()).model_dump()
        return UniformResponse.success_response(
            message="Authentication verified",
            data={"user": user_response},
        )

    except Exception as e:
        log.error(f"Auth token verification failed: {str(e)}")
        return UniformResponse.error_response(
            message="Authentication verification failed", errors=[str(e)]
        )


@router.get("/me", response_model=UniformResponse[dict])
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    log.debug(f"User info endpoint called for user: {current_user.id}")

    try:
        user_data = UserResponse.model_validate(current_user.model_dump()).model_dump()
        return UniformResponse.success_response(
            message="User information retrieved successfully",
            data={"user": user_data},
        )

    except Exception as e:
        log.error(f"Failed to retrieve user info for {current_user.id}: {str(e)}")
        return UniformResponse.error_response(
            message="Failed to retrieve user information", errors=[str(e)]
        )


@router.post("/sync-firebase", response_model=UniformResponse[dict])
async def sync_firebase_data(current_user: User = Depends(get_current_active_user)):
    """Sync user data from Firebase Auth"""
    log.info(f"Firebase data sync requested for user: {current_user.id}")

    try:
        updated_user = await auth_service.sync_firebase_user_data(
            current_user.firebase_uid
        )
        if not updated_user:
            return UniformResponse.error_response(
                message="Failed to sync Firebase data",
                errors=["User not found or sync failed"],
            )

        user_data = UserResponse.model_validate(updated_user.model_dump()).model_dump()
        return UniformResponse.success_response(
            message="Firebase data synced successfully",
            data={"user": user_data},
        )

    except Exception as e:
        log.error(f"Firebase sync failed for user {current_user.id}: {str(e)}")
        return UniformResponse.error_response(
            message="Firebase sync failed", errors=[str(e)]
        )


@router.post("/generate-parent-code", response_model=UniformResponse[dict])
async def generate_parent_code(current_user: User = Depends(get_parent_user)):
    """Generate a parent code for child registration"""
    log.info(f"Parent code generation endpoint called for user: {current_user.id}")

    try:
        code = await auth_service.generate_parent_code(current_user.id)
        log.success(f"Parent code generated successfully: {current_user.id}")

        return UniformResponse.success_response(
            message="Parent code generated successfully",
            data={"code": code},
            meta={"expires_in_hours": 24},
        )

    except Exception as e:
        log.error(f"Parent code generation failed for user {current_user.id}: {str(e)}")
        return UniformResponse.error_response(
            message="Parent code generation failed", errors=[str(e)]
        )


@router.put("/me", response_model=UniformResponse[dict])
async def update_my_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
):
    """Update current user's own profile"""
    log.info(f"Self-profile update request by user: {current_user.id}")

    # Prevent admin profile updates
    if current_user.role == UserRole.ADMIN:
        log.warning(f"Admin user attempted to update own profile: {current_user.id}")
        return UniformResponse.error_response(
            message="Admin profiles cannot be updated",
            errors=["Admin accounts have fixed profiles that cannot be modified"],
            meta={"error_type": "admin_restriction"},
        )

    try:
        from app.services.user import UserService

        user_service = UserService()
        user = await user_service.update_user_profile(
            current_user.id, update_data, current_user.id, current_user.role
        )

        user_data = UserResponse.model_validate(user.model_dump()).model_dump()
        return UniformResponse.success_response(
            message="Your profile has been updated successfully",
            data={"user": user_data},
        )

    except Exception as e:
        log.error(f"Self-profile update failed for user {current_user.id}: {str(e)}")
        return UniformResponse.error_response(
            message="Failed to update your profile", errors=[str(e)]
        )


@router.get("/status", response_model=UniformResponse[dict])
async def get_auth_status(current_user: User = Depends(get_current_active_user)):
    """Get current authentication status"""
    log.debug(f"Auth status check for user: {current_user.id}")

    try:
        return UniformResponse.success_response(
            message="User is authenticated",
            data={
                "is_authenticated": True,
                "user_id": current_user.id,
                "role": current_user.role.value,
                "is_active": current_user.is_active,
                "email_verified": current_user.is_verified,
            },
        )

    except Exception as e:
        log.error(f"Auth status check failed for user {current_user.id}: {str(e)}")
        return UniformResponse.error_response(
            message="Auth status check failed", errors=[str(e)]
        )
