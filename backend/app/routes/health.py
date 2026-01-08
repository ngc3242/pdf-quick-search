"""Health check endpoint."""

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Return health status of the API.

    Returns:
        JSON response with status ok
    """
    return jsonify({"status": "ok"}), 200
