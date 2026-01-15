"""Tests for AI Provider Interface.

This module tests the abstract interface contract for AI providers
used in typo checking functionality.
"""

import pytest

from app.services.ai.ai_provider_interface import (
    AIProviderInterface,
    TypoIssue,
    TypoCheckResult,
)


class TestTypoIssue:
    """Tests for TypoIssue dataclass."""

    def test_typo_issue_creation(self):
        """Test creating a TypoIssue with all fields."""
        issue = TypoIssue(
            original="안녕하세요",
            corrected="안녕하세요",
            position=0,
            issue_type="spelling",
            explanation="No issue found"
        )

        assert issue.original == "안녕하세요"
        assert issue.corrected == "안녕하세요"
        assert issue.position == 0
        assert issue.issue_type == "spelling"
        assert issue.explanation == "No issue found"

    def test_typo_issue_to_dict(self):
        """Test converting TypoIssue to dictionary."""
        issue = TypoIssue(
            original="틀린글",
            corrected="틀린 글",
            position=10,
            issue_type="spacing",
            explanation="띄어쓰기 오류"
        )

        result = issue.to_dict()

        assert isinstance(result, dict)
        assert result["original"] == "틀린글"
        assert result["corrected"] == "틀린 글"
        assert result["position"] == 10
        assert result["issue_type"] == "spacing"
        assert result["explanation"] == "띄어쓰기 오류"


class TestTypoCheckResult:
    """Tests for TypoCheckResult dataclass."""

    def test_typo_check_result_creation(self):
        """Test creating a TypoCheckResult with issues."""
        issues = [
            TypoIssue(
                original="테스트",
                corrected="테스트",
                position=0,
                issue_type="none",
                explanation=""
            )
        ]

        result = TypoCheckResult(
            original_text="테스트 텍스트",
            corrected_text="테스트 텍스트",
            issues=issues,
            provider="claude",
            success=True,
            error_message=None
        )

        assert result.original_text == "테스트 텍스트"
        assert result.corrected_text == "테스트 텍스트"
        assert len(result.issues) == 1
        assert result.provider == "claude"
        assert result.success is True
        assert result.error_message is None

    def test_typo_check_result_with_error(self):
        """Test creating a TypoCheckResult with error."""
        result = TypoCheckResult(
            original_text="테스트",
            corrected_text="",
            issues=[],
            provider="claude",
            success=False,
            error_message="API rate limit exceeded"
        )

        assert result.success is False
        assert result.error_message == "API rate limit exceeded"

    def test_typo_check_result_to_dict(self):
        """Test converting TypoCheckResult to dictionary."""
        issues = [
            TypoIssue(
                original="오타",
                corrected="오타 수정",
                position=5,
                issue_type="typo",
                explanation="오타 발견"
            )
        ]

        result = TypoCheckResult(
            original_text="원본 오타 텍스트",
            corrected_text="원본 오타 수정 텍스트",
            issues=issues,
            provider="claude",
            success=True,
            error_message=None
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["original_text"] == "원본 오타 텍스트"
        assert result_dict["corrected_text"] == "원본 오타 수정 텍스트"
        assert len(result_dict["issues"]) == 1
        assert result_dict["issues"][0]["original"] == "오타"
        assert result_dict["provider"] == "claude"
        assert result_dict["success"] is True


class TestAIProviderInterface:
    """Tests for AIProviderInterface abstract class."""

    def test_interface_is_abstract(self):
        """Test that AIProviderInterface cannot be instantiated."""
        with pytest.raises(TypeError):
            AIProviderInterface()

    def test_interface_has_check_typo_method(self):
        """Test that interface defines check_typo abstract method."""
        assert hasattr(AIProviderInterface, "check_typo")
        assert callable(getattr(AIProviderInterface, "check_typo", None))

    def test_interface_has_provider_name_property(self):
        """Test that interface defines provider_name property."""
        assert hasattr(AIProviderInterface, "provider_name")

    def test_interface_has_is_available_method(self):
        """Test that interface defines is_available method."""
        assert hasattr(AIProviderInterface, "is_available")
        assert callable(getattr(AIProviderInterface, "is_available", None))


class ConcreteProvider(AIProviderInterface):
    """Concrete implementation for testing interface contract."""

    @property
    def provider_name(self) -> str:
        return "test_provider"

    def is_available(self) -> bool:
        return True

    def check_typo(self, text: str) -> TypoCheckResult:
        return TypoCheckResult(
            original_text=text,
            corrected_text=text,
            issues=[],
            provider=self.provider_name,
            success=True,
            error_message=None
        )


class TestConcreteProviderImplementation:
    """Tests for concrete provider implementation."""

    def test_concrete_provider_can_be_instantiated(self):
        """Test that concrete implementation can be created."""
        provider = ConcreteProvider()
        assert provider is not None

    def test_concrete_provider_has_provider_name(self):
        """Test concrete provider returns provider name."""
        provider = ConcreteProvider()
        assert provider.provider_name == "test_provider"

    def test_concrete_provider_is_available(self):
        """Test concrete provider availability check."""
        provider = ConcreteProvider()
        assert provider.is_available() is True

    def test_concrete_provider_check_typo_returns_result(self):
        """Test concrete provider check_typo returns TypoCheckResult."""
        provider = ConcreteProvider()
        result = provider.check_typo("테스트 텍스트")

        assert isinstance(result, TypoCheckResult)
        assert result.original_text == "테스트 텍스트"
        assert result.provider == "test_provider"
        assert result.success is True
