"""Service for managing AI provider system prompts."""

from typing import Optional, List, Dict, Any

from app import db
from app.models.system_prompt import SystemPromptConfig
from app.services.ai.claude_provider import ClaudeProvider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.openai_provider import OpenAIProvider


class SystemPromptService:
    """Service for managing system prompt configurations.

    Provides CRUD operations for AI provider system prompts,
    with support for defaults from provider classes.
    """

    VALID_PROVIDERS = ["claude", "gemini", "openai"]

    @classmethod
    def get_all_prompts(cls) -> List[Dict[str, Any]]:
        """Get all system prompt configurations.

        Returns:
            List of prompt configurations as dictionaries
        """
        prompts = SystemPromptConfig.query.all()
        return [p.to_dict() for p in prompts]

    @classmethod
    def get_prompt(cls, provider: str) -> Optional[Dict[str, Any]]:
        """Get system prompt configuration for a specific provider.

        Args:
            provider: The provider name (claude, gemini, openai)

        Returns:
            Prompt configuration as dictionary, or None if not found
        """
        prompt = SystemPromptConfig.get_by_provider(provider)
        if prompt:
            return prompt.to_dict()
        return None

    @classmethod
    def get_prompt_text(cls, provider: str) -> Optional[str]:
        """Get only the prompt text for a provider.

        Args:
            provider: The provider name (claude, gemini, openai)

        Returns:
            The prompt text, or None if not configured in DB
        """
        prompt = SystemPromptConfig.get_by_provider(provider)
        if prompt and prompt.is_active:
            return prompt.prompt
        return None

    @classmethod
    def update_prompt(cls, provider: str, prompt: str) -> Dict[str, Any]:
        """Update or create a system prompt for a provider.

        Args:
            provider: The provider name (claude, gemini, openai)
            prompt: The new system prompt text

        Returns:
            Updated prompt configuration as dictionary

        Raises:
            ValueError: If provider is invalid or prompt is empty
        """
        if provider not in cls.VALID_PROVIDERS:
            raise ValueError(f"Invalid provider: {provider}")

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        existing = SystemPromptConfig.get_by_provider(provider)

        if existing:
            existing.prompt = prompt.strip()
            db.session.commit()
            return existing.to_dict()
        else:
            new_prompt = SystemPromptConfig(
                provider=provider,
                prompt=prompt.strip(),
                is_active=True,
            )
            db.session.add(new_prompt)
            db.session.commit()
            return new_prompt.to_dict()

    @classmethod
    def reset_to_default(cls, provider: str) -> bool:
        """Reset a provider's prompt to the default by removing custom config.

        Args:
            provider: The provider name (claude, gemini, openai)

        Returns:
            True if reset was successful

        Raises:
            ValueError: If provider is invalid
        """
        if provider not in cls.VALID_PROVIDERS:
            raise ValueError(f"Invalid provider: {provider}")

        existing = SystemPromptConfig.get_by_provider(provider)
        if existing:
            db.session.delete(existing)
            db.session.commit()

        return True

    @classmethod
    def get_default_prompt(cls, provider: str) -> str:
        """Get the default system prompt for a provider.

        Args:
            provider: The provider name (claude, gemini, openai)

        Returns:
            The default system prompt from the provider class

        Raises:
            ValueError: If provider is invalid
        """
        if provider not in cls.VALID_PROVIDERS:
            raise ValueError(f"Invalid provider: {provider}")

        if provider == "claude":
            return ClaudeProvider.SYSTEM_PROMPT
        elif provider == "gemini":
            return GeminiProvider.SYSTEM_PROMPT
        elif provider == "openai":
            return OpenAIProvider.SYSTEM_PROMPT

        # This should never be reached due to validation above
        raise ValueError(f"Invalid provider: {provider}")

    @classmethod
    def get_effective_prompt(cls, provider: str) -> str:
        """Get the effective prompt for a provider (custom or default).

        Args:
            provider: The provider name (claude, gemini, openai)

        Returns:
            The custom prompt if configured, otherwise the default
        """
        custom_prompt = cls.get_prompt_text(provider)
        if custom_prompt:
            return custom_prompt
        return cls.get_default_prompt(provider)
