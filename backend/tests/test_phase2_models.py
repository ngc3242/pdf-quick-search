"""Tests for Phase 2 models: SearchPage and ExtractionQueue."""

import pytest
from datetime import datetime, timezone


class TestSearchPageModel:
    """Test cases for SearchPage model."""

    def test_search_page_creation(self, app):
        """Test creating a SearchPage instance."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.page import SearchPage

        with app.app_context():
            # Create user and document first
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
                file_path="/storage/test.pdf",
                file_size_bytes=1024
            )
            db.session.add(document)
            db.session.commit()

            # Create search page
            page = SearchPage(
                document_id=document.id,
                page_number=1,
                content="This is the content of page 1",
                content_normalized="this is the content of page 1"
            )
            db.session.add(page)
            db.session.commit()

            assert page.id is not None
            assert page.document_id == document.id
            assert page.page_number == 1
            assert page.content == "This is the content of page 1"
            assert page.content_normalized == "this is the content of page 1"

    def test_search_page_document_relationship(self, app):
        """Test SearchPage relationship with SearchDocument."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.page import SearchPage

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

            page1 = SearchPage(
                document_id=document.id,
                page_number=1,
                content="Page 1 content"
            )
            page2 = SearchPage(
                document_id=document.id,
                page_number=2,
                content="Page 2 content"
            )
            db.session.add_all([page1, page2])
            db.session.commit()

            # Test relationship from document to pages
            assert len(document.pages) == 2
            assert document.pages[0].page_number == 1
            assert document.pages[1].page_number == 2

            # Test relationship from page to document
            assert page1.document.original_filename == "test.pdf"

    def test_search_page_cascade_delete(self, app):
        """Test SearchPage is deleted when document is deleted."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.page import SearchPage

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
            doc_id = document.id

            page = SearchPage(
                document_id=document.id,
                page_number=1,
                content="Page content"
            )
            db.session.add(page)
            db.session.commit()
            page_id = page.id

            # Delete document
            db.session.delete(document)
            db.session.commit()

            # Verify page is also deleted
            deleted_page = db.session.get(SearchPage, page_id)
            assert deleted_page is None

    def test_search_page_unique_constraint(self, app):
        """Test unique constraint on (document_id, page_number)."""
        from sqlalchemy.exc import IntegrityError
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.page import SearchPage

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

            page1 = SearchPage(
                document_id=document.id,
                page_number=1,
                content="Page 1"
            )
            db.session.add(page1)
            db.session.commit()

            # Try to add duplicate page number
            page2 = SearchPage(
                document_id=document.id,
                page_number=1,  # Same page number
                content="Duplicate page 1"
            )
            db.session.add(page2)

            with pytest.raises(IntegrityError):
                db.session.commit()

    def test_search_page_to_dict(self, app):
        """Test SearchPage to_dict method."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.page import SearchPage

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

            page = SearchPage(
                document_id=document.id,
                page_number=5,
                content="Page 5 content",
                content_normalized="page 5 content"
            )
            db.session.add(page)
            db.session.commit()

            page_dict = page.to_dict()

            assert page_dict["id"] == page.id
            assert page_dict["document_id"] == document.id
            assert page_dict["page_number"] == 5
            assert page_dict["content"] == "Page 5 content"


class TestExtractionQueueModel:
    """Test cases for ExtractionQueue model."""

    def test_extraction_queue_creation(self, app):
        """Test creating an ExtractionQueue instance."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.extraction_queue import ExtractionQueue

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

            queue_item = ExtractionQueue(
                document_id=document.id,
                priority=1
            )
            db.session.add(queue_item)
            db.session.commit()

            assert queue_item.id is not None
            assert queue_item.document_id == document.id
            assert queue_item.priority == 1
            assert queue_item.status == "pending"
            assert queue_item.retry_count == 0
            assert queue_item.created_at is not None

    def test_extraction_queue_default_values(self, app):
        """Test ExtractionQueue default values."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.extraction_queue import ExtractionQueue

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

            queue_item = ExtractionQueue(document_id=document.id)
            db.session.add(queue_item)
            db.session.commit()

            assert queue_item.priority == 0
            assert queue_item.status == "pending"
            assert queue_item.retry_count == 0
            assert queue_item.started_at is None
            assert queue_item.completed_at is None
            assert queue_item.error_message is None

    def test_extraction_queue_status_update(self, app):
        """Test updating ExtractionQueue status."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.extraction_queue import ExtractionQueue

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

            queue_item = ExtractionQueue(document_id=document.id)
            db.session.add(queue_item)
            db.session.commit()

            # Update to processing
            queue_item.status = "processing"
            queue_item.started_at = datetime.now(timezone.utc)
            db.session.commit()

            assert queue_item.status == "processing"
            assert queue_item.started_at is not None

            # Update to completed
            queue_item.status = "completed"
            queue_item.completed_at = datetime.now(timezone.utc)
            db.session.commit()

            assert queue_item.status == "completed"
            assert queue_item.completed_at is not None

    def test_extraction_queue_retry_count(self, app):
        """Test ExtractionQueue retry count increment."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.extraction_queue import ExtractionQueue

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

            queue_item = ExtractionQueue(document_id=document.id)
            db.session.add(queue_item)
            db.session.commit()

            # Increment retry count
            queue_item.retry_count += 1
            queue_item.error_message = "First attempt failed"
            db.session.commit()

            assert queue_item.retry_count == 1
            assert queue_item.error_message == "First attempt failed"

    def test_extraction_queue_document_relationship(self, app):
        """Test ExtractionQueue relationship with SearchDocument."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.extraction_queue import ExtractionQueue

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

            queue_item = ExtractionQueue(document_id=document.id)
            db.session.add(queue_item)
            db.session.commit()

            # Test relationship
            assert queue_item.document.original_filename == "test.pdf"
            assert document.extraction_queue is not None
            assert document.extraction_queue.id == queue_item.id

    def test_extraction_queue_cascade_delete(self, app):
        """Test ExtractionQueue is deleted when document is deleted."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.extraction_queue import ExtractionQueue

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

            queue_item = ExtractionQueue(document_id=document.id)
            db.session.add(queue_item)
            db.session.commit()
            queue_id = queue_item.id

            # Delete document
            db.session.delete(document)
            db.session.commit()

            # Verify queue item is also deleted
            deleted_queue = db.session.get(ExtractionQueue, queue_id)
            assert deleted_queue is None

    def test_extraction_queue_to_dict(self, app):
        """Test ExtractionQueue to_dict method."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models.extraction_queue import ExtractionQueue

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

            queue_item = ExtractionQueue(
                document_id=document.id,
                priority=2
            )
            db.session.add(queue_item)
            db.session.commit()

            queue_dict = queue_item.to_dict()

            assert queue_dict["id"] == queue_item.id
            assert queue_dict["document_id"] == document.id
            assert queue_dict["priority"] == 2
            assert queue_dict["status"] == "pending"
            assert queue_dict["retry_count"] == 0
