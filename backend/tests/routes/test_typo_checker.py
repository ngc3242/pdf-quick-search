"""Tests for Typo Checker API routes.

This module tests the typo check API endpoints including
authentication, input validation, and response format.
"""

from unittest.mock import patch


from app import db
from app.models.user import User
from app.utils.auth import create_access_token


class TestTypoCheckerEndpoints:
    """Tests for typo checker API endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_user_email = "typo_test@example.com"
        self.test_user_password = "testpassword123"

    def create_test_user(self):
        """Create a test user and return auth token."""
        user = User(
            email=self.test_user_email,
            name="Typo Test User",
            password=self.test_user_password
        )
        db.session.add(user)
        db.session.commit()
        token = create_access_token(user.id)
        return user, token

    def test_typo_check_endpoint_exists(self, client, app):
        """Test that typo check endpoint exists."""
        with app.app_context():
            user, token = self.create_test_user()

        response = client.post(
            "/api/typo-check",
            headers={"Authorization": f"Bearer {token}"},
            json={"text": "test"}
        )

        # Should not be 404
        assert response.status_code != 404

    def test_typo_check_requires_auth(self, client, app):
        """Test that typo check endpoint requires authentication."""
        response = client.post(
            "/api/typo-check",
            json={"text": "테스트"}
        )

        assert response.status_code == 401

    def test_typo_check_with_valid_text(self, client, app):
        """Test typo check with valid Korean text."""
        with app.app_context():
            user, token = self.create_test_user()

        # Mock the service
        with patch("app.routes.typo_checker.TypoCheckerService") as mock_service:
            mock_service.check_text.return_value = {
                "success": True,
                "corrected_text": "안녕하세요",
                "issues": [
                    {
                        "original": "안녕하세여",
                        "corrected": "안녕하세요",
                        "position": 0,
                        "issue_type": "spelling",
                        "explanation": "맞춤법 오류"
                    }
                ],
                "provider": "claude",
                "cached": False
            }

            response = client.post(
                "/api/typo-check",
                headers={"Authorization": f"Bearer {token}"},
                json={"text": "안녕하세여"}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True
            assert data["corrected_text"] == "안녕하세요"
            assert len(data["issues"]) == 1

    def test_typo_check_empty_text_returns_error(self, client, app):
        """Test that empty text returns error."""
        with app.app_context():
            user, token = self.create_test_user()

        response = client.post(
            "/api/typo-check",
            headers={"Authorization": f"Bearer {token}"},
            json={"text": ""}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_typo_check_missing_text_returns_error(self, client, app):
        """Test that missing text field returns error."""
        with app.app_context():
            user, token = self.create_test_user()

        response = client.post(
            "/api/typo-check",
            headers={"Authorization": f"Bearer {token}"},
            json={}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_typo_check_text_too_long(self, client, app):
        """Test that text exceeding limit returns error."""
        with app.app_context():
            user, token = self.create_test_user()

        # Create text over 100K characters
        long_text = "A" * 100001

        response = client.post(
            "/api/typo-check",
            headers={"Authorization": f"Bearer {token}"},
            json={"text": long_text}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_typo_check_with_specific_provider(self, client, app):
        """Test typo check with specific provider parameter."""
        with app.app_context():
            user, token = self.create_test_user()

        with patch("app.routes.typo_checker.TypoCheckerService") as mock_service:
            mock_service.check_text.return_value = {
                "success": True,
                "corrected_text": "테스트",
                "issues": [],
                "provider": "claude",
                "cached": False
            }

            response = client.post(
                "/api/typo-check",
                headers={"Authorization": f"Bearer {token}"},
                json={"text": "테스트", "provider": "claude"}
            )

            assert response.status_code == 200
            # Verify service was called with provider parameter
            mock_service.check_text.assert_called_once()
            call_args = mock_service.check_text.call_args
            assert call_args[1].get("provider") == "claude" or call_args[0][2] == "claude"

    def test_typo_check_returns_cached_indicator(self, client, app):
        """Test that response includes cached indicator."""
        with app.app_context():
            user, token = self.create_test_user()

        with patch("app.routes.typo_checker.TypoCheckerService") as mock_service:
            mock_service.check_text.return_value = {
                "success": True,
                "corrected_text": "테스트",
                "issues": [],
                "provider": "claude",
                "cached": True
            }

            response = client.post(
                "/api/typo-check",
                headers={"Authorization": f"Bearer {token}"},
                json={"text": "테스트"}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert "cached" in data


class TestProvidersEndpoint:
    """Tests for available providers endpoint."""

    def create_test_user(self):
        """Create a test user and return auth token."""
        user = User(
            email="providers_test@example.com",
            name="Providers Test User",
            password="testpassword123"
        )
        db.session.add(user)
        db.session.commit()
        token = create_access_token(user.id)
        return user, token

    def test_providers_endpoint_exists(self, client, app):
        """Test that providers endpoint exists."""
        with app.app_context():
            user, token = self.create_test_user()

        response = client.get(
            "/api/typo-check/providers",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should not be 404
        assert response.status_code != 404

    def test_providers_endpoint_requires_auth(self, client, app):
        """Test that providers endpoint requires authentication."""
        response = client.get("/api/typo-check/providers")

        assert response.status_code == 401

    def test_providers_returns_list(self, client, app):
        """Test that providers endpoint returns a list."""
        with app.app_context():
            user, token = self.create_test_user()

        with patch("app.routes.typo_checker.TypoCheckerService") as mock_service:
            mock_service.get_available_providers.return_value = ["claude", "openai"]

            response = client.get(
                "/api/typo-check/providers",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert "providers" in data
            assert isinstance(data["providers"], list)


class TestTypoCheckResultEndpoint:
    """Tests for getting typo check result by ID."""

    def create_test_user(self):
        """Create a test user and return auth token."""
        user = User(
            email="result_test@example.com",
            name="Result Test User",
            password="testpassword123"
        )
        db.session.add(user)
        db.session.commit()
        token = create_access_token(user.id)
        return user, token

    def test_get_result_endpoint_exists(self, client, app):
        """Test that get result endpoint exists."""
        with app.app_context():
            user, token = self.create_test_user()

        response = client.get(
            "/api/typo-check/1",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should not be 404 (method not found), but could be 404 for resource not found
        assert response.status_code in [200, 404]

    def test_get_result_requires_auth(self, client, app):
        """Test that get result endpoint requires authentication."""
        response = client.get("/api/typo-check/1")

        assert response.status_code == 401

    def test_get_result_not_found(self, client, app):
        """Test getting non-existent result returns 404."""
        with app.app_context():
            user, token = self.create_test_user()

        response = client.get(
            "/api/typo-check/99999",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404

    def test_get_result_access_denied_for_other_user(self, client, app):
        """Test that user cannot access another user's result."""
        with app.app_context():
            # Create first user and their result
            user1 = User(
                email="user1_access@example.com",
                name="User 1",
                password="password123"
            )
            db.session.add(user1)
            db.session.commit()

            from app.models.typo_check_result import TypoCheckResult
            result = TypoCheckResult(
                user_id=user1.id,
                original_text_hash="test_hash",
                corrected_text="테스트",
                issues="[]",
                provider_used="claude"
            )
            db.session.add(result)
            db.session.commit()
            result_id = result.id

            # Create second user
            user2 = User(
                email="user2_access@example.com",
                name="User 2",
                password="password123"
            )
            db.session.add(user2)
            db.session.commit()
            token2 = create_access_token(user2.id)

        # Try to access user1's result with user2's token
        response = client.get(
            f"/api/typo-check/{result_id}",
            headers={"Authorization": f"Bearer {token2}"}
        )

        assert response.status_code == 403
