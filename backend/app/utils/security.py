# app/utils/security.py
from firebase_admin import auth
from firebase_admin.exceptions import FirebaseError

from app.config.logging import log
from app.schemas.auth import FirebaseUserData


def verify_firebase_token(id_token: str) -> FirebaseUserData | None:
    """
    Verify Firebase ID token and extract user data
    This is the core security function for Firebase Auth
    """
    try:
        log.debug("Verifying Firebase ID token")

        # Verify the ID token using Firebase Admin SDK
        decoded_token = auth.verify_id_token(id_token, clock_skew_seconds=60)
        log.debug(f"Token verified for user: {decoded_token.get('uid')}")

        # Extract user data from the decoded token
        firebase_user_data = FirebaseUserData(
            firebase_uid=decoded_token.get("uid"),
            email=decoded_token.get("email"),
            email_verified=decoded_token.get("email_verified", False),
            name=decoded_token.get("name"),
            picture=decoded_token.get("picture"),
        )

        log.success(
            f"Firebase token verified successfully for user: {firebase_user_data.firebase_uid}"
        )
        return firebase_user_data

    except FirebaseError as e:
        log.warning(f"Firebase token verification failed: {str(e)}")
        return None
    except Exception as e:
        log.error(f"Unexpected error during token verification: {str(e)}")
        return None
