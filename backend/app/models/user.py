"""User model for authentication."""

import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

import bcrypt
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db

if TYPE_CHECKING:
    from app.models.user import User


class User(db.Model):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Approval fields
    approval_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    approved_by_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    approval_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    # Relationships
    documents = relationship(
        "SearchDocument",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    # Self-referential relationship for approved_by
    approved_by: Mapped[Optional["User"]] = relationship(
        "User",
        remote_side=[id],
        foreign_keys=[approved_by_id]
    )

    def __init__(
        self,
        email: str,
        name: str,
        password: str,
        phone: Optional[str] = None,
        role: str = "user",
        is_active: bool = True,
        approval_status: str = "pending"
    ):
        """Initialize a new User.

        Args:
            email: User email address
            name: User display name
            password: Plain text password (will be hashed)
            phone: Optional phone number
            role: User role (admin or user)
            is_active: Whether user account is active
            approval_status: Approval status (pending, approved, rejected)
        """
        self.id = str(uuid.uuid4())
        self.email = email
        self.name = name
        self.phone = phone
        self.role = role
        self.is_active = is_active
        self.password_hash = self._hash_password(password)
        self.created_at = datetime.now(timezone.utc)
        self.approval_status = approval_status

    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Check if provided password matches the stored hash.

        Args:
            password: Plain text password to check

        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(
            password.encode("utf-8"),
            self.password_hash.encode("utf-8")
        )

    def approve(self, approved_by: "User") -> None:
        """Approve the user.

        Args:
            approved_by: The admin user who approved this user
        """
        self.approval_status = "approved"
        self.approved_at = datetime.now(timezone.utc)
        self.approved_by_id = approved_by.id
        self.approval_reason = None

    def reject(self, reason: str) -> None:
        """Reject the user.

        Args:
            reason: The reason for rejection
        """
        self.approval_status = "rejected"
        self.approval_reason = reason
        self.approved_at = None
        self.approved_by_id = None

    def to_dict(self, exclude: Optional[list[str]] = None) -> dict:
        """Convert user to dictionary.

        Args:
            exclude: List of fields to exclude

        Returns:
            Dictionary representation of user
        """
        exclude = exclude or []
        data = {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "phone": self.phone,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "approval_status": self.approval_status,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approved_by_id": self.approved_by_id,
            "approval_reason": self.approval_reason
        }
        for field in exclude:
            data.pop(field, None)
        return data

    def __repr__(self) -> str:
        """Return string representation of user."""
        return f"<User {self.email}>"
