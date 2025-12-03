"""Chat schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Schema for chat message."""

    message: str = Field(..., min_length=1, max_length=2000)
    context_type: Optional[str] = Field(default=None, pattern="^(email|document|meeting|general)$")
    context_id: Optional[UUID] = None
    language: Optional[str] = Field(default=None, pattern="^(en|ro)$")


class ChatMessageResponse(BaseModel):
    """Schema for individual chat message in history."""

    id: UUID
    role: str  # user, assistant
    content: str
    context_type: Optional[str]
    context_id: Optional[UUID]
    created_at: datetime


class ChatResponse(BaseModel):
    """Schema for chat response."""

    message_id: UUID
    response: str
    sources: List[dict] = []
    suggested_actions: List[dict] = []
    response_time_ms: int
    llm_provider: str
    llm_model: str


class ChatHistory(BaseModel):
    """Schema for chat history."""

    messages: List[ChatMessageResponse]
    total: int


class ChatSuggestion(BaseModel):
    """Schema for chat suggestion."""

    text: str
    type: str  # question, action, follow_up


class ChatContext(BaseModel):
    """Schema for chat context."""

    recent_emails: int
    recent_meetings: int
    indexed_documents: int
    active_drafts: int
