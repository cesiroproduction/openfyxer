"""Pydantic schemas for OpenFyxer."""

from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    Token,
    TokenPayload,
    TwoFactorSetup,
    TwoFactorVerify,
)
from app.schemas.email import (
    EmailAccountCreate,
    EmailAccountUpdate,
    EmailAccountResponse,
    EmailResponse,
    EmailListResponse,
    EmailCategoryUpdate,
)
from app.schemas.draft import (
    DraftCreate,
    DraftUpdate,
    DraftResponse,
    DraftListResponse,
)
from app.schemas.calendar import (
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarEventResponse,
    CalendarEventListResponse,
    AvailableSlot,
    ScheduleMeetingRequest,
)
from app.schemas.rag import (
    RAGQuery,
    RAGResponse,
    DocumentUpload,
    DocumentResponse,
    DocumentListResponse,
)
from app.schemas.meeting import (
    MeetingCreate,
    MeetingUpdate,
    MeetingResponse,
    MeetingListResponse,
    TranscriptionRequest,
)
from app.schemas.settings import (
    UserSettingsUpdate,
    UserSettingsResponse,
)
from app.schemas.chat import (
    ChatMessage,
    ChatResponse,
    ChatHistory,
)
from app.schemas.audit import (
    AuditLogResponse,
    AuditLogListResponse,
)

__all__ = [
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenPayload",
    "TwoFactorSetup",
    "TwoFactorVerify",
    # Email
    "EmailAccountCreate",
    "EmailAccountUpdate",
    "EmailAccountResponse",
    "EmailResponse",
    "EmailListResponse",
    "EmailCategoryUpdate",
    # Draft
    "DraftCreate",
    "DraftUpdate",
    "DraftResponse",
    "DraftListResponse",
    # Calendar
    "CalendarEventCreate",
    "CalendarEventUpdate",
    "CalendarEventResponse",
    "CalendarEventListResponse",
    "AvailableSlot",
    "ScheduleMeetingRequest",
    # RAG
    "RAGQuery",
    "RAGResponse",
    "DocumentUpload",
    "DocumentResponse",
    "DocumentListResponse",
    # Meeting
    "MeetingCreate",
    "MeetingUpdate",
    "MeetingResponse",
    "MeetingListResponse",
    "TranscriptionRequest",
    # Settings
    "UserSettingsUpdate",
    "UserSettingsResponse",
    # Chat
    "ChatMessage",
    "ChatResponse",
    "ChatHistory",
    # Audit
    "AuditLogResponse",
    "AuditLogListResponse",
]
