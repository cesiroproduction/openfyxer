"""Draft model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.email import Email


class Draft(Base):
    """Draft model for storing AI-generated email drafts."""

    __tablename__ = "drafts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("emails.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    original_content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )  # Original AI-generated content before edits
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
    )  # pending, approved, sent, rejected
    llm_provider: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    llm_model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    generation_time_ms: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        nullable=True,
    )
    language: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )
    tone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # formal, friendly, professional, etc.
    edited_by_user: Mapped[bool] = mapped_column(
        default=False,
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
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    email: Mapped["Email"] = relationship(
        "Email",
        back_populates="drafts",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="drafts",
    )

    def __repr__(self) -> str:
        return f"<Draft {self.id} ({self.status})>"
