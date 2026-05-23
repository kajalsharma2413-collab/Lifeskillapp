# app/config/firebase.py
import firebase_admin
from firebase_admin import credentials, firestore_async

from app.config.logging import log
from app.config.settings import settings


def validate_firebase_config():
    """Validate that all required Firebase configuration is present"""
    required_fields = [
        "firebase_project_id",
        "firebase_private_key_id",
        "firebase_private_key",
        "firebase_client_email",
        "firebase_client_id",
    ]
    missing_fields = []
    for field in required_fields:
        if not getattr(settings, field, None):
            missing_fields.append(field)

    if missing_fields:
        raise ValueError(
            f"Missing required Firebase configuration: {', '.join(missing_fields)}"
        )
    log.info("Firebase configuration validation passed")


async def initialize_firebase():
    """Initialize Firebase Admin SDK with async client and validation"""
    try:
        # Check if app already exists
        app = firebase_admin.get_app()
        log.debug("Using existing Firebase app")
        # ← FIXED: was missing database_id here
        return firestore_async.client(app, database_id="lifeskill")
    except ValueError:
        # App doesn't exist, create it
        log.info("Initializing new Firebase app")

        # Validate configuration first
        validate_firebase_config()

        cred_dict = {
            "type": "service_account",
            "project_id": settings.firebase_project_id,
            "private_key_id": settings.firebase_private_key_id,
            "private_key": settings.firebase_private_key.replace("\\n", "\n"),
            "client_email": settings.firebase_client_email,
            "client_id": settings.firebase_client_id,
            "auth_uri": settings.firebase_auth_uri,
            "token_uri": settings.firebase_token_uri,
        }

        try:
            cred = credentials.Certificate(cred_dict)
            app = firebase_admin.initialize_app(cred)
            # ← already correct
            client = firestore_async.client(app, database_id="lifeskill")

            # Test connection with async operation
            test_doc = client.collection("_health_check").document("test")
            await test_doc.set({"timestamp": firestore_async.SERVER_TIMESTAMP})

            log.success(
                "Firebase async client initialized and connection tested successfully"
            )
            return client
        except Exception as e:
            log.error(f"Failed to initialize Firebase async client: {str(e)}")
            raise ConnectionError(f"Firebase async initialization failed: {str(e)}")


async def get_firebase_client():
    """Get Firebase client from app state for dependency injection"""
    from app.main import app

    if not hasattr(app.state, "firebase_client"):
        # Initialize client if not available
        firebase_client = await initialize_firebase()
        app.state.firebase_client = firebase_client

    return app.state.firebase_client