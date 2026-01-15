"""System Prompt Configuration model for AI providers."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, Text, event
from sqlalchemy.orm import Mapped, mapped_column

from app import db


class SystemPromptConfig(db.Model):
    """Model for storing AI provider system prompts.

    Allows administrators to customize the system prompts used by
    AI providers (Claude, Gemini, OpenAI) for typo checking.
    """

    __tablename__ = "system_prompt_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __init__(
        self,
        provider: str,
        prompt: str,
        is_active: bool = True,
    ):
        """Initialize a new SystemPromptConfig.

        Args:
            provider: AI provider name (claude, gemini, openai)
            prompt: The system prompt text
            is_active: Whether this prompt is active (default True)
        """
        self.provider = provider
        self.prompt = prompt
        self.is_active = is_active
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """Convert to dictionary representation.

        Returns:
            Dictionary with provider, prompt, is_active, and updated_at
        """
        return {
            "provider": self.provider,
            "prompt": self.prompt,
            "is_active": self.is_active,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_by_provider(cls, provider: str) -> Optional["SystemPromptConfig"]:
        """Get system prompt configuration by provider name.

        Args:
            provider: The provider name (claude, gemini, openai)

        Returns:
            SystemPromptConfig instance or None if not found
        """
        return cls.query.filter_by(provider=provider).first()

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<SystemPromptConfig {self.provider}>"


# Event listener to update updated_at on modification
@event.listens_for(SystemPromptConfig, "before_update")
def receive_before_update(mapper, connection, target):
    """Update the updated_at timestamp before any update."""
    target.updated_at = datetime.now(timezone.utc)
