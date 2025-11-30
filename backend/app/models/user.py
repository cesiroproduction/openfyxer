"""User model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.email_account import EmailAccount
    from app.models.draft import Draft
    from app.models.calendar_event import CalendarEvent
    from app.models.document import Document
    from app.models.meeting import Meeting
    from app.models.audit_log import AuditLog
    from app.models.user_settings import UserSettings


class User(Base):
    """User model for authentication and profile."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    totp_secret: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
    is_2fa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    language: Mapped[str] = mapped_column(
        String(5),
        default="en",
    )
    timezone: Mapped[str] = mapped_column(
        String(50),
        default="UTC",
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
    email_accounts: Mapped[List["EmailAccount"]] = relationship(
        "EmailAccount",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    drafts: Mapped[List["Draft"]] = relationship(
        "Draft",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    calendar_events: Mapped[List["CalendarEvent"]] = relationship(
        "CalendarEvent",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    meetings: Mapped[List["Meeting"]] = relationship(
        "Meeting",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    settings: Mapped[Optional["UserSettings"]] = relationship(
        "UserSettings",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
