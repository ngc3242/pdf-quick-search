"""TokenBlacklist model for JWT token invalidation."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app import db


class TokenBlacklist(db.Model):
    """Model for storing blacklisted JWT tokens."""

    __tablename__ = "token_blacklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    jti: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    token_type: Mapped[str] = mapped_column(String(20), default="access")
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True
    )
    blacklisted_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    @classmethod
    def is_blacklisted(cls, jti: str) -> bool:
        """Check if a token JTI is blacklisted.

        Args:
            jti: JWT ID to check

        Returns:
            True if token is blacklisted, False otherwise
        """
        token = cls.query.filter_by(jti=jti).first()
        return token is not None

    @classmethod
    def add_to_blacklist(
        cls,
        jti: str,
        expires_at: datetime,
        user_id: Optional[str] = None,
        token_type: str = "access"
    ) -> "TokenBlacklist":
        """Add a token to the blacklist.

        Args:
            jti: JWT ID
            expires_at: Token expiration time
            user_id: Optional user ID
            token_type: Type of token (access or refresh)

        Returns:
            Created TokenBlacklist instance
        """
        token = cls(
            jti=jti,
            token_type=token_type,
            user_id=user_id,
            expires_at=expires_at
        )
        db.session.add(token)
        db.session.commit()
        return token

    def __repr__(self) -> str:
        """Return string representation of blacklisted token."""
        return f"<TokenBlacklist {self.jti}>"
