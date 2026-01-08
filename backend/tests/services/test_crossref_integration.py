"""Tests for CrossRef metadata integration with SearchDocument model.

TDD RED Phase: Tests written first before implementation.
SPEC-CROSSREF-001: Extend SearchDocument model with CrossRef metadata fields.
"""

import json
from datetime import datetime, timezone


class TestSearchDocumentCrossRefFields:
    """Test cases for CrossRef metadata fields in SearchDocument model."""

    def test_doi_field_can_be_set_and_retrieved(self, app):
        """Test that doi field can be set and retrieved."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

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
                file_path="/storage/test.pdf",
                doi="10.1234/example.2024.001"
            )
            db.session.add(document)
            db.session.commit()

            # Retrieve and verify
            retrieved = db.session.get(SearchDocument, document.id)
            assert retrieved.doi == "10.1234/example.2024.001"

    def test_doi_field_is_nullable(self, app):
        """Test that doi field can be null."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

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
                # doi not set
            )
            db.session.add(document)
            db.session.commit()

            assert document.doi is None

    def test_doi_url_field_can_be_set_and_retrieved(self, app):
        """Test that doi_url field can be set and retrieved."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

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
                file_path="/storage/test.pdf",
                doi_url="https://doi.org/10.1234/example.2024.001"
            )
            db.session.add(document)
            db.session.commit()

            retrieved = db.session.get(SearchDocument, document.id)
            assert retrieved.doi_url == "https://doi.org/10.1234/example.2024.001"

    def test_publication_year_field_can_be_set_and_retrieved(self, app):
        """Test that publication_year field can be set and retrieved."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

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
                file_path="/storage/test.pdf",
                publication_year=2024
            )
            db.session.add(document)
            db.session.commit()

            retrieved = db.session.get(SearchDocument, document.id)
            assert retrieved.publication_year == 2024

    def test_first_author_field_can_be_set_and_retrieved(self, app):
        """Test that first_author field can be set and retrieved."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

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
                file_path="/storage/test.pdf",
                first_author="John Doe"
            )
            db.session.add(document)
            db.session.commit()

            retrieved = db.session.get(SearchDocument, document.id)
            assert retrieved.first_author == "John Doe"

    def test_co_authors_field_stores_json_array(self, app):
        """Test that co_authors field stores JSON array as string."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

            co_authors_list = ["Jane Smith", "Bob Wilson", "et al."]
            co_authors_json = json.dumps(co_authors_list)

            document = SearchDocument(
                owner_id=user.id,
                filename="test.pdf",
                original_filename="test.pdf",
                file_path="/storage/test.pdf",
                co_authors=co_authors_json
            )
            db.session.add(document)
            db.session.commit()

            retrieved = db.session.get(SearchDocument, document.id)
            # Parse JSON string back to list
            parsed_authors = json.loads(retrieved.co_authors)
            assert parsed_authors == ["Jane Smith", "Bob Wilson", "et al."]

    def test_journal_name_field_can_be_set_and_retrieved(self, app):
        """Test that journal_name field can be set and retrieved."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

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
                file_path="/storage/test.pdf",
                journal_name="Nature Communications"
            )
            db.session.add(document)
            db.session.commit()

            retrieved = db.session.get(SearchDocument, document.id)
            assert retrieved.journal_name == "Nature Communications"

    def test_publisher_field_can_be_set_and_retrieved(self, app):
        """Test that publisher field can be set and retrieved."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

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
                file_path="/storage/test.pdf",
                publisher="Springer Nature"
            )
            db.session.add(document)
            db.session.commit()

            retrieved = db.session.get(SearchDocument, document.id)
            assert retrieved.publisher == "Springer Nature"

    def test_metadata_status_default_is_pending(self, app):
        """Test that metadata_status defaults to 'pending'."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

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
                # metadata_status not set - should default to 'pending'
            )
            db.session.add(document)
            db.session.commit()

            assert document.metadata_status == "pending"

    def test_metadata_status_can_be_updated(self, app):
        """Test that metadata_status can be updated to valid values."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

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

            # Test all valid status values
            valid_statuses = ["pending", "processing", "completed", "failed"]
            for status in valid_statuses:
                document.metadata_status = status
                db.session.commit()
                assert document.metadata_status == status

    def test_metadata_fetched_at_field_can_be_set(self, app):
        """Test that metadata_fetched_at field can be set with timezone-aware datetime."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

            fetch_time = datetime.now(timezone.utc)
            document = SearchDocument(
                owner_id=user.id,
                filename="test.pdf",
                original_filename="test.pdf",
                file_path="/storage/test.pdf",
                metadata_fetched_at=fetch_time
            )
            db.session.add(document)
            db.session.commit()

            retrieved = db.session.get(SearchDocument, document.id)
            assert retrieved.metadata_fetched_at is not None

    def test_metadata_fetched_at_is_nullable(self, app):
        """Test that metadata_fetched_at field can be null."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

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

            assert document.metadata_fetched_at is None


