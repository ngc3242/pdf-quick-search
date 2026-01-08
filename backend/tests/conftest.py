"""Pytest configuration and fixtures."""

import os
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
