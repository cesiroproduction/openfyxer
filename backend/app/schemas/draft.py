"""Draft schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DraftCreate(BaseModel):
    """Schema for creating a draft."""

    email_id: UUID
    content: Optional[str] = None  # If None, AI will generate
    tone: Optional[str] = Field(
        default=None, pattern="^(formal|friendly|professional|concise)$"
    )
    language: Optional[str] = Field(default=None, pattern="^(en|ro)$")


class DraftUpdate(BaseModel):
    """Schema for updating a draft."""

    subject: Optional[str] = None
    content: Optional[str] = None


class DraftResponse(BaseModel):
    """Schema for draft response."""

    id: UUID
    email_id: UUID
    user_id: UUID
    subject: Optional[str]
    content: str
    original_content: Optional[str]
    status: str
    llm_provider: Optional[str]
    llm_model: Optional[str]
    generation_time_ms: Optional[int]
    confidence_score: Optional[float]
    language: Optional[str]
    tone: Optional[str]
    edited_by_user: bool
    created_at: datetime
    updated_at: datetime
    sent_at: Optional[datetime]

    class Config:
        from_attributes = True


class DraftListResponse(BaseModel):
    """Schema for paginated draft list response."""

    items: List[DraftResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DraftSend(BaseModel):
    """Schema for sending a draft."""

    subject: Optional[str] = None  # Override subject if needed
    content: Optional[str] = None  # Override content if needed


class DraftRegenerate(BaseModel):
    """Schema for regenerating a draft."""

    tone: Optional[str] = Field(
        default=None, pattern="^(formal|friendly|professional|concise)$"
    )
    language: Optional[str] = Field(default=None, pattern="^(en|ro)$")
    instructions: Optional[str] = Field(default=None, max_length=500)
