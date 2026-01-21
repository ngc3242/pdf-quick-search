"""Authentication API routes."""

from flask import Blueprint, request, jsonify, g

from app.services.auth_service import AuthService
from app.utils.auth import jwt_required, get_token_from_header

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["POST"])
def signup():
    """Signup endpoint for new user registration.

    Request body:
        email: User email
        name: User display name
        phone: User phone number
        password: User password

    Returns:
        JSON with success message and user info on success (201)
        JSON with error message on validation failure (400)
        JSON with error message on duplicate email (409)
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    email = data.get("email", "").strip()
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    password = data.get("password", "")

    result, error, status_code = AuthService.signup(email, name, phone, password)

    if error:
        return jsonify({"error": error}), status_code

    return jsonify(result), status_code


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login endpoint.

    Request body:
        email: User email
        password: User password

    Returns:
        JSON with access_token and user info on success (200)
        JSON with error message on invalid credentials (401)
        JSON with error message on pending/rejected/deactivated account (403)
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    result, error, status_code = AuthService.login(email, password)

    if error:
        return jsonify({"error": error}), status_code

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
