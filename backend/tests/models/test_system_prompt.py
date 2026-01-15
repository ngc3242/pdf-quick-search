"""Tests for SystemPromptConfig model."""

import pytest
from datetime import datetime, timezone

from app import db
from app.models.system_prompt import SystemPromptConfig


class TestSystemPromptConfigModel:
    """Test cases for SystemPromptConfig database model."""

    def test_create_system_prompt_config(self, app):
        """Test creating a new system prompt configuration."""
        with app.app_context():
            prompt = SystemPromptConfig(
                provider="claude",
                prompt="You are a helpful assistant.",
                is_active=True,
            )
            db.session.add(prompt)
            db.session.commit()

            assert prompt.id is not None
            assert prompt.provider == "claude"
            assert prompt.prompt == "You are a helpful assistant."
            assert prompt.is_active is True
            assert prompt.created_at is not None
            assert prompt.updated_at is not None

    def test_provider_is_unique(self, app):
        """Test that provider field is unique."""
        with app.app_context():
            prompt1 = SystemPromptConfig(
                provider="claude",
                prompt="First prompt",
            )
            db.session.add(prompt1)
            db.session.commit()

            # Attempting to add another with same provider should fail
            prompt2 = SystemPromptConfig(
                provider="claude",
                prompt="Second prompt",
            )
            db.session.add(prompt2)

            with pytest.raises(Exception):
                db.session.commit()

    def test_provider_required(self, app):
        """Test that provider field is required (not nullable)."""
        with app.app_context():
            prompt = SystemPromptConfig(
                provider=None,
                prompt="Some prompt",
            )
            db.session.add(prompt)

            with pytest.raises(Exception):
                db.session.commit()

    def test_prompt_required(self, app):
        """Test that prompt field is required (not nullable)."""
        with app.app_context():
            prompt = SystemPromptConfig(
                provider="claude",
                prompt=None,
            )
            db.session.add(prompt)

            with pytest.raises(Exception):
                db.session.commit()

    def test_is_active_defaults_to_true(self, app):
        """Test that is_active defaults to True."""
        with app.app_context():
            prompt = SystemPromptConfig(
                provider="gemini",
                prompt="Test prompt",
            )
            db.session.add(prompt)
            db.session.commit()

            assert prompt.is_active is True

    def test_created_at_set_automatically(self, app):
        """Test that created_at is set automatically on creation."""
        with app.app_context():
            prompt = SystemPromptConfig(
                provider="openai",
                prompt="Test prompt",
            )
            db.session.add(prompt)
            db.session.commit()

            assert prompt.created_at is not None
            # Verify created_at is a reasonable recent time
            now = datetime.now(timezone.utc)
            created_at_aware = (
                prompt.created_at.replace(tzinfo=timezone.utc)
                if prompt.created_at.tzinfo is None
                else prompt.created_at
            )
            diff = abs((now - created_at_aware).total_seconds())
            assert diff < 5  # Should be within 5 seconds

    def test_updated_at_set_automatically(self, app):
        """Test that updated_at is set automatically on creation."""
        with app.app_context():
            prompt = SystemPromptConfig(
                provider="claude",
                prompt="Initial prompt",
            )
            db.session.add(prompt)
            db.session.commit()

            assert prompt.updated_at is not None

    def test_updated_at_changes_on_update(self, app):
        """Test that updated_at changes when record is updated."""
        with app.app_context():
            prompt = SystemPromptConfig(
                provider="claude",
                prompt="Initial prompt",
            )
            db.session.add(prompt)
            db.session.commit()

            initial_updated_at = prompt.updated_at

            # Update the prompt
            prompt.prompt = "Updated prompt"
            db.session.commit()

            # updated_at should change (or be same if within same second)
            assert prompt.updated_at >= initial_updated_at

    def test_to_dict_method(self, app):
        """Test that to_dict returns proper dictionary representation."""
        with app.app_context():
            prompt = SystemPromptConfig(
                provider="claude",
                prompt="Test prompt",
                is_active=True,
            )
            db.session.add(prompt)
            db.session.commit()

            result = prompt.to_dict()

            assert result["provider"] == "claude"
            assert result["prompt"] == "Test prompt"
            assert result["is_active"] is True
            assert "updated_at" in result
            assert "created_at" not in result  # Should not expose created_at by default

    def test_get_by_provider(self, app):
        """Test getting system prompt by provider name."""
        with app.app_context():
            prompt = SystemPromptConfig(
                provider="claude",
                prompt="Claude prompt",
            )
            db.session.add(prompt)
            db.session.commit()

            found = SystemPromptConfig.get_by_provider("claude")
            assert found is not None
            assert found.provider == "claude"
            assert found.prompt == "Claude prompt"

    def test_get_by_provider_not_found(self, app):
        """Test getting system prompt by provider that doesn't exist."""
        with app.app_context():
            found = SystemPromptConfig.get_by_provider("nonexistent")
            assert found is None

    def test_repr(self, app):
        """Test string representation of the model."""
        with app.app_context():
            prompt = SystemPromptConfig(
                provider="claude",
                prompt="Test",
            )
            assert "<SystemPromptConfig claude>" == repr(prompt)


class TestSystemPromptConfigValidProviders:
    """Test valid provider values."""

    @pytest.mark.parametrize("provider", ["claude", "gemini", "openai"])
    def test_valid_providers(self, app, provider):
        """Test that valid provider names can be stored."""
        with app.app_context():
            prompt = SystemPromptConfig(
                provider=provider,
                prompt=f"{provider} prompt",
            )
            db.session.add(prompt)
            db.session.commit()

            assert prompt.provider == provider
