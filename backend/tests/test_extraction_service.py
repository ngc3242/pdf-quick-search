"""Tests for PDF text extraction service."""

import os
import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone


class TestExtractionService:
    """Test cases for extraction service."""

    def test_normalize_text_lowercase(self, app):
        """Test text normalization converts to lowercase."""
        from app.services.extraction_service import ExtractionService

        with app.app_context():
            result = ExtractionService.normalize_text("Hello WORLD Test")
            assert result == "hello world test"

    def test_normalize_text_unicode_nfc(self, app):
        """Test text normalization applies Unicode NFC."""
        from app.services.extraction_service import ExtractionService

        with app.app_context():
            # Korean text that might have different Unicode representations
            input_text = "한글 테스트"
            result = ExtractionService.normalize_text(input_text)
            # Should be NFC normalized
            import unicodedata
            expected = unicodedata.normalize("NFC", input_text.lower())
            assert result == expected

    def test_normalize_text_whitespace(self, app):
        """Test text normalization handles extra whitespace."""
        from app.services.extraction_service import ExtractionService

        with app.app_context():
            result = ExtractionService.normalize_text("  Multiple   spaces   ")
            assert result == "multiple spaces"

    def test_normalize_text_empty(self, app):
        """Test text normalization handles empty input."""
        from app.services.extraction_service import ExtractionService

        with app.app_context():
            assert ExtractionService.normalize_text("") == ""
            assert ExtractionService.normalize_text(None) == ""

    def test_add_to_queue_creates_queue_item(self, app):
        """Test adding document to extraction queue."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.extraction_queue import ExtractionQueue
        from app.services.extraction_service import ExtractionService

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

            document = SearchDocument(
                owner_id=user.id,
                filename="test.pdf",
                original_filename="test.pdf",
                file_path="/storage/test.pdf"
            )
            db.session.add(document)
            db.session.commit()

            queue_item = ExtractionService.add_to_queue(document.id)

            assert queue_item is not None
            assert queue_item.document_id == document.id
            assert queue_item.status == "pending"
            assert queue_item.priority == 0

    def test_add_to_queue_with_priority(self, app):
        """Test adding document to queue with custom priority."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.services.extraction_service import ExtractionService

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

            document = SearchDocument(
                owner_id=user.id,
                filename="test.pdf",
                original_filename="test.pdf",
                file_path="/storage/test.pdf"
            )
            db.session.add(document)
            db.session.commit()

            queue_item = ExtractionService.add_to_queue(document.id, priority=5)

            assert queue_item.priority == 5

    def test_get_next_pending_returns_highest_priority(self, app):
        """Test getting next pending item returns highest priority first."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.services.extraction_service import ExtractionService

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

            # Create documents with different priorities
            doc1 = SearchDocument(
                owner_id=user.id,
                filename="low.pdf",
                original_filename="low.pdf",
                file_path="/storage/low.pdf"
            )
            doc2 = SearchDocument(
                owner_id=user.id,
                filename="high.pdf",
                original_filename="high.pdf",
                file_path="/storage/high.pdf"
            )
            db.session.add_all([doc1, doc2])
            db.session.commit()

            # Add to queue with different priorities
            ExtractionService.add_to_queue(doc1.id, priority=1)
            ExtractionService.add_to_queue(doc2.id, priority=10)

            # Should get highest priority first
            next_item = ExtractionService.get_next_pending()
            assert next_item is not None
            assert next_item.document_id == doc2.id

    def test_get_next_pending_fifo_same_priority(self, app):
        """Test FIFO ordering for same priority items."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.services.extraction_service import ExtractionService
        import time

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

            doc1 = SearchDocument(
                owner_id=user.id,
                filename="first.pdf",
                original_filename="first.pdf",
                file_path="/storage/first.pdf"
            )
            db.session.add(doc1)
            db.session.commit()
            ExtractionService.add_to_queue(doc1.id, priority=1)

            doc2 = SearchDocument(
                owner_id=user.id,
                filename="second.pdf",
                original_filename="second.pdf",
                file_path="/storage/second.pdf"
            )
            db.session.add(doc2)
            db.session.commit()
            ExtractionService.add_to_queue(doc2.id, priority=1)

            # Should get first added (FIFO)
            next_item = ExtractionService.get_next_pending()
            assert next_item.document_id == doc1.id

    def test_get_next_pending_empty_queue(self, app):
        """Test getting next pending when queue is empty."""
        from app.services.extraction_service import ExtractionService

        with app.app_context():
            next_item = ExtractionService.get_next_pending()
            assert next_item is None

    def test_process_next_success(self, app):
        """Test processing next item successfully."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.page import SearchPage
        from app.services.extraction_service import ExtractionService

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

            # Create a real temp PDF file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                temp_path = f.name

            try:
                # Create a simple PDF with pdfplumber-compatible content
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas

                c = canvas.Canvas(temp_path, pagesize=letter)
                c.drawString(100, 750, "Page 1 content for testing")
                c.showPage()
                c.drawString(100, 750, "Page 2 content for testing")
                c.showPage()
                c.save()

                document = SearchDocument(
                    owner_id=user.id,
                    filename="test.pdf",
                    original_filename="test.pdf",
                    file_path=temp_path
                )
                db.session.add(document)
                db.session.commit()

                ExtractionService.add_to_queue(document.id)

                success, error = ExtractionService.process_next()

                assert success is True
                assert error is None

                # Verify pages were created
                pages = SearchPage.query.filter_by(document_id=document.id).all()
                assert len(pages) == 2

                # Verify document status updated
                db.session.refresh(document)
                assert document.extraction_status == "completed"
                assert document.page_count == 2

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def test_extract_text_creates_pages(self, app):
        """Test text extraction creates SearchPage records."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.page import SearchPage
        from app.services.extraction_service import ExtractionService

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                temp_path = f.name

            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas

                c = canvas.Canvas(temp_path, pagesize=letter)
                c.drawString(100, 750, "Test Content")
                c.showPage()
                c.save()

                document = SearchDocument(
                    owner_id=user.id,
                    filename="test.pdf",
                    original_filename="test.pdf",
                    file_path=temp_path
                )
                db.session.add(document)
                db.session.commit()

                page_count = ExtractionService.extract_text(document.id)

                assert page_count == 1
                pages = SearchPage.query.filter_by(document_id=document.id).all()
                assert len(pages) == 1
                assert pages[0].page_number == 1
                assert pages[0].content is not None
                assert pages[0].content_normalized is not None

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def test_extract_text_normalizes_content(self, app):
        """Test extracted text is properly normalized."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.page import SearchPage
        from app.services.extraction_service import ExtractionService

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                temp_path = f.name

            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas

                c = canvas.Canvas(temp_path, pagesize=letter)
                c.drawString(100, 750, "UPPERCASE TEXT Here")
                c.showPage()
                c.save()

                document = SearchDocument(
                    owner_id=user.id,
                    filename="test.pdf",
                    original_filename="test.pdf",
                    file_path=temp_path
                )
                db.session.add(document)
                db.session.commit()

                ExtractionService.extract_text(document.id)

                page = SearchPage.query.filter_by(document_id=document.id).first()
                # Normalized content should be lowercase
                assert page.content_normalized == page.content_normalized.lower()

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def test_process_next_failure_increments_retry(self, app):
        """Test processing failure increments retry count."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.extraction_queue import ExtractionQueue
        from app.services.extraction_service import ExtractionService

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

            # Non-existent file path
            document = SearchDocument(
                owner_id=user.id,
                filename="test.pdf",
                original_filename="test.pdf",
                file_path="/nonexistent/path.pdf"
            )
            db.session.add(document)
            db.session.commit()

            queue_item = ExtractionService.add_to_queue(document.id)

            success, error = ExtractionService.process_next()

            assert success is False
            assert error is not None

            db.session.refresh(queue_item)
            assert queue_item.retry_count == 1
            assert queue_item.status == "pending"  # Still pending for retry
            assert queue_item.error_message is not None

    def test_process_next_max_retries_marks_failed(self, app):
        """Test max retries (3) marks queue item as failed."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.extraction_queue import ExtractionQueue
        from app.services.extraction_service import ExtractionService

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

            document = SearchDocument(
                owner_id=user.id,
                filename="test.pdf",
                original_filename="test.pdf",
                file_path="/nonexistent/path.pdf"
            )
            db.session.add(document)
            db.session.commit()

            queue_item = ExtractionService.add_to_queue(document.id)
            queue_item.retry_count = 2  # Already retried twice
            db.session.commit()

            success, error = ExtractionService.process_next()

            assert success is False

            db.session.refresh(queue_item)
            assert queue_item.retry_count == 3
            assert queue_item.status == "failed"

            db.session.refresh(document)
            assert document.extraction_status == "failed"

    def test_extract_text_file_not_found(self, app):
        """Test extraction handles missing file gracefully."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.services.extraction_service import ExtractionService

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

            document = SearchDocument(
                owner_id=user.id,
                filename="test.pdf",
                original_filename="test.pdf",
                file_path="/nonexistent/path.pdf"
            )
            db.session.add(document)
            db.session.commit()

            with pytest.raises(FileNotFoundError):
                ExtractionService.extract_text(document.id)

    def test_extract_text_invalid_pdf(self, app):
        """Test extraction handles invalid PDF file."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.services.extraction_service import ExtractionService

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

            # Create an invalid PDF file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(b"This is not a valid PDF content")
                temp_path = f.name

            try:
                document = SearchDocument(
                    owner_id=user.id,
                    filename="invalid.pdf",
                    original_filename="invalid.pdf",
                    file_path=temp_path
                )
                db.session.add(document)
                db.session.commit()

                with pytest.raises(Exception):
                    ExtractionService.extract_text(document.id)

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
