"""Admin API routes."""

from flask import Blueprint, request, jsonify

from app.services.admin_service import AdminService
from app.utils.auth import jwt_required
from app.utils.admin import admin_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/users", methods=["GET"])
@jwt_required
@admin_required
def list_users():
    """List all users with document counts.

    Returns:
        JSON with users array
    """
    users = AdminService.list_users()
    return jsonify({"users": users}), 200


@admin_bp.route("/users", methods=["POST"])
@jwt_required
@admin_required
def create_user():
    """Create a new user.

    Request body:
        email: User email (required)
        name: User name (required)
        password: User password (required)
        phone: User phone (optional)
        role: User role (optional, default "user")

    Returns:
        201 Created with user info
        400 Bad Request on validation error
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    email = data.get("email")
    name = data.get("name")
    password = data.get("password")

    if not email or not name or not password:
        return jsonify({"error": "email, name, and password are required"}), 400

    phone = data.get("phone")
    role = data.get("role", "user")

    user, error = AdminService.create_user(
        email=email,
        name=name,
        password=password,
        phone=phone,
        role=role
    )

    if error:
        return jsonify({"error": error}), 400

    return jsonify({"user": user.to_dict()}), 201


@admin_bp.route("/users/<user_id>", methods=["PATCH"])
@jwt_required
@admin_required
def update_user(user_id: str):
    """Update user information.

    Args:
        user_id: User ID

    Request body:
        name: User name (optional)
        phone: User phone (optional)
        role: User role (optional)
        is_active: Active status (optional)

    Returns:
        200 OK with updated user info
        404 Not Found if user doesn't exist
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    user, error = AdminService.update_user(user_id, data)

    if error:
        status_code = 404 if error == "User not found" else 400
        return jsonify({"error": error}), status_code

    return jsonify({"user": user.to_dict()}), 200


@admin_bp.route("/users/<user_id>/password", methods=["POST"])
@jwt_required
@admin_required
def reset_password(user_id: str):
    """Reset a user's password.

    Args:
        user_id: User ID

    Request body:
        new_password: New password (required)

    Returns:
        200 OK on success
        400/404 on error
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    new_password = data.get("new_password")
    if not new_password:
        return jsonify({"error": "new_password is required"}), 400

    success, error = AdminService.reset_password(user_id, new_password)

    if not success:
        status_code = 404 if error == "User not found" else 400
        return jsonify({"error": error}), status_code

    return jsonify({"message": "Password reset successfully"}), 200


@admin_bp.route("/users/<user_id>", methods=["DELETE"])
@jwt_required
@admin_required
def delete_user(user_id: str):
    """Delete a user and their documents.

    Args:
        user_id: User ID

    Returns:
        200 OK on success
        404 Not Found if user doesn't exist
    """
    success, error = AdminService.delete_user(user_id)

    if not success:
        return jsonify({"error": error}), 404

    return jsonify({"message": "User deleted successfully"}), 200


@admin_bp.route("/users/<user_id>/documents", methods=["GET"])
@jwt_required
@admin_required
def get_user_documents(user_id: str):
    """Get all documents for a specific user.

    Args:
        user_id: User ID

    Returns:
        200 OK with documents array
        404 Not Found if user doesn't exist
    """
    documents, error = AdminService.get_user_documents(user_id)

    if error:
        return jsonify({"error": error}), 404

    return jsonify({"documents": documents}), 200
