"""ExtractionQueue model for managing PDF text extraction jobs."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db


class ExtractionQueue(db.Model):
    """Model for managing PDF text extraction queue."""

    __tablename__ = "extraction_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("search_documents.id", ondelete="CASCADE"),
        nullable=False
    )
    priority: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    document = relationship("SearchDocument", back_populates="extraction_queue")

    def to_dict(self) -> dict:
        """Convert queue item to dictionary.

        Returns:
            Dictionary representation of queue item
        """
        return {
            "id": self.id,
            "document_id": self.document_id,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count
        }

    def __repr__(self) -> str:
        """Return string representation of queue item."""
        return f"<ExtractionQueue doc={self.document_id} status={self.status}>"
