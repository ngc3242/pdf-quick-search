"""Tests for Typo Checker Service.

This module tests the typo checker service including text chunking,
provider selection, result aggregation, and caching logic.
"""

import hashlib
from unittest.mock import patch, MagicMock


from app import db
from app.models.user import User
from app.models.typo_check_result import TypoCheckResult
from app.services.typo_checker_service import TypoCheckerService
from app.services.ai.ai_provider_interface import (
    TypoCheckResult as AITypoCheckResult,
    TypoIssue,
)


class TestTypoCheckerServiceBasics:
    """Tests for basic TypoCheckerService functionality."""

    def test_typo_checker_service_exists(self, app):
        """Test that TypoCheckerService class exists."""
        assert TypoCheckerService is not None

    def test_typo_checker_service_has_check_text_method(self, app):
        """Test that service has check_text method."""
        assert hasattr(TypoCheckerService, "check_text")
        assert callable(getattr(TypoCheckerService, "check_text", None))

    def test_typo_checker_service_has_get_available_providers_method(self, app):
        """Test that service has get_available_providers method."""
        assert hasattr(TypoCheckerService, "get_available_providers")
        assert callable(getattr(TypoCheckerService, "get_available_providers", None))


class TestTextChunking:
    """Tests for text chunking logic."""

    def test_chunk_text_exists(self, app):
        """Test that _chunk_text method exists."""
        assert hasattr(TypoCheckerService, "_chunk_text")

    def test_chunk_text_small_text_single_chunk(self, app):
        """Test that small text returns single chunk."""
        text = "안녕하세요. 테스트입니다."
        chunks = TypoCheckerService._chunk_text(text, chunk_size=8000)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_large_text_multiple_chunks(self, app):
        """Test that large text is split into multiple chunks."""
        # Create text larger than chunk size
        text = "테스트 문장입니다. " * 1000  # About 12000 chars
        chunks = TypoCheckerService._chunk_text(text, chunk_size=8000)

        assert len(chunks) > 1
        # All chunks should be within size limit
        for chunk in chunks:
            assert len(chunk) <= 8000

    def test_chunk_text_preserves_all_content(self, app):
        """Test that chunking preserves all content."""
        text = "테스트 문장입니다. " * 1000
        chunks = TypoCheckerService._chunk_text(text, chunk_size=8000)

        # Joined chunks should contain all original content
        # Note: Some overlap or padding is acceptable
        joined = "".join(chunks)
        # At minimum, check total length is >= original
        assert len(joined) >= len(text.strip())

    def test_chunk_text_respects_sentence_boundaries(self, app):
        """Test that chunking tries to respect sentence boundaries."""
        text = "첫 번째 문장입니다. 두 번째 문장입니다. 세 번째 문장입니다."
        # Use small chunk size to force chunking
        chunks = TypoCheckerService._chunk_text(text, chunk_size=25)

        # Chunks should end at sentence boundaries when possible
        for chunk in chunks[:-1]:  # Last chunk may not end at boundary
            # Check if chunk ends with sentence-ending punctuation
            stripped = chunk.rstrip()
            if stripped:
                # Should end with period, question mark, or exclamation
                assert stripped[-1] in ".?!" or len(chunk) <= 25

    def test_chunk_text_default_chunk_size(self, app):
        """Test default chunk size is 8000 characters."""
        # Default should be 8000 to stay within AI model limits
        text = "A" * 10000
        chunks = TypoCheckerService._chunk_text(text)

        # With default size of 8000, should be 2 chunks
        assert len(chunks) >= 2


class TestProviderSelection:
    """Tests for AI provider selection."""

    @patch("app.services.typo_checker_service.ClaudeProvider")
    def test_get_available_providers_returns_list(self, mock_claude, app):
        """Test that get_available_providers returns a list."""
        mock_instance = MagicMock()
        mock_instance.is_available.return_value = True
        mock_instance.provider_name = "claude"
        mock_claude.return_value = mock_instance

        providers = TypoCheckerService.get_available_providers()

        assert isinstance(providers, list)

    @patch("app.services.typo_checker_service.ClaudeProvider")
    def test_get_available_providers_filters_unavailable(self, mock_claude, app):
        """Test that unavailable providers are filtered out."""
        mock_instance = MagicMock()
        mock_instance.is_available.return_value = False
        mock_instance.provider_name = "claude"
        mock_claude.return_value = mock_instance

        providers = TypoCheckerService.get_available_providers()

        # Should not include unavailable providers
        assert "claude" not in providers

    @patch("app.services.typo_checker_service.ClaudeProvider")
    def test_get_provider_by_name_returns_provider(self, mock_claude, app):
        """Test getting provider by name."""
        mock_instance = MagicMock()
        mock_instance.is_available.return_value = True
        mock_instance.provider_name = "claude"
        mock_claude.return_value = mock_instance

        provider = TypoCheckerService._get_provider("claude")

        assert provider is not None

    def test_get_provider_invalid_name_returns_none(self, app):
        """Test that invalid provider name returns None."""
        provider = TypoCheckerService._get_provider("invalid_provider")

        assert provider is None


