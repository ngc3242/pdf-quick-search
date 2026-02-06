"""Typo checker API routes.

This module provides API endpoints for Korean typo checking functionality.
"""

import hashlib
import json

from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, g

from app import db
from app.services.typo_checker_service import TypoCheckerService, MAX_TEXT_LENGTH
from app.models.typo_check_result import TypoCheckResult
from app.models.typo_check_job import TypoCheckJob
from app.utils.auth import jwt_required

typo_checker_bp = Blueprint("typo_checker", __name__)


@typo_checker_bp.route("", methods=["POST"])
@jwt_required
def check_typo():
    """Submit text for async typo checking.

    Returns cached result (200) immediately if available,
    otherwise creates a background job and returns 202.
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

    provider = data.get("provider", "gemini")

    # Check cache first (fast path)
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    try:
        cached_result = TypoCheckResult.query.filter_by(
            user_id=g.user_id,
            original_text_hash=text_hash,
            provider_used=provider,
        ).first()
    except Exception:
        db.session.rollback()
        cached_result = None

    if cached_result:
        return jsonify({
            "success": True,
            "cached": True,
            "corrected_text": cached_result.corrected_text,
            "issues": json.loads(cached_result.issues) if cached_result.issues else [],
            "provider": cached_result.provider_used,
        }), 200

    # Check concurrent job limit per user
    active_jobs = TypoCheckJob.query.filter(
        TypoCheckJob.user_id == g.user_id,
        TypoCheckJob.status.in_(["pending", "processing"]),
    ).count()
    if active_jobs >= 3:
        return jsonify({"error": "Too many pending checks. Please wait."}), 429

    # Create async job
    job = TypoCheckJob(
        user_id=g.user_id,
        original_text=text,
        original_text_hash=text_hash,
        provider=provider,
    )
    db.session.add(job)
    db.session.commit()

    # Wake up the worker
    from app.typo_worker import typo_check_worker

    typo_check_worker.wake_up()

    return jsonify({
        "job_id": job.id,
        "status": "pending",
    }), 202


@typo_checker_bp.route("/jobs/<int:job_id>", methods=["GET"])
@jwt_required
def get_job_status(job_id: int):
    """Poll job status and progress."""
    job = db.session.get(TypoCheckJob, job_id)

    if not job:
        return jsonify({"error": "Job not found"}), 404

    if job.user_id != g.user_id:
        return jsonify({"error": "Access denied"}), 403

    response = job.to_dict()

    # If completed, include the full result
    if job.status == "completed" and job.result_id:
        result = db.session.get(TypoCheckResult, job.result_id)
        if result:
            response["result"] = {
                "corrected_text": result.corrected_text,
                "issues": json.loads(result.issues) if result.issues else [],
                "provider": result.provider_used,
                "original_text": result.original_text,
            }

    return jsonify(response), 200


@typo_checker_bp.route("/jobs/<int:job_id>/cancel", methods=["POST"])
@jwt_required
def cancel_job(job_id: int):
    """Cancel a pending or processing job."""
    job = db.session.get(TypoCheckJob, job_id)

    if not job:
        return jsonify({"error": "Job not found"}), 404

    if job.user_id != g.user_id:
        return jsonify({"error": "Access denied"}), 403

    if job.status in ("completed", "failed", "cancelled"):
        return jsonify(
            {"error": f"Cannot cancel job with status '{job.status}'"}
        ), 400

    job.status = "cancelled"
    job.completed_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({"success": True, "status": "cancelled"}), 200


@typo_checker_bp.route("/providers", methods=["GET"])
@jwt_required
def get_providers():
    """Get list of available AI providers."""
    available_list = TypoCheckerService.get_available_providers()

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
    """Generate and download typo check report."""
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
    """Get paginated history of typo check results."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

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
    """Get or delete a specific typo check result by ID."""
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
