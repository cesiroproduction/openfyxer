"""Meeting schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MeetingCreate(BaseModel):
    """Schema for creating a meeting."""

    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    calendar_event_id: Optional[UUID] = None
    meeting_date: Optional[datetime] = None
    participants: Optional[List[str]] = None


class MeetingUpdate(BaseModel):
    """Schema for updating a meeting."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = None
    participants: Optional[List[str]] = None


class MeetingResponse(BaseModel):
    """Schema for meeting response."""

    id: UUID
    user_id: UUID
    calendar_event_id: Optional[UUID]
    title: str
    description: Optional[str]
    audio_file_path: Optional[str]
    audio_duration_seconds: Optional[int]
    audio_format: Optional[str]
    transcript: Optional[str]
    transcript_language: Optional[str]
    summary: Optional[str]
    action_items: Optional[List[str]]
    key_decisions: Optional[List[str]]
    participants: Optional[List[str]]
    topics: Optional[List[str]]
    status: str
    transcription_model: Optional[str]
    transcription_time_seconds: Optional[float]
    follow_up_email_sent: bool
    meeting_date: Optional[datetime]
    transcribed_at: Optional[datetime]
    summarized_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MeetingListResponse(BaseModel):
    """Schema for paginated meeting list response."""

    items: List[MeetingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TranscriptionRequest(BaseModel):
    """Schema for transcription request."""

    language: Optional[str] = Field(default=None, pattern="^(en|ro|auto)$")
    model: Optional[str] = Field(default=None, pattern="^(tiny|base|small|medium|large)$")


class SummarizationRequest(BaseModel):
    """Schema for summarization request."""

    include_action_items: bool = True
    include_key_decisions: bool = True
    include_topics: bool = True
    language: Optional[str] = Field(default=None, pattern="^(en|ro)$")


class FollowUpEmailRequest(BaseModel):
    """Schema for generating follow-up email."""

    recipients: List[str]
    include_summary: bool = True
    include_action_items: bool = True
    include_key_decisions: bool = False
    additional_notes: Optional[str] = None
    tone: Optional[str] = Field(
        default="professional", pattern="^(formal|friendly|professional|concise)$"
    )


class TranscriptionProgress(BaseModel):
    """Schema for transcription progress."""

    meeting_id: UUID
    status: str
    progress_percent: float
    estimated_time_remaining_seconds: Optional[int]
    error_message: Optional[str]
