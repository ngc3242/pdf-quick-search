"""TypoCheckResult model for storing typo check results."""

import json
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db


class TypoCheckResult(db.Model):
    """Model for storing typo check results.

    Stores the results of AI-powered Korean typo checking operations,
    including the corrected text and detailed issue information.
    """

    __tablename__ = "typo_check_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    original_text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    original_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    corrected_text: Mapped[str] = mapped_column(Text, nullable=False)
    issues: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    provider_used: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = relationship("User", backref="typo_check_results")

    def to_dict(self) -> dict:
        """Convert TypoCheckResult to dictionary.

        Returns:
            Dictionary representation of the typo check result
        """
        # Parse issues JSON string to list
        try:
            issues_list = json.loads(self.issues) if self.issues else []
        except json.JSONDecodeError:
            issues_list = []

        return {
            "id": self.id,
            "user_id": self.user_id,
            "original_text_hash": self.original_text_hash,
            "original_text": self.original_text,
            "corrected_text": self.corrected_text,
            "issues": issues_list,
            "provider": self.provider_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        """Return string representation of TypoCheckResult."""
        return f"<TypoCheckResult {self.id}>"
