"""Meeting model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.calendar_event import CalendarEvent


class Meeting(Base):
    """Meeting model for storing meeting recordings and transcriptions."""

    __tablename__ = "meetings"

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
    calendar_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calendar_events.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    audio_file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    audio_duration_seconds: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )
    audio_format: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )  # mp3, wav, m4a, etc.
    transcript: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    transcript_language: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    action_items: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    key_decisions: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    participants: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    topics: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
    )  # pending, transcribing, transcribed, summarized, error
    transcription_model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    transcription_time_seconds: Mapped[Optional[float]] = mapped_column(
        nullable=True,
    )
    follow_up_email_sent: Mapped[bool] = mapped_column(
        default=False,
    )
    follow_up_email_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    neo4j_node_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    meeting_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    transcribed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    summarized_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
        back_populates="meetings",
    )
    calendar_event: Mapped[Optional["CalendarEvent"]] = relationship(
        "CalendarEvent",
        back_populates="meetings",
    )

    def __repr__(self) -> str:
        return f"<Meeting {self.title}>"
