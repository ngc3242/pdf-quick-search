"""OpenAI Provider for Korean typo checking.

This module implements the AIProviderInterface using OpenAI's API
to provide Korean text typo checking functionality.
"""

import json
import logging
import os
from typing import List, Optional

from app.services.ai.ai_provider_interface import (
    AIProviderInterface,
    TypoCheckResult,
    TypoIssue,
)

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProviderInterface):
    """OpenAI provider for Korean typo checking.

    Uses OpenAI's API to analyze Korean text for spelling,
    grammar, and spacing errors.
    """

    DEFAULT_MODEL = "gpt-5.2"
    # GPT-5.2 supports up to 128,000 max output tokens
    DEFAULT_MAX_TOKENS = 128000

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
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key. If not provided, uses OPENAI_API_KEY env var.
            model: OpenAI model to use. Defaults to gpt-4o.
            max_tokens: Maximum tokens for response. Defaults to 4096.
        """
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or self.DEFAULT_MODEL
        self.max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        self._client = None

    @property
    def provider_name(self) -> str:
        """Return the provider name.

        Returns:
            String 'openai' as the provider identifier
        """
        return "openai"

    def is_available(self) -> bool:
        """Check if OpenAI provider is available.

        Returns:
            True if API key is configured, False otherwise
        """
        return self._api_key is not None and len(self._api_key) > 0

    def _get_client(self):
        """Get or create OpenAI client.

        Returns:
            OpenAI client instance
        """
        if self._client is None:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=self._api_key)
            except ImportError:
                logger.error("OpenAI package not installed. Run: pip install openai")
                raise
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
        """Check Korean text for typos using OpenAI API.

        Args:
            text: Korean text to check for typos

        Returns:
            TypoCheckResult containing corrections and issues found
        """
        logger.info("[OpenAI] ========== START check_typo ==========")
        logger.info("[OpenAI] Input text length: %d chars", len(text))
        logger.info(
            "[OpenAI] Input text preview: %s...",
            text[:200] if len(text) > 200 else text,
        )

        # Check if API key is available
        api_key_exists = self._api_key is not None
        api_key_length = len(self._api_key) if self._api_key else 0
        logger.info(
            "[OpenAI] API key exists: %s, length: %d", api_key_exists, api_key_length
        )

        if not self.is_available():
            logger.error("[OpenAI] API key is not configured!")
            return TypoCheckResult(
                original_text=text,
                corrected_text="",
                issues=[],
                provider=self.provider_name,
                success=False,
                error_message="API key is not configured",
            )

        try:
            logger.info("[OpenAI] Creating OpenAI client...")
            client = self._get_client()
            logger.info("[OpenAI] Client created successfully")

            # Get system prompt (custom from DB or default)
            system_prompt = self.get_system_prompt()
            logger.info("[OpenAI] System prompt length: %d chars", len(system_prompt))
            logger.info("[OpenAI] Using model: %s", self.model)
            logger.info("[OpenAI] Max completion tokens: %d", self.max_tokens)

            logger.info("[OpenAI] Sending API request...")
            response = client.chat.completions.create(
                model=self.model,
                max_completion_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"다음 한국어 텍스트의 맞춤법, 띄어쓰기, 문법 오류를 검사해주세요:\n\n{text}",
                    },
                ],
            )
            logger.info("[OpenAI] API response received!")
            logger.info("[OpenAI] Response id: %s", getattr(response, "id", "N/A"))
            logger.info(
                "[OpenAI] Response model: %s", getattr(response, "model", "N/A")
            )

            # Log usage info
            if hasattr(response, "usage") and response.usage:
                logger.info(
                    "[OpenAI] Usage - prompt_tokens: %d, completion_tokens: %d, total_tokens: %d",
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                    response.usage.total_tokens,
                )

            # Log finish reason
            if response.choices:
                logger.info(
                    "[OpenAI] Finish reason: %s", response.choices[0].finish_reason
                )

            result = self._parse_response(text, response)
            logger.info(
                "[OpenAI] Parse result - success: %s, issues_count: %d",
                result.success,
                len(result.issues),
            )
            logger.info("[OpenAI] ========== END check_typo ==========")
            return result

        except Exception as e:
            logger.error("[OpenAI] ========== EXCEPTION ==========")
            logger.error("[OpenAI] Exception type: %s", type(e).__name__)
            logger.error("[OpenAI] Exception message: %s", str(e))
            logger.error("[OpenAI] Full exception:", exc_info=True)
            return TypoCheckResult(
                original_text=text,
                corrected_text="",
                issues=[],
                provider=self.provider_name,
                success=False,
                error_message=f"API Error: {str(e)}",
            )

    def _parse_response(self, original_text: str, response) -> TypoCheckResult:
        """Parse OpenAI API response into TypoCheckResult.

        Args:
            original_text: The original text that was checked
            response: Raw API response from OpenAI

        Returns:
            TypoCheckResult with parsed data
        """
        logger.info("[OpenAI] Parsing response...")

        if not response.choices:
            logger.error("[OpenAI] No choices in response!")
            return TypoCheckResult(
                original_text=original_text,
                corrected_text="",
                issues=[],
                provider=self.provider_name,
                success=False,
                error_message="Empty response from API",
            )

        try:
            response_text = response.choices[0].message.content
            logger.info(
                "[OpenAI] Raw response length: %d chars",
                len(response_text) if response_text else 0,
            )
            logger.info(
                "[OpenAI] Raw response preview: %s",
                response_text[:500] if response_text else "None",
            )

            # Remove markdown code block if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
                logger.info("[OpenAI] Removed ```json prefix")
            if response_text.startswith("```"):
                response_text = response_text[3:]
                logger.info("[OpenAI] Removed ``` prefix")
            if response_text.endswith("```"):
                response_text = response_text[:-3]
                logger.info("[OpenAI] Removed ``` suffix")
            response_text = response_text.strip()

            # Parse JSON response
            logger.info("[OpenAI] Parsing JSON...")
            data = json.loads(response_text)
            logger.info("[OpenAI] JSON parsed successfully")

            corrected_text = data.get("corrected_text", original_text)
            logger.info("[OpenAI] Corrected text length: %d chars", len(corrected_text))

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

            logger.info("[OpenAI] Found %d issues", len(issues))

            return TypoCheckResult(
                original_text=original_text,
                corrected_text=corrected_text,
                issues=issues,
                provider=self.provider_name,
                success=True,
                error_message=None,
            )

        except json.JSONDecodeError as e:
            logger.error("[OpenAI] JSON decode error: %s", str(e))
            logger.error(
                "[OpenAI] Failed response text: %s",
                response_text if "response_text" in locals() else "N/A",
            )
            return TypoCheckResult(
                original_text=original_text,
                corrected_text="",
                issues=[],
                provider=self.provider_name,
                success=False,
                error_message=f"Invalid JSON response: {str(e)}",
            )
        except Exception as e:
            logger.error("[OpenAI] Parse error: %s", str(e), exc_info=True)
            return TypoCheckResult(
                original_text=original_text,
                corrected_text="",
                issues=[],
                provider=self.provider_name,
                success=False,
                error_message=f"Error parsing response: {str(e)}",
            )
