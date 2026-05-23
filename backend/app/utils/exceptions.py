# app/utils/exceptions.py - Simplified meta responses
import json

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.config.logging import log
from app.schemas.base import UniformResponse
from app.utils.security import verify_firebase_token


class BaseAPIException(HTTPException):
    """Base exception class for API errors"""

    def __init__(
        self,
        status_code: int,
        message: str = "An error occurred",
        errors: list[str] | None = None,
        meta: dict | None = None,
    ):
        self.message = message
        self.errors = errors or []
        self.meta = meta or {}
        super().__init__(status_code=status_code, detail=message)


class AuthenticationError(BaseAPIException):
    def __init__(
        self, message: str = "Authentication failed", errors: list[str] | None = None
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            errors=errors,
            meta={"error_type": "authentication"},
        )


class AuthorizationError(BaseAPIException):
    def __init__(
        self, message: str = "Not enough permissions", errors: list[str] | None = None
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            errors=errors,
            meta={"error_type": "authorization"},
        )


class NotFoundError(BaseAPIException):
    def __init__(
        self, message: str = "Resource not found", errors: list[str] | None = None
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            errors=errors,
            meta={"error_type": "not_found"},
        )


class ValidationError(BaseAPIException):
    def __init__(
        self, message: str = "Validation error", errors: list[str] | None = None
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            errors=errors,
            meta={"error_type": "validation"},
        )


class ConflictError(BaseAPIException):
    def __init__(
        self, message: str = "Resource already exists", errors: list[str] | None = None
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            errors=errors,
            meta={"error_type": "conflict"},
        )


class BadRequestError(BaseAPIException):
    def __init__(self, message: str = "Bad request", errors: list[str] | None = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            errors=errors,
            meta={"error_type": "bad_request"},
        )


class InternalServerError(BaseAPIException):
    def __init__(
        self, message: str = "Internal server error", errors: list[str] | None = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            errors=errors,
            meta={"error_type": "internal_server"},
        )


class RateLimitError(BaseAPIException):
    def __init__(
        self, message: str = "Rate limit exceeded", errors: list[str] | None = None
    ):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=message,
            errors=errors,
            meta={"error_type": "rate_limit"},
        )


class ServiceUnavailableError(BaseAPIException):
    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        errors: list[str] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=message,
            errors=errors,
            meta={"error_type": "service_unavailable"},
        )


# Exception handlers
async def base_api_exception_handler(request: Request, exc: BaseAPIException):
    """Handle custom API exceptions with uniform response format"""
    log.warning(f"API Exception: {exc.message} - {exc.errors}")

    # Special cleanup for registration validation errors
    if (
        request.url.path == "/api/v1/auth/complete-registration"
        and exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    ):
        await _handle_registration_cleanup(request)

    response = UniformResponse.error_response(
        message=exc.message,
        errors=exc.errors,
        meta=exc.meta
        if exc.meta and exc.meta != {"error_type": exc.meta.get("error_type")}
        else None,
    )

    return JSONResponse(status_code=exc.status_code, content=response.model_dump())


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle standard HTTP exceptions with uniform response format"""
    log.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")

    response = UniformResponse.error_response(
        message=str(exc.detail),
        errors=[str(exc.detail)],
        meta={"error_type": "http_exception"} if exc.status_code >= 500 else None,
    )

    return JSONResponse(status_code=exc.status_code, content=response.model_dump())


async def validation_exception_handler(request: Request, exc: PydanticValidationError):
    """Handle Pydantic validation exceptions with enhanced cleanup"""
    log.warning(f"Validation Exception on {request.url.path}: {exc.errors()}")

    # Enhanced cleanup for registration validation failures
    cleanup_attempted = False
    if request.url.path == "/api/v1/auth/complete-registration":
        await _handle_registration_cleanup(request)
        cleanup_attempted = True

    # Generate user-friendly error messages
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(x) for x in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")

    message = "Validation failed"
    if cleanup_attempted:
        message += " - Firebase Auth user has been cleaned up"

    response = UniformResponse.error_response(
        message=message,
        errors=errors,
        meta={"error_type": "validation"} if not cleanup_attempted else None,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump(),
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    import traceback

    log.error(f"Unhandled exception: {str(exc)}")
    log.error(f"Traceback: {traceback.format_exc()}")

    # Cleanup for registration errors
    cleanup_attempted = False
    if request.url.path == "/api/v1/auth/complete-registration":
        await _handle_registration_cleanup(request)
        cleanup_attempted = True

    from app.config.settings import settings

    if settings.debug:
        error_detail = str(exc)
        errors = [str(exc)]
    else:
        error_detail = "An unexpected error occurred"
        errors = ["Internal server error"]

    message = error_detail
    if cleanup_attempted:
        message += " - Firebase Auth user has been cleaned up"

    response = UniformResponse.error_response(
        message=message,
        errors=errors,
        meta={"error_type": "internal_server"},
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response.model_dump()
    )


async def _handle_registration_cleanup(request: Request):
    """Enhanced cleanup for registration validation failures"""
    log.warning("🧹 Registration validation failed - initiating Firebase cleanup")

    try:
        # Get request body
        body = await request.body()
        if not body:
            log.warning("❌ No request body found for cleanup")
            return

        # Parse JSON
        try:
            request_data = json.loads(body)
        except json.JSONDecodeError:
            log.warning("❌ Could not parse request body JSON")
            return

        # Extract Firebase token
        firebase_token = request_data.get("firebase_id_token")
        if not firebase_token:
            log.warning("❌ No firebase_id_token found in request")
            return

        # Verify token and extract UID
        firebase_user_data = verify_firebase_token(firebase_token)
        if not firebase_user_data:
            log.warning("❌ Invalid Firebase token for cleanup")
            return

        firebase_uid = firebase_user_data.firebase_uid
        log.info(f"🔍 Found Firebase UID for cleanup: {firebase_uid}")

        # Import AuthService and perform cleanup
        from app.services.auth import AuthService

        auth_service = AuthService()

        log.warning(f"🧹 Starting Firebase Auth cleanup for: {firebase_uid}")
        cleanup_success = await auth_service.cleanup_firebase_auth_user(firebase_uid)

        if cleanup_success:
            log.success(
                f"✅ Firebase Auth user cleaned up successfully: {firebase_uid}"
            )
        else:
            log.error(f"❌ Failed to cleanup Firebase Auth user: {firebase_uid}")

    except Exception as cleanup_error:
        log.error(
            f"❌ Critical error during registration cleanup: {str(cleanup_error)}"
        )
        import traceback

        log.error(f"Cleanup traceback: {traceback.format_exc()}")
