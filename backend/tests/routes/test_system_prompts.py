"""Tests for system prompts API endpoints."""

import json

from app import db
from app.models.user import User
from app.models.system_prompt import SystemPromptConfig


class TestSystemPromptsEndpointAuth:
    """Test authentication for system prompts endpoints."""

    def test_get_prompts_requires_auth(self, client):
        """Test GET /api/admin/system-prompts requires authentication."""
        response = client.get("/api/admin/system-prompts")
        assert response.status_code == 401

    def test_get_prompts_requires_admin(self, app, client):
        """Test GET /api/admin/system-prompts requires admin role."""
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

        # Login as regular user
        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "user@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.get(
            "/api/admin/system-prompts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


class TestGetAllSystemPrompts:
    """Tests for GET /api/admin/system-prompts."""

    def test_get_all_prompts_empty(self, app, client):
        """Test getting prompts when none are configured."""
        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin",
                password="password123",
                role="admin",
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
            "/api/admin/system-prompts",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "prompts" in data
        # Should have default prompts for all providers
        assert len(data["prompts"]) == 3
        providers = [p["provider"] for p in data["prompts"]]
        assert "claude" in providers
        assert "gemini" in providers
        assert "openai" in providers

    def test_get_all_prompts_with_custom(self, app, client):
        """Test getting prompts with custom configurations."""
        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin",
                password="password123",
                role="admin",
            )
            custom_prompt = SystemPromptConfig(
                provider="claude",
                prompt="Custom Claude prompt",
            )
            db.session.add(admin)
            db.session.add(custom_prompt)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.get(
            "/api/admin/system-prompts",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["prompts"]) == 3

        claude_prompt = next(p for p in data["prompts"] if p["provider"] == "claude")
        assert claude_prompt["prompt"] == "Custom Claude prompt"
        assert claude_prompt["is_custom"] is True


class TestGetSystemPrompt:
    """Tests for GET /api/admin/system-prompts/<provider>."""

    def test_get_prompt_default(self, app, client):
        """Test getting default prompt for a provider."""
        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin",
                password="password123",
                role="admin",
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
            "/api/admin/system-prompts/claude",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["provider"] == "claude"
        assert "prompt" in data
        assert data["is_custom"] is False

    def test_get_prompt_custom(self, app, client):
        """Test getting custom prompt for a provider."""
        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin",
                password="password123",
                role="admin",
            )
            custom_prompt = SystemPromptConfig(
                provider="gemini",
                prompt="My custom Gemini prompt",
            )
            db.session.add(admin)
            db.session.add(custom_prompt)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.get(
            "/api/admin/system-prompts/gemini",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["provider"] == "gemini"
        assert data["prompt"] == "My custom Gemini prompt"
        assert data["is_custom"] is True

    def test_get_prompt_invalid_provider(self, app, client):
        """Test getting prompt for invalid provider returns 400."""
        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin",
                password="password123",
                role="admin",
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
            "/api/admin/system-prompts/invalid_provider",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert "error" in response.get_json()


class TestUpdateSystemPrompt:
    """Tests for PUT /api/admin/system-prompts/<provider>."""

    def test_update_prompt_create_new(self, app, client):
        """Test creating a new custom prompt."""
        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin",
                password="password123",
                role="admin",
            )
            db.session.add(admin)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.put(
            "/api/admin/system-prompts/claude",
            data=json.dumps({"prompt": "New custom prompt for Claude"}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["provider"] == "claude"
        assert data["prompt"] == "New custom prompt for Claude"
        assert data["is_active"] is True

    def test_update_prompt_modify_existing(self, app, client):
        """Test modifying an existing custom prompt."""
        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin",
                password="password123",
                role="admin",
            )
            existing_prompt = SystemPromptConfig(
                provider="openai",
                prompt="Original prompt",
            )
            db.session.add(admin)
            db.session.add(existing_prompt)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.put(
            "/api/admin/system-prompts/openai",
            data=json.dumps({"prompt": "Updated prompt"}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["prompt"] == "Updated prompt"

    def test_update_prompt_empty_rejected(self, app, client):
        """Test that empty prompt is rejected."""
        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin",
                password="password123",
                role="admin",
            )
            db.session.add(admin)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.put(
            "/api/admin/system-prompts/claude",
            data=json.dumps({"prompt": ""}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert "error" in response.get_json()

    def test_update_prompt_missing_body(self, app, client):
        """Test that missing prompt field is rejected."""
        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin",
                password="password123",
                role="admin",
            )
            db.session.add(admin)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.put(
            "/api/admin/system-prompts/claude",
            data=json.dumps({}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400

    def test_update_prompt_invalid_provider(self, app, client):
        """Test that invalid provider is rejected."""
        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin",
                password="password123",
                role="admin",
            )
            db.session.add(admin)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.put(
            "/api/admin/system-prompts/invalid",
            data=json.dumps({"prompt": "Some prompt"}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400


class TestResetSystemPrompt:
    """Tests for POST /api/admin/system-prompts/<provider>/reset."""

    def test_reset_prompt_success(self, app, client):
        """Test resetting a custom prompt to default."""
        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin",
                password="password123",
                role="admin",
            )
            custom_prompt = SystemPromptConfig(
                provider="claude",
                prompt="Custom prompt to be reset",
            )
            db.session.add(admin)
            db.session.add(custom_prompt)
            db.session.commit()

        login_response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            content_type="application/json",
        )
        token = login_response.get_json()["access_token"]

        response = client.post(
            "/api/admin/system-prompts/claude/reset",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Prompt reset to default"
        assert "default_prompt" in data

        # Verify the custom prompt is deleted
        with app.app_context():
            saved = SystemPromptConfig.get_by_provider("claude")
            assert saved is None

    def test_reset_prompt_already_default(self, app, client):
        """Test resetting when already at default (no custom config)."""
        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin",
                password="password123",
                role="admin",
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
            "/api/admin/system-prompts/gemini/reset",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    def test_reset_prompt_invalid_provider(self, app, client):
        """Test resetting with invalid provider returns 400."""
        with app.app_context():
            admin = User(
                email="admin@example.com",
                name="Admin",
                password="password123",
                role="admin",
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
            "/api/admin/system-prompts/invalid/reset",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
