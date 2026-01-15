"""Typo checker API routes.

This module provides API endpoints for Korean typo checking functionality.
"""

from flask import Blueprint, request, jsonify, g

from app.services.typo_checker_service import TypoCheckerService, MAX_TEXT_LENGTH
from app.models.typo_check_result import TypoCheckResult
from app.utils.auth import jwt_required

typo_checker_bp = Blueprint("typo_checker", __name__)


@typo_checker_bp.route("", methods=["POST"])
@jwt_required
def check_typo():
    """Check text for typos.

    Request body:
        text: Korean text to check (required, max 100K chars)
        provider: Optional specific AI provider to use

    Returns:
        200 OK with correction results on success
        400 Bad Request on validation error
        401 Unauthorized if not authenticated
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    text = data.get("text")

    if not text:
        return jsonify({"error": "Text is required"}), 400

    if not text.strip():
        return jsonify({"error": "Text cannot be empty"}), 400

    if len(text) > MAX_TEXT_LENGTH:
        return jsonify(
            {"error": f"Text exceeds maximum limit of {MAX_TEXT_LENGTH} characters"}
        ), 400

    provider = data.get("provider")

    # Call the service
    result = TypoCheckerService.check_text(
        text=text, user_id=g.user_id, provider=provider
    )

    if not result["success"]:
        return jsonify(
            {"success": False, "error": result.get("error", "Failed to check typos")}
        ), 400

    return jsonify(result), 200


@typo_checker_bp.route("/providers", methods=["GET"])
@jwt_required
def get_providers():
    """Get list of available AI providers.

    Returns:
        200 OK with list of available provider names
        401 Unauthorized if not authenticated
    """
    providers = TypoCheckerService.get_available_providers()

    return jsonify({"providers": providers}), 200


@typo_checker_bp.route("/<int:result_id>", methods=["GET"])
@jwt_required
def get_result(result_id: int):
    """Get a specific typo check result by ID.

    Args:
        result_id: ID of the typo check result

    Returns:
        200 OK with result data
        401 Unauthorized if not authenticated
        403 Forbidden if result belongs to another user
        404 Not Found if result doesn't exist
    """
    result = TypoCheckResult.query.filter_by(id=result_id).first()

    if not result:
        return jsonify({"error": "Result not found"}), 404

    if result.user_id != g.user_id:
        return jsonify({"error": "Access denied"}), 403

    return jsonify({"result": result.to_dict()}), 200
