#!/usr/bin/env python3
"""
scripts/create_admin.py
-----------------------
One-time CLI script to bootstrap an admin user.

Usage:
    python scripts/create_admin.py
    python scripts/create_admin.py --email admin@example.com --password S3cur3Pass!

The script:
  1. Creates the user in Firebase Auth (email + password).
  2. Writes a matching document to the Firestore `users` collection
     with role = "admin".
  3. Prints the credentials so you can log in immediately.

Run this ONCE per environment. Re-running with the same email will
detect the existing account and skip creation safely.
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Make sure the project root is on sys.path so app.* imports resolve
# whether you run this from the repo root or from scripts/
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Load .env before importing anything from app.*
from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

# ---------------------------------------------------------------------------
# Now it is safe to import Firebase / app modules
# ---------------------------------------------------------------------------
import firebase_admin  # noqa: E402
from firebase_admin import auth, credentials, firestore  # noqa: E402

from app.config.logging import log  # noqa: E402
from app.models.base import UserRole  # noqa: E402


# ---------------------------------------------------------------------------
# Firebase initialisation (standalone — no FastAPI lifespan needed)
# ---------------------------------------------------------------------------

def _init_firebase() -> firestore.AsyncClient:
    """Initialise Firebase Admin SDK from env vars (same as app.config.firebase)."""
    if firebase_admin._apps:
        # Already initialised (e.g. during testing)
        app = firebase_admin.get_app()
    else:
        private_key = os.environ["FIREBASE_PRIVATE_KEY"].replace("\\n", "\n")
        cred = credentials.Certificate(
            {
                "type": "service_account",
                "project_id": os.environ["FIREBASE_PROJECT_ID"],
                "private_key_id": os.environ["FIREBASE_PRIVATE_KEY_ID"],
                "private_key": private_key,
                "client_email": os.environ["FIREBASE_CLIENT_EMAIL"],
                "client_id": os.environ["FIREBASE_CLIENT_ID"],
                "auth_uri": os.environ.get(
                    "FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"
                ),
                "token_uri": os.environ.get(
                    "FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"
                ),
            }
        )
        app = firebase_admin.initialize_app(cred)

    return firestore.AsyncClient(
        project=os.environ["FIREBASE_PROJECT_ID"],
        credentials=app.credential.get_credential(),
    )


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

async def create_admin(email: str, password: str, username: str) -> None:
    log.info(f"🔧 Creating admin account for: {email}")

    db = _init_firebase()

    # ------------------------------------------------------------------
    # 1. Firebase Auth — create or reuse
    # ------------------------------------------------------------------
    firebase_uid: str

    try:
        firebase_user = auth.create_user(
            email=email,
            password=password,
            email_verified=True,
            display_name=username,
        )
        firebase_uid = firebase_user.uid
        log.success(f"✅ Firebase Auth user created: {firebase_uid}")

    except auth.EmailAlreadyExistsError:
        # Already exists — reuse the existing Firebase Auth account
        existing = auth.get_user_by_email(email)
        firebase_uid = existing.uid
        log.warning(
            f"⚠️  Firebase Auth user already exists ({firebase_uid}). "
            "Checking Firestore..."
        )

    # ------------------------------------------------------------------
    # 2. Firestore — check for existing admin doc
    # ------------------------------------------------------------------
    users_ref = db.collection("users")
    existing_docs = await users_ref.where(
        "firebase_uid", "==", firebase_uid
    ).get()

    if existing_docs:
        existing_role = existing_docs[0].to_dict().get("role")
        if existing_role == UserRole.ADMIN.value:
            log.info("ℹ️  Admin user already exists in Firestore. Nothing to do.")
            _print_credentials(email, password)
            return
        else:
            log.warning(
                f"⚠️  Firestore doc exists but role is '{existing_role}'. "
                "Updating role to admin..."
            )
            await existing_docs[0].reference.update(
                {
                    "role": UserRole.ADMIN.value,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            log.success("✅ Role updated to admin in Firestore.")
            _print_credentials(email, password)
            return

    # ------------------------------------------------------------------
    # 3. Create Firestore user document with admin role
    # ------------------------------------------------------------------
    user_doc = {
        "email": email,
        "firebase_uid": firebase_uid,
        "username": username,
        "first_name": "Admin",
        "last_name": "User",
        "role": UserRole.ADMIN.value,
        "is_active": True,
        "is_verified": True,
        # Fields required by the User model — sensible defaults for admin
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
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    _ts, doc_ref = await db.collection("users").add(user_doc)
    log.success(f"✅ Admin Firestore document created: {doc_ref.id}")

    # ------------------------------------------------------------------
    # 4. Set custom claim on Firebase Auth so middleware can verify role
    # ------------------------------------------------------------------
    auth.set_custom_user_claims(firebase_uid, {"role": UserRole.ADMIN.value})
    log.success("✅ Firebase custom claim set: role=admin")

    _print_credentials(email, password)


def _print_credentials(email: str, password: str) -> None:
    print("\n" + "=" * 50)
    print("  🎉  Admin account ready")
    print("=" * 50)
    print(f"  Email   : {email}")
    print(f"  Password: {password}")
    print("=" * 50)
    print("  Use these credentials to log in via the app.")
    print("  Store the password somewhere safe and")
    print("  delete this output from your terminal history.")
    print("=" * 50 + "\n")


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap an admin user for Life Skills World."
    )
    parser.add_argument(
        "--email",
        default="admin@lifeskillsworld.com",
        help="Admin email address (default: admin@lifeskillsworld.com)",
    )
    parser.add_argument(
        "--password",
        default=None,
        help=(
            "Admin password. If omitted you will be prompted interactively "
            "(recommended so the password is not stored in shell history)."
        ),
    )
    parser.add_argument(
        "--username",
        default="admin",
        help="Display username (default: admin)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    # Prompt for password interactively if not passed as a flag
    password = args.password
    if not password:
        import getpass
        password = getpass.getpass("Enter admin password (min 8 chars): ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("❌ Passwords do not match. Aborting.")
            sys.exit(1)

    if len(password) < 8:
        print("❌ Password must be at least 8 characters. Aborting.")
        sys.exit(1)

    asyncio.run(create_admin(email=args.email, password=password, username=args.username))