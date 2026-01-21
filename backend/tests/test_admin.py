"""Tests for admin API endpoints and service."""

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
                role="admin",
                approval_status="approved",
            )
            db.session.add(admin)
            db.session.commit()

        # Login as admin
        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        # Access admin endpoint
        response = client.get(
            "/api/admin/users", headers={"Authorization": f"Bearer {token}"}
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
                role="user",
                approval_status="approved",
            )
            db.session.add(user)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "user@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.get(
            "/api/admin/users", headers={"Authorization": f"Bearer {token}"}
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
                role="admin",
                approval_status="approved",
            )
            user1 = User(
                email="user1@example.com",
                name="User 1",
                password="password123",
                approval_status="approved",
            )
            user2 = User(
                email="user2@example.com",
                name="User 2",
                password="password123",
                approval_status="approved",
            )
            db.session.add_all([admin, user1, user2])
            db.session.commit()

            # Add documents for user1
            doc = SearchDocument(
                owner_id=user1.id,
                filename="doc.pdf",
                original_filename="doc.pdf",
                file_path="/storage/doc.pdf",
            )
            db.session.add(doc)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.get(
            "/api/admin/users", headers={"Authorization": f"Bearer {token}"}
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
                role="admin",
                approval_status="approved",
            )
            db.session.add(admin)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.post(
            "/api/admin/users",
            data=json.dumps(
                {
                    "email": "newuser@example.com",
                    "name": "New User",
                    "password": "newpassword123",
                }
            ),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
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
                role="admin",
                approval_status="approved",
            )
            existing = User(
                email="existing@example.com",
                name="Existing User",
                password="password123",
                approval_status="approved",
            )
            db.session.add_all([admin, existing])
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.post(
            "/api/admin/users",
            data=json.dumps(
                {
                    "email": "existing@example.com",
                    "name": "Duplicate User",
                    "password": "password123",
                }
            ),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
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
                role="admin",
                approval_status="approved",
            )
            db.session.add(admin)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.post(
            "/api/admin/users",
            data=json.dumps({"email": "newuser@example.com"}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
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
                role="admin",
                approval_status="approved",
            )
            user = User(
                email="user@example.com",
                name="Original Name",
                password="password123",
                approval_status="approved",
            )
            db.session.add_all([admin, user])
            db.session.commit()
            user_id = user.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.patch(
            f"/api/admin/users/{user_id}",
            data=json.dumps({"name": "Updated Name", "phone": "123-456-7890"}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
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
                role="admin",
                approval_status="approved",
            )
            user = User(
                email="user@example.com",
                name="User",
                password="password123",
                role="user",
                approval_status="approved",
            )
            db.session.add_all([admin, user])
            db.session.commit()
            user_id = user.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.patch(
            f"/api/admin/users/{user_id}",
            data=json.dumps({"role": "admin"}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
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
                role="admin",
                approval_status="approved",
            )
            user = User(
                email="user@example.com",
                name="User",
                password="password123",
                approval_status="approved",
            )
            db.session.add_all([admin, user])
            db.session.commit()
            user_id = user.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.patch(
            f"/api/admin/users/{user_id}",
            data=json.dumps({"is_active": False}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
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
                role="admin",
                approval_status="approved",
            )
            db.session.add(admin)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.patch(
            "/api/admin/users/nonexistent-id",
            data=json.dumps({"name": "Test"}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
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
                role="admin",
                approval_status="approved",
            )
            user = User(
                email="user@example.com",
                name="User",
                password="oldpassword",
                approval_status="approved",
            )
            db.session.add_all([admin, user])
            db.session.commit()
            user_id = user.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.post(
            f"/api/admin/users/{user_id}/password",
            data=json.dumps({"new_password": "newpassword123"}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

        # Verify new password works
        login_response = client.post(
            "/api/auth/login",
            data=json.dumps(
                {"email": "user@example.com", "password": "newpassword123"}
            ),
            content_type="application/json",
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
                role="admin",
                approval_status="approved",
            )
            user = User(
                email="user@example.com",
                name="User",
                password="password123",
                approval_status="approved",
            )
            db.session.add_all([admin, user])
            db.session.commit()
            user_id = user.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.delete(
            f"/api/admin/users/{user_id}", headers={"Authorization": f"Bearer {token}"}
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
                role="admin",
                approval_status="approved",
            )
            user = User(
                email="user@example.com",
                name="User",
                password="password123",
                approval_status="approved",
            )
            db.session.add_all([admin, user])
            db.session.commit()
            user_id = user.id

            doc = SearchDocument(
                owner_id=user.id,
                filename="doc.pdf",
                original_filename="doc.pdf",
                file_path="/storage/doc.pdf",
            )
            db.session.add(doc)
            db.session.commit()
            doc_id = doc.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.delete(
            f"/api/admin/users/{user_id}", headers={"Authorization": f"Bearer {token}"}
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
                role="admin",
                approval_status="approved",
            )
            user = User(
                email="user@example.com",
                name="User",
                password="password123",
                approval_status="approved",
            )
            db.session.add_all([admin, user])
            db.session.commit()
            user_id = user.id

            doc1 = SearchDocument(
                owner_id=user.id,
                filename="doc1.pdf",
                original_filename="doc1.pdf",
                file_path="/storage/doc1.pdf",
            )
            doc2 = SearchDocument(
                owner_id=user.id,
                filename="doc2.pdf",
                original_filename="doc2.pdf",
                file_path="/storage/doc2.pdf",
            )
            db.session.add_all([doc1, doc2])
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.get(
            f"/api/admin/users/{user_id}/documents",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["documents"]) == 2


class TestAdminListPendingUsers:
    """Test cases for listing pending users endpoint."""

    def test_list_pending_users_returns_only_pending(self, app, client):
        """Test listing pending users only returns users with pending status."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin",
                approval_status="approved",
            )
            pending1 = User(
                email="pending1@example.com",
                name="Pending User 1",
                password="password123",
                phone="010-1111-1111",
                approval_status="pending",
            )
            pending2 = User(
                email="pending2@example.com",
                name="Pending User 2",
                password="password123",
                phone="010-2222-2222",
                approval_status="pending",
            )
            approved = User(
                email="approved@example.com",
                name="Approved User",
                password="password123",
                approval_status="approved",
            )
            rejected = User(
                email="rejected@example.com",
                name="Rejected User",
                password="password123",
                approval_status="rejected",
            )
            db.session.add_all([admin, pending1, pending2, approved, rejected])
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.get(
            "/api/admin/users/pending", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "users" in data
        assert "total" in data
        assert data["total"] == 2
        assert len(data["users"]) == 2

        # Verify all returned users are pending
        for user in data["users"]:
            assert user["approval_status"] == "pending"

        # Verify correct users are returned
        emails = [u["email"] for u in data["users"]]
        assert "pending1@example.com" in emails
        assert "pending2@example.com" in emails
        assert "approved@example.com" not in emails
        assert "rejected@example.com" not in emails

    def test_list_pending_users_includes_user_info(self, app, client):
        """Test pending users list includes necessary user information."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin",
                approval_status="approved",
            )
            pending = User(
                email="pending@example.com",
                name="Pending User",
                password="password123",
                phone="010-1234-5678",
                approval_status="pending",
            )
            db.session.add_all([admin, pending])
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.get(
            "/api/admin/users/pending", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.get_json()
        user = data["users"][0]

        # Check required fields are present
        assert "id" in user
        assert "email" in user
        assert "name" in user
        assert "phone" in user
        assert "approval_status" in user
        assert "created_at" in user

        assert user["email"] == "pending@example.com"
        assert user["name"] == "Pending User"
        assert user["phone"] == "010-1234-5678"

    def test_list_pending_users_empty(self, app, client):
        """Test listing pending users when no pending users exist."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin",
                approval_status="approved",
            )
            db.session.add(admin)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.get(
            "/api/admin/users/pending", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["total"] == 0
        assert len(data["users"]) == 0


class TestAdminApproveUser:
    """Test cases for approving users."""

    def test_approve_user_success(self, app, client):
        """Test successfully approving a pending user."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin",
                approval_status="approved",
            )
            pending = User(
                email="pending@example.com",
                name="Pending User",
                password="password123",
                phone="010-1234-5678",
                approval_status="pending",
            )
            db.session.add_all([admin, pending])
            db.session.commit()
            pending_id = pending.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.post(
            f"/api/admin/users/{pending_id}/approve",
            data=json.dumps({}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert data["user"]["approval_status"] == "approved"
        assert data["user"]["approved_at"] is not None

    def test_approve_user_sets_status_in_database(self, app, client):
        """Test approving user updates database correctly."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin",
                approval_status="approved",
            )
            pending = User(
                email="pending@example.com",
                name="Pending User",
                password="password123",
                approval_status="pending",
            )
            db.session.add_all([admin, pending])
            db.session.commit()
            pending_id = pending.id
            admin_id = admin.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        client.post(
            f"/api/admin/users/{pending_id}/approve",
            data=json.dumps({}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

        with app.app_context():
            user = User.query.filter_by(id=pending_id).first()
            assert user.approval_status == "approved"
            assert user.approved_at is not None
            assert user.approved_by_id == admin_id

    def test_approve_user_with_role(self, app, client):
        """Test approving user with custom role."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin",
                approval_status="approved",
            )
            pending = User(
                email="pending@example.com",
                name="Pending User",
                password="password123",
                approval_status="pending",
            )
            db.session.add_all([admin, pending])
            db.session.commit()
            pending_id = pending.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.post(
            f"/api/admin/users/{pending_id}/approve",
            data=json.dumps({"role": "admin"}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

        with app.app_context():
            user = User.query.filter_by(id=pending_id).first()
            assert user.role == "admin"

    def test_approve_user_allows_login(self, app, client):
        """Test approved user can now login."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin",
                approval_status="approved",
            )
            pending = User(
                email="pending@example.com",
                name="Pending User",
                password="Password123",
                approval_status="pending",
            )
            db.session.add_all([admin, pending])
            db.session.commit()
            pending_id = pending.id

        # Login as admin
        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        # Approve user
        client.post(
            f"/api/admin/users/{pending_id}/approve",
            data=json.dumps({}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Try to login as approved user
        response = client.post(
            "/api/auth/login",
            data=json.dumps(
                {"email": "pending@example.com", "password": "Password123"}
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        assert "access_token" in response.get_json()

    def test_approve_already_approved_user_returns_400(self, app, client):
        """Test approving already approved user returns 400."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin",
                approval_status="approved",
            )
            approved = User(
                email="approved@example.com",
                name="Approved User",
                password="password123",
                approval_status="approved",
            )
            db.session.add_all([admin, approved])
            db.session.commit()
            approved_id = approved.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.post(
            f"/api/admin/users/{approved_id}/approve",
            data=json.dumps({}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert "이미 승인된" in response.get_json()["error"]

    def test_approve_rejected_user_returns_400(self, app, client):
        """Test approving rejected user returns 400."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin",
                approval_status="approved",
            )
            rejected = User(
                email="rejected@example.com",
                name="Rejected User",
                password="password123",
                approval_status="rejected",
            )
            db.session.add_all([admin, rejected])
            db.session.commit()
            rejected_id = rejected.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.post(
            f"/api/admin/users/{rejected_id}/approve",
            data=json.dumps({}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert "이미 거부된" in response.get_json()["error"]

    def test_approve_nonexistent_user_returns_404(self, app, client):
        """Test approving non-existent user returns 404."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin",
                approval_status="approved",
            )
            db.session.add(admin)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.post(
            "/api/admin/users/nonexistent-id/approve",
            data=json.dumps({}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        assert "찾을 수 없습니다" in response.get_json()["error"]


class TestAdminRejectUser:
    """Test cases for rejecting users."""

    def test_reject_user_success(self, app, client):
        """Test successfully rejecting a pending user."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin",
                approval_status="approved",
            )
            pending = User(
                email="pending@example.com",
                name="Pending User",
                password="password123",
                approval_status="pending",
            )
            db.session.add_all([admin, pending])
            db.session.commit()
            pending_id = pending.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.post(
            f"/api/admin/users/{pending_id}/reject",
            data=json.dumps({"reason": "Not eligible for access"}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert data["user"]["approval_status"] == "rejected"

    def test_reject_user_saves_reason(self, app, client):
        """Test rejecting user saves rejection reason."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin",
                approval_status="approved",
            )
            pending = User(
                email="pending@example.com",
                name="Pending User",
                password="password123",
                approval_status="pending",
            )
            db.session.add_all([admin, pending])
            db.session.commit()
            pending_id = pending.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        rejection_reason = "User does not meet membership criteria"

        client.post(
            f"/api/admin/users/{pending_id}/reject",
            data=json.dumps({"reason": rejection_reason}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

        with app.app_context():
            user = User.query.filter_by(id=pending_id).first()
            assert user.approval_status == "rejected"
            assert user.approval_reason == rejection_reason

    def test_reject_user_without_reason_returns_400(self, app, client):
        """Test rejecting user without reason returns 400."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin",
                approval_status="approved",
            )
            pending = User(
                email="pending@example.com",
                name="Pending User",
                password="password123",
                approval_status="pending",
            )
            db.session.add_all([admin, pending])
            db.session.commit()
            pending_id = pending.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        # Empty body (no reason)
        response = client.post(
            f"/api/admin/users/{pending_id}/reject",
            data=json.dumps({}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert "거부 사유" in response.get_json()["error"]

    def test_reject_user_with_empty_reason_returns_400(self, app, client):
        """Test rejecting user with empty reason returns 400."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin",
                approval_status="approved",
            )
            pending = User(
                email="pending@example.com",
                name="Pending User",
                password="password123",
                approval_status="pending",
            )
            db.session.add_all([admin, pending])
            db.session.commit()
            pending_id = pending.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.post(
            f"/api/admin/users/{pending_id}/reject",
            data=json.dumps({"reason": "   "}),  # Empty/whitespace reason
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert "거부 사유" in response.get_json()["error"]

    def test_reject_already_approved_user_returns_400(self, app, client):
        """Test rejecting already approved user returns 400."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin",
                approval_status="approved",
            )
            approved = User(
                email="approved@example.com",
                name="Approved User",
                password="password123",
                approval_status="approved",
            )
            db.session.add_all([admin, approved])
            db.session.commit()
            approved_id = approved.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.post(
            f"/api/admin/users/{approved_id}/reject",
            data=json.dumps({"reason": "Testing rejection"}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert "이미 승인된" in response.get_json()["error"]

    def test_reject_already_rejected_user_returns_400(self, app, client):
        """Test rejecting already rejected user returns 400."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin",
                approval_status="approved",
            )
            rejected = User(
                email="rejected@example.com",
                name="Rejected User",
                password="password123",
                approval_status="rejected",
            )
            db.session.add_all([admin, rejected])
            db.session.commit()
            rejected_id = rejected.id

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.post(
            f"/api/admin/users/{rejected_id}/reject",
            data=json.dumps({"reason": "Testing rejection again"}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert "이미 거부된" in response.get_json()["error"]

    def test_reject_nonexistent_user_returns_404(self, app, client):
        """Test rejecting non-existent user returns 404."""
        from app.models import db
        from app.models.user import User

        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin User",
                password="password123",
                role="admin",
                approval_status="approved",
            )
            db.session.add(admin)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.post(
            "/api/admin/users/nonexistent-id/reject",
            data=json.dumps({"reason": "Test reason"}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        assert "찾을 수 없습니다" in response.get_json()["error"]
