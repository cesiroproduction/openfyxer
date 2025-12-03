"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    audit,
    auth,
    calendar,
    chat,
    drafts,
    emails,
    integrations_google,
    meetings,
    rag,
    settings,
    users,
)

api_router = APIRouter()

# Authentication endpoints
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

# User endpoints
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
)

# Email endpoints
api_router.include_router(
    emails.router,
    prefix="/emails",
    tags=["Emails"],
)

# Draft endpoints
api_router.include_router(
    drafts.router,
    prefix="/drafts",
    tags=["Drafts"],
)

# Calendar endpoints
api_router.include_router(
    calendar.router,
    prefix="/calendar",
    tags=["Calendar"],
)

# RAG/Knowledge Base endpoints
api_router.include_router(
    rag.router,
    prefix="/rag",
    tags=["RAG / Knowledge Base"],
)

# Meeting endpoints
api_router.include_router(
    meetings.router,
    prefix="/meetings",
    tags=["Meetings"],
)

# Settings endpoints
api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["Settings"],
)

# Chat endpoints
api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat"],
)

# Audit endpoints
api_router.include_router(
    audit.router,
    prefix="/audit",
    tags=["Audit"],
)

# Google OAuth integration endpoints
api_router.include_router(
    integrations_google.router,
    prefix="/integrations/google",
    tags=["Google Integration"],
)
