# app/utils/pagination.py - Simplified meta responses
from collections.abc import Callable
from datetime import datetime
from typing import Any, TypeVar

from google.cloud.firestore import FieldFilter

from app.config.logging import log
from app.schemas.base import PaginatedResponse, PaginationParams
from app.services.firebase import FirebaseService

T = TypeVar("T")


class LifeSkillsPaginator:
    """Enhanced paginator specifically designed for Life Skills App"""

    def __init__(self, firebase_service: FirebaseService):
        self.firebase_service = firebase_service
        log.debug("LifeSkillsPaginator initialized")

    async def paginate_collection(
        self,
        collection: str,
        pagination: PaginationParams,
        order_by: str = "created_at",
        order_direction: str = "desc",
        filters: list[tuple[str, str, Any]] | None = None,
        transform_func: Callable[[dict], T] | None = None,
    ) -> PaginatedResponse[T]:
        """Paginate Firebase collection with enhanced features for Life Skills App"""
        log.info(f"Paginating collection: {collection}")

        try:
            # Set defaults
            skip = pagination.skip or 0
            limit = pagination.limit or 20

            # Get total count (for small collections only)
            total_count = await self._get_efficient_count(collection, filters)

            # Build and execute query
            documents = await self._execute_paginated_query(
                collection, skip, limit, order_by, order_direction, filters
            )

            # Transform documents if function provided
            if transform_func:
                transformed_data = [transform_func(doc) for doc in documents]
            else:
                transformed_data = documents

            # Calculate pagination info
            page = (skip // limit) + 1 if limit > 0 else 1

            # Create response
            response = PaginatedResponse.success_response(
                data=transformed_data,
                total_count=total_count,
                page=page,
                page_size=limit,
                message=f"Retrieved {len(transformed_data)} items from {collection}",
            )

            log.success(f"Pagination completed: {len(transformed_data)} items returned")
            return response

        except Exception as e:
            log.error(f"Pagination failed for collection {collection}: {str(e)}")
            return PaginatedResponse.error_response(
                message=f"Failed to paginate {collection}", errors=[str(e)]
            )

    async def paginate_user_children(
        self,
        parent_id: str,
        pagination: PaginationParams,
        include_inactive: bool = False,
        order_by: str = "created_at",
    ) -> PaginatedResponse[dict]:
        """Specialized pagination for user children"""
        log.info(f"Paginating children for parent: {parent_id}")

        # Get parent document to access children_ids
        parent_doc = await self.firebase_service.get_document("users", parent_id)
        if not parent_doc:
            return PaginatedResponse.error_response(
                message="Parent not found", errors=["Invalid parent ID"]
            )

        children_ids = parent_doc.get("children_ids", [])
        if not children_ids:
            return PaginatedResponse.success_response(
                data=[], total_count=0, page=1, page_size=0, message="No children found"
            )

        # Get children documents
        children = []
        for child_id in children_ids:
            try:
                child_doc = await self.firebase_service.get_document("users", child_id)
                if child_doc:
                    if include_inactive or child_doc.get("is_active", True):
                        children.append(child_doc)
            except Exception as e:
                log.warning(f"Failed to load child {child_id}: {str(e)}")
                continue

        # Apply pagination
        skip = pagination.skip or 0
        limit = pagination.limit or len(children)
        paginated_children = children[skip : skip + limit]
        page = (skip // limit) + 1 if limit > 0 else 1

        return PaginatedResponse.success_response(
            data=paginated_children,
            total_count=len(children),
            page=page,
            page_size=len(paginated_children),
            message=f"Retrieved {len(paginated_children)} children",
        )

    async def paginate_user_activities(
        self,
        user_id: str,
        pagination: PaginationParams,
        activity_type: str | None = None,
        date_range: tuple[datetime, datetime] | None = None,
    ) -> PaginatedResponse[dict]:
        """Specialized pagination for user activities/progress"""
        log.info(f"Paginating activities for user: {user_id}")

        # Build filters
        filters = [("user_id", "==", user_id)]
        if activity_type:
            filters.append(("type", "==", activity_type))
        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [("created_at", ">=", start_date), ("created_at", "<=", end_date)]
            )

        return await self.paginate_collection(
            collection="activities",
            pagination=pagination,
            order_by="created_at",
            order_direction="desc",
            filters=filters,
        )

    async def _execute_paginated_query(
        self,
        collection: str,
        skip: int,
        limit: int,
        order_by: str,
        order_direction: str,
        filters: list[tuple[str, str, Any]] | None = None,
    ) -> list[dict]:
        """Execute paginated query against Firestore"""
        await self.firebase_service.ensure_client()

        # Build query
        query = self.firebase_service.db.collection(collection)

        # Apply filters
        if filters:
            for field, operator, value in filters:
                query = query.where(filter=FieldFilter(field, operator, value))

        # Apply ordering
        if order_direction.lower() == "desc":
            query = query.order_by(order_by, direction="DESCENDING")
        else:
            query = query.order_by(order_by, direction="ASCENDING")

        # Apply pagination
        # For large offsets, consider using cursor-based pagination
        query = query.limit(skip + limit) if skip > 0 else query.limit(limit)

        # Execute query
        docs = []
        async for doc in query.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            docs.append(data)

        # Apply skip manually (not ideal for large datasets)
        if skip > 0:
            docs = docs[skip:]

        return docs

    async def _get_efficient_count(
        self,
        collection: str,
        filters: list[tuple[str, str, Any]] | None = None,
        max_count_threshold: int = 1000,
    ) -> int:
        """Get document count efficiently, with safeguards for large collections"""
        try:
            await self.firebase_service.ensure_client()

            # Build query for counting
            query = self.firebase_service.db.collection(collection)
            if filters:
                for field, operator, value in filters:
                    query = query.where(filter=FieldFilter(field, operator, value))

            # Limit count query to prevent performance issues
            query = query.limit(max_count_threshold + 1)

            count = 0
            async for _ in query.stream():
                count += 1
                if count > max_count_threshold:
                    log.warning(f"Collection {collection} exceeds count threshold")
                    return count  # Return approximate count

            return count

        except Exception as e:
            log.error(f"Failed to count documents in {collection}: {str(e)}")
            return 0


class CursorPaginator:
    """Cursor-based pagination for better performance on large datasets"""

    def __init__(self, firebase_service: FirebaseService):
        self.firebase_service = firebase_service

    async def paginate_with_cursor(
        self,
        collection: str,
        limit: int = 20,
        cursor: str | None = None,
        order_by: str = "created_at",
        filters: list[tuple[str, str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Cursor-based pagination for large collections
        Returns: {data: [], next_cursor: str, has_more: bool}
        """
        await self.firebase_service.ensure_client()

        query = self.firebase_service.db.collection(collection)

        # Apply filters
        if filters:
            for field, operator, value in filters:
                query = query.where(filter=FieldFilter(field, operator, value))

        # Apply ordering
        query = query.order_by(order_by)

        # Apply cursor if provided
        if cursor:
            # Decode cursor (in real implementation, you'd decode a secure cursor)
            cursor_doc = await self.firebase_service.get_document(collection, cursor)
            if cursor_doc:
                query = query.start_after(cursor_doc)

        # Fetch one extra document to determine if there are more
        query = query.limit(limit + 1)

        docs = []
        async for doc in query.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            docs.append(data)

        # Check if there are more documents
        has_more = len(docs) > limit
        if has_more:
            docs = docs[:-1]  # Remove the extra document

        # Generate next cursor
        next_cursor = docs[-1]["id"] if docs and has_more else None

        return {
            "data": docs,
            "next_cursor": next_cursor,
            "has_more": has_more,
            "page_size": len(docs),
        }
