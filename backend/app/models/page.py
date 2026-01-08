"""SearchPage model for storing extracted PDF page content."""

from typing import Optional

from sqlalchemy import Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db


class SearchPage(db.Model):
    """Model for storing extracted text from PDF pages."""

    __tablename__ = "search_pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("search_documents.id", ondelete="CASCADE"),
        nullable=False
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_normalized: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Unique constraint on (document_id, page_number)
    __table_args__ = (
        UniqueConstraint("document_id", "page_number", name="uq_document_page"),
    )

    # Relationships
    document = relationship("SearchDocument", back_populates="pages")

    def to_dict(self) -> dict:
        """Convert page to dictionary.

        Returns:
            Dictionary representation of page
        """
        return {
            "id": self.id,
            "document_id": self.document_id,
            "page_number": self.page_number,
            "content": self.content,
            "content_normalized": self.content_normalized
        }

    def __repr__(self) -> str:
        """Return string representation of page."""
        return f"<SearchPage doc={self.document_id} page={self.page_number}>"
