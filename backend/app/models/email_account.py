"""Email account model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.email import Email
    from app.models.user import User


class EmailAccount(Base):
    """Email account model for storing connected email accounts."""

    __tablename__ = "email_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # gmail, outlook, yahoo, imap
    email_address: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    display_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    oauth_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )  # Encrypted
    oauth_refresh_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )  # Encrypted
    oauth_token_expiry: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    imap_host: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    imap_port: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )
    imap_password: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )  # Encrypted
    smtp_host: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    smtp_port: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )
    last_sync: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_history_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )  # For Gmail incremental sync
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
    sync_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="email_accounts",
    )
    emails: Mapped[List["Email"]] = relationship(
        "Email",
        back_populates="account",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<EmailAccount {self.email_address} ({self.provider})>"
