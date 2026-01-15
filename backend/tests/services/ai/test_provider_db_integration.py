"""Tests for AI provider database integration."""

from unittest.mock import patch, MagicMock

from app import db
from app.models.system_prompt import SystemPromptConfig
from app.services.ai.claude_provider import ClaudeProvider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.openai_provider import OpenAIProvider


class TestClaudeProviderDBIntegration:
    """Tests for Claude provider loading prompts from database."""

    def test_uses_default_prompt_when_no_db_config(self, app):
        """Test Claude uses default prompt when no DB configuration exists."""
        with app.app_context():
            provider = ClaudeProvider(api_key="test-key")
            prompt = provider.get_system_prompt()

            assert prompt == ClaudeProvider.SYSTEM_PROMPT

    def test_uses_custom_prompt_from_db(self, app):
        """Test Claude uses custom prompt from database."""
        with app.app_context():
            # Create custom prompt in DB
            custom_prompt = SystemPromptConfig(
                provider="claude",
                prompt="Custom Claude system prompt from DB",
                is_active=True,
            )
            db.session.add(custom_prompt)
            db.session.commit()

            provider = ClaudeProvider(api_key="test-key")
            prompt = provider.get_system_prompt()

            assert prompt == "Custom Claude system prompt from DB"

    def test_falls_back_to_default_when_inactive(self, app):
        """Test Claude falls back to default when DB prompt is inactive."""
        with app.app_context():
            # Create inactive custom prompt
            custom_prompt = SystemPromptConfig(
                provider="claude",
                prompt="Inactive prompt",
                is_active=False,
            )
            db.session.add(custom_prompt)
            db.session.commit()

            provider = ClaudeProvider(api_key="test-key")
            prompt = provider.get_system_prompt()

            assert prompt == ClaudeProvider.SYSTEM_PROMPT


class TestGeminiProviderDBIntegration:
    """Tests for Gemini provider loading prompts from database."""

    def test_uses_default_prompt_when_no_db_config(self, app):
        """Test Gemini uses default prompt when no DB configuration exists."""
        with app.app_context():
            provider = GeminiProvider(api_key="test-key")
            prompt = provider.get_system_prompt()

            assert prompt == GeminiProvider.SYSTEM_PROMPT

    def test_uses_custom_prompt_from_db(self, app):
        """Test Gemini uses custom prompt from database."""
        with app.app_context():
            custom_prompt = SystemPromptConfig(
                provider="gemini",
                prompt="Custom Gemini system prompt",
                is_active=True,
            )
            db.session.add(custom_prompt)
            db.session.commit()

            provider = GeminiProvider(api_key="test-key")
            prompt = provider.get_system_prompt()

            assert prompt == "Custom Gemini system prompt"


class TestOpenAIProviderDBIntegration:
    """Tests for OpenAI provider loading prompts from database."""

    def test_uses_default_prompt_when_no_db_config(self, app):
        """Test OpenAI uses default prompt when no DB configuration exists."""
        with app.app_context():
            provider = OpenAIProvider(api_key="test-key")
            prompt = provider.get_system_prompt()

            assert prompt == OpenAIProvider.SYSTEM_PROMPT

    def test_uses_custom_prompt_from_db(self, app):
        """Test OpenAI uses custom prompt from database."""
        with app.app_context():
            custom_prompt = SystemPromptConfig(
                provider="openai",
                prompt="Custom OpenAI system prompt",
                is_active=True,
            )
            db.session.add(custom_prompt)
            db.session.commit()

            provider = OpenAIProvider(api_key="test-key")
            prompt = provider.get_system_prompt()

            assert prompt == "Custom OpenAI system prompt"


class TestProviderCheckTypoUsesDBPrompt:
    """Tests that check_typo methods use prompts from database."""

    @patch.object(ClaudeProvider, '_get_client')
    def test_claude_check_typo_uses_db_prompt(self, mock_get_client, app):
        """Test Claude check_typo uses custom prompt from DB."""
        with app.app_context():
            # Create custom prompt
            custom_prompt = SystemPromptConfig(
                provider="claude",
                prompt="DB Claude prompt for typo checking",
                is_active=True,
            )
            db.session.add(custom_prompt)
            db.session.commit()

            # Mock the API client
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text='{"corrected_text": "test", "issues": []}')]
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            provider = ClaudeProvider(api_key="test-key")
            provider.check_typo("테스트 텍스트")

            # Verify the API was called with the custom prompt
            call_args = mock_client.messages.create.call_args
            assert call_args.kwargs['system'] == "DB Claude prompt for typo checking"

    @patch.object(GeminiProvider, '_get_client')
    def test_gemini_check_typo_uses_db_prompt(self, mock_get_client, app):
        """Test Gemini check_typo uses custom prompt from DB."""
        with app.app_context():
            # Create custom prompt
            custom_prompt = SystemPromptConfig(
                provider="gemini",
                prompt="DB Gemini prompt",
                is_active=True,
            )
            db.session.add(custom_prompt)
            db.session.commit()

            # Mock the API client
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = '{"corrected_text": "test", "issues": []}'
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client

            provider = GeminiProvider(api_key="test-key")
            provider.check_typo("테스트 텍스트")

            # Verify the API was called with content containing custom prompt
            call_args = mock_client.models.generate_content.call_args
            prompt_content = call_args.kwargs['contents']
            assert "DB Gemini prompt" in prompt_content

    @patch.object(OpenAIProvider, '_get_client')
    def test_openai_check_typo_uses_db_prompt(self, mock_get_client, app):
        """Test OpenAI check_typo uses custom prompt from DB."""
        with app.app_context():
            # Create custom prompt
            custom_prompt = SystemPromptConfig(
                provider="openai",
                prompt="DB OpenAI prompt",
                is_active=True,
            )
            db.session.add(custom_prompt)
            db.session.commit()

            # Mock the API client
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [
                MagicMock(message=MagicMock(content='{"corrected_text": "test", "issues": []}'))
            ]
            mock_client.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            provider = OpenAIProvider(api_key="test-key")
            provider.check_typo("테스트 텍스트")

            # Verify the API was called with the custom prompt
            call_args = mock_client.chat.completions.create.call_args
            system_message = call_args.kwargs['messages'][0]
            assert system_message['role'] == 'system'
            assert system_message['content'] == "DB OpenAI prompt"
