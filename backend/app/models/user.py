"""User model for authentication."""

import uuid
from datetime import datetime, timezone
from typing import Optional

import bcrypt
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app import db


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

    # Relationships
    documents = relationship(
        "SearchDocument",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    def __init__(
        self,
        email: str,
        name: str,
        password: str,
        phone: Optional[str] = None,
        role: str = "user",
        is_active: bool = True
    ):
        """Initialize a new User.

        Args:
            email: User email address
            name: User display name
            password: Plain text password (will be hashed)
            phone: Optional phone number
            role: User role (admin or user)
            is_active: Whether user account is active
        """
        self.id = str(uuid.uuid4())
        self.email = email
        self.name = name
        self.phone = phone
        self.role = role
        self.is_active = is_active
        self.password_hash = self._hash_password(password)
        self.created_at = datetime.now(timezone.utc)

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
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        for field in exclude:
            data.pop(field, None)
        return data

    def __repr__(self) -> str:
        """Return string representation of user."""
        return f"<User {self.email}>"
