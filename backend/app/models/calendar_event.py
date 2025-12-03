"""Calendar event model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import StringArray

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.meeting import Meeting


class CalendarEvent(Base):
    """Calendar event model for storing calendar events."""

    __tablename__ = "calendar_events"

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
    )  # google, outlook
    external_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    calendar_id: Mapped[Optional[str]] = mapped_column(
        String(255),
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
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    timezone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    meeting_link: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    attendees: Mapped[Optional[List[str]]] = mapped_column(
        StringArray(),
        nullable=True,
    )
    organizer: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    is_all_day: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    is_recurring: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    recurrence_rule: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # confirmed, tentative, cancelled
    reminder_minutes: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )
    color: Mapped[Optional[str]] = mapped_column(
        String(20),
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
        back_populates="calendar_events",
    )
    meetings: Mapped[List["Meeting"]] = relationship(
        "Meeting",
        back_populates="calendar_event",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<CalendarEvent {self.title}>"