class TestSearchDocumentToDictWithCrossRef:
    """Test cases for to_dict() method including CrossRef fields."""

    def test_to_dict_includes_doi(self, app):
        """Test that to_dict includes doi field."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

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
                file_path="/storage/test.pdf",
                doi="10.1234/example.2024.001"
            )
            db.session.add(document)
            db.session.commit()

            doc_dict = document.to_dict()
            assert "doi" in doc_dict
            assert doc_dict["doi"] == "10.1234/example.2024.001"

    def test_to_dict_includes_doi_url(self, app):
        """Test that to_dict includes doi_url field."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

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
                file_path="/storage/test.pdf",
                doi_url="https://doi.org/10.1234/example.2024.001"
            )
            db.session.add(document)
            db.session.commit()

            doc_dict = document.to_dict()
            assert "doi_url" in doc_dict
            assert doc_dict["doi_url"] == "https://doi.org/10.1234/example.2024.001"

    def test_to_dict_includes_publication_year(self, app):
        """Test that to_dict includes publication_year field."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

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
                file_path="/storage/test.pdf",
                publication_year=2024
            )
            db.session.add(document)
            db.session.commit()

            doc_dict = document.to_dict()
            assert "publication_year" in doc_dict
            assert doc_dict["publication_year"] == 2024

    def test_to_dict_includes_first_author(self, app):
        """Test that to_dict includes first_author field."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

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
                file_path="/storage/test.pdf",
                first_author="John Doe"
            )
            db.session.add(document)
            db.session.commit()

            doc_dict = document.to_dict()
            assert "first_author" in doc_dict
            assert doc_dict["first_author"] == "John Doe"

    def test_to_dict_includes_co_authors(self, app):
        """Test that to_dict includes co_authors field."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

            co_authors_json = json.dumps(["Jane Smith", "et al."])
            document = SearchDocument(
                owner_id=user.id,
                filename="test.pdf",
                original_filename="test.pdf",
                file_path="/storage/test.pdf",
                co_authors=co_authors_json
            )
            db.session.add(document)
            db.session.commit()

            doc_dict = document.to_dict()
            assert "co_authors" in doc_dict
            assert doc_dict["co_authors"] == co_authors_json

    def test_to_dict_includes_journal_name(self, app):
        """Test that to_dict includes journal_name field."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

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
                file_path="/storage/test.pdf",
                journal_name="Nature Communications"
            )
            db.session.add(document)
            db.session.commit()

            doc_dict = document.to_dict()
            assert "journal_name" in doc_dict
            assert doc_dict["journal_name"] == "Nature Communications"

    def test_to_dict_includes_publisher(self, app):
        """Test that to_dict includes publisher field."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

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
                file_path="/storage/test.pdf",
                publisher="Springer Nature"
            )
            db.session.add(document)
            db.session.commit()

            doc_dict = document.to_dict()
            assert "publisher" in doc_dict
            assert doc_dict["publisher"] == "Springer Nature"

    def test_to_dict_includes_metadata_status(self, app):
        """Test that to_dict includes metadata_status field."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

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
                file_path="/storage/test.pdf",
                metadata_status="completed"
            )
            db.session.add(document)
            db.session.commit()

            doc_dict = document.to_dict()
            assert "metadata_status" in doc_dict
            assert doc_dict["metadata_status"] == "completed"

    def test_to_dict_includes_metadata_fetched_at(self, app):
        """Test that to_dict includes metadata_fetched_at field."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

            fetch_time = datetime.now(timezone.utc)
            document = SearchDocument(
                owner_id=user.id,
                filename="test.pdf",
                original_filename="test.pdf",
                file_path="/storage/test.pdf",
                metadata_fetched_at=fetch_time
            )
            db.session.add(document)
            db.session.commit()

            doc_dict = document.to_dict()
            assert "metadata_fetched_at" in doc_dict
            # Should be ISO format string
            assert doc_dict["metadata_fetched_at"] is not None

    def test_to_dict_metadata_fetched_at_null_returns_none(self, app):
        """Test that to_dict returns None for null metadata_fetched_at."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

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

            doc_dict = document.to_dict()
            assert "metadata_fetched_at" in doc_dict
            assert doc_dict["metadata_fetched_at"] is None

    def test_to_dict_all_crossref_fields_with_complete_data(self, app):
        """Test to_dict with all CrossRef fields populated."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

            fetch_time = datetime.now(timezone.utc)
            co_authors_json = json.dumps(["Jane Smith", "Bob Wilson", "et al."])

            document = SearchDocument(
                owner_id=user.id,
                filename="test.pdf",
                original_filename="research_paper.pdf",
                file_path="/storage/test.pdf",
                doi="10.1234/example.2024.001",
                doi_url="https://doi.org/10.1234/example.2024.001",
                publication_year=2024,
                first_author="John Doe",
                co_authors=co_authors_json,
                journal_name="Nature Communications",
                publisher="Springer Nature",
                metadata_status="completed",
                metadata_fetched_at=fetch_time
            )
            db.session.add(document)
            db.session.commit()

            doc_dict = document.to_dict()

            # Verify all CrossRef fields are present
            assert doc_dict["doi"] == "10.1234/example.2024.001"
            assert doc_dict["doi_url"] == "https://doi.org/10.1234/example.2024.001"
            assert doc_dict["publication_year"] == 2024
            assert doc_dict["first_author"] == "John Doe"
            assert doc_dict["co_authors"] == co_authors_json
            assert doc_dict["journal_name"] == "Nature Communications"
            assert doc_dict["publisher"] == "Springer Nature"
            assert doc_dict["metadata_status"] == "completed"
            assert doc_dict["metadata_fetched_at"] is not None
