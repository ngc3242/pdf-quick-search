"""Typo Checker Service for Korean text typo checking.

This service provides the main interface for checking Korean text
for typos using various AI providers. It handles text chunking,
provider selection, result aggregation, and caching.
"""

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

from app import db
from app.models.typo_check_result import TypoCheckResult
from app.services.ai.ai_provider_interface import AIProviderInterface

logger = logging.getLogger(__name__)


# Maximum text length allowed (100K characters)
MAX_TEXT_LENGTH = 100000

# Default chunk size for splitting large texts
DEFAULT_CHUNK_SIZE = 8000


class TypoCheckerService:
    """Service for checking Korean text for typos.

    Provides text chunking, provider selection, result aggregation,
    and caching functionality.
    """

    # Registry of available providers
    _provider_registry: dict = {}

    @classmethod
    def _init_providers(cls):
        """Initialize provider registry with lazy imports."""
        if not cls._provider_registry:
            from app.services.ai.claude_provider import ClaudeProvider
            from app.services.ai.openai_provider import OpenAIProvider
            from app.services.ai.gemini_provider import GeminiProvider

            cls._provider_registry = {
                "claude": ClaudeProvider,
                "openai": OpenAIProvider,
                "gemini": GeminiProvider,
            }

    @staticmethod
    def check_text(
        text: str, user_id: str, provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check text for typos and return corrections.

        Args:
            text: Korean text to check for typos
            user_id: User ID for caching and tracking
            provider: Optional specific provider to use

        Returns:
            Dictionary containing:
                - success: Boolean indicating success
                - corrected_text: The corrected text
                - issues: List of issues found
                - provider: Provider used
                - error: Error message if failed
        """
        # Validate input
        if not text or not text.strip():
            return {
                "success": False,
                "error": "Text cannot be empty",
                "corrected_text": "",
                "issues": [],
                "provider": None,
            }

        if len(text) > MAX_TEXT_LENGTH:
            return {
                "success": False,
                "error": f"Text exceeds maximum limit of {MAX_TEXT_LENGTH} characters",
                "corrected_text": "",
                "issues": [],
                "provider": None,
            }

        # Check cache first
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        cached_result = TypoCheckResult.query.filter_by(
            user_id=user_id, original_text_hash=text_hash
        ).first()

        if cached_result:
            return {
                "success": True,
                "corrected_text": cached_result.corrected_text,
                "issues": json.loads(cached_result.issues)
                if cached_result.issues
                else [],
                "provider": cached_result.provider_used,
                "cached": True,
            }

        # Get provider
        if provider:
            ai_provider = TypoCheckerService._get_provider(provider)
            if not ai_provider or not ai_provider.is_available():
                return {
                    "success": False,
                    "error": f"Provider '{provider}' is not available",
                    "corrected_text": "",
                    "issues": [],
                    "provider": None,
                }
        else:
            ai_provider = TypoCheckerService._get_default_provider()
            if not ai_provider:
                return {
                    "success": False,
                    "error": "No AI provider is available",
                    "corrected_text": "",
                    "issues": [],
                    "provider": None,
                }

        # Chunk text if needed
        chunks = TypoCheckerService._chunk_text(text)

        # Process each chunk
        all_issues: List[Dict] = []
        corrected_chunks: List[str] = []
        current_position = 0

        for chunk in chunks:
            result = ai_provider.check_typo(chunk)

            if not result.success:
                return {
                    "success": False,
                    "error": result.error_message or "Failed to check typos",
                    "corrected_text": "",
                    "issues": [],
                    "provider": ai_provider.provider_name,
                }

            corrected_chunks.append(result.corrected_text)

            # Adjust issue positions for chunk offset
            for issue in result.issues:
                issue_dict = issue.to_dict()
                issue_dict["position"] += current_position
                all_issues.append(issue_dict)

            current_position += len(chunk)

        # Combine results
        final_corrected = "".join(corrected_chunks)
        provider_name = ai_provider.provider_name

        # If corrected text is significantly shorter than original,
        # reconstruct it by applying issues to original text
        if len(final_corrected) < len(text) * 0.5:
            logger.info(
                f"Reconstructing corrected text: original={len(text)}, "
                f"returned={len(final_corrected)}, issues={len(all_issues)}"
            )
            final_corrected = TypoCheckerService._reconstruct_corrected_text(
                text, all_issues
            )

        # Store result in database
        db_result = TypoCheckResult(
            user_id=user_id,
            original_text_hash=text_hash,
            corrected_text=final_corrected,
            issues=json.dumps(all_issues),
            provider_used=provider_name,
        )
        db.session.add(db_result)
        db.session.commit()

        return {
            "success": True,
            "corrected_text": final_corrected,
            "issues": all_issues,
            "provider": provider_name,
            "cached": False,
        }

    @staticmethod
    def get_user_history(
        user_id: str, page: int = 1, per_page: int = 20
    ) -> Dict[str, Any]:
        """Get paginated history of typo check results for a user.

        Args:
            user_id: User ID to get history for
            page: Page number (1-indexed)
            per_page: Number of results per page

        Returns:
            Dictionary containing:
                - success: Boolean indicating success
                - items: List of result dictionaries
                - total: Total number of results
                - page: Current page number
                - per_page: Results per page
                - pages: Total number of pages

        Note:
            Original text is NOT stored (only hash for caching).
            Results are ordered by created_at descending (newest first).
        """
        # Query user's results, ordered by newest first
        query = TypoCheckResult.query.filter_by(user_id=user_id).order_by(
            TypoCheckResult.created_at.desc()
        )

        # Get total count
        total = query.count()

        # Calculate pagination
        if total == 0:
            return {
                "success": True,
                "history": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
                "pages": 0,
            }

        # Calculate total pages
        pages = (total + per_page - 1) // per_page

        # Get paginated results
        offset = (page - 1) * per_page
        results = query.offset(offset).limit(per_page).all()

        # Convert to dictionaries
        items = [result.to_dict() for result in results]

        return {
            "success": True,
            "history": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }

    @staticmethod
    def delete_result(result_id: int, user_id: str) -> Dict[str, Any]:
        """Delete a typo check result.

        Args:
            result_id: ID of the result to delete
            user_id: User ID requesting the deletion (for ownership check)

        Returns:
            Dictionary containing:
                - success: Boolean indicating success
                - error: Error message if failed
        """
        # Find the result
        result = TypoCheckResult.query.filter_by(id=result_id).first()

        if not result:
            return {
                "success": False,
                "error": "Result not found",
            }

        # Check ownership
        if result.user_id != user_id:
            return {
                "success": False,
                "error": "Access denied",
            }

        # Delete the result
        db.session.delete(result)
        db.session.commit()

        return {
            "success": True,
        }

    @staticmethod
    def get_available_providers() -> List[str]:
        """Get list of available AI providers.

        Returns:
            List of provider names that are currently available
        """
        # Initialize providers
        TypoCheckerService._init_providers()

        available = []
        for name, provider_class in TypoCheckerService._provider_registry.items():
            try:
                provider = provider_class()
                is_avail = provider.is_available()
                logger.info(f"[DEBUG] Provider '{name}' is_available: {is_avail}")
                if is_avail:
                    available.append(name)
            except Exception as e:
                logger.error(f"[DEBUG] Provider '{name}' error: {e}")
                continue

        logger.info(f"[DEBUG] Available providers: {available}")
        return available

    @staticmethod
    def _get_provider(name: str) -> Optional[AIProviderInterface]:
        """Get a specific provider by name.

        Args:
            name: Provider name

        Returns:
            Provider instance or None if not found
        """
        TypoCheckerService._init_providers()
        provider_class = TypoCheckerService._provider_registry.get(name)
        if provider_class:
            try:
                return provider_class()
            except Exception:
                return None
        return None

    @staticmethod
    def _get_default_provider() -> Optional[AIProviderInterface]:
        """Get the default available provider.

        Returns:
            First available provider or None
        """
        TypoCheckerService._init_providers()
        # Try providers in order of preference
        preference_order = ["claude", "openai", "gemini"]

        for name in preference_order:
            provider = TypoCheckerService._get_provider(name)
            if provider and provider.is_available():
                return provider

        # Try any available provider
        for name in TypoCheckerService._provider_registry:
            provider = TypoCheckerService._get_provider(name)
            if provider and provider.is_available():
                return provider

        return None

    @staticmethod
    def _reconstruct_corrected_text(original_text: str, issues: List[Dict]) -> str:
        """Reconstruct corrected text by applying issues to original.

        When AI providers return truncated corrected_text, this method
        rebuilds the full corrected text by applying each issue's
        correction to the original text.

        Args:
            original_text: The original text
            issues: List of issue dictionaries with original/corrected pairs

        Returns:
            Reconstructed corrected text
        """
        if not issues:
            return original_text

        # Sort issues by position in reverse order to apply from end to start
        # This prevents position shifts from affecting subsequent replacements
        sorted_issues = sorted(
            issues,
            key=lambda x: x.get("position", 0),
            reverse=True,
        )

        result = original_text

        for issue in sorted_issues:
            original = issue.get("original", "")
            corrected = issue.get("corrected", "")
            position = issue.get("position", 0)

            if not original or original == corrected:
                continue

            # Try to find and replace at the specified position first
            if position >= 0 and position < len(result):
                # Check if the original text matches at the position
                end_pos = position + len(original)
                if result[position:end_pos] == original:
                    result = result[:position] + corrected + result[end_pos:]
                    continue

            # Fallback: find first occurrence and replace
            idx = result.find(original)
            if idx != -1:
                result = result[:idx] + corrected + result[idx + len(original) :]

        return result

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE) -> List[str]:
        """Split text into chunks for processing.

        Attempts to split at sentence boundaries when possible.

        Args:
            text: Text to split
            chunk_size: Maximum size of each chunk

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        current_pos = 0
        text_len = len(text)

        while current_pos < text_len:
            # Calculate end position
            end_pos = min(current_pos + chunk_size, text_len)

            # If not at the end, try to find a sentence boundary
            if end_pos < text_len:
                # Look for sentence endings within the last 20% of the chunk
                search_start = current_pos + int(chunk_size * 0.8)
                search_text = text[search_start:end_pos]

                # Find last sentence boundary
                best_boundary = -1
                for boundary_char in [". ", "? ", "! ", ".\n", "?\n", "!\n"]:
                    pos = search_text.rfind(boundary_char)
                    if pos > best_boundary:
                        best_boundary = pos

                if best_boundary > 0:
                    # Adjust end position to sentence boundary
                    end_pos = search_start + best_boundary + 1

            chunk = text[current_pos:end_pos]
            chunks.append(chunk)
            current_pos = end_pos

        return chunks