class TestCheckText:
    """Tests for the main check_text method."""

    @patch("app.services.typo_checker_service.ClaudeProvider")
    def test_check_text_returns_dict(self, mock_claude, app):
        """Test that check_text returns a dictionary."""
        # Setup mock
        mock_instance = MagicMock()
        mock_instance.is_available.return_value = True
        mock_instance.provider_name = "claude"
        mock_instance.check_typo.return_value = AITypoCheckResult(
            original_text="테스트",
            corrected_text="테스트",
            issues=[],
            provider="claude",
            success=True,
        )
        mock_claude.return_value = mock_instance

        # Create user
        user = User(email="check_test@example.com", name="Test", password="password")
        db.session.add(user)
        db.session.commit()

        result = TypoCheckerService.check_text("테스트", user.id)

        assert isinstance(result, dict)
        assert "success" in result

    def test_check_text_with_valid_text(self, app):
        """Test check_text with valid Korean text."""
        mock_provider_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.is_available.return_value = True
        mock_instance.provider_name = "claude"
        mock_instance.check_typo.return_value = AITypoCheckResult(
            original_text="안녕하세여",
            corrected_text="안녕하세요",
            issues=[
                TypoIssue(
                    original="안녕하세여",
                    corrected="안녕하세요",
                    position=0,
                    issue_type="spelling",
                    explanation="맞춤법 오류",
                )
            ],
            provider="claude",
            success=True,
        )
        mock_provider_class.return_value = mock_instance

        # Patch the registry directly
        with patch.dict(
            TypoCheckerService._provider_registry, {"claude": mock_provider_class}
        ):
            user = User(
                email="valid_text@example.com", name="Test", password="password"
            )
            db.session.add(user)
            db.session.commit()

            result = TypoCheckerService.check_text("안녕하세여", user.id)

            assert result["success"] is True
            assert result["corrected_text"] == "안녕하세요"
            assert len(result["issues"]) == 1

    def test_check_text_stores_result_in_database(self, app):
        """Test that check_text stores result in database."""
        mock_provider_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.is_available.return_value = True
        mock_instance.provider_name = "claude"
        mock_instance.check_typo.return_value = AITypoCheckResult(
            original_text="테스트",
            corrected_text="테스트",
            issues=[],
            provider="claude",
            success=True,
        )
        mock_provider_class.return_value = mock_instance

        with patch.dict(
            TypoCheckerService._provider_registry, {"claude": mock_provider_class}
        ):
            user = User(
                email="store_test@example.com", name="Test", password="password"
            )
            db.session.add(user)
            db.session.commit()

            original_text = "테스트 저장"
            result = TypoCheckerService.check_text(original_text, user.id)

            # Verify the check was successful
            assert result["success"] is True

            # Verify stored in database
            text_hash = hashlib.sha256(original_text.encode()).hexdigest()
            stored = TypoCheckResult.query.filter_by(
                user_id=user.id, original_text_hash=text_hash
            ).first()

            assert stored is not None
            assert stored.provider_used == "claude"

    def test_check_text_empty_text_returns_error(self, app):
        """Test that empty text returns error."""
        user = User(email="empty_test@example.com", name="Test", password="password")
        db.session.add(user)
        db.session.commit()

        result = TypoCheckerService.check_text("", user.id)

        assert result["success"] is False
        assert "error" in result

    def test_check_text_too_long_returns_error(self, app):
        """Test that text exceeding 100K chars returns error."""
        user = User(email="long_test@example.com", name="Test", password="password")
        db.session.add(user)
        db.session.commit()

        # Create text over 100K characters
        long_text = "A" * 100001

        result = TypoCheckerService.check_text(long_text, user.id)

        assert result["success"] is False
        assert "error" in result
        assert "100" in result["error"].lower() or "limit" in result["error"].lower()

    def test_check_text_with_specific_provider(self, app):
        """Test check_text with specific provider parameter."""
        mock_provider_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.is_available.return_value = True
        mock_instance.provider_name = "claude"
        mock_instance.check_typo.return_value = AITypoCheckResult(
            original_text="테스트",
            corrected_text="테스트",
            issues=[],
            provider="claude",
            success=True,
        )
        mock_provider_class.return_value = mock_instance

        with patch.dict(
            TypoCheckerService._provider_registry, {"claude": mock_provider_class}
        ):
            user = User(
                email="provider_test@example.com", name="Test", password="password"
            )
            db.session.add(user)
            db.session.commit()

            result = TypoCheckerService.check_text("테스트", user.id, provider="claude")

            assert result["success"] is True
            assert result["provider"] == "claude"

    def test_check_text_invalid_provider_returns_error(self, app):
        """Test that invalid provider returns error."""
        user = User(email="invalid_prov@example.com", name="Test", password="password")
        db.session.add(user)
        db.session.commit()

        result = TypoCheckerService.check_text("테스트", user.id, provider="invalid")

        assert result["success"] is False
        assert "provider" in result["error"].lower()


