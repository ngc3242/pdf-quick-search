"""Authentication service for user login and token management."""

import re
from typing import Optional, Tuple

from app.models import db
from app.models.user import User
from app.models.token_blacklist import TokenBlacklist
from app.utils.auth import create_access_token, get_token_jti_and_exp


class AuthService:
    """Service class for authentication operations."""

    # Validation patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^01[0-9]-?\d{3,4}-?\d{4}$')

    @staticmethod
    def validate_email(email: str) -> Optional[str]:
        """Validate email format and uniqueness.

        Args:
            email: Email address to validate

        Returns:
            Error message if invalid, None if valid
        """
        if not email:
            return "이메일은 필수 항목입니다."

        if not AuthService.EMAIL_PATTERN.match(email):
            return "올바른 이메일 형식이 아닙니다."

        # Check uniqueness
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "이미 등록된 이메일입니다."

        return None

    @staticmethod
    def validate_name(name: str) -> Optional[str]:
        """Validate name format.

        Args:
            name: Name to validate

        Returns:
            Error message if invalid, None if valid
        """
        if not name:
            return "이름은 필수 항목입니다."

        if len(name) < 2:
            return "이름은 2자 이상이어야 합니다."

        if len(name) > 100:
            return "이름은 100자 이하여야 합니다."

        return None

    @staticmethod
    def validate_phone(phone: str) -> Optional[str]:
        """Validate Korean phone number format.

        Args:
            phone: Phone number to validate

        Returns:
            Error message if invalid, None if valid
        """
        if not phone:
            return "전화번호는 필수 항목입니다."

        # Remove hyphens for validation
        normalized_phone = phone.replace("-", "")

        if not AuthService.PHONE_PATTERN.match(phone) and not re.match(r'^01[0-9]\d{7,8}$', normalized_phone):
            return "올바른 전화번호 형식이 아닙니다. (예: 010-1234-5678 또는 01012345678)"

        return None

    @staticmethod
    def validate_password(password: str) -> Optional[str]:
        """Validate password requirements.

        Args:
            password: Password to validate

        Returns:
            Error message if invalid, None if valid
        """
        if not password:
            return "비밀번호는 필수 항목입니다."

        if len(password) < 8:
            return "비밀번호는 8자 이상이어야 합니다."

        if not re.search(r'[A-Z]', password):
            return "비밀번호는 대문자를 포함해야 합니다."

        if not re.search(r'[a-z]', password):
            return "비밀번호는 소문자를 포함해야 합니다."

        if not re.search(r'\d', password):
            return "비밀번호는 숫자를 포함해야 합니다."

        return None

    @staticmethod
    def signup(
        email: str,
        name: str,
        phone: str,
        password: str
    ) -> Tuple[Optional[dict], Optional[str], int]:
        """Register a new user with pending approval status.

        Args:
            email: User email address
            name: User display name
            phone: User phone number
            password: User password

        Returns:
            Tuple of (response data dict, error message, status code)
        """
        # Validate all inputs
        email_error = AuthService.validate_email(email)
        if email_error:
            # Check if it's a duplicate email error
            if "이미 등록된" in email_error:
                return None, email_error, 409
            return None, email_error, 400

        name_error = AuthService.validate_name(name)
        if name_error:
            return None, name_error, 400

        phone_error = AuthService.validate_phone(phone)
        if phone_error:
            return None, phone_error, 400

        password_error = AuthService.validate_password(password)
        if password_error:
            return None, password_error, 400

        # Create user with pending status
        user = User(
            email=email,
            name=name,
            phone=phone,
            password=password,
            role="user",
            is_active=True,
            approval_status="pending"
        )

        db.session.add(user)
        db.session.commit()

        return {
            "message": "회원가입이 완료되었습니다. 관리자 승인 후 로그인이 가능합니다.",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "approval_status": user.approval_status
            }
        }, None, 201

    @staticmethod
    def authenticate(email: str, password: str) -> Tuple[Optional[User], Optional[str], int]:
        """Authenticate user with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            Tuple of (User object, error message, HTTP status code)
        """
        user = User.query.filter_by(email=email).first()

        if not user:
            return None, "Invalid email or password", 401

        if not user.check_password(password):
            return None, "Invalid email or password", 401

        # Check approval status (skip for admin users)
        if user.role != "admin":
            if user.approval_status == "pending":
                return None, "계정이 관리자 승인 대기 중입니다.", 403
            if user.approval_status == "rejected":
                return None, "계정이 거부되었습니다. 관리자에게 문의하세요.", 403

        if not user.is_active:
            return None, "Account is deactivated", 403

        return user, None, 200

    @staticmethod
    def login(email: str, password: str) -> Tuple[Optional[dict], Optional[str], int]:
        """Login user and return token.

        Args:
            email: User email
            password: User password

        Returns:
            Tuple of (response data dict, error message, HTTP status code)
        """
        user, error, status_code = AuthService.authenticate(email, password)

        if error:
            return None, error, status_code

        access_token = create_access_token(user.id)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user.to_dict()
        }, None, 200

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
