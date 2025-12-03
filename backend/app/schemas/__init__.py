"""Pydantic schemas for OpenFyxer."""

from app.schemas.audit import AuditLogListResponse, AuditLogResponse
from app.schemas.calendar import (
    AvailableSlot,
    CalendarEventCreate,
    CalendarEventListResponse,
    CalendarEventResponse,
    CalendarEventUpdate,
    ScheduleMeetingRequest,
)
from app.schemas.chat import ChatHistory, ChatMessage, ChatResponse
from app.schemas.draft import DraftCreate, DraftListResponse, DraftResponse, DraftUpdate
from app.schemas.email import (
    EmailAccountCreate,
    EmailAccountResponse,
    EmailAccountUpdate,
    EmailCategoryUpdate,
    EmailListResponse,
    EmailResponse,
)
from app.schemas.meeting import (
    MeetingCreate,
    MeetingListResponse,
    MeetingResponse,
    MeetingUpdate,
    TranscriptionRequest,
)
from app.schemas.rag import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUpload,
    RAGQuery,
    RAGResponse,
)
from app.schemas.settings import UserSettingsResponse, UserSettingsUpdate
from app.schemas.user import (
    Token,
    TokenPayload,
    TwoFactorSetup,
    TwoFactorVerify,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
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
