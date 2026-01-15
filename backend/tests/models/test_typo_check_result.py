"""Tests for TypoCheckResult model.

This module tests the database model for storing typo check results,
including model validation, JSON serialization, and relationships.
"""

import hashlib
import json
from datetime import datetime, timezone


from app import db
from app.models.typo_check_result import TypoCheckResult
from app.models.user import User


class TestTypoCheckResultModel:
    """Tests for TypoCheckResult database model."""

    def test_typo_check_result_model_exists(self, app):
        """Test that TypoCheckResult model is defined."""
        assert TypoCheckResult is not None

    def test_typo_check_result_has_required_fields(self, app):
        """Test that TypoCheckResult has all required fields."""
        # Verify model has necessary columns
        assert hasattr(TypoCheckResult, "id")
        assert hasattr(TypoCheckResult, "user_id")
        assert hasattr(TypoCheckResult, "original_text_hash")
        assert hasattr(TypoCheckResult, "corrected_text")
        assert hasattr(TypoCheckResult, "issues")
        assert hasattr(TypoCheckResult, "created_at")
        assert hasattr(TypoCheckResult, "provider_used")

    def test_create_typo_check_result(self, app):
        """Test creating a TypoCheckResult instance."""
        # Create user first
        user = User(email="test@example.com", name="Test User", password="password123")
        db.session.add(user)
        db.session.commit()

        # Create typo check result
        original_text = "안녕하세여"
        text_hash = hashlib.sha256(original_text.encode()).hexdigest()
        issues = [
            {
                "original": "안녕하세여",
                "corrected": "안녕하세요",
                "position": 0,
                "issue_type": "spelling",
                "explanation": "맞춤법 오류",
            }
        ]

        result = TypoCheckResult(
            user_id=user.id,
            original_text_hash=text_hash,
            corrected_text="안녕하세요",
            issues=json.dumps(issues),
            provider_used="claude",
        )

        db.session.add(result)
        db.session.commit()

        assert result.id is not None
        assert result.user_id == user.id
        assert result.original_text_hash == text_hash
        assert result.corrected_text == "안녕하세요"
        assert result.provider_used == "claude"
        assert result.created_at is not None

    def test_typo_check_result_issues_json_storage(self, app):
        """Test that issues are stored and retrieved as JSON."""
        user = User(
            email="json_test@example.com", name="JSON Test User", password="password123"
        )
        db.session.add(user)
        db.session.commit()

        issues = [
            {
                "original": "테스트",
                "corrected": "테스트",
                "position": 0,
                "issue_type": "none",
                "explanation": "",
            },
            {
                "original": "오류",
                "corrected": "오류수정",
                "position": 10,
                "issue_type": "spelling",
                "explanation": "맞춤법",
            },
        ]

        result = TypoCheckResult(
            user_id=user.id,
            original_text_hash="test_hash",
            corrected_text="테스트 오류수정",
            issues=json.dumps(issues),
            provider_used="claude",
        )

        db.session.add(result)
        db.session.commit()

        # Retrieve and verify JSON
        retrieved = TypoCheckResult.query.get(result.id)
        parsed_issues = json.loads(retrieved.issues)

        assert len(parsed_issues) == 2
        assert parsed_issues[0]["original"] == "테스트"
        assert parsed_issues[1]["issue_type"] == "spelling"

    def test_typo_check_result_created_at_default(self, app):
        """Test that created_at is set automatically."""
        user = User(
            email="timestamp_test@example.com",
            name="Timestamp User",
            password="password123",
        )
        db.session.add(user)
        db.session.commit()

        before_create = datetime.now(timezone.utc)

        result = TypoCheckResult(
            user_id=user.id,
            original_text_hash="timestamp_hash",
            corrected_text="테스트",
            issues="[]",
            provider_used="claude",
        )

        db.session.add(result)
        db.session.commit()

        after_create = datetime.now(timezone.utc)

        assert result.created_at is not None
        # Allow some margin for timing
        assert (
            before_create
            <= result.created_at.replace(tzinfo=timezone.utc)
            <= after_create
        )

    def test_typo_check_result_to_dict(self, app):
        """Test converting TypoCheckResult to dictionary."""
        user = User(
            email="todict_test@example.com", name="ToDict User", password="password123"
        )
        db.session.add(user)
        db.session.commit()

        issues = [{"original": "test", "corrected": "test"}]
        result = TypoCheckResult(
            user_id=user.id,
            original_text_hash="dict_hash",
            corrected_text="수정된 텍스트",
            issues=json.dumps(issues),
            provider_used="openai",
        )

        db.session.add(result)
        db.session.commit()

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["id"] == result.id
        assert result_dict["user_id"] == user.id
        assert result_dict["original_text_hash"] == "dict_hash"
        assert result_dict["corrected_text"] == "수정된 텍스트"
        assert result_dict["provider_used"] == "openai"
        assert "created_at" in result_dict
        # Issues should be parsed JSON list in dict output
        assert isinstance(result_dict["issues"], list)

    def test_typo_check_result_user_relationship(self, app):
        """Test relationship between TypoCheckResult and User."""
        user = User(
            email="rel_test@example.com",
            name="Relationship User",
            password="password123",
        )
        db.session.add(user)
        db.session.commit()

        result = TypoCheckResult(
            user_id=user.id,
            original_text_hash="rel_hash",
            corrected_text="테스트",
            issues="[]",
            provider_used="claude",
        )

        db.session.add(result)
        db.session.commit()

        # Test relationship
        assert result.user is not None
        assert result.user.id == user.id
        assert result.user.email == "rel_test@example.com"

    def test_typo_check_result_foreign_key_constraint(self, app):
        """Test that foreign key constraint exists for user_id.

        Note: Cascade delete behavior depends on database backend.
        SQLite in testing doesn't enforce FK cascades by default.
        This test verifies the FK relationship is properly defined.
        """
        user = User(
            email="cascade_test@example.com",
            name="Cascade User",
            password="password123",
        )
        db.session.add(user)
        db.session.commit()

        result = TypoCheckResult(
            user_id=user.id,
            original_text_hash="cascade_hash",
            corrected_text="테스트",
            issues="[]",
            provider_used="claude",
        )

        db.session.add(result)
        db.session.commit()

        # Verify FK relationship is established
        assert result.user_id == user.id
        assert result.user is not None

        # Verify ondelete CASCADE is defined in the model
        from sqlalchemy import inspect

        mapper = inspect(TypoCheckResult)
        user_id_col = mapper.columns["user_id"]
        fk = list(user_id_col.foreign_keys)[0]
        assert fk.ondelete == "CASCADE"

    def test_typo_check_result_repr(self, app):
        """Test string representation of TypoCheckResult."""
        user = User(
            email="repr_test@example.com", name="Repr User", password="password123"
        )
        db.session.add(user)
        db.session.commit()

        result = TypoCheckResult(
            user_id=user.id,
            original_text_hash="repr_hash",
            corrected_text="테스트",
            issues="[]",
            provider_used="claude",
        )

        db.session.add(result)
        db.session.commit()

        repr_str = repr(result)
        assert "TypoCheckResult" in repr_str
        assert str(result.id) in repr_str


