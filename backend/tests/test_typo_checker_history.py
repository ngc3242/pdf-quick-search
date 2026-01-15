"""Tests for Typo Checker History API.

This module tests the history listing and deletion endpoints
for typo check results, including pagination and ownership verification.
"""

import json
from datetime import datetime, timezone, timedelta

from app import db
from app.models.user import User
from app.models.typo_check_result import TypoCheckResult
from app.utils.auth import create_access_token
from app.services.typo_checker_service import TypoCheckerService


class TestTypoCheckerHistoryService:
    """Tests for TypoCheckerService history methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_user_email = "history_service_test@example.com"
        self.test_user_password = "testpassword123"

    def create_test_user(self):
        """Create a test user."""
        user = User(
            email=self.test_user_email,
            name="History Test User",
            password=self.test_user_password,
        )
        db.session.add(user)
        db.session.commit()
        return user

    def create_test_results(self, user_id: str, count: int = 5):
        """Create multiple test results for a user."""
        results = []
        for i in range(count):
            result = TypoCheckResult(
                user_id=user_id,
                original_text_hash=f"hash_{i}_{user_id}",
                corrected_text=f"Corrected text {i}",
                issues=json.dumps([{"original": f"error{i}", "corrected": f"fix{i}"}]),
                provider_used="claude",
                created_at=datetime.now(timezone.utc) - timedelta(days=i),
            )
            db.session.add(result)
            results.append(result)
        db.session.commit()
        return results

    # TASK-001: get_user_history tests

    def test_get_user_history_method_exists(self, app):
        """Test that get_user_history method exists in TypoCheckerService."""
        assert hasattr(TypoCheckerService, "get_user_history")
        assert callable(getattr(TypoCheckerService, "get_user_history", None))

    def test_get_user_history_returns_user_results_only(self, app):
        """Test that get_user_history returns only the user's own results."""
        with app.app_context():
            # Create two users
            user1 = User(
                email="user1_history@example.com", name="User 1", password="password123"
            )
            user2 = User(
                email="user2_history@example.com", name="User 2", password="password123"
            )
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()

            # Create results for both users
            self.create_test_results(user1.id, count=3)
            self.create_test_results(user2.id, count=2)

            # Get history for user1
            result = TypoCheckerService.get_user_history(user1.id)

            assert result["success"] is True
            assert len(result["items"]) == 3
            for item in result["items"]:
                assert item["user_id"] == user1.id

    def test_get_user_history_ordered_by_created_at_desc(self, app):
        """Test that results are ordered by created_at descending (newest first)."""
        with app.app_context():
            user = self.create_test_user()
            self.create_test_results(user.id, count=5)

            result = TypoCheckerService.get_user_history(user.id)

            assert result["success"] is True
            items = result["items"]
            # Verify descending order
            for i in range(len(items) - 1):
                assert items[i]["created_at"] >= items[i + 1]["created_at"]

    def test_get_user_history_pagination_default_values(self, app):
        """Test default pagination values (page=1, per_page=20)."""
        with app.app_context():
            user = self.create_test_user()
            self.create_test_results(user.id, count=25)

            result = TypoCheckerService.get_user_history(user.id)

            assert result["success"] is True
            assert result["page"] == 1
            assert result["per_page"] == 20
            assert len(result["items"]) == 20
            assert result["total"] == 25
            assert result["pages"] == 2

    def test_get_user_history_pagination_custom_values(self, app):
        """Test pagination with custom page and per_page values."""
        with app.app_context():
            user = self.create_test_user()
            self.create_test_results(user.id, count=15)

            result = TypoCheckerService.get_user_history(user.id, page=2, per_page=5)

            assert result["success"] is True
            assert result["page"] == 2
            assert result["per_page"] == 5
            assert len(result["items"]) == 5
            assert result["total"] == 15
            assert result["pages"] == 3

    def test_get_user_history_empty_results(self, app):
        """Test get_user_history returns empty list when no results exist."""
        with app.app_context():
            user = self.create_test_user()

            result = TypoCheckerService.get_user_history(user.id)

            assert result["success"] is True
            assert result["items"] == []
            assert result["total"] == 0
            assert result["pages"] == 0

    def test_get_user_history_result_format(self, app):
        """Test that each result item has expected fields."""
        with app.app_context():
            user = self.create_test_user()
            self.create_test_results(user.id, count=1)

            result = TypoCheckerService.get_user_history(user.id)

            assert result["success"] is True
            item = result["items"][0]
            assert "id" in item
            assert "user_id" in item
            assert "original_text_hash" in item
            assert "corrected_text" in item
            assert "issues" in item
            assert "provider_used" in item
            assert "created_at" in item

    # TASK-002: delete_result tests

    def test_delete_result_method_exists(self, app):
        """Test that delete_result method exists in TypoCheckerService."""
        assert hasattr(TypoCheckerService, "delete_result")
        assert callable(getattr(TypoCheckerService, "delete_result", None))

    def test_delete_result_success(self, app):
        """Test successful deletion of a result."""
        with app.app_context():
            user = self.create_test_user()
            results = self.create_test_results(user.id, count=1)
            result_id = results[0].id

            delete_result = TypoCheckerService.delete_result(result_id, user.id)

            assert delete_result["success"] is True

            # Verify result is deleted
            deleted = TypoCheckResult.query.filter_by(id=result_id).first()
            assert deleted is None

    def test_delete_result_not_found(self, app):
        """Test deletion of non-existent result returns error."""
        with app.app_context():
            user = self.create_test_user()

            delete_result = TypoCheckerService.delete_result(99999, user.id)

            assert delete_result["success"] is False
            assert "not found" in delete_result["error"].lower()

    def test_delete_result_ownership_check(self, app):
        """Test that users cannot delete other users' results."""
        with app.app_context():
            # Create two users
            user1 = User(
                email="owner_history@example.com",
                name="Owner User",
                password="password123",
            )
            user2 = User(
                email="other_history@example.com",
                name="Other User",
                password="password123",
            )
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()

            # Create result for user1
            result = TypoCheckResult(
                user_id=user1.id,
                original_text_hash="test_hash",
                corrected_text="Test",
                issues="[]",
                provider_used="claude",
            )
            db.session.add(result)
            db.session.commit()
            result_id = result.id

            # Try to delete with user2
            delete_result = TypoCheckerService.delete_result(result_id, user2.id)

            assert delete_result["success"] is False
            assert (
                "denied" in delete_result["error"].lower()
                or "forbidden" in delete_result["error"].lower()
            )

            # Verify result still exists
            still_exists = TypoCheckResult.query.filter_by(id=result_id).first()
            assert still_exists is not None


