"""Admin service for user management."""

from typing import List, Optional, Tuple

from sqlalchemy import func

from app.models import db
from app.models.user import User
from app.models.document import SearchDocument


class AdminService:
    """Service class for admin operations."""

    @staticmethod
    def list_users() -> List[dict]:
        """List all users with document counts.

        Returns:
            List of user dictionaries with document_count
        """
        # Query users with document count
        users_with_counts = (
            db.session.query(
                User,
                func.count(SearchDocument.id).label("document_count")
            )
            .outerjoin(SearchDocument, User.id == SearchDocument.owner_id)
            .group_by(User.id)
            .all()
        )

        result = []
        for user, doc_count in users_with_counts:
            user_dict = user.to_dict()
            user_dict["document_count"] = doc_count
            result.append(user_dict)

        return result

    @staticmethod
    def list_pending_users() -> Tuple[List[dict], int]:
        """List users with pending approval status.

        Returns:
            Tuple of (list of user dictionaries, total count)
        """
        users = User.query.filter_by(approval_status="pending").all()
        result = [
            {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "phone": user.phone,
                "approval_status": user.approval_status,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            for user in users
        ]
        return result, len(result)

    @staticmethod
    def approve_user(
        user_id: str,
        admin_user: User,
        role: str = "user"
    ) -> Tuple[Optional[User], Optional[str]]:
        """Approve a pending user.

        Args:
            user_id: User ID to approve
            admin_user: Admin user performing the approval
            role: Role to assign to the user (default "user")

        Returns:
            Tuple of (User object, error message)
        """
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return None, "사용자를 찾을 수 없습니다."

        if user.approval_status == "approved":
            return None, "이미 승인된 사용자입니다."

        if user.approval_status == "rejected":
            return None, "이미 거부된 사용자입니다."

        # Use the User model's approve method
        user.approve(admin_user)
        user.role = role
        db.session.commit()

        return user, None

    @staticmethod
    def reject_user(
        user_id: str,
        reason: str
    ) -> Tuple[Optional[User], Optional[str]]:
        """Reject a pending user.

        Args:
            user_id: User ID to reject
            reason: Reason for rejection

        Returns:
            Tuple of (User object, error message)
        """
        if not reason or not reason.strip():
            return None, "거부 사유를 입력해주세요."

        user = User.query.filter_by(id=user_id).first()
        if not user:
            return None, "사용자를 찾을 수 없습니다."

        if user.approval_status == "approved":
            return None, "이미 승인된 사용자입니다."

        if user.approval_status == "rejected":
            return None, "이미 거부된 사용자입니다."

        # Use the User model's reject method
        user.reject(reason)
        db.session.commit()

        return user, None

    @staticmethod
    def create_user(
        email: str,
        name: str,
        password: str,
        phone: Optional[str] = None,
        role: str = "user"
    ) -> Tuple[Optional[User], Optional[str]]:
        """Create a new user.

        Args:
            email: User email
            name: User name
            password: User password
            phone: Optional phone number
            role: User role (default "user")

        Returns:
            Tuple of (User object, error message)
        """
        # Check for duplicate email
        existing = User.query.filter_by(email=email).first()
        if existing:
            return None, "Email already registered"

        user = User(
            email=email,
            name=name,
            password=password,
            phone=phone,
            role=role
        )
        db.session.add(user)
        db.session.commit()

        return user, None

    @staticmethod
    def update_user(
        user_id: str,
        data: dict
    ) -> Tuple[Optional[User], Optional[str]]:
        """Update user information.

        Allowed fields: name, phone, role, is_active

        Args:
            user_id: User ID to update
            data: Dictionary of fields to update

        Returns:
            Tuple of (User object, error message)
        """
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return None, "User not found"

        # Update allowed fields
        allowed_fields = ["name", "phone", "role", "is_active"]
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])

        db.session.commit()
        return user, None

    @staticmethod
    def reset_password(
        user_id: str,
        new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """Reset a user's password.

        Args:
            user_id: User ID
            new_password: New password

        Returns:
            Tuple of (success, error message)
        """
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return False, "User not found"

        user.password_hash = user._hash_password(new_password)
        db.session.commit()

        return True, None

    @staticmethod
    def delete_user(user_id: str) -> Tuple[bool, Optional[str]]:
        """Delete a user and cascade delete their documents.

        Args:
            user_id: User ID to delete

        Returns:
            Tuple of (success, error message)
        """
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return False, "User not found"

        db.session.delete(user)
        db.session.commit()

        return True, None

    @staticmethod
    def get_user_documents(user_id: str) -> Tuple[Optional[List[dict]], Optional[str]]:
        """Get all documents for a specific user.

        Args:
            user_id: User ID

        Returns:
            Tuple of (list of document dicts, error message)
        """
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return None, "User not found"

        documents = SearchDocument.query.filter_by(owner_id=user_id).all()
        return [doc.to_dict() for doc in documents], None
