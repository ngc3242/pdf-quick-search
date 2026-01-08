"""Authentication API routes."""

from flask import Blueprint, request, jsonify, g

from app.services.auth_service import AuthService
from app.utils.auth import jwt_required, get_token_from_header

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login endpoint.

    Request body:
        email: User email
        password: User password

    Returns:
        JSON with access_token and user info on success
        JSON with error message on failure
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    result, error = AuthService.login(email, password)

    if error:
        return jsonify({"error": error}), 401

    return jsonify(result), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required
def logout():
    """Logout endpoint.

    Blacklists the current token.

    Returns:
        JSON with success message
    """
    token = get_token_from_header()
    user_id = g.user_id

    AuthService.logout(token, user_id)

    return jsonify({"message": "Successfully logged out"}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required
def me():
    """Get current user info.

    Returns:
        JSON with current user info
    """
    user = AuthService.get_user_by_id(g.user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"user": user.to_dict()}), 200
