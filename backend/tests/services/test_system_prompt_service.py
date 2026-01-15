"""Tests for SystemPromptService."""

import pytest

from app import db
from app.models.system_prompt import SystemPromptConfig
from app.services.system_prompt_service import SystemPromptService


class TestSystemPromptServiceGetAllPrompts:
    """Tests for get_all_prompts method."""

    def test_get_all_prompts_empty(self, app):
        """Test getting all prompts when none exist."""
        with app.app_context():
            result = SystemPromptService.get_all_prompts()
            assert result == []

    def test_get_all_prompts_with_data(self, app):
        """Test getting all prompts with existing data."""
        with app.app_context():
            # Create test prompts
            prompts = [
                SystemPromptConfig(provider="claude", prompt="Claude prompt"),
                SystemPromptConfig(provider="gemini", prompt="Gemini prompt"),
                SystemPromptConfig(provider="openai", prompt="OpenAI prompt"),
            ]
            for p in prompts:
                db.session.add(p)
            db.session.commit()

            result = SystemPromptService.get_all_prompts()

            assert len(result) == 3
            providers = [p["provider"] for p in result]
            assert "claude" in providers
            assert "gemini" in providers
            assert "openai" in providers


class TestSystemPromptServiceGetPrompt:
    """Tests for get_prompt method."""

    def test_get_prompt_existing(self, app):
        """Test getting an existing prompt."""
        with app.app_context():
            prompt = SystemPromptConfig(
                provider="claude",
                prompt="You are a helpful assistant.",
            )
            db.session.add(prompt)
            db.session.commit()

            result = SystemPromptService.get_prompt("claude")

            assert result is not None
            assert result["provider"] == "claude"
            assert result["prompt"] == "You are a helpful assistant."

    def test_get_prompt_not_found(self, app):
        """Test getting a prompt that doesn't exist."""
        with app.app_context():
            result = SystemPromptService.get_prompt("nonexistent")
            assert result is None

    def test_get_prompt_text_existing(self, app):
        """Test getting prompt text for existing provider."""
        with app.app_context():
            prompt = SystemPromptConfig(
                provider="claude",
                prompt="Custom Claude prompt",
            )
            db.session.add(prompt)
            db.session.commit()

            result = SystemPromptService.get_prompt_text("claude")
            assert result == "Custom Claude prompt"

    def test_get_prompt_text_fallback_to_default(self, app):
        """Test getting prompt text falls back to default when not in DB."""
        with app.app_context():
            # No prompt in DB, should return None (caller handles default)
            result = SystemPromptService.get_prompt_text("claude")
            assert result is None


class TestSystemPromptServiceUpdatePrompt:
    """Tests for update_prompt method."""

    def test_update_prompt_create_new(self, app):
        """Test creating a new prompt when none exists."""
        with app.app_context():
            result = SystemPromptService.update_prompt(
                provider="claude",
                prompt="New Claude prompt",
            )

            assert result["provider"] == "claude"
            assert result["prompt"] == "New Claude prompt"
            assert result["is_active"] is True

            # Verify it's in the database
            saved = SystemPromptConfig.get_by_provider("claude")
            assert saved is not None
            assert saved.prompt == "New Claude prompt"

    def test_update_prompt_update_existing(self, app):
        """Test updating an existing prompt."""
        with app.app_context():
            # Create initial prompt
            prompt = SystemPromptConfig(
                provider="gemini",
                prompt="Original prompt",
            )
            db.session.add(prompt)
            db.session.commit()

            # Update it
            result = SystemPromptService.update_prompt(
                provider="gemini",
                prompt="Updated prompt",
            )

            assert result["provider"] == "gemini"
            assert result["prompt"] == "Updated prompt"

            # Verify in database
            saved = SystemPromptConfig.get_by_provider("gemini")
            assert saved.prompt == "Updated prompt"

    def test_update_prompt_empty_prompt_rejected(self, app):
        """Test that empty prompt is rejected."""
        with app.app_context():
            with pytest.raises(ValueError, match="Prompt cannot be empty"):
                SystemPromptService.update_prompt(
                    provider="claude",
                    prompt="",
                )

    def test_update_prompt_invalid_provider_rejected(self, app):
        """Test that invalid provider is rejected."""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid provider"):
                SystemPromptService.update_prompt(
                    provider="invalid_provider",
                    prompt="Some prompt",
                )


class TestSystemPromptServiceResetToDefault:
    """Tests for reset_to_default method."""

    def test_reset_to_default_existing(self, app):
        """Test resetting an existing prompt to default."""
        with app.app_context():
            # Create a custom prompt
            prompt = SystemPromptConfig(
                provider="claude",
                prompt="Custom prompt",
            )
            db.session.add(prompt)
            db.session.commit()

            # Reset to default
            result = SystemPromptService.reset_to_default("claude")

            assert result is True

            # Verify the prompt is deleted from DB
            saved = SystemPromptConfig.get_by_provider("claude")
            assert saved is None

    def test_reset_to_default_not_existing(self, app):
        """Test resetting when no custom prompt exists."""
        with app.app_context():
            # Should return True even if nothing to reset
            result = SystemPromptService.reset_to_default("claude")
            assert result is True

    def test_reset_to_default_invalid_provider(self, app):
        """Test resetting with invalid provider."""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid provider"):
                SystemPromptService.reset_to_default("invalid_provider")


class TestSystemPromptServiceGetDefaultPrompt:
    """Tests for get_default_prompt method."""

    def test_get_default_prompt_claude(self, app):
        """Test getting default prompt for Claude."""
        with app.app_context():
            result = SystemPromptService.get_default_prompt("claude")
            assert result is not None
            assert isinstance(result, str)
            assert len(result) > 0

    def test_get_default_prompt_gemini(self, app):
        """Test getting default prompt for Gemini."""
        with app.app_context():
            result = SystemPromptService.get_default_prompt("gemini")
            assert result is not None
            assert isinstance(result, str)
            assert len(result) > 0

    def test_get_default_prompt_openai(self, app):
        """Test getting default prompt for OpenAI."""
        with app.app_context():
            result = SystemPromptService.get_default_prompt("openai")
            assert result is not None
            assert isinstance(result, str)
            assert len(result) > 0

    def test_get_default_prompt_invalid_provider(self, app):
        """Test getting default prompt for invalid provider."""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid provider"):
                SystemPromptService.get_default_prompt("invalid_provider")


class TestSystemPromptServiceValidProviders:
    """Tests for valid providers constant."""

    def test_valid_providers_list(self, app):
        """Test that VALID_PROVIDERS contains expected providers."""
        with app.app_context():
            assert "claude" in SystemPromptService.VALID_PROVIDERS
            assert "gemini" in SystemPromptService.VALID_PROVIDERS
            assert "openai" in SystemPromptService.VALID_PROVIDERS
            assert len(SystemPromptService.VALID_PROVIDERS) == 3
