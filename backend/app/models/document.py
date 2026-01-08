"""SearchDocument model for PDF document management."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db


class SearchDocument(db.Model):
    """Model for storing PDF document metadata."""

    __tablename__ = "search_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), default="application/pdf")
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extraction_status: Mapped[str] = mapped_column(String(20), default="pending")
    extraction_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    extraction_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # CrossRef metadata fields (SPEC-CROSSREF-001)
    doi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    doi_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    publication_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    first_author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    co_authors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    journal_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    publisher: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata_status: Mapped[str] = mapped_column(String(20), default="pending")
    metadata_fetched_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Relationships
    owner = relationship("User", back_populates="documents")
    pages = relationship(
        "SearchPage",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="SearchPage.page_number",
    )
    extraction_queue = relationship(
        "ExtractionQueue",
        back_populates="document",
        cascade="all, delete-orphan",
        uselist=False,
    )

    def to_dict(self) -> dict:
        """Convert document to dictionary.

        Returns:
            Dictionary representation of document
        """
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_size_bytes": self.file_size_bytes,
            "mime_type": self.mime_type,
            "page_count": self.page_count,
            "extraction_status": self.extraction_status,
            "extraction_error": self.extraction_error,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "extraction_completed_at": (
                self.extraction_completed_at.isoformat()
                if self.extraction_completed_at
                else None
            ),
            "is_active": self.is_active,
            # CrossRef metadata fields
            "doi": self.doi,
            "doi_url": self.doi_url,
            "publication_year": self.publication_year,
            "first_author": self.first_author,
            "co_authors": self.co_authors,
            "journal_name": self.journal_name,
            "publisher": self.publisher,
            "metadata_status": self.metadata_status,
            "metadata_fetched_at": (
                self.metadata_fetched_at.isoformat()
                if self.metadata_fetched_at
                else None
            ),
        }

    def __repr__(self) -> str:
        """Return string representation of document."""
        return f"<SearchDocument {self.original_filename}>"
