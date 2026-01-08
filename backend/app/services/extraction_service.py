"""PDF text extraction service."""

import os
import re
import unicodedata
from datetime import datetime, timezone
from typing import Optional, Tuple

import pdfplumber

from app.models import db
from app.models.document import SearchDocument
from app.models.page import SearchPage
from app.models.extraction_queue import ExtractionQueue


class ExtractionService:
    """Service class for PDF text extraction operations."""

    MAX_RETRIES = 3

    @staticmethod
    def normalize_text(text: Optional[str]) -> str:
        """Normalize text for consistent searching.

        Applies Unicode NFC normalization and converts to lowercase.
        Also normalizes whitespace.

        Args:
            text: Input text to normalize

        Returns:
            Normalized text string
        """
        if not text:
            return ""

        # Apply Unicode NFC normalization
        normalized = unicodedata.normalize("NFC", text)

        # Convert to lowercase
        normalized = normalized.lower()

        # Normalize whitespace: replace multiple spaces with single space
        normalized = re.sub(r"\s+", " ", normalized)

        # Strip leading/trailing whitespace
        normalized = normalized.strip()

        return normalized

    @staticmethod
    def add_to_queue(document_id: int, priority: int = 0) -> ExtractionQueue:
        """Add a document to the extraction queue.

        Args:
            document_id: ID of the document to process
            priority: Priority level (higher = processed first)

        Returns:
            Created ExtractionQueue item
        """
        queue_item = ExtractionQueue(
            document_id=document_id,
            priority=priority
        )
        db.session.add(queue_item)
        db.session.commit()
        return queue_item

    @staticmethod
    def get_next_pending() -> Optional[ExtractionQueue]:
        """Get the next pending item from the queue.

        Returns items ordered by:
        1. Highest priority first
        2. Oldest created_at first (FIFO for same priority)

        Returns:
            Next ExtractionQueue item or None if queue is empty
        """
        return ExtractionQueue.query.filter_by(
            status="pending"
        ).order_by(
            ExtractionQueue.priority.desc(),
            ExtractionQueue.created_at.asc()
        ).first()

    @staticmethod
    def extract_text(document_id: int) -> int:
        """Extract text from a PDF document.

        Uses pdfplumber to extract text from each page and stores
        it in SearchPage records.

        Args:
            document_id: ID of the document to extract

        Returns:
            Number of pages extracted

        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            Exception: If the PDF cannot be parsed
        """
        document = db.session.get(SearchDocument, document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        file_path = document.file_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Delete any existing pages for this document
        SearchPage.query.filter_by(document_id=document_id).delete()
        db.session.commit()

        page_count = 0

        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    content = page.extract_text() or ""
                    content_normalized = ExtractionService.normalize_text(content)

                    search_page = SearchPage(
                        document_id=document_id,
                        page_number=page_num,
                        content=content,
                        content_normalized=content_normalized
                    )
                    db.session.add(search_page)
                    page_count += 1

                db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise

        return page_count

    @staticmethod
    def process_next() -> Tuple[bool, Optional[str]]:
        """Process the next item in the extraction queue.

        Retrieves the next pending item, extracts text from its document,
        and updates statuses accordingly. Handles retries up to MAX_RETRIES.

        Returns:
            Tuple of (success, error_message)
        """
        queue_item = ExtractionService.get_next_pending()
        if not queue_item:
            return True, None

        document = queue_item.document
        if not document:
            queue_item.status = "failed"
            queue_item.error_message = "Document not found"
            db.session.commit()
            return False, "Document not found"

        # Mark as processing
        queue_item.status = "processing"
        queue_item.started_at = datetime.now(timezone.utc)
        document.extraction_status = "processing"
        db.session.commit()

        try:
            page_count = ExtractionService.extract_text(document.id)

            # Success
            queue_item.status = "completed"
            queue_item.completed_at = datetime.now(timezone.utc)
            document.extraction_status = "completed"
            document.page_count = page_count
            document.extraction_completed_at = datetime.now(timezone.utc)
            db.session.commit()

            return True, None

        except Exception as e:
            error_message = str(e)

            queue_item.retry_count += 1
            queue_item.error_message = error_message

            if queue_item.retry_count >= ExtractionService.MAX_RETRIES:
                # Max retries reached, mark as failed
                queue_item.status = "failed"
                queue_item.completed_at = datetime.now(timezone.utc)
                document.extraction_status = "failed"
                document.extraction_error = error_message
            else:
                # Still have retries left, keep as pending
                queue_item.status = "pending"
                queue_item.started_at = None

            db.session.commit()

            return False, error_message
