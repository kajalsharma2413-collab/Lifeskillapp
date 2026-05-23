# app/services/auth.py
import uuid
from datetime import datetime, timedelta, timezone

from firebase_admin import auth
from firebase_admin.exceptions import FirebaseError

from app.config.logging import log
from app.models.base import UserRole
from app.models.user import User
from app.schemas.auth import (
    AccountDeletionRequest,
    ChildAccountDeletionRequest,
    FirebaseAuthToken,
    UserRegistrationComplete,
)
from app.services.firebase import FirebaseService
from app.utils.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.utils.security import verify_firebase_token


class AuthService:
    def __init__(self):
        self.firebase_service = FirebaseService()
        log.debug("AuthService initialized for Firebase Auth flow")

    async def validate_registration_data(
        self, registration_data: UserRegistrationComplete
    ) -> dict:
        """
        Validate registration data WITHOUT creating anything
        This should be called BEFORE creating Firebase Auth user
        """
        log.info("Validating registration data before Firebase user creation")

        # PREVENT ADMIN REGISTRATION
        if registration_data.role == UserRole.ADMIN:
            raise ValidationError("Admin role registration is not allowed")

        # Verify Firebase token is valid
        firebase_user_data = verify_firebase_token(registration_data.firebase_id_token)
        if not firebase_user_data:
            raise AuthenticationError("Invalid Firebase ID token")

        # Check if user already exists in our database
        existing_user = await self.firebase_service.get_user_by_firebase_uid(
            firebase_user_data.firebase_uid
        )
        if existing_user:
            raise ConflictError("User profile already exists")

        # Check username availability
        existing_username = await self.firebase_service.get_user_by_username(
            registration_data.username
        )
        if existing_username:
            raise ConflictError("Username already taken")

        # Validate child-specific requirements
        if registration_data.role == UserRole.USER:
            if not registration_data.age:
                raise ValidationError("Age is required for child users")
            if registration_data.age < 8 or registration_data.age > 14:
                raise ValidationError("Age must be between 8 and 14 for child users")
            if not registration_data.grade_level:
                raise ValidationError("Grade level is required for child users")
            if not registration_data.parent_code:
                raise ValidationError("Parent code is required for child users")

        # Verify parent code if provided
        parent_id = None
        if registration_data.role == UserRole.USER and registration_data.parent_code:
            parent_id = await self._verify_parent_code(registration_data.parent_code)

        log.success("Registration data validation passed")
        return {
            "firebase_user_data": firebase_user_data,
            "parent_id": parent_id,
            "validation_passed": True,
        }

    async def complete_registration(
        self, registration_data: UserRegistrationComplete
    ) -> User:
        """
        Complete user registration after Firebase Auth signup
        INCLUDES ENHANCED CLEANUP for any failures
        """
        log.info("Completing user registration after Firebase Auth")
        firebase_uid = None
        try:
            # First validate everything
            validation_result = await self.validate_registration_data(registration_data)
            firebase_user_data = validation_result["firebase_user_data"]
            parent_id = validation_result["parent_id"]
            firebase_uid = firebase_user_data.firebase_uid

            # Create user profile in our database
            user_doc_data = {
                "email": firebase_user_data.email,
                "firebase_uid": firebase_user_data.firebase_uid,
                "username": registration_data.username,
                "first_name": registration_data.first_name,
                "last_name": registration_data.last_name,
                "role": registration_data.role.value,
                "is_active": True,
                "is_verified": firebase_user_data.email_verified,
                "age": registration_data.age,
                "grade_level": registration_data.grade_level,
                "parent_id": parent_id,
                "children_ids": [],
                "current_skills": [],
                "completed_skills": [],
                "points": 0,
                "badges": [],
                "emergency_contacts": [],
                "preferences": {},
                "avatar_url": firebase_user_data.picture,
                "firebase_synced_at": datetime.now(timezone.utc),
            }

            log.debug("Creating user profile in Firestore")
            user_id = await self.firebase_service.create_document(
                "users", user_doc_data
            )
            log.success(f"User profile created with ID: {user_id}")

            # Update parent's children list if applicable
            if parent_id:
                await self._add_child_to_parent(parent_id, user_id)

            # Return user object
            user_doc_data["id"] = user_id
            user = User(**user_doc_data)
            log.success(
                f"User registration completed successfully: {firebase_user_data.email}"
            )
            return user

        except Exception as e:
            log.error(f"Registration completion failed: {str(e)}")
            # ENHANCED CLEANUP: Always try to cleanup Firebase Auth user if we have the UID
            if firebase_uid:
                log.warning(
                    f"🧹 CLEANUP: Registration failed, cleaning up Firebase user: {firebase_uid}"
                )
                cleanup_success = await self.cleanup_firebase_auth_user(firebase_uid)
                if cleanup_success:
                    log.success(f"✅ Firebase Auth user cleaned up: {firebase_uid}")
                else:
                    log.error(
                        f"❌ Failed to cleanup Firebase Auth user: {firebase_uid}"
                    )
            # Re-raise the original exception
            raise

    async def delete_child_account(
        self,
        user_id: str,
        deletion_request: ChildAccountDeletionRequest,
        requesting_user_id: str,
    ) -> bool:
        """
        Delete child account - requires parent code validation
        Only the child can delete their own account
        """
        log.info(f"Child account deletion request for user: {user_id}")

        # Ensure child can only delete their own account
        if user_id != requesting_user_id:
            raise AuthorizationError("Children can only delete their own accounts")

        # Get user to verify it's a child
        user_doc = await self.firebase_service.get_document("users", user_id)
        if not user_doc:
            raise NotFoundError("User not found")

        if user_doc.get("role") != UserRole.USER.value:
            raise AuthorizationError("This endpoint is only for child accounts")

        # Verify parent code
        parent_id = user_doc.get("parent_id")
        if not parent_id:
            raise ValidationError("Child account has no linked parent")

        # Verify the parent code
        await self._verify_parent_code_for_deletion(
            deletion_request.parent_code, parent_id
        )

        # Delete from Firebase Auth
        firebase_uid = user_doc.get("firebase_uid")
        if firebase_uid:
            try:
                auth.delete_user(firebase_uid)
                log.info(f"Firebase Auth user deleted: {firebase_uid}")
            except FirebaseError as e:
                log.warning(f"Failed to delete Firebase Auth user: {str(e)}")

        # Remove child from parent's children list
        await self._remove_child_from_parent(parent_id, user_id)

        # Delete user document from Firestore
        await self.firebase_service.delete_document("users", user_id)

        log.success(f"Child account deleted successfully: {user_id}")
        return True

    async def delete_parent_account(
        self,
        user_id: str,
        deletion_request: AccountDeletionRequest,
        requesting_user_id: str,
    ) -> bool:
        """
        Delete parent account - only if no children are linked
        Only the parent can delete their own account
        """
        log.info(f"Parent account deletion request for user: {user_id}")

        # Ensure parent can only delete their own account
        if user_id != requesting_user_id:
            raise AuthorizationError("Parents can only delete their own accounts")

        # Get user to verify it's a parent
        user_doc = await self.firebase_service.get_document("users", user_id)
        if not user_doc:
            raise NotFoundError("User not found")

        if user_doc.get("role") != UserRole.PARENT.value:
            raise AuthorizationError("This endpoint is only for parent accounts")

        # Check if any children are linked
        children_ids = user_doc.get("children_ids", [])
        if children_ids:
            raise ConflictError(
                f"Cannot delete parent account with {len(children_ids)} linked children. "
                "Please remove all children first or contact support."
            )

        # Delete from Firebase Auth
        firebase_uid = user_doc.get("firebase_uid")
        if firebase_uid:
            try:
                auth.delete_user(firebase_uid)
                log.info(f"Firebase Auth user deleted: {firebase_uid}")
            except FirebaseError as e:
                log.warning(f"Failed to delete Firebase Auth user: {str(e)}")

        # Delete user document from Firestore
        await self.firebase_service.delete_document("users", user_id)

        log.success(f"Parent account deleted successfully: {user_id}")
        return True

    async def cleanup_firebase_auth_user(self, firebase_uid: str) -> bool:
        """
        Delete a Firebase Auth user by UID - ENHANCED VERSION
        """
        import asyncio

        try:
            log.warning(
                f"🧹 STARTING CLEANUP: Deleting Firebase Auth user: {firebase_uid}"
            )
            # Step 1: Verify Firebase is initialized
            try:
                import firebase_admin

                firebase_admin.get_app()
                log.debug("✅ Firebase Admin SDK verified")
            except ValueError:
                log.error("❌ Firebase Admin SDK not initialized!")
                return False

            # Step 2: Wait for propagation
            log.debug("⏳ Waiting for Firebase user creation to propagate...")
            await asyncio.sleep(2)

            # Step 3: Check if user exists
            try:
                firebase_user = auth.get_user(firebase_uid)
                log.info(f"✅ Found user to delete: {firebase_user.email}")
            except FirebaseError as e:
                if "USER_NOT_FOUND" in str(e) or "user-not-found" in str(e).lower():
                    log.warning(f"👻 User already deleted: {firebase_uid}")
                    return True
                else:
                    log.error(f"❌ Error checking user: {e}")
                    return False

            # Step 4: Delete the user
            log.warning(f"🗑️ DELETING Firebase Auth user: {firebase_uid}")
            auth.delete_user(firebase_uid)

            # Step 5: Verify deletion with retries
            for attempt in range(5):
                await asyncio.sleep(1)
                try:
                    auth.get_user(firebase_uid)
                    log.warning(f"⏳ Attempt {attempt + 1}/5: User still exists...")
                    if attempt == 4:
                        log.error(
                            "❌ CLEANUP FAILED: User still exists after 5 attempts"
                        )
                        return False
                except FirebaseError as e:
                    error_msg = str(e).lower()
                    if any(
                        indicator in error_msg
                        for indicator in [
                            "user_not_found",
                            "user-not-found",
                            "no user record",
                            "user record not found",
                            "user does not exist",
                        ]
                    ):
                        log.success(f"✅ CLEANUP SUCCESS: User deleted: {firebase_uid}")
                        return True
                    else:
                        log.warning(f"⚠️ Unexpected error: {e}")
                        continue

            return False
        except Exception as e:
            log.error(f"❌ Critical cleanup error: {str(e)}")
            return False

    async def authenticate_user(self, auth_token: FirebaseAuthToken) -> User:
        """Authenticate user with Firebase ID token"""
        log.info("Authenticating user with Firebase ID token")
        firebase_user_data = verify_firebase_token(auth_token.firebase_id_token)
        if not firebase_user_data:
            raise AuthenticationError("Invalid authentication token")

        user_doc = await self.firebase_service.get_user_by_firebase_uid(
            firebase_user_data.firebase_uid
        )
        if not user_doc:
            raise AuthenticationError("User not found")

        if not user_doc.get("is_active", True):
            raise AuthenticationError("Account is deactivated")

        # Update last login
        await self.firebase_service.update_document(
            "users",
            user_doc["id"],
            {
                "last_login": datetime.now(timezone.utc),
                "is_verified": firebase_user_data.email_verified,
                "firebase_synced_at": datetime.now(timezone.utc),
            },
        )

        user = User(**user_doc)
        log.success(f"User authentication successful: {firebase_user_data.email}")
        return user

    async def sync_firebase_user_data(self, firebase_uid: str) -> User | None:
        """Sync user data from Firebase Auth to our database"""
        log.debug(f"Syncing Firebase user data: {firebase_uid}")
        try:
            firebase_user = auth.get_user(firebase_uid)
            user_doc = await self.firebase_service.get_user_by_firebase_uid(
                firebase_uid
            )
            if not user_doc:
                return None

            update_data = {
                "email": firebase_user.email,
                "is_verified": firebase_user.email_verified,
                "firebase_synced_at": datetime.now(timezone.utc),
            }

            if firebase_user.photo_url != user_doc.get("avatar_url"):
                update_data["avatar_url"] = firebase_user.photo_url

            await self.firebase_service.update_document(
                "users", user_doc["id"], update_data
            )

            updated_user_doc = await self.firebase_service.get_document(
                "users", user_doc["id"]
            )
            return User(**updated_user_doc)
        except FirebaseError as e:
            log.error(f"Failed to sync Firebase user data: {str(e)}")
            return None

    async def generate_parent_code(self, parent_id: str) -> str:
        """Generate a parent code for child registration"""
        log.info(f"Generating parent code for parent: {parent_id}")
        code = str(uuid.uuid4())[:8].upper()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        code_data = {
            "code": code,
            "parent_id": parent_id,
            "expires_at": expires_at,
            "used": False,
        }

        await self.firebase_service.create_document("parent_codes", code_data)
        log.success(f"Parent code generated: {code}")
        return code

    async def _verify_parent_code(self, code: str) -> str | None:
        """Verify parent code and return parent ID"""
        log.debug(f"Verifying parent code: {code}")
        codes = await self.firebase_service.query_documents(
            "parent_codes", "code", "==", code
        )

        if not codes:
            raise NotFoundError("Invalid parent code")

        code_doc = codes[0]

        if code_doc.get("used", False):
            raise ConflictError("Parent code already used")

        if code_doc.get("expires_at") < datetime.now(timezone.utc):
            raise ConflictError("Parent code expired")

        # Mark code as used
        await self.firebase_service.update_document(
            "parent_codes", code_doc["id"], {"used": True}
        )

        return code_doc["parent_id"]

    async def _verify_parent_code_for_deletion(
        self, code: str, expected_parent_id: str
    ) -> bool:
        """Verify parent code for account deletion - generates new temporary code"""
        log.debug(f"Verifying parent code for deletion: {code}")
        codes = await self.firebase_service.query_documents(
            "parent_codes", "code", "==", code
        )

        if not codes:
            raise NotFoundError("Invalid parent code")

        code_doc = codes[0]

        if code_doc.get("parent_id") != expected_parent_id:
            raise AuthorizationError("Parent code does not match linked parent")

        if code_doc.get("expires_at") < datetime.now(timezone.utc):
            raise ConflictError("Parent code expired")

        # Don't mark as used for deletion - parent might need to delete multiple children
        return True

    async def _add_child_to_parent(self, parent_id: str, child_id: str) -> bool:
        """Add child ID to parent's children list"""
        log.debug(f"Adding child {child_id} to parent {parent_id}")
        parent_doc = await self.firebase_service.get_document("users", parent_id)
        if not parent_doc:
            return False

        children_ids = parent_doc.get("children_ids", [])
        if child_id not in children_ids:
            children_ids.append(child_id)
            await self.firebase_service.update_document(
                "users", parent_id, {"children_ids": children_ids}
            )

        return True

    async def _remove_child_from_parent(self, parent_id: str, child_id: str) -> bool:
        """Remove child ID from parent's children list"""
        log.debug(f"Removing child {child_id} from parent {parent_id}")
        parent_doc = await self.firebase_service.get_document("users", parent_id)
        if not parent_doc:
            return False

        children_ids = parent_doc.get("children_ids", [])
        if child_id in children_ids:
            children_ids.remove(child_id)
            await self.firebase_service.update_document(
                "users", parent_id, {"children_ids": children_ids}
            )

        return True
