"""Settings schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings."""

    # LLM Settings
    llm_provider: Optional[str] = Field(
        default=None, pattern="^(local|openai|gemini|claude|cohere)$"
    )
    llm_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    allow_cloud_llm_for_sensitive: Optional[bool] = None

    # Notification Settings
    slack_webhook_url: Optional[str] = None
    sms_provider: Optional[str] = None
    sms_api_key: Optional[str] = None
    sms_phone_number: Optional[str] = None
    notification_email: Optional[str] = None
    notification_preferences: Optional[Dict[str, Any]] = None

    # Email Style Settings
    email_style: Optional[str] = Field(
        default=None, pattern="^(formal|friendly|professional|concise)$"
    )
    email_signature: Optional[str] = None

    # Email Processing Settings
    auto_categorize: Optional[bool] = None
    auto_draft: Optional[bool] = None
    auto_send: Optional[bool] = None
    follow_up_days: Optional[int] = Field(default=None, ge=1, le=30)
    priority_contacts: Optional[List[str]] = None

    # Calendar Settings
    working_hours_start: Optional[str] = Field(
        default=None, pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
    )
    working_hours_end: Optional[str] = Field(
        default=None, pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
    )
    working_days: Optional[List[int]] = None
    meeting_buffer_minutes: Optional[int] = Field(default=None, ge=0, le=60)
    default_meeting_duration: Optional[int] = Field(default=None, ge=15, le=480)

    # Whisper/STT Settings
    whisper_model: Optional[str] = Field(
        default=None, pattern="^(tiny|base|small|medium|large)$"
    )

    # UI Settings
    theme: Optional[str] = Field(default=None, pattern="^(light|dark|system)$")
    dashboard_widgets: Optional[Dict[str, Any]] = None


class UserSettingsResponse(BaseModel):
    """Schema for user settings response."""

    id: UUID
    user_id: UUID

    # LLM Settings
    llm_provider: str
    llm_model: Optional[str]
    has_openai_key: bool = False
    has_gemini_key: bool = False
    has_claude_key: bool = False
    has_cohere_key: bool = False
    allow_cloud_llm_for_sensitive: bool

    # Notification Settings
    has_slack_webhook: bool = False
    sms_provider: Optional[str]
    has_sms_key: bool = False
    sms_phone_number: Optional[str]
    notification_email: Optional[str]
    notification_preferences: Optional[Dict[str, Any]]

    # Email Style Settings
    email_style: Optional[str]
    email_signature: Optional[str]

    # Email Processing Settings
    auto_categorize: bool
    auto_draft: bool
    auto_send: bool
    follow_up_days: int
    priority_contacts: Optional[List[str]]

    # Calendar Settings
    working_hours_start: Optional[str]
    working_hours_end: Optional[str]
    working_days: Optional[List[int]]
    meeting_buffer_minutes: int
    default_meeting_duration: int

    # Whisper/STT Settings
    whisper_model: str

    # UI Settings
    theme: str
    dashboard_widgets: Optional[Dict[str, Any]]

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationTest(BaseModel):
    """Schema for testing notifications."""

    channel: str = Field(..., pattern="^(slack|sms|email|webhook)$")
    message: Optional[str] = Field(default="Test notification from OpenFyxer")


class StyleAnalysisRequest(BaseModel):
    """Schema for requesting style analysis."""

    analyze_sent_emails: bool = True
    max_emails: int = Field(default=500, ge=10, le=1000)


class StyleAnalysisResponse(BaseModel):
    """Schema for style analysis response."""

    average_length: int
    common_greetings: List[str]
    common_closings: List[str]
    tone_profile: Dict[str, float]
    vocabulary_complexity: str
    formality_level: str
    analyzed_emails_count: int
