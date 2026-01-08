"""PDF text extraction service."""

import json
import logging
import os
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import pdfplumber

from app.models import db
from app.models.document import SearchDocument
from app.models.page import SearchPage
from app.models.extraction_queue import ExtractionQueue
from app.services.crossref_service import CrossRefService
from app.services.doi_service import DOIService

logger = logging.getLogger(__name__)


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
        queue_item = ExtractionQueue(document_id=document_id, priority=priority)
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
        return (
            ExtractionQueue.query.filter_by(status="pending")
            .order_by(ExtractionQueue.priority.desc(), ExtractionQueue.created_at.asc())
            .first()
        )

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
                        content_normalized=content_normalized,
                    )
                    db.session.add(search_page)
                    page_count += 1

                db.session.commit()

        except Exception:
            db.session.rollback()
            raise

        return page_count

    @staticmethod
    def _format_author_name(given: str, family: str) -> str:
        """Format author name as 'Family, G.' format.

        Args:
            given: Given name(s)
            family: Family name

        Returns:
            Formatted author name
        """
        if given and family:
            # Get first initial from given name
            initial = given[0].upper() + "."
            return f"{family}, {initial}"
        elif family:
            return family
        elif given:
            return given
        return ""

    @staticmethod
    def _process_metadata(document: SearchDocument, metadata: Dict[str, Any]) -> bool:
        """Process and save CrossRef metadata to document.

        Only saves metadata if title exists (per REQ-UNW-002).

        Args:
            document: Document to update
            metadata: Metadata dictionary from CrossRef

        Returns:
            True if metadata was saved, False otherwise
        """
        # REQ-UNW-002: Do NOT save incomplete metadata (must have title)
        title = metadata.get("title")
        if not title:
            logger.warning(
                f"Document {document.id}: Skipping metadata - no title found"
            )
            return False

        # Process authors
        authors = metadata.get("authors", [])
        if authors:
            # Parse first author - CrossRef returns "Given Family" format
            first_author_full = authors[0]
            parts = first_author_full.rsplit(" ", 1)
            if len(parts) == 2:
                given, family = parts
                document.first_author = ExtractionService._format_author_name(
                    given, family
                )
            else:
                document.first_author = first_author_full

            # Process co-authors (remaining authors)
            if len(authors) > 1:
                co_authors_list = []
                for author_full in authors[1:]:
                    parts = author_full.rsplit(" ", 1)
                    if len(parts) == 2:
                        given, family = parts
                        co_authors_list.append(
                            ExtractionService._format_author_name(given, family)
                        )
                    else:
                        co_authors_list.append(author_full)
                document.co_authors = json.dumps(co_authors_list)

        # Set other metadata fields
        document.journal_name = metadata.get("journal")
        document.publication_year = metadata.get("year")
        document.publisher = metadata.get("publisher")

        logger.info(
            f"Document {document.id}: Metadata saved - "
            f"first_author={document.first_author}, "
            f"journal={document.journal_name}, "
            f"year={document.publication_year}"
        )

        return True

    @staticmethod
    def _extract_and_fetch_metadata(document: SearchDocument) -> None:
        """Extract DOI and fetch CrossRef metadata for a document.

        This method implements graceful degradation (REQ-UNW-003):
        - If DOI not found: metadata_status = 'completed' (no metadata to fetch)
        - If CrossRef API fails: metadata_status = 'failed', but extraction succeeds
        - Never fails the entire upload due to metadata issues

        Args:
            document: Document to process for metadata
        """
        # TASK-006: Extract DOI from PDF
        doi, doi_error = DOIService.extract_doi_from_pdf(document.file_path)

        if doi_error:
            logger.warning(
                f"Document {document.id}: DOI extraction error - {doi_error}"
            )

        if not doi:
            # No DOI found - mark as completed (nothing to fetch)
            document.metadata_status = "completed"
            logger.info(f"Document {document.id}: No DOI found in PDF")
            return

        # Store DOI information
        document.doi = doi
        document.doi_url = f"https://doi.org/{doi}"
        document.metadata_status = "processing"
        db.session.commit()

        logger.info(f"Document {document.id}: DOI extracted - {doi}")

        # TASK-007: Fetch CrossRef metadata
        metadata, api_error = CrossRefService.fetch_metadata(doi)

        if api_error:
            # REQ-UNW-003: Continue operation even if CrossRef API fails
            document.metadata_status = "failed"
            logger.warning(f"Document {document.id}: CrossRef API error - {api_error}")
            return

        if not metadata:
            document.metadata_status = "failed"
            logger.warning(
                f"Document {document.id}: No metadata returned from CrossRef"
            )
            return

        # Process and save metadata
        saved = ExtractionService._process_metadata(document, metadata)

        if saved:
            document.metadata_status = "completed"
            document.metadata_fetched_at = datetime.now(timezone.utc)
        else:
            # REQ-UNW-002: Incomplete metadata (no title)
            document.metadata_status = "failed"

    @staticmethod
    def process_next() -> Tuple[bool, Optional[str]]:
        """Process the next item in the extraction queue.

        Retrieves the next pending item, extracts text from its document,
        extracts DOI and fetches CrossRef metadata, and updates statuses
        accordingly. Handles retries up to MAX_RETRIES.

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

            # Success - update extraction status
            queue_item.status = "completed"
            queue_item.completed_at = datetime.now(timezone.utc)
            document.extraction_status = "completed"
            document.page_count = page_count
            document.extraction_completed_at = datetime.now(timezone.utc)
            db.session.commit()

            # TASK-006 & TASK-007: Extract DOI and fetch metadata
            # This runs after successful text extraction
            # Metadata failures do not affect extraction success
            try:
                ExtractionService._extract_and_fetch_metadata(document)
                db.session.commit()
            except Exception as metadata_error:
                # REQ-UNW-003: Never fail the entire upload due to metadata issues
                logger.error(
                    f"Document {document.id}: Metadata processing error - "
                    f"{str(metadata_error)}"
                )
                document.metadata_status = "failed"
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
