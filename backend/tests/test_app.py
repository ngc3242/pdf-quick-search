"""Tests for Flask application factory."""

import pytest


class TestAppFactory:
    """Test cases for application factory."""

    def test_create_app_returns_flask_instance(self, app):
        """Test that create_app returns a Flask application instance."""
        from flask import Flask

        assert isinstance(app, Flask)

    def test_app_has_testing_config(self, app):
        """Test that app is configured for testing."""
        assert app.config["TESTING"] is True

    def test_app_has_database_configured(self, app):
        """Test that database is configured."""
        assert "SQLALCHEMY_DATABASE_URI" in app.config
        assert app.config["SQLALCHEMY_DATABASE_URI"] is not None

    def test_app_has_jwt_config(self, app):
        """Test that JWT configuration is present."""
        assert "JWT_SECRET_KEY" in app.config
        assert app.config["JWT_SECRET_KEY"] is not None

    def test_health_endpoint_returns_ok(self, client):
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json["status"] == "ok"
