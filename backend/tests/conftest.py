"""Pytest configuration and fixtures."""

import os
import json
import pytest
from app import create_app
from app.models import db

# Set testing environment
os.environ["FLASK_ENV"] = "testing"


@pytest.fixture(scope="function")
def app():
    """Create application for testing.

    Each test function gets a fresh app with clean database.
    """
    application = create_app("testing")

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Create database session for testing."""
    with app.app_context():
        yield db.session


@pytest.fixture
def approved_user(app):
    """Create an approved user for testing."""
    from app.models.user import User

    with app.app_context():
        user = User(
            email="test@example.com",
            name="Test User",
            password="password123",
            approval_status="approved"
        )
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "email": user.email}


@pytest.fixture
def auth_token(app, client, approved_user):
    """Get an auth token for the approved user."""
    response = client.post(
        "/api/auth/login",
        data=json.dumps({"email": "test@example.com", "password": "password123"}),
        content_type="application/json"
    )
    return response.get_json()["access_token"]


@pytest.fixture
def admin_user(app):
    """Create an admin user for testing."""
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
        return {"id": admin.id, "email": admin.email}


@pytest.fixture
def admin_token(app, client, admin_user):
    """Get an auth token for the admin user."""
    response = client.post(
        "/api/auth/login",
        data=json.dumps({"email": "admin@example.com", "password": "password123"}),
        content_type="application/json"
    )
    return response.get_json()["access_token"]
