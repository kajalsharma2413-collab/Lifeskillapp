# app/services/firebase.py
from datetime import datetime, timezone
from typing import Any

from firebase_admin import firestore_async

from app.config.firebase import initialize_firebase
from app.config.logging import log


class FirebaseService:
    def __init__(self):
        self.db = None
        log.debug("FirebaseService initialized (async client will be set on first use)")

    async def ensure_client(self):
        """Ensure async client is initialized"""
        if self.db is None:
            self.db = await initialize_firebase()
            log.debug("Async Firestore client initialized")

    async def create_document(
        self, collection: str, data: dict[str, Any], doc_id: str | None = None
    ) -> str:
        """Create a new document in Firestore using async operations"""
        await self.ensure_client()
        log.debug(f"Creating document in collection: {collection}")

        data["created_at"] = datetime.now(timezone.utc)
        data["updated_at"] = datetime.now(timezone.utc)

        try:
            if doc_id:
                log.debug(f"Creating document with custom ID: {doc_id}")
                doc_ref = self.db.collection(collection).document(doc_id)
                await doc_ref.set(data)
                log.success(f"Document created successfully: {collection}/{doc_id}")
                return doc_id
            else:
                log.debug("Creating document with auto-generated ID")
                doc_ref = self.db.collection(collection)
                _, doc_ref = await doc_ref.add(data)
                document_id = doc_ref.id
                log.success(
                    f"Document created successfully: {collection}/{document_id}"
                )
                return document_id
        except Exception as e:
            log.error(f"Failed to create document in {collection}: {str(e)}")
            raise

    async def get_document(self, collection: str, doc_id: str) -> dict[str, Any] | None:
        """Get a document by ID using async operations"""
        await self.ensure_client()
        log.debug(f"Retrieving document: {collection}/{doc_id}")

        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc = await doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                data["id"] = doc.id
                log.debug(f"Document retrieved successfully: {collection}/{doc_id}")
                return data
            else:
                log.warning(f"Document not found: {collection}/{doc_id}")
                return None
        except Exception as e:
            log.error(f"Failed to retrieve document {collection}/{doc_id}: {str(e)}")
            raise

    async def update_document(
        self, collection: str, doc_id: str, data: dict[str, Any]
    ) -> bool:
        """Update a document using async operations"""
        await self.ensure_client()
        log.debug(f"Updating document: {collection}/{doc_id}")

        data["updated_at"] = datetime.now(timezone.utc)

        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            await doc_ref.update(data)
            log.success(f"Document updated successfully: {collection}/{doc_id}")
            return True
        except Exception as e:
            log.error(f"Failed to update document {collection}/{doc_id}: {str(e)}")
            raise

    async def delete_document(self, collection: str, doc_id: str) -> bool:
        """Delete a document using async operations"""
        await self.ensure_client()
        log.info(f"Deleting document: {collection}/{doc_id}")

        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            await doc_ref.delete()
            log.success(f"Document deleted successfully: {collection}/{doc_id}")
            return True
        except Exception as e:
            log.error(f"Failed to delete document {collection}/{doc_id}: {str(e)}")
            raise

    async def query_documents(
        self, collection: str, field: str, operator: str, value: Any
    ) -> list[dict[str, Any]]:
        """Query documents with a single condition using async operations"""
        await self.ensure_client()
        log.debug(f"Querying collection {collection}: {field} {operator} {value}")
        try:
            from google.cloud.firestore import FieldFilter

            query = self.db.collection(collection).where(
                filter=FieldFilter(field, operator, value)
            )
            docs = query.stream()
            results = []
            async for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                results.append(data)
            log.debug(
                f"Query completed - {len(results)} documents found in {collection}"
            )
            return results
        except Exception as e:
            log.error(f"Failed to query collection {collection}: {str(e)}")
            raise

    async def batch_create_documents(
        self, collection: str, documents: list[dict[str, Any]]
    ) -> list[str]:
        """Create multiple documents in a batch operation"""
        await self.ensure_client()
        log.debug(
            f"Creating {len(documents)} documents in batch for collection: {collection}"
        )

        try:
            batch = self.db.batch()
            doc_ids = []

            for doc_data in documents:
                doc_data["created_at"] = datetime.now(timezone.utc)
                doc_data["updated_at"] = datetime.now(timezone.utc)
                doc_ref = self.db.collection(collection).document()
                batch.set(doc_ref, doc_data)
                doc_ids.append(doc_ref.id)

            await batch.commit()
            log.success(f"Batch created {len(documents)} documents successfully")
            return doc_ids
        except Exception as e:
            log.error(f"Failed to batch create documents in {collection}: {str(e)}")
            raise

    async def transaction_update(
        self, collection: str, doc_id: str, update_func, *args, **kwargs
    ) -> Any:
        """Perform a transaction update"""
        await self.ensure_client()
        log.debug(f"Starting transaction for document: {collection}/{doc_id}")

        @firestore_async.transactional
        async def update_in_transaction(transaction):
            doc_ref = self.db.collection(collection).document(doc_id)
            doc = await doc_ref.get(transaction=transaction)

            if not doc.exists:
                raise ValueError(f"Document {collection}/{doc_id} does not exist")

            current_data = doc.to_dict()
            updated_data = update_func(current_data, *args, **kwargs)
            updated_data["updated_at"] = datetime.now(timezone.utc)
            transaction.update(doc_ref, updated_data)
            return updated_data

        try:
            result = await update_in_transaction(self.db.transaction())
            log.success(f"Transaction completed for document: {collection}/{doc_id}")
            return result
        except Exception as e:
            log.error(
                f"Transaction failed for document {collection}/{doc_id}: {str(e)}"
            )
            raise

    # Firebase Auth specific methods

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Get user by email using async operations"""
        log.debug(f"Looking up user by email: {email}")
        users = await self.query_documents("users", "email", "==", email)
        result = users[0] if users else None

        if result:
            log.debug(f"User found by email: {email}")
        else:
            log.debug(f"No user found with email: {email}")
        return result

    async def get_user_by_firebase_uid(
        self, firebase_uid: str
    ) -> dict[str, Any] | None:
        """Get user by Firebase UID - primary lookup method for Firebase Auth"""
        log.debug(f"Looking up user by Firebase UID: {firebase_uid}")
        users = await self.query_documents("users", "firebase_uid", "==", firebase_uid)
        result = users[0] if users else None

        if result:
            log.debug(f"User found by Firebase UID: {firebase_uid}")
        else:
            log.debug(f"No user found with Firebase UID: {firebase_uid}")
        return result

    async def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        """Get user by username using async operations"""
        log.debug(f"Looking up user by username: {username}")
        users = await self.query_documents("users", "username", "==", username)
        result = users[0] if users else None

        if result:
            log.debug(f"User found by username: {username}")
        else:
            log.debug(f"No user found with username: {username}")
        return result
