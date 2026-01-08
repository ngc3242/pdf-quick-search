"""JWT authentication utilities."""

import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Optional, Tuple

import jwt
from flask import request, g, current_app, jsonify

from app.models.token_blacklist import TokenBlacklist


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token.

    Args:
        user_id: User ID to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    if expires_delta is None:
        expires_delta = current_app.config.get(
            "JWT_ACCESS_TOKEN_EXPIRES", timedelta(hours=24)
        )

    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
        "type": "access"
    }

    token = jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm="HS256"
    )
    return token


def decode_token(token: str) -> Tuple[Optional[dict], Optional[str]]:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Tuple of (payload dict, error message)
    """
    try:
        payload = jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=["HS256"]
        )

        # Check if token is blacklisted
        if TokenBlacklist.is_blacklisted(payload.get("jti", "")):
            return None, "Token has been revoked"

        return payload, None

    except jwt.ExpiredSignatureError:
        return None, "Token has expired"
    except jwt.InvalidTokenError as e:
        return None, f"Invalid token: {str(e)}"


def get_token_from_header() -> Optional[str]:
    """Extract JWT token from Authorization header.

    Returns:
        Token string or None if not found
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


def jwt_required(f):
    """Decorator to require valid JWT token for endpoint.

    Sets g.user_id and g.token_payload on successful authentication.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()

        if not token:
            return jsonify({"error": "Missing authorization token"}), 401

        payload, error = decode_token(token)

        if error:
            return jsonify({"error": error}), 401

        g.user_id = payload.get("sub")
        g.token_payload = payload

        return f(*args, **kwargs)

    return decorated


def get_token_jti_and_exp(token: str) -> Tuple[Optional[str], Optional[datetime]]:
    """Extract JTI and expiration from token for blacklisting.

    Args:
        token: JWT token string

    Returns:
        Tuple of (jti, expiration datetime)
    """
    try:
        # Decode without verification to get claims for blacklisting
        payload = jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
        jti = payload.get("jti")
        exp_timestamp = payload.get("exp")
        exp = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc) if exp_timestamp else None
        return jti, exp
    except jwt.InvalidTokenError:
        return None, None
