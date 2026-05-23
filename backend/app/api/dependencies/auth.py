# app/api/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config.logging import log
from app.models.base import UserRole
from app.models.user import User
from app.services.user import UserService
from app.utils.exceptions import AuthenticationError
from app.utils.security import verify_firebase_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Get current authenticated user using Firebase ID token"""
    log.debug("Authenticating user from Firebase ID token")

    # Verify Firebase ID token
    firebase_user_data = verify_firebase_token(credentials.credentials)
    if not firebase_user_data:
        log.warning("Invalid Firebase ID token provided")
        raise AuthenticationError("Invalid authentication token")

    # Get user from our database using Firebase UID
    user_service = UserService()
    try:
        user = await user_service.get_user_by_firebase_uid(
            firebase_user_data.firebase_uid
        )
        if not user:
            log.warning(
                f"User not found in database: {firebase_user_data.firebase_uid}"
            )
            raise AuthenticationError("User not found")

        if not user.is_active:
            log.warning(f"Inactive user attempted access: {user.id}")
            raise AuthenticationError("Account is deactivated")

        log.debug(f"User authenticated successfully: {user.id}")
        return user

    except Exception as e:
        log.error(f"User authentication failed: {str(e)}")
        raise AuthenticationError("Authentication failed")


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        log.warning(f"Inactive user attempted access: {current_user.id}")
        raise AuthenticationError("Inactive user")

    log.debug(f"Active user verified: {current_user.id}")
    return current_user


async def get_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Require admin role"""
    log.debug(
        f"Checking admin access for user: {current_user.id}, role: {current_user.role}"
    )

    if current_user.role != UserRole.ADMIN:
        log.warning(f"Non-admin user attempted admin access: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    log.debug(f"Admin access granted to user: {current_user.id}")
    return current_user


async def get_parent_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Require parent role"""
    log.debug(
        f"Checking parent access for user: {current_user.id}, role: {current_user.role}"
    )

    if current_user.role not in [UserRole.PARENT]:
        log.warning(f"Non-parent user attempted parent access: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Parent access required"
        )

    log.debug(f"Parent access granted to user: {current_user.id}")
    return current_user
