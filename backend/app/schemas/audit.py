"""Audit log schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    """Schema for audit log response."""

    id: UUID
    user_id: UUID
    action: str
    entity_type: Optional[str]
    entity_id: Optional[UUID]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    status: str
    error_message: Optional[str]
    duration_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Schema for paginated audit log list response."""

    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AuditLogFilter(BaseModel):
    """Schema for filtering audit logs."""

    action: Optional[str] = None
    entity_type: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(success|failure|error)$")
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class AuditStats(BaseModel):
    """Schema for audit statistics."""

    total_actions: int
    actions_today: int
    actions_this_week: int
    actions_this_month: int
    success_rate: float
    most_common_actions: List[Dict[str, Any]]
    recent_errors: List[AuditLogResponse]
