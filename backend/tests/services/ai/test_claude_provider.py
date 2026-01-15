"""Tests for Claude AI Provider implementation.

This module tests the Claude provider for Korean typo checking,
including API interactions, error handling, and response parsing.
"""

from unittest.mock import patch, MagicMock
import json

from app.services.ai.claude_provider import ClaudeProvider
from app.services.ai.ai_provider_interface import (
    AIProviderInterface,
    TypoCheckResult,
)


class TestClaudeProviderBasics:
    """Tests for basic ClaudeProvider functionality."""

    def test_claude_provider_implements_interface(self):
        """Test that ClaudeProvider implements AIProviderInterface."""
        assert issubclass(ClaudeProvider, AIProviderInterface)

    def test_claude_provider_instantiation_without_api_key(self):
        """Test ClaudeProvider can be instantiated without API key."""
        with patch.dict("os.environ", {}, clear=True):
            provider = ClaudeProvider()
            assert provider is not None

    def test_claude_provider_instantiation_with_api_key(self):
        """Test ClaudeProvider instantiation with API key."""
        provider = ClaudeProvider(api_key="test-api-key")
        assert provider is not None

    def test_provider_name_is_claude(self):
        """Test that provider name is 'claude'."""
        provider = ClaudeProvider(api_key="test-key")
        assert provider.provider_name == "claude"


class TestClaudeProviderAvailability:
    """Tests for ClaudeProvider availability checking."""

    def test_is_available_returns_true_with_api_key(self):
        """Test is_available returns True when API key is set."""
        provider = ClaudeProvider(api_key="test-api-key")
        assert provider.is_available() is True

    def test_is_available_returns_false_without_api_key(self):
        """Test is_available returns False when API key is not set."""
        with patch.dict("os.environ", {}, clear=True):
            provider = ClaudeProvider(api_key=None)
            assert provider.is_available() is False

    def test_is_available_with_env_variable(self):
        """Test is_available uses environment variable."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-api-key"}):
            provider = ClaudeProvider()
            assert provider.is_available() is True


class TestClaudeProviderCheckTypo:
    """Tests for ClaudeProvider check_typo method."""

    @patch("app.services.ai.claude_provider.Anthropic")
    def test_check_typo_returns_typo_check_result(self, mock_anthropic_class):
        """Test check_typo returns TypoCheckResult."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text=json.dumps({"corrected_text": "안녕하세요", "issues": []}))
        ]
        mock_client.messages.create.return_value = mock_response

        provider = ClaudeProvider(api_key="test-key")
        result = provider.check_typo("안녕하세요")

        assert isinstance(result, TypoCheckResult)
        assert result.success is True

    @patch("app.services.ai.claude_provider.Anthropic")
    def test_check_typo_with_typo_text(self, mock_anthropic_class):
        """Test check_typo correctly processes text with typos."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "corrected_text": "안녕하세요 반갑습니다",
                        "issues": [
                            {
                                "original": "안녕하세여",
                                "corrected": "안녕하세요",
                                "position": 0,
                                "issue_type": "spelling",
                                "explanation": "맞춤법 오류: '세여' -> '세요'",
                            }
                        ],
                    }
                )
            )
        ]
        mock_client.messages.create.return_value = mock_response

        provider = ClaudeProvider(api_key="test-key")
        result = provider.check_typo("안녕하세여 반갑습니다")

        assert result.success is True
        assert result.corrected_text == "안녕하세요 반갑습니다"
        assert len(result.issues) == 1
        assert result.issues[0].original == "안녕하세여"
        assert result.issues[0].corrected == "안녕하세요"

    @patch("app.services.ai.claude_provider.Anthropic")
    def test_check_typo_preserves_original_text(self, mock_anthropic_class):
        """Test that original text is preserved in result."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text=json.dumps({"corrected_text": "테스트", "issues": []}))
        ]
        mock_client.messages.create.return_value = mock_response

        provider = ClaudeProvider(api_key="test-key")
        original = "테스트"
        result = provider.check_typo(original)

        assert result.original_text == original

    @patch("app.services.ai.claude_provider.Anthropic")
    def test_check_typo_sets_provider_name(self, mock_anthropic_class):
        """Test that provider name is set in result."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text=json.dumps({"corrected_text": "테스트", "issues": []}))
        ]
        mock_client.messages.create.return_value = mock_response

        provider = ClaudeProvider(api_key="test-key")
        result = provider.check_typo("테스트")

        assert result.provider == "claude"


class TestClaudeProviderErrorHandling:
    """Tests for ClaudeProvider error handling."""

    @patch("app.services.ai.claude_provider.Anthropic")
    def test_check_typo_handles_api_error(self, mock_anthropic_class):
        """Test check_typo handles API errors gracefully."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API Error")

        provider = ClaudeProvider(api_key="test-key")
        result = provider.check_typo("테스트")

        assert result.success is False
        assert result.error_message is not None
        assert "API Error" in result.error_message

    @patch("app.services.ai.claude_provider.Anthropic")
    def test_check_typo_handles_invalid_json_response(self, mock_anthropic_class):
        """Test check_typo handles invalid JSON in response."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="not valid json")]
        mock_client.messages.create.return_value = mock_response

        provider = ClaudeProvider(api_key="test-key")
        result = provider.check_typo("테스트")

        assert result.success is False
        assert result.error_message is not None

    @patch("app.services.ai.claude_provider.Anthropic")
    def test_check_typo_handles_empty_response(self, mock_anthropic_class):
        """Test check_typo handles empty response."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = []
        mock_client.messages.create.return_value = mock_response

        provider = ClaudeProvider(api_key="test-key")
        result = provider.check_typo("테스트")

        assert result.success is False
        assert result.error_message is not None

    def test_check_typo_without_api_key_fails(self):
        """Test check_typo fails when API key is not available."""
        with patch.dict("os.environ", {}, clear=True):
            provider = ClaudeProvider(api_key=None)
            result = provider.check_typo("테스트")

            assert result.success is False
            assert "api key" in result.error_message.lower()


