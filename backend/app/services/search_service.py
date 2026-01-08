"""Search service for full-text document search."""

import re
from typing import List, Tuple, Optional

from sqlalchemy import func

from app.models import db
from app.models.document import SearchDocument
from app.models.page import SearchPage


class SearchService:
    """Service class for document search operations."""

    MIN_QUERY_LENGTH = 2
    DEFAULT_LIMIT = 50
    MAX_LIMIT = 100
    SNIPPET_CONTEXT_LENGTH = 100

    @staticmethod
    def search(
        user_id: str,
        query: str,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0
    ) -> Tuple[List[dict], int]:
        """Search documents for matching content.

        Uses ILIKE for case-insensitive matching on content_normalized.
        Only returns documents owned by the specified user.

        Args:
            user_id: ID of the user performing the search
            query: Search query string
            limit: Maximum number of results (default 50, max 100)
            offset: Number of results to skip

        Returns:
            Tuple of (list of result dicts, total count)
        """
        # Validate query length
        if not query or len(query) < SearchService.MIN_QUERY_LENGTH:
            return [], 0

        # Normalize query for searching
        query_normalized = query.lower().strip()

        # Limit the limit
        limit = min(limit, SearchService.MAX_LIMIT)

        # Build the base query
        # Join SearchPage with SearchDocument and filter by owner
        base_query = (
            db.session.query(SearchPage, SearchDocument)
            .join(SearchDocument, SearchPage.document_id == SearchDocument.id)
            .filter(SearchDocument.owner_id == user_id)
            .filter(SearchDocument.extraction_status == "completed")
            .filter(SearchPage.content_normalized.ilike(f"%{query_normalized}%"))
        )

        # Get total count
        total = base_query.count()

        # Get paginated results
        results = base_query.offset(offset).limit(limit).all()

        # Build response
        search_results = []
        seen_documents = set()

        for page, document in results:
            # Avoid duplicate documents in results
            if document.id in seen_documents:
                continue
            seen_documents.add(document.id)

            snippet = SearchService.generate_snippet(
                page.content or "",
                query
            )

            search_results.append({
                "document": document.to_dict(),
                "page_number": page.page_number,
                "snippet": snippet
            })

        return search_results, total

    @staticmethod
    def generate_snippet(
        content: str,
        query: str,
        context_length: int = SNIPPET_CONTEXT_LENGTH
    ) -> str:
        """Generate a snippet with context around the search term.

        Args:
            content: Full page content
            query: Search query to find
            context_length: Number of characters of context on each side

        Returns:
            Snippet string with context around the match
        """
        if not content:
            return ""

        query_lower = query.lower()
        content_lower = content.lower()

        # Find the first occurrence of the query
        match_index = content_lower.find(query_lower)

        if match_index == -1:
            # Query not found, return truncated content
            return content[:context_length * 2] + "..." if len(content) > context_length * 2 else content

        # Calculate start and end positions for context
        start = max(0, match_index - context_length)
        end = min(len(content), match_index + len(query) + context_length)

        # Build snippet
        snippet = content[start:end]

        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet
