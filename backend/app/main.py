# app/main.py - Simplified health check responses
import traceback
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from firebase_admin import auth as firebase_auth
from firebase_admin.exceptions import FirebaseError
from pydantic import ValidationError

from app.api.v1.router import api_router
from app.config.firebase import initialize_firebase
from app.config.logging import log
from app.config.settings import settings
from app.schemas.base import UniformResponse
from app.utils.exceptions import (
    BaseAPIException,
    base_api_exception_handler,
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)

# Initialize logging first
log.info("Starting Life Skills App API...")


async def seed_admin_user():
    """
    Check if any admin user exists in the 'users' collection.
    If not, create one in both Firebase Auth and Firestore.
    """
    ADMIN_EMAIL = "admin12@gmail.com"
    ADMIN_PASSWORD = "admin12"

    log.info("Checking for existing admin user...")

    from app.services.firebase import FirebaseService
    firebase_service = FirebaseService()

    # Query Firestore for any user with role == "admin"
    existing_admins = await firebase_service.query_documents(
        "users", "role", "==", "admin"
    )

    if existing_admins:
        log.info("Admin user already exists, skipping seed.")
        return

    log.warning("No admin user found. Creating default admin user...")

    # Step 1: Create user in Firebase Auth
    try:
        firebase_user = firebase_auth.create_user(
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            email_verified=True,
            display_name="Admin",
        )
        firebase_uid = firebase_user.uid
        log.success(f"Firebase Auth admin user created: {firebase_uid}")
    except FirebaseError as e:
        # If user already exists in Firebase Auth but not in Firestore, fetch them
        if "EMAIL_EXISTS" in str(e) or "email-already-exists" in str(e).lower():
            log.warning("Admin already exists in Firebase Auth, fetching existing user...")
            firebase_user = firebase_auth.get_user_by_email(ADMIN_EMAIL)
            firebase_uid = firebase_user.uid
        else:
            log.error(f"Failed to create admin Firebase Auth user: {e}")
            raise

    # Step 2: Create admin document in Firestore
    try:
        admin_doc = {
            "email": ADMIN_EMAIL,
            "firebase_uid": firebase_uid,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin",
            "is_active": True,
            "is_verified": True,
            "age": None,
            "grade_level": None,
            "parent_id": None,
            "children_ids": [],
            "current_skills": [],
            "completed_skills": [],
            "points": 0,
            "badges": [],
            "emergency_contacts": [],
            "preferences": {},
            "avatar_url": None,
            "firebase_synced_at": datetime.now(timezone.utc),
        }

        doc_id = await firebase_service.create_document("users", admin_doc)
        log.success(f"Admin Firestore document created with ID: {doc_id}")

    except Exception as e:
        # Rollback: delete the Firebase Auth user we just created to avoid orphans
        log.error(f"Failed to create admin Firestore document: {e}")
        log.warning(f"Rolling back Firebase Auth user: {firebase_uid}")
        try:
            firebase_auth.delete_user(firebase_uid)
        except Exception:
            pass
        raise


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize Firebase on startup and cleanup on shutdown"""
    log.info("Initializing async Firebase client...")
    try:
        # Initialize async Firebase client
        firebase_client = await initialize_firebase()
        # Store client in app state for access by services
        app.state.firebase_client = firebase_client
        log.success("Async Firebase client initialized successfully")
    except Exception as e:
        log.error(f"Failed to initialize async Firebase client: {e}")
        log.error(f"Traceback: {traceback.format_exc()}")
        raise

    # Seed admin user if not present
    try:
        await seed_admin_user()
    except Exception as e:
        log.error(f"Admin seeding failed: {e}")
        # Non-fatal — app continues running even if seed fails
        log.warning("App will continue without admin seeding.")

    yield

    # Cleanup code here if needed
    log.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    description="Backend API for Life Skills App - Helping children develop essential life skills",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",           # Local development
        "https://lifeskillapp.vercel.app", # Production Vercel deployment
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
log.info("CORS middleware configured")

# Register exception handlers
app.add_exception_handler(BaseAPIException, base_api_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
log.info("Exception handlers registered")

# Include API routes
app.include_router(api_router)
log.info("API routes registered")


@app.get("/health", response_model=UniformResponse[dict])
async def health_check():
    """Comprehensive health check including async Firebase connectivity"""
    log.debug("Health check requested")

    health_data = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "environment": settings.environment,
    }

    # Check Firebase connectivity using async operations
    try:
        from app.services.firebase import FirebaseService

        firebase_service = FirebaseService()

        # Try a simple async operation
        test_collection = "_health_check"
        current_time = datetime.now(timezone.utc)

        # Create a test document
        test_data = {"timestamp": current_time, "health_check": True}
        doc_id = await firebase_service.create_document(test_collection, test_data)

        # Try to retrieve it
        retrieved_doc = await firebase_service.get_document(test_collection, doc_id)

        if retrieved_doc:
            # Clean up the test document
            await firebase_service.delete_document(test_collection, doc_id)
            health_data["firebase_status"] = "healthy"
        else:
            health_data["status"] = "degraded"
            health_data["firebase_status"] = "unhealthy"

    except Exception as e:
        health_data["status"] = "degraded"
        health_data["firebase_status"] = "unhealthy"
        log.warning(f"Firebase async health check failed: {str(e)}")

    # Determine response based on status
    if health_data["status"] == "healthy":
        return UniformResponse.success_response(
            message="All systems operational",
            data=health_data,
        )
    else:
        return UniformResponse.error_response(
            message="Some services are experiencing issues",
            errors=["Firebase connection issues"],
            meta={"error_type": "service_degraded"},
        )


@app.get("/", response_model=UniformResponse[dict])
async def root():
    """Root endpoint with API information"""
    log.debug("Root endpoint accessed")

    api_info = {
        "name": settings.app_name,
        "version": "1.0.0",
        "description": "Backend API for Life Skills App - Helping children develop essential life skills",
        "environment": settings.environment,
        "endpoints": {
            "documentation": "/docs",
            "health_check": "/health",
            "api_base": "/api/v1",
        },
    }

    return UniformResponse.success_response(
        message="Welcome to Life Skills App API",
        data=api_info,
    )


@app.api_route(
    "/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]
)
async def catch_all_handler(request: Request, path: str):
    """Catch-all handler for undefined routes"""
    log.warning(f"Undefined route accessed: {request.method} {request.url}")

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=UniformResponse.error_response(
            message=f"Route not found: {request.method} /{path}",
            errors=[
                f"The requested endpoint '{request.method} /{path}' does not exist",
                "Please check the available endpoints below or visit /docs for API documentation",
            ],
            meta={"error_type": "route_not_found"},
        ).model_dump(),
    )
