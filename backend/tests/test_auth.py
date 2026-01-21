"""Tests for authentication API."""

import pytest
import json
from datetime import datetime, timedelta, timezone


class TestAuthLogin:
    """Test cases for login endpoint."""

    def test_login_success(self, app, client):
        """Test successful login returns JWT token."""
        from app.models.user import User
        from app.models import db

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123",
                approval_status="approved"
            )
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "test@example.com", "password": "password123"}),
            content_type="application/json"
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"

    def test_login_invalid_email(self, app, client):
        """Test login with non-existent email returns 401."""
        response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "nonexistent@example.com", "password": "password123"}),
            content_type="application/json"
        )

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data

    def test_login_wrong_password(self, app, client):
        """Test login with wrong password returns 401."""
        from app.models.user import User
        from app.models import db

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123",
                approval_status="approved"
            )
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "test@example.com", "password": "wrongpassword"}),
            content_type="application/json"
        )

        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        """Test login with missing fields returns 400."""
        response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "test@example.com"}),
            content_type="application/json"
        )

        assert response.status_code == 400

    def test_login_inactive_user(self, app, client):
        """Test login with inactive user returns 403."""
        from app.models.user import User
        from app.models import db

        with app.app_context():
            user = User(
                email="inactive@example.com",
                name="Inactive User",
                password="password123",
                is_active=False,
                approval_status="approved"
            )
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "inactive@example.com", "password": "password123"}),
            content_type="application/json"
        )

        assert response.status_code == 403
        data = response.get_json()
        assert data["error"] == "Account is deactivated"

    def test_login_pending_user(self, app, client):
        """Test login with pending approval status returns 403."""
        from app.models.user import User
        from app.models import db

        with app.app_context():
            user = User(
                email="pending@example.com",
                name="Pending User",
                password="password123",
                approval_status="pending"
            )
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "pending@example.com", "password": "password123"}),
            content_type="application/json"
        )

        assert response.status_code == 403
        data = response.get_json()
        assert data["error"] == "계정이 관리자 승인 대기 중입니다."

    def test_login_rejected_user(self, app, client):
        """Test login with rejected approval status returns 403."""
        from app.models.user import User
        from app.models import db

        with app.app_context():
            user = User(
                email="rejected@example.com",
                name="Rejected User",
                password="password123",
                approval_status="rejected"
            )
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "rejected@example.com", "password": "password123"}),
            content_type="application/json"
        )

        assert response.status_code == 403
        data = response.get_json()
        assert data["error"] == "계정이 거부되었습니다. 관리자에게 문의하세요."

    def test_login_admin_bypasses_approval_check(self, app, client):
        """Test admin users can login regardless of approval status."""
        from app.models.user import User
        from app.models import db

        with app.app_context():
            user = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin",
                approval_status="pending"  # Even with pending status
            )
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json"
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data


class TestAuthLogout:
    """Test cases for logout endpoint."""

    def test_logout_success(self, app, client):
        """Test successful logout blacklists token."""
        from app.models.user import User
        from app.models.token_blacklist import TokenBlacklist
        from app.models import db

        # Create user and login
        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123",
                approval_status="approved"
            )
            db.session.add(user)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "test@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        # Logout
        logout_response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert logout_response.status_code == 200
        data = logout_response.get_json()
        assert data["message"] == "Successfully logged out"

    def test_logout_no_token(self, client):
        """Test logout without token returns 401."""
        response = client.post("/api/auth/logout")
        assert response.status_code == 401

    def test_logout_token_blacklisted(self, app, client):
        """Test using blacklisted token returns 401."""
        from app.models.user import User
        from app.models import db

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123",
                approval_status="approved"
            )
            db.session.add(user)
            db.session.commit()

        # Login
        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "test@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        # Logout (blacklist token)
        client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Try to use blacklisted token
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 401


class TestAuthMe:
    """Test cases for current user endpoint."""

    def test_me_returns_current_user(self, app, client):
        """Test /me endpoint returns current user info."""
        from app.models.user import User
        from app.models import db

        with app.app_context():
            user = User(
                email="test@example.com",
                name="Test User",
                password="password123",
                approval_status="approved"
            )
            db.session.add(user)
            db.session.commit()

        # Login
        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "test@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        # Get current user
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["name"] == "Test User"

    def test_me_without_token(self, client):
        """Test /me endpoint without token returns 401."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_me_with_invalid_token(self, client):
        """Test /me endpoint with invalid token returns 401."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
