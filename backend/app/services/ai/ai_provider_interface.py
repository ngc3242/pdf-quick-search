"""Abstract interface for AI providers used in typo checking.

This module defines the contract that all AI providers must implement
for Korean typo checking functionality.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TypoIssue:
    """Represents a single typo issue found in the text.

    Attributes:
        original: The original text segment with the issue
        corrected: The corrected text segment
        position: Character position in the original text where issue starts
        issue_type: Type of issue (spelling, spacing, grammar, etc.)
        explanation: Human-readable explanation of the issue
    """

    original: str
    corrected: str
    position: int
    issue_type: str
    explanation: str

    def to_dict(self) -> dict:
        """Convert TypoIssue to dictionary representation.

        Returns:
            Dictionary containing all issue fields
        """
        return {
            "original": self.original,
            "corrected": self.corrected,
            "position": self.position,
            "issue_type": self.issue_type,
            "explanation": self.explanation,
        }


@dataclass
class TypoCheckResult:
    """Result of a typo check operation.

    Attributes:
        original_text: The original text that was checked
        corrected_text: The fully corrected text
        issues: List of individual issues found
        provider: Name of the AI provider used
        success: Whether the check completed successfully
        error_message: Error message if check failed
    """

    original_text: str
    corrected_text: str
    issues: List[TypoIssue] = field(default_factory=list)
    provider: str = ""
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert TypoCheckResult to dictionary representation.

        Returns:
            Dictionary containing all result fields
        """
        return {
            "original_text": self.original_text,
            "corrected_text": self.corrected_text,
            "issues": [issue.to_dict() for issue in self.issues],
            "provider": self.provider,
            "success": self.success,
            "error_message": self.error_message,
        }


class AIProviderInterface(ABC):
    """Abstract base class for AI typo checking providers.

    All AI providers (Claude, OpenAI, Gemini, etc.) must implement
    this interface to be used in the typo checking system.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider.

        Returns:
            String identifier for this provider (e.g., 'claude', 'openai')
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available for use.

        This should verify that API keys are configured and the
        service is reachable.

        Returns:
            True if provider can be used, False otherwise
        """
        pass

    @abstractmethod
    def check_typo(self, text: str) -> TypoCheckResult:
        """Check text for typos and return corrections.

        Args:
            text: Korean text to check for typos

        Returns:
            TypoCheckResult containing original text, corrected text,
            and list of issues found
        """
        pass
