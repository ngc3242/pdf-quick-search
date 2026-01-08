"""Tests for admin API endpoints and service."""

import pytest
import json


class TestAdminDecorator:
    """Test cases for @admin_required decorator."""

    def test_admin_required_allows_admin(self, app, client):
        """Test admin decorator allows admin users."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()

        # Login as admin
        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        # Access admin endpoint
        response = client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

    def test_admin_required_denies_regular_user(self, app, client):
        """Test admin decorator returns 403 for non-admin users."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            user = User(
                email="user@example.com",
                name="Regular User",
                password="password123",
                role="user"
            )
            db.session.add(user)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "user@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        response = client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403

    def test_admin_required_no_token(self, client):
        """Test admin endpoint returns 401 without token."""
        response = client.get("/api/admin/users")
        assert response.status_code == 401


class TestAdminListUsers:
    """Test cases for list users endpoint."""

    def test_list_users_returns_all_users(self, app, client):
        """Test listing all users with document counts."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin"
            )
            user1 = User(
                email="user1@example.com",
                name="User 1",
                password="password123"
            )
            user2 = User(
                email="user2@example.com",
                name="User 2",
                password="password123"
            )
            db.session.add_all([admin, user1, user2])
            db.session.commit()

            # Add documents for user1
            doc = SearchDocument(
                owner_id=user1.id,
                filename="doc.pdf",
                original_filename="doc.pdf",
                file_path="/storage/doc.pdf"
            )
            db.session.add(doc)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        response = client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "users" in data
        assert len(data["users"]) == 3

        # Check document count is included
        user1_data = next(u for u in data["users"] if u["email"] == "user1@example.com")
        assert user1_data["document_count"] == 1


class TestAdminCreateUser:
    """Test cases for create user endpoint."""

    def test_create_user_success(self, app, client):
        """Test creating a new user."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        response = client.post(
            "/api/admin/users",
            data=json.dumps({
                "email": "newuser@example.com",
                "name": "New User",
                "password": "newpassword123"
            }),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["user"]["email"] == "newuser@example.com"

    def test_create_user_duplicate_email(self, app, client):
        """Test creating user with duplicate email returns 400."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin"
            )
            existing = User(
                email="existing@example.com",
                name="Existing User",
                password="password123"
            )
            db.session.add_all([admin, existing])
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        response = client.post(
            "/api/admin/users",
            data=json.dumps({
                "email": "existing@example.com",
                "name": "Duplicate User",
                "password": "password123"
            }),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400
        assert "email" in response.get_json()["error"].lower()

    def test_create_user_missing_fields(self, app, client):
        """Test creating user with missing fields returns 400."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        response = client.post(
            "/api/admin/users",
            data=json.dumps({"email": "newuser@example.com"}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400


class TestAdminUpdateUser:
    """Test cases for update user endpoint."""

    def test_update_user_success(self, app, client):
        """Test updating user info."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin"
            )
            user = User(
                email="user@example.com",
                name="Original Name",
                password="password123"
            )
            db.session.add_all([admin, user])
            db.session.commit()
            user_id = user.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        response = client.patch(
            f"/api/admin/users/{user_id}",
            data=json.dumps({
                "name": "Updated Name",
                "phone": "123-456-7890"
            }),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["user"]["name"] == "Updated Name"
        assert data["user"]["phone"] == "123-456-7890"

    def test_update_user_role(self, app, client):
        """Test updating user role."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin"
            )
            user = User(
                email="user@example.com",
                name="User",
                password="password123",
                role="user"
            )
            db.session.add_all([admin, user])
            db.session.commit()
            user_id = user.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        response = client.patch(
            f"/api/admin/users/{user_id}",
            data=json.dumps({"role": "admin"}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.get_json()["user"]["role"] == "admin"

    def test_update_user_is_active(self, app, client):
        """Test deactivating a user."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin"
            )
            user = User(
                email="user@example.com",
                name="User",
                password="password123"
            )
            db.session.add_all([admin, user])
            db.session.commit()
            user_id = user.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        response = client.patch(
            f"/api/admin/users/{user_id}",
            data=json.dumps({"is_active": False}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.get_json()["user"]["is_active"] is False

    def test_update_nonexistent_user(self, app, client):
        """Test updating non-existent user returns 404."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        response = client.patch(
            "/api/admin/users/nonexistent-id",
            data=json.dumps({"name": "Test"}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404


class TestAdminResetPassword:
    """Test cases for password reset endpoint."""

    def test_reset_password_success(self, app, client):
        """Test resetting a user's password."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin"
            )
            user = User(
                email="user@example.com",
                name="User",
                password="oldpassword"
            )
            db.session.add_all([admin, user])
            db.session.commit()
            user_id = user.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        response = client.post(
            f"/api/admin/users/{user_id}/password",
            data=json.dumps({"new_password": "newpassword123"}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

        # Verify new password works
        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "user@example.com", "password": "newpassword123"}),
            content_type="application/json"
        )
        assert login_response.status_code == 200


class TestAdminDeleteUser:
    """Test cases for delete user endpoint."""

    def test_delete_user_success(self, app, client):
        """Test deleting a user."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin"
            )
            user = User(
                email="user@example.com",
                name="User",
                password="password123"
            )
            db.session.add_all([admin, user])
            db.session.commit()
            user_id = user.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        response = client.delete(
            f"/api/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

        # Verify user is deleted
        with app.app_context():
            deleted = User.query.filter_by(id=user_id).first()
            assert deleted is None

    def test_delete_user_cascade_documents(self, app, client):
        """Test deleting user also deletes their documents."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin"
            )
            user = User(
                email="user@example.com",
                name="User",
                password="password123"
            )
            db.session.add_all([admin, user])
            db.session.commit()
            user_id = user.id

            doc = SearchDocument(
                owner_id=user.id,
                filename="doc.pdf",
                original_filename="doc.pdf",
                file_path="/storage/doc.pdf"
            )
            db.session.add(doc)
            db.session.commit()
            doc_id = doc.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        response = client.delete(
            f"/api/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

        # Verify document is also deleted
        with app.app_context():
            deleted_doc = SearchDocument.query.filter_by(id=doc_id).first()
            assert deleted_doc is None


class TestAdminGetUserDocuments:
    """Test cases for getting user's documents."""

    def test_get_user_documents(self, app, client):
        """Test getting a specific user's documents."""
        from app.models import db
        from app.models.user import User
        from app.models.document import SearchDocument

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin"
            )
            user = User(
                email="user@example.com",
                name="User",
                password="password123"
            )
            db.session.add_all([admin, user])
            db.session.commit()
            user_id = user.id

            doc1 = SearchDocument(
                owner_id=user.id,
                filename="doc1.pdf",
                original_filename="doc1.pdf",
                file_path="/storage/doc1.pdf"
            )
            doc2 = SearchDocument(
                owner_id=user.id,
                filename="doc2.pdf",
                original_filename="doc2.pdf",
                file_path="/storage/doc2.pdf"
            )
            db.session.add_all([doc1, doc2])
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json"
        )
        token = login_response.get_json()["access_token"]

        response = client.get(
            f"/api/admin/users/{user_id}/documents",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["documents"]) == 2
