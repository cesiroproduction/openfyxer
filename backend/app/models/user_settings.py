"""User settings model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserSettings(Base):
    """User settings model for storing user preferences and API keys."""

    __tablename__ = "user_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # LLM Settings
    llm_provider: Mapped[str] = mapped_column(
        String(50),
        default="local",
    )  # local, openai, gemini, claude, cohere
    llm_model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    openai_api_key: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )  # Encrypted
    gemini_api_key: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )  # Encrypted
    claude_api_key: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )  # Encrypted
    cohere_api_key: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )  # Encrypted
    allow_cloud_llm_for_sensitive: Mapped[bool] = mapped_column(
        default=False,
    )  # Allow sending sensitive data to cloud LLM

    # Notification Settings
    slack_webhook_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    sms_provider: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # twilio, etc.
    sms_api_key: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )  # Encrypted
    sms_phone_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    notification_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    notification_preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )  # Detailed notification rules

    # Email Style Settings
    email_style: Mapped[Optional[str]] = mapped_column(
        String(50),
        default="professional",
    )  # formal, friendly, professional, concise
    email_signature: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    learned_style_profile: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )  # AI-learned style preferences

    # Email Processing Settings
    auto_categorize: Mapped[bool] = mapped_column(
        default=True,
    )
    auto_draft: Mapped[bool] = mapped_column(
        default=True,
    )
    auto_send: Mapped[bool] = mapped_column(
        default=False,
    )  # Auto-send approved drafts
    follow_up_days: Mapped[int] = mapped_column(
        Integer,
        default=3,
    )
    priority_contacts: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
    )  # VIP contacts for urgent notifications

    # Calendar Settings
    working_hours_start: Mapped[Optional[str]] = mapped_column(
        String(5),
        default="09:00",
    )
    working_hours_end: Mapped[Optional[str]] = mapped_column(
        String(5),
        default="17:00",
    )
    working_days: Mapped[Optional[List[int]]] = mapped_column(
        ARRAY(Integer),
        default=[1, 2, 3, 4, 5],  # Monday to Friday
    )
    meeting_buffer_minutes: Mapped[int] = mapped_column(
        Integer,
        default=15,
    )
    default_meeting_duration: Mapped[int] = mapped_column(
        Integer,
        default=30,
    )

    # Whisper/STT Settings
    whisper_model: Mapped[str] = mapped_column(
        String(50),
        default="base",
    )

    # UI Settings
    theme: Mapped[str] = mapped_column(
        String(20),
        default="light",
    )  # light, dark, system
    dashboard_widgets: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
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
        back_populates="settings",
    )

    def __repr__(self) -> str:
        return f"<UserSettings for {self.user_id}>"
