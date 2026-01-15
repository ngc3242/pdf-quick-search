"""Google Gemini Provider for Korean typo checking.

This module implements the AIProviderInterface using Google's Gemini API
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


class GeminiProvider(AIProviderInterface):
    """Google Gemini provider for Korean typo checking.

    Uses Google's Gemini API to analyze Korean text for spelling,
    grammar, and spacing errors.
    """

    DEFAULT_MODEL = "gemini-2.0-flash"

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
    ):
        """Initialize Gemini provider.

        Args:
            api_key: Google API key. If not provided, uses GOOGLE_API_KEY or GEMINI_API_KEY env var.
            model: Gemini model to use. Defaults to gemini-2.0-flash.
        """
        self._api_key = (
            api_key
            or os.environ.get("GOOGLE_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
        )
        self.model = model or self.DEFAULT_MODEL
        self._client = None

    @property
    def provider_name(self) -> str:
        """Return the provider name.

        Returns:
            String 'gemini' as the provider identifier
        """
        return "gemini"

    def is_available(self) -> bool:
        """Check if Gemini provider is available.

        Returns:
            True if API key is configured, False otherwise
        """
        return self._api_key is not None and len(self._api_key.strip()) > 0

    def _get_client(self):
        """Get or create Gemini client.

        Returns:
            Gemini client instance
        """
        if self._client is None:
            try:
                from google import genai

                self._client = genai.Client(api_key=self._api_key)
            except ImportError:
                logger.error(
                    "google-genai package not installed. Run: pip install google-genai"
                )
                raise
        return self._client

    def check_typo(self, text: str) -> TypoCheckResult:
        """Check Korean text for typos using Gemini API.

        Args:
            text: Korean text to check for typos

        Returns:
            TypoCheckResult containing corrections and issues found
        """
        if not self.is_available():
            return TypoCheckResult(
                original_text=text,
                corrected_text="",
                issues=[],
                provider=self.provider_name,
                success=False,
                error_message="API key is not configured",
            )

        try:
            client = self._get_client()

            prompt = f"""{self.SYSTEM_PROMPT}

다음 한국어 텍스트의 맞춤법, 띄어쓰기, 문법 오류를 검사해주세요:

{text}"""

            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
            )

            return self._parse_response(text, response)

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return TypoCheckResult(
                original_text=text,
                corrected_text="",
                issues=[],
                provider=self.provider_name,
                success=False,
                error_message=f"API Error: {str(e)}",
            )

    def _parse_response(self, original_text: str, response) -> TypoCheckResult:
        """Parse Gemini API response into TypoCheckResult.

        Args:
            original_text: The original text that was checked
            response: Raw API response from Gemini

        Returns:
            TypoCheckResult with parsed data
        """
        if not response.text:
            return TypoCheckResult(
                original_text=original_text,
                corrected_text="",
                issues=[],
                provider=self.provider_name,
                success=False,
                error_message="Empty response from API",
            )

        try:
            response_text = response.text

            # Remove markdown code block if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            # Parse JSON response
            data = json.loads(response_text)

            corrected_text = data.get("corrected_text", original_text)

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
            return TypoCheckResult(
                original_text=original_text,
                corrected_text="",
                issues=[],
                provider=self.provider_name,
                success=False,
                error_message=f"Invalid JSON response: {str(e)}",
            )
        except Exception as e:
            return TypoCheckResult(
                original_text=original_text,
                corrected_text="",
                issues=[],
                provider=self.provider_name,
                success=False,
                error_message=f"Error parsing response: {str(e)}",
            )
