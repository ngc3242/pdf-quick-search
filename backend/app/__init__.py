"""Flask application factory."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate

from config import config

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name: str = "default") -> Flask:
    """Create and configure the Flask application.

    Args:
        config_name: Configuration name (development, testing, production)

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Register blueprints
    from app.routes.health import health_bp
    from app.routes.auth import auth_bp
    from app.routes.documents import documents_bp
    from app.routes.search import search_bp
    from app.routes.admin import admin_bp
    from app.routes.typo_checker import typo_checker_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(documents_bp, url_prefix="/api/documents")
    app.register_blueprint(search_bp, url_prefix="/api/search")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(typo_checker_bp, url_prefix="/api/typo-check")

    # Register CLI commands
    from app.cli import register_cli

    register_cli(app)

    # Initialize extraction worker (adaptive polling)
    if app.config.get("ENABLE_EXTRACTION_WORKER", True):
        from app.worker import init_worker

        init_worker(app)

    return app
