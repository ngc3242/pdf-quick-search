"""Authentication service for user login and token management."""

from typing import Optional, Tuple

from app.models import db
from app.models.user import User
from app.models.token_blacklist import TokenBlacklist
from app.utils.auth import create_access_token, get_token_jti_and_exp


class AuthService:
    """Service class for authentication operations."""

    @staticmethod
    def authenticate(email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """Authenticate user with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            Tuple of (User object, error message)
        """
        user = User.query.filter_by(email=email).first()

        if not user:
            return None, "Invalid email or password"

        if not user.is_active:
            return None, "Account is deactivated"

        if not user.check_password(password):
            return None, "Invalid email or password"

        return user, None

    @staticmethod
    def login(email: str, password: str) -> Tuple[Optional[dict], Optional[str]]:
        """Login user and return token.

        Args:
            email: User email
            password: User password

        Returns:
            Tuple of (response data dict, error message)
        """
        user, error = AuthService.authenticate(email, password)

        if error:
            return None, error

        access_token = create_access_token(user.id)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user.to_dict()
        }, None

    @staticmethod
    def logout(token: str, user_id: str) -> bool:
        """Logout user by blacklisting token.

        Args:
            token: JWT token to blacklist
            user_id: User ID

        Returns:
            True if successful
        """
        jti, exp = get_token_jti_and_exp(token)

        if jti and exp:
            TokenBlacklist.add_to_blacklist(
                jti=jti,
                expires_at=exp,
                user_id=user_id,
                token_type="access"
            )
            return True

        return False

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object or None
        """
        return User.query.filter_by(id=user_id, is_active=True).first()
