"""Claude AI Provider for Korean typo checking.

This module implements the AIProviderInterface using Anthropic's Claude API
to provide Korean text typo checking functionality.
"""

import json
import logging
import os
from typing import List, Optional

from anthropic import Anthropic

from app.services.ai.ai_provider_interface import (
    AIProviderInterface,
    TypoCheckResult,
    TypoIssue,
)

# Configure logger for this module
logger = logging.getLogger(__name__)


class ClaudeProvider(AIProviderInterface):
    """Claude AI provider for Korean typo checking.

    Uses Anthropic's Claude API to analyze Korean text for spelling,
    grammar, and spacing errors.
    """

    DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
    # Claude Sonnet 4.5 supports up to 64K (65,536) max output tokens
    DEFAULT_MAX_TOKENS = 65536

    SYSTEM_PROMPT = """You are a Korean language expert specializing in proofreading and typo correction.
Your task is to analyze Korean text and identify all typos, spelling errors, grammar mistakes, and spacing issues.

You MUST respond with a valid JSON object in the following format:
{
    "corrected_text": "The fully corrected version of the input text",
    "issues": [
        {
            "original": "The original incorrect text segment",
            "corrected": "The corrected version of that segment",
            "position": 0,
            "issue_type": "spelling|spacing|grammar|punctuation",
            "explanation": "Brief explanation of the error in Korean"
        }
    ]
}

Guidelines:
1. Preserve the original meaning and style
2. Fix all Korean spelling errors (맞춤법)
3. Fix spacing errors (띄어쓰기)
4. Fix grammar errors (문법)
5. Fix punctuation errors (구두점)
6. If no errors are found, return the original text with an empty issues array
7. Position should be the character index where the error starts in the original text
8. Explanations should be in Korean for Korean users

IMPORTANT: Return ONLY the JSON object, no additional text or markdown formatting."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ):
        """Initialize Claude provider.

        Args:
            api_key: Anthropic API key. If not provided, uses ANTHROPIC_API_KEY env var.
            model: Claude model to use. Defaults to claude-sonnet-4-20250514.
            max_tokens: Maximum tokens for response. Defaults to 4096.
        """
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model or self.DEFAULT_MODEL
        self.max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        self._client: Optional[Anthropic] = None

    @property
    def provider_name(self) -> str:
        """Return the provider name.

        Returns:
            String 'claude' as the provider identifier
        """
        return "claude"

    def is_available(self) -> bool:
        """Check if Claude provider is available.

        Returns:
            True if API key is configured, False otherwise
        """
        return self._api_key is not None and len(self._api_key) > 0

    def _get_client(self) -> Anthropic:
        """Get or create Anthropic client.

        Returns:
            Anthropic client instance
        """
        if self._client is None:
            self._client = Anthropic(api_key=self._api_key)
        return self._client

    def get_system_prompt(self) -> str:
        """Get the system prompt, checking database for custom configuration.

        Returns:
            Custom prompt from database if available and active,
            otherwise returns the default SYSTEM_PROMPT.
        """
        try:
            from app.models.system_prompt import SystemPromptConfig

            config = SystemPromptConfig.get_by_provider(self.provider_name)
            if config and config.is_active:
                return config.prompt
        except Exception:
            # If database is not available, fall back to default
            pass

        return self.SYSTEM_PROMPT

    def check_typo(self, text: str) -> TypoCheckResult:
        """Check Korean text for typos using Claude API.

        Args:
            text: Korean text to check for typos

        Returns:
            TypoCheckResult containing corrections and issues found
        """
        logger.info("[Claude] ========== START check_typo ==========")
        logger.info("[Claude] Input text length: %d chars", len(text))
        logger.info(
            "[Claude] Input text preview: %s...",
            text[:200] if len(text) > 200 else text,
        )

        # Check if API key is available
        api_key_exists = self._api_key is not None
        api_key_length = len(self._api_key) if self._api_key else 0
        logger.info(
            "[Claude] API key exists: %s, length: %d", api_key_exists, api_key_length
        )

        if not self.is_available():
            logger.error("[Claude] API key is not configured!")
            return TypoCheckResult(
                original_text=text,
                corrected_text="",
                issues=[],
                provider=self.provider_name,
                success=False,
                error_message="API key is not configured",
            )

        try:
            logger.info("[Claude] Creating Anthropic client...")
            client = self._get_client()
            logger.info("[Claude] Client created successfully")

            # Get system prompt (custom from DB or default)
            system_prompt = self.get_system_prompt()
            logger.info("[Claude] System prompt length: %d chars", len(system_prompt))
            logger.info("[Claude] Using model: %s", self.model)
            logger.info("[Claude] Max tokens: %d", self.max_tokens)

            # Make API request
            logger.info("[Claude] Sending API request...")
            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"다음 한국어 텍스트의 맞춤법, 띄어쓰기, 문법 오류를 검사해주세요:\n\n{text}",
                    }
                ],
            )
            logger.info("[Claude] API response received!")
            logger.info("[Claude] Response id: %s", getattr(response, "id", "N/A"))
            logger.info(
                "[Claude] Response model: %s", getattr(response, "model", "N/A")
            )
            logger.info(
                "[Claude] Response stop_reason: %s",
                getattr(response, "stop_reason", "N/A"),
            )

            # Log usage info
            if hasattr(response, "usage"):
                logger.info(
                    "[Claude] Usage - input_tokens: %d, output_tokens: %d",
                    response.usage.input_tokens,
                    response.usage.output_tokens,
                )

            # Parse response
            result = self._parse_response(text, response)
            logger.info(
                "[Claude] Parse result - success: %s, issues_count: %d",
                result.success,
                len(result.issues),
            )
            logger.info("[Claude] ========== END check_typo ==========")
            return result

        except Exception as e:
            logger.error("[Claude] ========== EXCEPTION ==========")
            logger.error("[Claude] Exception type: %s", type(e).__name__)
            logger.error("[Claude] Exception message: %s", str(e))
            logger.error("[Claude] Full exception:", exc_info=True)
            return TypoCheckResult(
                original_text=text,
                corrected_text="",
                issues=[],
                provider=self.provider_name,
                success=False,
                error_message=f"API Error: {str(e)}",
            )

    def _parse_response(self, original_text: str, response) -> TypoCheckResult:
        """Parse Claude API response into TypoCheckResult.

        Args:
            original_text: The original text that was checked
            response: Raw API response from Claude

        Returns:
            TypoCheckResult with parsed data
        """
        # Check for empty response
        if not response.content:
            return TypoCheckResult(
                original_text=original_text,
                corrected_text="",
                issues=[],
                provider=self.provider_name,
                success=False,
                error_message="Empty response from API",
            )

        try:
            # Extract text content from response
            raw_response_text = response.content[0].text
            logger.info(
                "[Claude] Raw response length: %d chars", len(raw_response_text)
            )
            logger.debug("[Claude] Raw response: %s", raw_response_text[:500])

            response_text = raw_response_text

            # Remove markdown code block if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
                logger.debug("[Claude] Removed ```json prefix")
            if response_text.startswith("```"):
                response_text = response_text[3:]
                logger.debug("[Claude] Removed ``` prefix")
            if response_text.endswith("```"):
                response_text = response_text[:-3]
                logger.debug("[Claude] Removed ``` suffix")
            response_text = response_text.strip()

            logger.debug(
                "[Claude] Cleaned response (first 300 chars): %s", response_text[:300]
            )

            # Parse JSON response
            data = json.loads(response_text)

            # Extract corrected text
            corrected_text = data.get("corrected_text", original_text)

            # Parse issues
            issues: List[TypoIssue] = []
            for issue_data in data.get("issues", []):
                issue = TypoIssue(
                    original=issue_data.get("original", ""),
                    corrected=issue_data.get("corrected", ""),
                    position=issue_data.get("position", 0),
                    issue_type=issue_data.get("issue_type", "unknown"),
                    explanation=issue_data.get("explanation", ""),
                )
                issues.append(issue)

            return TypoCheckResult(
                original_text=original_text,
                corrected_text=corrected_text,
                issues=issues,
                provider=self.provider_name,
                success=True,
                error_message=None,
            )

        except json.JSONDecodeError as e:
            logger.error("[Claude] JSON decode error: %s", str(e))
            logger.error("[Claude] Failed to parse response: %s", raw_response_text)
            return TypoCheckResult(
                original_text=original_text,
                corrected_text="",
                issues=[],
                provider=self.provider_name,
                success=False,
                error_message=f"Invalid JSON response: {str(e)}",
            )
        except Exception as e:
            logger.error("[Claude] Unexpected error: %s", str(e), exc_info=True)
            return TypoCheckResult(
                original_text=original_text,
                corrected_text="",
                issues=[],
                provider=self.provider_name,
                success=False,
                error_message=f"Error parsing response: {str(e)}",
            )
