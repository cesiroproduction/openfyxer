"""Calendar schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CalendarEventCreate(BaseModel):
    """Schema for creating a calendar event."""

    provider: str = Field(default="local", pattern="^(google|outlook|local)$")
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    timezone: Optional[str] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    attendees: Optional[List[str]] = None
    is_all_day: bool = False
    reminder_minutes: Optional[int] = Field(default=15, ge=0, le=10080)


class CalendarEventUpdate(BaseModel):
    """Schema for updating a calendar event."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    attendees: Optional[List[str]] = None
    reminder_minutes: Optional[int] = Field(default=None, ge=0, le=10080)


class CalendarEventResponse(BaseModel):
    """Schema for calendar event response."""

    id: UUID
    user_id: UUID
    provider: str
    external_id: Optional[str]
    calendar_id: Optional[str]
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    timezone: Optional[str]
    location: Optional[str]
    meeting_link: Optional[str]
    attendees: Optional[List[str]]
    organizer: Optional[str]
    is_all_day: bool
    is_recurring: bool
    status: Optional[str]
    reminder_minutes: Optional[int]
    color: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CalendarEventListResponse(BaseModel):
    """Schema for paginated calendar event list response."""

    items: List[CalendarEventResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AvailableSlot(BaseModel):
    """Schema for available time slot."""

    start_time: datetime
    end_time: datetime
    duration_minutes: int


class AvailableSlotsRequest(BaseModel):
    """Schema for requesting available slots."""

    duration_minutes: int = Field(default=30, ge=15, le=480)
    date_from: datetime
    date_to: datetime
    attendees: Optional[List[str]] = None
    respect_working_hours: bool = True


class AvailableSlotsResponse(BaseModel):
    """Schema for available slots response."""

    slots: List[AvailableSlot]
    total: int


class ScheduleMeetingRequest(BaseModel):
    """Schema for auto-scheduling a meeting."""

    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    duration_minutes: int = Field(default=30, ge=15, le=480)
    attendees: List[str]
    preferred_times: Optional[List[datetime]] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    send_invites: bool = True


class ConflictResponse(BaseModel):
    """Schema for calendar conflict response."""

    has_conflict: bool
    conflicting_events: List[CalendarEventResponse]
    suggested_alternatives: List[AvailableSlot]