class TestTypoCheckerHistoryEndpoint:
    """Tests for GET /api/typo-check/history endpoint."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_user_email = "history_endpoint_test@example.com"
        self.test_user_password = "testpassword123"

    def create_test_user(self):
        """Create a test user and return auth token."""
        user = User(
            email=self.test_user_email,
            name="History Endpoint Test User",
            password=self.test_user_password,
        )
        db.session.add(user)
        db.session.commit()
        token = create_access_token(user.id)
        return user, token

    def create_test_results(self, user_id: str, count: int = 5):
        """Create multiple test results for a user."""
        results = []
        for i in range(count):
            result = TypoCheckResult(
                user_id=user_id,
                original_text_hash=f"endpoint_hash_{i}_{user_id}",
                corrected_text=f"Endpoint corrected text {i}",
                issues=json.dumps([]),
                provider_used="claude",
                created_at=datetime.now(timezone.utc) - timedelta(days=i),
            )
            db.session.add(result)
            results.append(result)
        db.session.commit()
        return results

    # TASK-003: GET /api/typo-check/history endpoint tests

    def test_history_endpoint_exists(self, client, app):
        """Test that history endpoint exists."""
        with app.app_context():
            user, token = self.create_test_user()

        response = client.get(
            "/api/typo-check/history", headers={"Authorization": f"Bearer {token}"}
        )

        # Should not be 404
        assert response.status_code != 404

    def test_history_endpoint_requires_auth(self, client, app):
        """Test that history endpoint requires authentication."""
        response = client.get("/api/typo-check/history")

        assert response.status_code == 401

    def test_history_endpoint_returns_paginated_results(self, client, app):
        """Test that history endpoint returns paginated results."""
        with app.app_context():
            user, token = self.create_test_user()
            self.create_test_results(user.id, count=5)

        response = client.get(
            "/api/typo-check/history", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "pages" in data

    def test_history_endpoint_with_pagination_params(self, client, app):
        """Test history endpoint with pagination query parameters."""
        with app.app_context():
            user, token = self.create_test_user()
            self.create_test_results(user.id, count=15)

        response = client.get(
            "/api/typo-check/history?page=2&per_page=5",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["page"] == 2
        assert data["per_page"] == 5
        assert len(data["items"]) == 5

    def test_history_endpoint_returns_newest_first(self, client, app):
        """Test that history endpoint returns results in descending order."""
        with app.app_context():
            user, token = self.create_test_user()
            self.create_test_results(user.id, count=3)

        response = client.get(
            "/api/typo-check/history", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.get_json()
        items = data["items"]
        for i in range(len(items) - 1):
            assert items[i]["created_at"] >= items[i + 1]["created_at"]

    def test_history_endpoint_returns_only_user_results(self, client, app):
        """Test that history endpoint returns only the authenticated user's results."""
        with app.app_context():
            # Create two users
            user1 = User(
                email="history_user1@example.com", name="User 1", password="password123"
            )
            user2 = User(
                email="history_user2@example.com", name="User 2", password="password123"
            )
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()

            # Create results for both users
            self.create_test_results(user1.id, count=3)
            self.create_test_results(user2.id, count=2)

            token1 = create_access_token(user1.id)

        response = client.get(
            "/api/typo-check/history", headers={"Authorization": f"Bearer {token1}"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["total"] == 3
        for item in data["items"]:
            assert item["user_id"] == user1.id

    def test_history_endpoint_with_invalid_page(self, client, app):
        """Test history endpoint with invalid page number (< 1)."""
        with app.app_context():
            user, token = self.create_test_user()
            self.create_test_results(user.id, count=5)

        response = client.get(
            "/api/typo-check/history?page=0",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        # Should default to page 1
        assert data["page"] == 1

    def test_history_endpoint_with_invalid_per_page(self, client, app):
        """Test history endpoint with invalid per_page (< 1)."""
        with app.app_context():
            user, token = self.create_test_user()
            self.create_test_results(user.id, count=5)

        response = client.get(
            "/api/typo-check/history?per_page=0",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        # Should default to per_page 1
        assert data["per_page"] == 1

    def test_history_endpoint_with_large_per_page(self, client, app):
        """Test history endpoint with per_page exceeding maximum (> 100)."""
        with app.app_context():
            user, token = self.create_test_user()
            self.create_test_results(user.id, count=5)

        response = client.get(
            "/api/typo-check/history?per_page=200",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        # Should cap at 100
        assert data["per_page"] == 100


class TestTypoCheckerGetResultEndpoint:
    """Tests for GET /api/typo-check/{id} endpoint (via combined route)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_user_email = "get_result_test@example.com"
        self.test_user_password = "testpassword123"

    def create_test_user(self):
        """Create a test user and return auth token."""
        user = User(
            email=self.test_user_email,
            name="Get Result Test User",
            password=self.test_user_password,
        )
        db.session.add(user)
        db.session.commit()
        token = create_access_token(user.id)
        return user, token

    def test_get_result_success(self, client, app):
        """Test successful GET of a result."""
        with app.app_context():
            user, token = self.create_test_user()

            result = TypoCheckResult(
                user_id=user.id,
                original_text_hash="get_test_hash",
                corrected_text="Test corrected",
                issues="[]",
                provider_used="claude",
            )
            db.session.add(result)
            db.session.commit()
            result_id = result.id

        response = client.get(
            f"/api/typo-check/{result_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "result" in data
        assert data["result"]["id"] == result_id

    def test_get_result_not_found(self, client, app):
        """Test GET of non-existent result returns 404."""
        with app.app_context():
            user, token = self.create_test_user()

        response = client.get(
            "/api/typo-check/99999",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    def test_get_result_access_denied(self, client, app):
        """Test that users cannot GET other users' results."""
        with app.app_context():
            # Create owner
            owner = User(
                email="get_owner@example.com", name="Owner", password="password123"
            )
            db.session.add(owner)
            db.session.commit()

            result = TypoCheckResult(
                user_id=owner.id,
                original_text_hash="owner_get_hash",
                corrected_text="Owner's result",
                issues="[]",
                provider_used="claude",
            )
            db.session.add(result)
            db.session.commit()
            result_id = result.id

            # Create another user
            other_user = User(
                email="get_other@example.com",
                name="Other User",
                password="password123",
            )
            db.session.add(other_user)
            db.session.commit()
            other_token = create_access_token(other_user.id)

        response = client.get(
            f"/api/typo-check/{result_id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )

        assert response.status_code == 403


class TestTypoCheckerDeleteEndpoint:
    """Tests for DELETE /api/typo-check/{id} endpoint."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_user_email = "delete_endpoint_test@example.com"
        self.test_user_password = "testpassword123"

    def create_test_user(self):
        """Create a test user and return auth token."""
        user = User(
            email=self.test_user_email,
            name="Delete Endpoint Test User",
            password=self.test_user_password,
        )
        db.session.add(user)
        db.session.commit()
        token = create_access_token(user.id)
        return user, token

    # TASK-004: DELETE /api/typo-check/{id} endpoint tests

    def test_delete_endpoint_exists(self, client, app):
        """Test that delete endpoint exists."""
        with app.app_context():
            user, token = self.create_test_user()

        response = client.delete(
            "/api/typo-check/1", headers={"Authorization": f"Bearer {token}"}
        )

        # Should not be 405 (Method Not Allowed)
        assert response.status_code != 405

    def test_delete_endpoint_requires_auth(self, client, app):
        """Test that delete endpoint requires authentication."""
        response = client.delete("/api/typo-check/1")

        assert response.status_code == 401

    def test_delete_endpoint_success(self, client, app):
        """Test successful deletion via endpoint."""
        with app.app_context():
            user, token = self.create_test_user()

            result = TypoCheckResult(
                user_id=user.id,
                original_text_hash="delete_test_hash",
                corrected_text="Test",
                issues="[]",
                provider_used="claude",
            )
            db.session.add(result)
            db.session.commit()
            result_id = result.id

        response = client.delete(
            f"/api/typo-check/{result_id}", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data.get("success") is True or "message" in data

        # Verify deletion
        with app.app_context():
            deleted = TypoCheckResult.query.filter_by(id=result_id).first()
            assert deleted is None

    def test_delete_endpoint_not_found(self, client, app):
        """Test deletion of non-existent result returns 404."""
        with app.app_context():
            user, token = self.create_test_user()

        response = client.delete(
            "/api/typo-check/99999", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404

    def test_delete_endpoint_access_denied(self, client, app):
        """Test that users cannot delete other users' results."""
        with app.app_context():
            # Create owner
            owner = User(
                email="delete_owner@example.com", name="Owner", password="password123"
            )
            db.session.add(owner)
            db.session.commit()

            result = TypoCheckResult(
                user_id=owner.id,
                original_text_hash="owner_hash",
                corrected_text="Owner's result",
                issues="[]",
                provider_used="claude",
            )
            db.session.add(result)
            db.session.commit()
            result_id = result.id

            # Create another user
            other_user = User(
                email="delete_other@example.com",
                name="Other User",
                password="password123",
            )
            db.session.add(other_user)
            db.session.commit()
            other_token = create_access_token(other_user.id)

        response = client.delete(
            f"/api/typo-check/{result_id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )

        assert response.status_code == 403

        # Verify result still exists
        with app.app_context():
            still_exists = TypoCheckResult.query.filter_by(id=result_id).first()
            assert still_exists is not None
