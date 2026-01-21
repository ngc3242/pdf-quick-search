"""Tests for signup API endpoint and authentication flows."""

import json


class TestSignupValidation:
    """Test cases for signup input validation."""

    def test_signup_missing_body(self, client):
        """Test signup with no request body returns 400."""
        response = client.post(
            "/api/auth/signup", data=json.dumps({}), content_type="application/json"
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data is not None
        assert "error" in data

    def test_signup_missing_email(self, client):
        """Test signup with missing email returns 400."""
        response = client.post(
            "/api/auth/signup",
            data=json.dumps(
                {
                    "name": "Test User",
                    "phone": "010-1234-5678",
                    "password": "Password123",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "이메일" in response.get_json()["error"]

    def test_signup_missing_name(self, client):
        """Test signup with missing name returns 400."""
        response = client.post(
            "/api/auth/signup",
            data=json.dumps(
                {
                    "email": "test@example.com",
                    "phone": "010-1234-5678",
                    "password": "Password123",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "이름" in response.get_json()["error"]

    def test_signup_missing_phone(self, client):
        """Test signup with missing phone returns 400."""
        response = client.post(
            "/api/auth/signup",
            data=json.dumps(
                {
                    "email": "test@example.com",
                    "name": "Test User",
                    "password": "Password123",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "전화번호" in response.get_json()["error"]

    def test_signup_missing_password(self, client):
        """Test signup with missing password returns 400."""
        response = client.post(
            "/api/auth/signup",
            data=json.dumps(
                {
                    "email": "test@example.com",
                    "name": "Test User",
                    "phone": "010-1234-5678",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "비밀번호" in response.get_json()["error"]

    def test_signup_invalid_email_format(self, client):
        """Test signup with invalid email format returns 400."""
        response = client.post(
            "/api/auth/signup",
            data=json.dumps(
                {
                    "email": "invalid-email",
                    "name": "Test User",
                    "phone": "010-1234-5678",
                    "password": "Password123",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "이메일" in response.get_json()["error"]

    def test_signup_invalid_phone_format(self, client):
        """Test signup with invalid phone format returns 400."""
        response = client.post(
            "/api/auth/signup",
            data=json.dumps(
                {
                    "email": "test@example.com",
                    "name": "Test User",
                    "phone": "123-456-7890",  # Invalid Korean phone format
                    "password": "Password123",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "전화번호" in response.get_json()["error"]

    def test_signup_name_too_short(self, client):
        """Test signup with name less than 2 characters returns 400."""
        response = client.post(
            "/api/auth/signup",
            data=json.dumps(
                {
                    "email": "test@example.com",
                    "name": "A",  # Too short
                    "phone": "010-1234-5678",
                    "password": "Password123",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "이름" in response.get_json()["error"]


class TestSignupPasswordValidation:
    """Test cases for password validation during signup."""

    def test_signup_password_too_short(self, client):
        """Test signup with password less than 8 characters returns 400."""
        response = client.post(
            "/api/auth/signup",
            data=json.dumps(
                {
                    "email": "test@example.com",
                    "name": "Test User",
                    "phone": "010-1234-5678",
                    "password": "Pass1",  # Too short
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "비밀번호" in response.get_json()["error"]
        assert "8자" in response.get_json()["error"]

    def test_signup_password_no_uppercase(self, client):
        """Test signup with password without uppercase returns 400."""
        response = client.post(
            "/api/auth/signup",
            data=json.dumps(
                {
                    "email": "test@example.com",
                    "name": "Test User",
                    "phone": "010-1234-5678",
                    "password": "password123",  # No uppercase
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "대문자" in response.get_json()["error"]

    def test_signup_password_no_lowercase(self, client):
        """Test signup with password without lowercase returns 400."""
        response = client.post(
            "/api/auth/signup",
            data=json.dumps(
                {
                    "email": "test@example.com",
                    "name": "Test User",
                    "phone": "010-1234-5678",
                    "password": "PASSWORD123",  # No lowercase
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "소문자" in response.get_json()["error"]

    def test_signup_password_no_number(self, client):
        """Test signup with password without number returns 400."""
        response = client.post(
            "/api/auth/signup",
            data=json.dumps(
                {
                    "email": "test@example.com",
                    "name": "Test User",
                    "phone": "010-1234-5678",
                    "password": "Passwordabc",  # No number
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "숫자" in response.get_json()["error"]


class TestSignupSuccess:
    """Test cases for successful signup."""

    def test_signup_success(self, app, client):
        """Test successful signup creates user with pending status."""
        response = client.post(
            "/api/auth/signup",
            data=json.dumps(
                {
                    "email": "newuser@example.com",
                    "name": "New User",
                    "phone": "010-1234-5678",
                    "password": "Password123",
                }
            ),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert "message" in data
        assert "user" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["name"] == "New User"
        assert data["user"]["approval_status"] == "pending"

    def test_signup_creates_user_in_database(self, app, client):
        """Test signup actually creates user in database."""
        from app.models.user import User

        response = client.post(
            "/api/auth/signup",
            data=json.dumps(
                {
                    "email": "dbuser@example.com",
                    "name": "DB User",
                    "phone": "010-9876-5432",
                    "password": "Password123",
                }
            ),
            content_type="application/json",
        )

        assert response.status_code == 201

        with app.app_context():
            user = User.query.filter_by(email="dbuser@example.com").first()
            assert user is not None
            assert user.name == "DB User"
            assert user.phone == "010-9876-5432"
            assert user.approval_status == "pending"
            assert user.role == "user"
            assert user.is_active is True

    def test_signup_with_phone_without_dashes(self, app, client):
        """Test signup accepts phone number without dashes."""
        response = client.post(
            "/api/auth/signup",
            data=json.dumps(
                {
                    "email": "nodash@example.com",
                    "name": "No Dash User",
                    "phone": "01012345678",
                    "password": "Password123",
                }
            ),
            content_type="application/json",
        )

        assert response.status_code == 201


class TestSignupDuplicateEmail:
    """Test cases for duplicate email handling."""

    def test_signup_duplicate_email(self, app, client):
        """Test signup with duplicate email returns 409."""
        from app.models import db
        from app.models.user import User

        # Create existing user
        with app.app_context():
            existing = User(
                email="existing@example.com",
                name="Existing User",
                password="Password123",
                phone="010-1111-2222",
                approval_status="approved",
            )
            db.session.add(existing)
            db.session.commit()

        # Try to signup with same email
        response = client.post(
            "/api/auth/signup",
            data=json.dumps(
                {
                    "email": "existing@example.com",
                    "name": "New User",
                    "phone": "010-3333-4444",
                    "password": "Password123",
                }
            ),
            content_type="application/json",
        )

        assert response.status_code == 409
        assert "이미 등록된" in response.get_json()["error"]

    def test_signup_duplicate_email_case_insensitive(self, app, client):
        """Test signup email check is case sensitive (as per current implementation)."""
        from app.models import db
        from app.models.user import User

        # Create existing user
        with app.app_context():
            existing = User(
                email="test@example.com",
                name="Existing User",
                password="Password123",
                phone="010-1111-2222",
                approval_status="approved",
            )
            db.session.add(existing)
            db.session.commit()

        # Try to signup with same email (exact match)
        response = client.post(
            "/api/auth/signup",
            data=json.dumps(
                {
                    "email": "test@example.com",
                    "name": "New User",
                    "phone": "010-3333-4444",
                    "password": "Password123",
                }
            ),
            content_type="application/json",
        )

        assert response.status_code == 409


class TestLoginWithApprovalStatus:
    """Test cases for login behavior based on approval status."""

    def test_login_pending_user_returns_403(self, app, client):
        """Test login with pending user returns 403."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            user = User(
                email="pending@example.com",
                name="Pending User",
                password="Password123",
                phone="010-1234-5678",
                approval_status="pending",
            )
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/api/auth/login",
            data=json.dumps(
                {"email": "pending@example.com", "password": "Password123"}
            ),
            content_type="application/json",
        )

        assert response.status_code == 403
        assert "승인 대기" in response.get_json()["error"]

    def test_login_rejected_user_returns_403(self, app, client):
        """Test login with rejected user returns 403."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            user = User(
                email="rejected@example.com",
                name="Rejected User",
                password="Password123",
                phone="010-1234-5678",
                approval_status="rejected",
            )
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/api/auth/login",
            data=json.dumps(
                {"email": "rejected@example.com", "password": "Password123"}
            ),
            content_type="application/json",
        )

        assert response.status_code == 403
        assert "거부" in response.get_json()["error"]

    def test_login_approved_user_success(self, app, client):
        """Test login with approved user succeeds."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            user = User(
                email="approved@example.com",
                name="Approved User",
                password="Password123",
                phone="010-1234-5678",
                approval_status="approved",
            )
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/api/auth/login",
            data=json.dumps(
                {"email": "approved@example.com", "password": "Password123"}
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data
        assert data["user"]["email"] == "approved@example.com"

    def test_login_admin_bypasses_approval_check(self, app, client):
        """Test admin users can login regardless of approval status."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="Password123",
                role="admin",
                approval_status="pending",  # Even with pending status
            )
            db.session.add(admin)
            db.session.commit()

        response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "Password123"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        assert "access_token" in response.get_json()

    def test_login_deactivated_user_returns_403(self, app, client):
        """Test login with deactivated user returns 403."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            user = User(
                email="deactivated@example.com",
                name="Deactivated User",
                password="Password123",
                phone="010-1234-5678",
                approval_status="approved",
                is_active=False,
            )
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/api/auth/login",
            data=json.dumps(
                {"email": "deactivated@example.com", "password": "Password123"}
            ),
            content_type="application/json",
        )

        assert response.status_code == 403
        assert "deactivated" in response.get_json()["error"].lower()

    def test_login_invalid_credentials(self, app, client):
        """Test login with wrong password returns 401."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            user = User(
                email="user@example.com",
                name="User",
                password="Password123",
                approval_status="approved",
            )
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/api/auth/login",
            data=json.dumps(
                {"email": "user@example.com", "password": "WrongPassword123"}
            ),
            content_type="application/json",
        )

        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user returns 401."""
        response = client.post(
            "/api/auth/login",
            data=json.dumps(
                {"email": "nonexistent@example.com", "password": "Password123"}
            ),
            content_type="application/json",
        )

        assert response.status_code == 401
