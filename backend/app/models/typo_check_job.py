"""TypoCheckJob model for managing async typo check processing."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app import db


class TypoCheckJob(db.Model):
    """Model for managing async typo check job queue."""

    __tablename__ = "typo_check_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    original_text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )
    progress_current: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    progress_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("typo_check_results.id", ondelete="SET NULL"),
        nullable=True,
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        """Convert job to dictionary for API response."""
        progress_total = self.progress_total or 0
        progress_current = self.progress_current or 0
        percentage = (
            int(progress_current / progress_total * 100) if progress_total > 0 else 0
        )

        return {
            "id": self.id,
            "status": self.status,
            "progress": {
                "current_chunk": progress_current,
                "total_chunks": progress_total,
                "percentage": percentage,
            },
            "error_message": self.error_message,
            "result_id": self.result_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
        }

    def __repr__(self) -> str:
        return f"<TypoCheckJob id={self.id} status={self.status}>"