class TestClaudeProviderPrompt:
    """Tests for Claude provider prompt construction."""

    @patch("app.services.ai.claude_provider.Anthropic")
    def test_check_typo_uses_correct_model(self, mock_anthropic_class):
        """Test that check_typo uses the correct Claude model."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text=json.dumps({"corrected_text": "테스트", "issues": []}))
        ]
        mock_client.messages.create.return_value = mock_response

        provider = ClaudeProvider(api_key="test-key")
        provider.check_typo("테스트")

        call_kwargs = mock_client.messages.create.call_args[1]
        assert "claude" in call_kwargs["model"].lower()

    @patch("app.services.ai.claude_provider.Anthropic")
    def test_check_typo_sends_korean_instructions(self, mock_anthropic_class):
        """Test that check_typo sends Korean-specific instructions."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text=json.dumps({"corrected_text": "테스트", "issues": []}))
        ]
        mock_client.messages.create.return_value = mock_response

        provider = ClaudeProvider(api_key="test-key")
        provider.check_typo("테스트")

        call_kwargs = mock_client.messages.create.call_args[1]
        # Check that system prompt contains Korean typo checking instructions
        assert "system" in call_kwargs or any(
            "korean" in str(msg).lower() or "한국어" in str(msg)
            for msg in call_kwargs.get("messages", [])
        )


class TestClaudeProviderConfiguration:
    """Tests for Claude provider configuration."""

    def test_default_model_configuration(self):
        """Test default model is set correctly."""
        provider = ClaudeProvider(api_key="test-key")
        assert hasattr(provider, "model")
        assert provider.model is not None

    def test_custom_model_configuration(self):
        """Test custom model can be specified."""
        provider = ClaudeProvider(api_key="test-key", model="claude-3-haiku-20240307")
        assert provider.model == "claude-3-haiku-20240307"

    def test_max_tokens_configuration(self):
        """Test max_tokens is configurable."""
        provider = ClaudeProvider(api_key="test-key", max_tokens=2000)
        assert provider.max_tokens == 2000

    def test_default_max_tokens(self):
        """Test default max_tokens value."""
        provider = ClaudeProvider(api_key="test-key")
        assert provider.max_tokens >= 1000  # Should have reasonable default