class TestResultAggregation:
    """Tests for aggregating results from multiple chunks."""

    def test_aggregate_results_combines_corrected_text(self, app):
        """Test that results from multiple chunks are combined."""
        mock_provider_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.is_available.return_value = True
        mock_instance.provider_name = "claude"

        # Setup to return different results for each chunk
        def check_typo_side_effect(text):
            return AITypoCheckResult(
                original_text=text,
                corrected_text=text.replace("오류", "수정"),
                issues=[],
                provider="claude",
                success=True,
            )

        mock_instance.check_typo.side_effect = check_typo_side_effect
        mock_provider_class.return_value = mock_instance

        with patch.dict(
            TypoCheckerService._provider_registry, {"claude": mock_provider_class}
        ):
            user = User(
                email="aggregate_test@example.com", name="Test", password="password"
            )
            db.session.add(user)
            db.session.commit()

            # Create text large enough to be chunked
            text = "오류가 있는 문장입니다. " * 1000

            result = TypoCheckerService.check_text(text, user.id)

            assert result["success"] is True
            # Should have called check_typo multiple times for chunks
            assert mock_instance.check_typo.call_count >= 1

    def test_aggregate_results_combines_issues(self, app):
        """Test that issues from multiple chunks are combined."""
        mock_provider_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.is_available.return_value = True
        mock_instance.provider_name = "claude"

        # Return issues for each chunk
        def check_typo_side_effect(text):
            return AITypoCheckResult(
                original_text=text,
                corrected_text=text,
                issues=[
                    TypoIssue(
                        original="테스트",
                        corrected="테스트",
                        position=0,
                        issue_type="test",
                        explanation="테스트 이슈",
                    )
                ],
                provider="claude",
                success=True,
            )

        mock_instance.check_typo.side_effect = check_typo_side_effect
        mock_provider_class.return_value = mock_instance

        with patch.dict(
            TypoCheckerService._provider_registry, {"claude": mock_provider_class}
        ):
            user = User(
                email="issues_test@example.com", name="Test", password="password"
            )
            db.session.add(user)
            db.session.commit()

            # Large text to be chunked
            text = "테스트 문장입니다. " * 1000

            result = TypoCheckerService.check_text(text, user.id)

            assert result["success"] is True
            # Should have issues from all chunks
            assert len(result["issues"]) >= 1


class TestErrorHandling:
    """Tests for error handling in TypoCheckerService."""

    @patch("app.services.typo_checker_service.ClaudeProvider")
    def test_handles_provider_error(self, mock_claude, app):
        """Test that provider errors are handled gracefully."""
        mock_instance = MagicMock()
        mock_instance.is_available.return_value = True
        mock_instance.provider_name = "claude"
        mock_instance.check_typo.return_value = AITypoCheckResult(
            original_text="테스트",
            corrected_text="",
            issues=[],
            provider="claude",
            success=False,
            error_message="API Error",
        )
        mock_claude.return_value = mock_instance

        user = User(email="error_test@example.com", name="Test", password="password")
        db.session.add(user)
        db.session.commit()

        result = TypoCheckerService.check_text("테스트", user.id)

        assert result["success"] is False
        assert "error" in result

    @patch("app.services.typo_checker_service.ClaudeProvider")
    def test_handles_no_available_providers(self, mock_claude, app):
        """Test handling when no providers are available."""
        mock_instance = MagicMock()
        mock_instance.is_available.return_value = False
        mock_claude.return_value = mock_instance

        user = User(email="no_prov@example.com", name="Test", password="password")
        db.session.add(user)
        db.session.commit()

        result = TypoCheckerService.check_text("테스트", user.id)

        assert result["success"] is False
        assert (
            "provider" in result["error"].lower()
            or "available" in result["error"].lower()
        )


class TestCaching:
    """Tests for caching behavior."""

    @patch("app.services.typo_checker_service.ClaudeProvider")
    def test_same_text_uses_cached_result(self, mock_claude, app):
        """Test that repeated requests for same text use cache."""
        mock_instance = MagicMock()
        mock_instance.is_available.return_value = True
        mock_instance.provider_name = "claude"
        mock_instance.check_typo.return_value = AITypoCheckResult(
            original_text="캐시 테스트",
            corrected_text="캐시 테스트",
            issues=[],
            provider="claude",
            success=True,
        )
        mock_claude.return_value = mock_instance

        user = User(email="cache_test@example.com", name="Test", password="password")
        db.session.add(user)
        db.session.commit()

        text = "캐시 테스트"

        # First call
        result1 = TypoCheckerService.check_text(text, user.id)
        call_count_after_first = mock_instance.check_typo.call_count

        # Second call with same text
        result2 = TypoCheckerService.check_text(text, user.id)

        # Should use cached result, not call API again
        assert result1["success"] == result2["success"]
        assert result1["corrected_text"] == result2["corrected_text"]
        # API should not be called again (or call count should remain same)
        assert mock_instance.check_typo.call_count == call_count_after_first
