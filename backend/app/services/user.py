# app/services/user.py
from app.config.logging import log
from app.models.base import UserRole
from app.models.user import User
from app.schemas.user import UserUpdate
from app.services.firebase import FirebaseService
from app.utils.exceptions import AuthorizationError, NotFoundError, ValidationError


class UserService:
    def __init__(self):
        self.firebase_service = FirebaseService()
        log.debug("UserService initialized")

    async def get_user_by_id(self, user_id: str) -> User:
        """Get user by ID"""
        log.debug(f"Fetching user by ID: {user_id}")
        user_doc = await self.firebase_service.get_document("users", user_id)
        if not user_doc:
            log.warning(f"User not found: {user_id}")
            raise NotFoundError("User not found")

        log.debug(f"User retrieved successfully: {user_id}")
        return User(**user_doc)

    async def get_user_by_firebase_uid(self, firebase_uid: str) -> User | None:
        """Get user by Firebase UID - primary method for Firebase Auth"""
        log.debug(f"Fetching user by Firebase UID: {firebase_uid}")
        user_doc = await self.firebase_service.get_user_by_firebase_uid(firebase_uid)
        if not user_doc:
            log.warning(f"User not found by Firebase UID: {firebase_uid}")
            return None

        log.debug(f"User retrieved successfully by Firebase UID: {firebase_uid}")
        return User(**user_doc)

    async def get_user_profile(
        self, user_id: str, requesting_user_id: str, requesting_user_role: UserRole
    ) -> User:
        """Get user profile with authorization check"""
        log.info(
            f"Profile access request - Target: {user_id}, Requester: {requesting_user_id}, Role: {requesting_user_role}"
        )

        user = await self.get_user_by_id(user_id)

        # Authorization checks
        if requesting_user_id == user_id:
            # Users can always view their own profile
            log.debug("Self-profile access granted")
            return user
        elif requesting_user_role == UserRole.ADMIN:
            # Admins can view any profile
            log.debug("Admin profile access granted")
            return user
        elif requesting_user_role == UserRole.PARENT:
            # Parents can view their children's profiles
            children = await self._get_user_children(requesting_user_id)
            if user_id in children:
                log.debug("Parent-child profile access granted")
                return user
            else:
                log.warning(
                    f"Unauthorized profile access attempt - Parent {requesting_user_id} trying to access {user_id}"
                )
                raise AuthorizationError("Not authorized to view this profile")
        else:
            log.warning(
                f"Unauthorized profile access attempt - User {requesting_user_id} trying to access {user_id}"
            )
            raise AuthorizationError("Not authorized to view this profile")

    # app/services/user.py - Updated update_user_profile method
    async def update_user_profile(
        self,
        user_id: str,
        update_data: UserUpdate,
        requesting_user_id: str,
        requesting_user_role: UserRole,
    ) -> User:
        """Update user profile with authorization check - ADMIN PROFILES CANNOT BE UPDATED"""
        log.info(
            f"Profile update request - Target: {user_id}, Requester: {requesting_user_id}, Role: {requesting_user_role}"
        )

        # Get target user to check role
        target_user = await self.get_user_by_id(user_id)

        # PREVENT ADMIN PROFILE UPDATES
        if target_user.role == UserRole.ADMIN:
            log.warning(f"Attempted to update admin profile: {user_id}")
            raise ValidationError("Admin profiles cannot be updated")

        # Authorization check
        if requesting_user_id != user_id and requesting_user_role != UserRole.ADMIN:
            if requesting_user_role == UserRole.PARENT:
                children = await self._get_user_children(requesting_user_id)
                if user_id not in children:
                    log.warning(
                        f"Unauthorized profile update attempt - Parent {requesting_user_id} trying to update {user_id}"
                    )
                    raise AuthorizationError("Not authorized to update this profile")
            else:
                log.warning(
                    f"Unauthorized profile update attempt - User {requesting_user_id} trying to update {user_id}"
                )
                raise AuthorizationError("Not authorized to update this profile")

        # Prepare update data with role-based field validation
        update_dict = update_data.dict(exclude_unset=True)

        # PREVENT AGE/GRADE UPDATES FOR NON-CHILDREN
        if target_user.role != UserRole.USER:
            restricted_fields = []
            if "age" in update_dict:
                del update_dict["age"]
                restricted_fields.append("age")
            if "grade_level" in update_dict:
                del update_dict["grade_level"]
                restricted_fields.append("grade_level")

            if restricted_fields:
                log.warning(
                    f"Removed restricted fields {restricted_fields} from {target_user.role.value} profile update"
                )

        log.debug(
            f"Updating profile for user {user_id} with data: {list(update_dict.keys())}"
        )

        # Update user document
        await self.firebase_service.update_document("users", user_id, update_dict)
        log.success(f"Profile updated successfully for user: {user_id}")

        # Return updated user
        return await self.get_user_by_id(user_id)

    async def get_user_children(self, parent_id: str) -> list[User]:
        """Get all children for a parent"""
        log.info(f"Fetching children for parent: {parent_id}")
        parent_doc = await self.firebase_service.get_document("users", parent_id)
        if not parent_doc:
            log.error(f"Parent not found: {parent_id}")
            raise NotFoundError("Parent not found")

        children_ids = parent_doc.get("children_ids", [])
        log.debug(f"Found {len(children_ids)} children IDs for parent {parent_id}")

        children = []
        for child_id in children_ids:
            try:
                child = await self.get_user_by_id(child_id)
                children.append(child)
                log.debug(f"Child loaded successfully: {child_id}")
            except NotFoundError:
                # Child document not found, skip
                log.warning(f"Child document not found, skipping: {child_id}")
                continue

        log.success(f"Retrieved {len(children)} children for parent {parent_id}")
        return children

    async def _get_user_children(self, parent_id: str) -> list[str]:
        """Get list of children IDs for a parent"""
        log.debug(f"Getting children IDs for parent: {parent_id}")
        parent_doc = await self.firebase_service.get_document("users", parent_id)
        children_ids = parent_doc.get("children_ids", []) if parent_doc else []
        log.debug(f"Found {len(children_ids)} children for parent {parent_id}")
        return children_ids
