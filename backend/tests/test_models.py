"""Tests for database models."""

import pytest
from datetime import datetime, timedelta, timezone
import uuid


class TestUserModel:
    """Test cases for User model."""

    def test_user_creation(self, app):
        """Test creating a new user."""
        from app.models.user import User

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="securepassword123"
            )
            assert user.email == "test@example.com"
            assert user.name == "Test User"
            assert user.role == "user"
            assert user.is_active is True

    def test_user_password_hashing(self, app):
        """Test that password is hashed correctly."""
        from app.models.user import User

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="securepassword123"
            )
            # Password should be hashed, not stored in plain text
            assert user.password_hash != "securepassword123"
            # Should be able to verify password
            assert user.check_password("securepassword123") is True
            assert user.check_password("wrongpassword") is False

    def test_user_has_uuid_id(self, app):
        """Test that user has UUID as id."""
        from app.models.user import User
        from app.models import db

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="securepassword123"
            )
            db.session.add(user)
            db.session.commit()

            # User should have a UUID id
            assert user.id is not None
            assert isinstance(user.id, uuid.UUID) or isinstance(user.id, str)

    def test_user_to_dict(self, app):
        """Test user to_dict method excludes sensitive data."""
        from app.models.user import User

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="securepassword123",
                phone="010-1234-5678"
            )
            user_dict = user.to_dict()

            assert "email" in user_dict
            assert "name" in user_dict
            assert "password_hash" not in user_dict
            assert "password" not in user_dict

    def test_user_unique_email(self, app):
        """Test that email must be unique."""
        from app.models.user import User
        from app.models import db
        from sqlalchemy.exc import IntegrityError

        with app.app_context():
            user1 = User(
                email="test@example.com",
                name="User One",
                password="password123"
            )
            db.session.add(user1)
            db.session.commit()

            user2 = User(
                email="test@example.com",
                name="User Two",
                password="password456"
            )
            db.session.add(user2)

            with pytest.raises(IntegrityError):
                db.session.commit()


class TestSearchDocumentModel:
    """Test cases for SearchDocument model."""

    def test_document_creation(self, app):
        """Test creating a new document."""
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models import db

        with app.app_context():
            user = User(
                email="owner@example.com",
                name="Owner",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

            doc = SearchDocument(
                owner_id=user.id,
                filename="abc123.pdf",
                original_filename="my_document.pdf",
                file_path="/storage/uploads/abc123.pdf",
                file_size_bytes=1024
            )
            db.session.add(doc)
            db.session.commit()

            assert doc.id is not None
            assert doc.owner_id == user.id
            assert doc.extraction_status == "pending"
            assert doc.is_active is True

    def test_document_owner_relationship(self, app):
        """Test document has owner relationship."""
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models import db

        with app.app_context():
            user = User(
                email="owner@example.com",
                name="Owner",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

            doc = SearchDocument(
                owner_id=user.id,
                filename="abc123.pdf",
                original_filename="my_document.pdf",
                file_path="/storage/uploads/abc123.pdf"
            )
            db.session.add(doc)
            db.session.commit()

            # Should be able to access owner through relationship
            assert doc.owner is not None
            assert doc.owner.email == "owner@example.com"

    def test_document_cascade_delete(self, app):
        """Test that documents are deleted when owner is deleted."""
        from app.models.user import User
        from app.models.document import SearchDocument
        from app.models import db

        with app.app_context():
            user = User(
                email="owner@example.com",
                name="Owner",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            doc = SearchDocument(
                owner_id=user.id,
                filename="abc123.pdf",
                original_filename="my_document.pdf",
                file_path="/storage/uploads/abc123.pdf"
            )
            db.session.add(doc)
            db.session.commit()
            doc_id = doc.id

            # Delete user
            db.session.delete(user)
            db.session.commit()

            # Document should also be deleted
            deleted_doc = db.session.get(SearchDocument, doc_id)
            assert deleted_doc is None


class TestTokenBlacklistModel:
    """Test cases for TokenBlacklist model."""

    def test_blacklist_token_creation(self, app):
        """Test creating a blacklisted token."""
        from app.models.user import User
        from app.models.token_blacklist import TokenBlacklist
        from app.models import db

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

            token = TokenBlacklist(
                jti="unique-token-id-123",
                token_type="access",
                user_id=user.id,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
            )
            db.session.add(token)
            db.session.commit()

            assert token.id is not None
            assert token.jti == "unique-token-id-123"
            assert token.token_type == "access"

    def test_is_token_blacklisted(self, app):
        """Test checking if token is blacklisted."""
        from app.models.user import User
        from app.models.token_blacklist import TokenBlacklist
        from app.models import db

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123"
            )
            db.session.add(user)
            db.session.commit()

            token = TokenBlacklist(
                jti="blacklisted-token-123",
                token_type="access",
                user_id=user.id,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
            )
            db.session.add(token)
            db.session.commit()

            # Should find blacklisted token
            assert TokenBlacklist.is_blacklisted("blacklisted-token-123") is True
            # Should not find non-blacklisted token
            assert TokenBlacklist.is_blacklisted("non-existent-token") is False
