"""Email schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class EmailAccountCreate(BaseModel):
    """Schema for creating an email account."""

    provider: str = Field(..., pattern="^(gmail|outlook|yahoo|imap)$")
    email_address: EmailStr
    display_name: Optional[str] = None
    # For IMAP accounts
    imap_host: Optional[str] = None
    imap_port: Optional[int] = Field(default=993, ge=1, le=65535)
    imap_password: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = Field(default=587, ge=1, le=65535)


class EmailAccountUpdate(BaseModel):
    """Schema for updating an email account."""

    display_name: Optional[str] = None
    sync_enabled: Optional[bool] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = Field(default=None, ge=1, le=65535)
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = Field(default=None, ge=1, le=65535)


class EmailAccountResponse(BaseModel):
    """Schema for email account response."""

    id: UUID
    provider: str
    email_address: str
    display_name: Optional[str]
    is_active: bool
    sync_enabled: bool
    last_sync: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class EmailResponse(BaseModel):
    """Schema for email response."""

    id: UUID
    account_id: UUID
    message_id: str
    thread_id: Optional[str]
    subject: Optional[str]
    sender: str
    sender_name: Optional[str]
    recipients: Optional[List[str]]
    cc: Optional[List[str]]
    body_text: Optional[str]
    body_html: Optional[str]
    snippet: Optional[str]
    category: Optional[str]
    labels: Optional[List[str]]
    folder: Optional[str]
    has_attachments: bool
    is_read: bool
    is_starred: bool
    is_archived: bool
    language: Optional[str]
    sentiment: Optional[str]
    priority_score: Optional[float]
    received_at: Optional[datetime]
    processed_at: Optional[datetime]
    created_at: datetime
    has_draft: bool = False
    draft_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class EmailListResponse(BaseModel):
    """Schema for paginated email list response."""

    items: List[EmailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class EmailCategoryUpdate(BaseModel):
    """Schema for updating email category."""

    category: str = Field(..., pattern="^(urgent|to_respond|fyi|newsletter|spam|archived)$")


class EmailMarkRead(BaseModel):
    """Schema for marking email as read/unread."""

    is_read: bool


class EmailStar(BaseModel):
    """Schema for starring/unstarring email."""

    is_starred: bool


class EmailArchive(BaseModel):
    """Schema for archiving email."""

    is_archived: bool


class EmailSearch(BaseModel):
    """Schema for email search."""

    query: str = Field(..., min_length=1, max_length=500)
    account_id: Optional[UUID] = None
    category: Optional[str] = None
    is_read: Optional[bool] = None
    has_attachments: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sender: Optional[str] = None
