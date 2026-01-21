"""Admin authorization utilities."""

from functools import wraps
from flask import g, jsonify

from app.models.user import User


def admin_required(f):
    """Decorator to require admin role for endpoint.

    Must be used after @jwt_required to ensure user is authenticated.
    Sets g.current_user to the authenticated admin user.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = getattr(g, "user_id", None)

        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        user = User.query.filter_by(id=user_id).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

        if user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403

        # Store current user for use in route handlers
        g.current_user = user

        return f(*args, **kwargs)

    return decorated
