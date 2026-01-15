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
        200 OK with provider availability object
        401 Unauthorized if not authenticated
    """
    available_list = TypoCheckerService.get_available_providers()

    # Convert list to availability object for frontend compatibility
    availability = {
        "claude": "claude" in available_list,
        "openai": "openai" in available_list,
        "gemini": "gemini" in available_list,
    }

    return jsonify(availability), 200


@typo_checker_bp.route("/debug-providers", methods=["GET"])
def debug_providers():
    """Debug endpoint to check provider availability (no auth required)."""
    import os

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    available_list = TypoCheckerService.get_available_providers()

    debug_info = {
        "env_check": {
            "ANTHROPIC_API_KEY_exists": anthropic_key is not None,
            "ANTHROPIC_API_KEY_length": len(anthropic_key) if anthropic_key else 0,
            "ANTHROPIC_API_KEY_prefix": anthropic_key[:15] if anthropic_key else None,
        },
        "providers_list": available_list,
        "providers_object": {
            "claude": "claude" in available_list,
            "openai": "openai" in available_list,
            "gemini": "gemini" in available_list,
        },
    }

    return jsonify(debug_info), 200


@typo_checker_bp.route("/report/<format_type>", methods=["POST"])
@jwt_required
def download_report(format_type: str):
    """Generate and download typo check report.

    Args:
        format_type: Report format ('html' or 'pdf')

    Request body:
        TypoCheckResult data

    Returns:
        200 OK with file blob
        400 Bad Request on validation error
        401 Unauthorized if not authenticated
    """
    if format_type not in ["html", "pdf"]:
        return jsonify({"error": "Invalid format. Use 'html' or 'pdf'"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    from app.services.report_generator import ReportGenerator

    try:
        if format_type == "html":
            content = ReportGenerator.generate_html(data)
            mimetype = "text/html"
            filename = "typo-check-report.html"
        else:  # pdf
            content = ReportGenerator.generate_pdf(data)
            mimetype = "application/pdf"
            filename = "typo-check-report.pdf"

        from flask import Response

        response = Response(content, mimetype=mimetype)
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response

    except Exception as e:
        return jsonify({"error": f"Failed to generate report: {str(e)}"}), 500


@typo_checker_bp.route("/history", methods=["GET"])
@jwt_required
def get_history():
    """Get paginated history of typo check results.

    Query parameters:
        page: Page number (default: 1)
        per_page: Results per page (default: 20)

    Returns:
        200 OK with paginated results
        401 Unauthorized if not authenticated

    Note:
        Original text is NOT stored (only hash for caching).
        Results are ordered by created_at descending (newest first).
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Validate pagination parameters
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 1
    if per_page > 100:
        per_page = 100

    result = TypoCheckerService.get_user_history(
        user_id=g.user_id, page=page, per_page=per_page
    )

    return jsonify(result), 200


@typo_checker_bp.route("/<int:result_id>", methods=["GET", "DELETE"])
@jwt_required
def get_or_delete_result(result_id: int):
    """Get or delete a specific typo check result by ID.

    Args:
        result_id: ID of the typo check result

    Returns:
        GET:
            200 OK with result data
            401 Unauthorized if not authenticated
            403 Forbidden if result belongs to another user
            404 Not Found if result doesn't exist
        DELETE:
            200 OK with success message
            401 Unauthorized if not authenticated
            403 Forbidden if result belongs to another user
            404 Not Found if result doesn't exist
    """
    if request.method == "DELETE":
        result = TypoCheckerService.delete_result(result_id, g.user_id)

        if not result["success"]:
            error_msg = result.get("error", "Failed to delete result")
            if "not found" in error_msg.lower():
                return jsonify({"error": error_msg}), 404
            if "denied" in error_msg.lower():
                return jsonify({"error": error_msg}), 403
            return jsonify({"error": error_msg}), 400

        return jsonify({"success": True, "message": "Result deleted successfully"}), 200

    # GET request
    result = TypoCheckResult.query.filter_by(id=result_id).first()

    if not result:
        return jsonify({"error": "Result not found"}), 404

    if result.user_id != g.user_id:
        return jsonify({"error": "Access denied"}), 403

    return jsonify({"result": result.to_dict()}), 200