class TestTypoCheckResultProviders:
    """Tests for provider field validation."""

    def test_supported_providers(self, app):
        """Test that various providers can be stored."""
        user = User(
            email="providers_test@example.com",
            name="Providers User",
            password="password123",
        )
        db.session.add(user)
        db.session.commit()

        providers = ["claude", "openai", "gemini"]

        for provider in providers:
            result = TypoCheckResult(
                user_id=user.id,
                original_text_hash=f"hash_{provider}",
                corrected_text="테스트",
                issues="[]",
                provider_used=provider,
            )
            db.session.add(result)

        db.session.commit()

        # Verify all results saved
        results = TypoCheckResult.query.filter_by(user_id=user.id).all()
        assert len(results) == 3

        stored_providers = [r.provider_used for r in results]
        for provider in providers:
            assert provider in stored_providers


class TestTypoCheckResultFiltering:
    """Tests for querying and filtering TypoCheckResult."""

    def test_filter_by_user(self, app):
        """Test filtering results by user."""
        user1 = User(
            email="filter_user1@example.com",
            name="Filter User 1",
            password="password123",
        )
        user2 = User(
            email="filter_user2@example.com",
            name="Filter User 2",
            password="password123",
        )
        db.session.add_all([user1, user2])
        db.session.commit()

        # Create results for user1
        for i in range(3):
            result = TypoCheckResult(
                user_id=user1.id,
                original_text_hash=f"user1_hash_{i}",
                corrected_text="테스트",
                issues="[]",
                provider_used="claude",
            )
            db.session.add(result)

        # Create results for user2
        for i in range(2):
            result = TypoCheckResult(
                user_id=user2.id,
                original_text_hash=f"user2_hash_{i}",
                corrected_text="테스트",
                issues="[]",
                provider_used="claude",
            )
            db.session.add(result)

        db.session.commit()

        # Filter by user
        user1_results = TypoCheckResult.query.filter_by(user_id=user1.id).all()
        user2_results = TypoCheckResult.query.filter_by(user_id=user2.id).all()

        assert len(user1_results) == 3
        assert len(user2_results) == 2

    def test_filter_by_hash(self, app):
        """Test filtering results by original text hash."""
        user = User(
            email="hash_filter_test@example.com",
            name="Hash Filter User",
            password="password123",
        )
        db.session.add(user)
        db.session.commit()

        # Create result with specific hash
        target_hash = "unique_target_hash_12345"
        result = TypoCheckResult(
            user_id=user.id,
            original_text_hash=target_hash,
            corrected_text="테스트",
            issues="[]",
            provider_used="claude",
        )
        db.session.add(result)

        # Create some other results
        for i in range(3):
            other_result = TypoCheckResult(
                user_id=user.id,
                original_text_hash=f"other_hash_{i}",
                corrected_text="테스트",
                issues="[]",
                provider_used="claude",
            )
            db.session.add(other_result)

        db.session.commit()

        # Filter by hash
        found_result = TypoCheckResult.query.filter_by(
            user_id=user.id, original_text_hash=target_hash
        ).first()

        assert found_result is not None
        assert found_result.original_text_hash == target_hash
