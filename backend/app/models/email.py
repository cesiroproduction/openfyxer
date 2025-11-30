"""Email model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.email_account import EmailAccount
    from app.models.draft import Draft
    from app.models.document import Document


class Email(Base):
    """Email model for storing email messages."""

    __tablename__ = "emails"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    message_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    thread_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    subject: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    sender: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    sender_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    recipients: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    cc: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    bcc: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    body_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    body_html: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    snippet: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # urgent, to_respond, fyi, newsletter, spam
    labels: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    folder: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    has_attachments: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    is_starred: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    is_draft: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    is_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    language: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )
    sentiment: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )  # positive, negative, neutral
    priority_score: Mapped[Optional[float]] = mapped_column(
        nullable=True,
    )
    received_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    indexed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Relationships
    account: Mapped["EmailAccount"] = relationship(
        "EmailAccount",
        back_populates="emails",
    )
    drafts: Mapped[List["Draft"]] = relationship(
        "Draft",
        back_populates="email",
        cascade="all, delete-orphan",
    )
    attachments: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="email",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        # Unique constraint on account_id and message_id
        {"sqlite_autoincrement": True},
    )

    def __repr__(self) -> str:
        return f"<Email {self.subject[:50] if self.subject else 'No Subject'}>"
