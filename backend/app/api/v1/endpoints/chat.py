"""Chat endpoints."""

import logging
import uuid
from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.exceptions import LLMError
from app.db.session import get_db
from app.models.document import Document
from app.models.draft import Draft
from app.models.email import Email
from app.models.email_account import EmailAccount
from app.models.meeting import Meeting
from app.models.user import User
from app.schemas.chat import (
    ChatContext,
    ChatHistory,
    ChatMessage,
    ChatMessageResponse,
    ChatResponse,
    ChatSuggestion,
)
from app.services import LLMService

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory chat history (in production, use Redis or database)
chat_histories: dict = {}


@router.post("", response_model=ChatResponse)
async def send_chat_message(
    message_in: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Send a message to the AI assistant."""
    import time

    start_time = time.time()

    user_id = str(current_user.id)

    # Initialize chat history for user if not exists
    if user_id not in chat_histories:
        chat_histories[user_id] = []

    # Create user message
    user_message = ChatMessageResponse(
        id=uuid.uuid4(),
        role="user",
        content=message_in.message,
        context_type=message_in.context_type,
        context_id=message_in.context_id,
        created_at=datetime.utcnow(),
    )
    chat_histories[user_id].append(user_message)

    # Get context if specified
    context_text = ""
    if message_in.context_type and message_in.context_id:
        if message_in.context_type == "email":
            accounts_result = await db.execute(
                select(EmailAccount.id).where(EmailAccount.user_id == current_user.id)
            )
            account_ids = [row[0] for row in accounts_result.fetchall()]

            email_result = await db.execute(
                select(Email).where(
                    Email.id == message_in.context_id,
                    Email.account_id.in_(account_ids),
                )
            )
            email = email_result.scalar_one_or_none()
            if email:
                context_text = f"Email subject: {email.subject}\nFrom: {email.sender}\nContent: {email.body_text[:1000] if email.body_text else ''}"

        elif message_in.context_type == "document":
            doc_result = await db.execute(
                select(Document).where(
                    Document.id == message_in.context_id,
                    Document.user_id == current_user.id,
                )
            )
            doc = doc_result.scalar_one_or_none()
            if doc:
                context_text = f"Document: {doc.filename}\nContent: {doc.content_text[:1000] if doc.content_text else ''}"

        elif message_in.context_type == "meeting":
            meeting_result = await db.execute(
                select(Meeting).where(
                    Meeting.id == message_in.context_id,
                    Meeting.user_id == current_user.id,
                )
            )
            meeting = meeting_result.scalar_one_or_none()
            if meeting:
                context_text = f"Meeting: {meeting.title}\nTranscript: {meeting.transcript[:1000] if meeting.transcript else ''}\nSummary: {meeting.summary or ''}"

    # Build system prompt for the AI assistant
    system_prompt = (
        "You are OpenFyxer, an AI executive assistant that helps manage emails, "
        "calendar, documents and meetings. Be concise, helpful, and professional. "
        "If you don't know something, say so honestly."
    )

    # Initialize LLM provider and model
    llm_provider = "local"
    llm_model = getattr(settings, "LOCAL_LLM_MODEL", "tinyllama")

    try:
        llm = LLMService(provider=llm_provider, model=llm_model)

        if context_text:
            # Use the helper that's meant for QA over context
            response_text = await llm.answer_question(
                question=message_in.message,
                context=context_text,
                language=message_in.language or "en",
            )
        else:
            response_text = await llm.generate(
                prompt=message_in.message,
                system_prompt=system_prompt,
                max_tokens=500,
                temperature=0.7,
            )

        logger.info(f"LLM response generated successfully using {llm_provider}/{llm_model}")

    except LLMError as e:
        # Known LLM/HTTP issues: log, then fall back
        logger.exception("LLMError while generating chat response")
        response_text = (
            f"I received your message but the AI model is temporarily unavailable. "
            f"Please try again in a moment. Error: {str(e)}"
        )
        llm_provider = "error"
        llm_model = "placeholder"
    except Exception:
        # Any unexpected error: keep old placeholder behavior
        logger.exception("Unexpected error while generating chat response")
        response_text = (
            f"I received your message: '{message_in.message}'. "
            f"However, I encountered an issue connecting to the AI model."
        )
        llm_provider = "placeholder"
        llm_model = "placeholder"

    # Add some helpful suggestions based on message content
    suggested_actions = []
    message_lower = message_in.message.lower()

    if "email" in message_lower:
        suggested_actions.append(
            {
                "type": "action",
                "text": "View inbox",
                "action": "navigate",
                "target": "/inbox",
            }
        )

    if "meeting" in message_lower or "calendar" in message_lower:
        suggested_actions.append(
            {
                "type": "action",
                "text": "View calendar",
                "action": "navigate",
                "target": "/calendar",
            }
        )

    if "document" in message_lower or "file" in message_lower:
        suggested_actions.append(
            {
                "type": "action",
                "text": "View knowledge base",
                "action": "navigate",
                "target": "/knowledge-base",
            }
        )

    # Create assistant message
    assistant_message = ChatMessageResponse(
        id=uuid.uuid4(),
        role="assistant",
        content=response_text,
        context_type=message_in.context_type,
        context_id=message_in.context_id,
        created_at=datetime.utcnow(),
    )
    chat_histories[user_id].append(assistant_message)

    # Keep only last 100 messages
    if len(chat_histories[user_id]) > 100:
        chat_histories[user_id] = chat_histories[user_id][-100:]

    response_time_ms = int((time.time() - start_time) * 1000)

    return ChatResponse(
        message_id=assistant_message.id,
        response=response_text,
        sources=[],
        suggested_actions=suggested_actions,
        response_time_ms=response_time_ms,
        llm_provider="placeholder",
        llm_model="placeholder",
    )


@router.get("/history", response_model=ChatHistory)
async def get_chat_history(
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get chat history."""
    user_id = str(current_user.id)

    if user_id not in chat_histories:
        return ChatHistory(messages=[], total=0)

    messages = chat_histories[user_id][-limit:]

    return ChatHistory(
        messages=messages,
        total=len(chat_histories[user_id]),
    )


@router.delete("/history")
async def clear_chat_history(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Clear chat history."""
    user_id = str(current_user.id)

    if user_id in chat_histories:
        chat_histories[user_id] = []

    return {"message": "Chat history cleared"}


@router.get("/suggestions", response_model=List[ChatSuggestion])
async def get_chat_suggestions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get suggested questions/actions based on current context."""
    suggestions = []

    # Get counts for context
    accounts_result = await db.execute(
        select(EmailAccount.id).where(EmailAccount.user_id == current_user.id)
    )
    account_ids = [row[0] for row in accounts_result.fetchall()]

    # Check for unread emails
    if account_ids:
        unread_result = await db.execute(
            select(func.count(Email.id)).where(
                Email.account_id.in_(account_ids),
                Email.is_read.is_(False),
            )
        )
        unread_count = unread_result.scalar() or 0

        if unread_count > 0:
            suggestions.append(
                ChatSuggestion(
                    text=f"Summarize my {unread_count} unread emails",
                    type="question",
                )
            )

    # Check for pending drafts
    drafts_result = await db.execute(
        select(func.count(Draft.id)).where(
            Draft.user_id == current_user.id,
            Draft.status == "pending",
        )
    )
    pending_drafts = drafts_result.scalar() or 0

    if pending_drafts > 0:
        suggestions.append(
            ChatSuggestion(
                text=f"Review my {pending_drafts} pending drafts",
                type="action",
            )
        )

    # Add general suggestions
    suggestions.extend(
        [
            ChatSuggestion(
                text="What meetings do I have today?",
                type="question",
            ),
            ChatSuggestion(
                text="Find emails about project updates",
                type="question",
            ),
            ChatSuggestion(
                text="Help me draft a follow-up email",
                type="action",
            ),
        ]
    )

    return suggestions[:5]


@router.get("/context", response_model=ChatContext)
async def get_chat_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get current context for chat."""
    # Get email accounts
    accounts_result = await db.execute(
        select(EmailAccount.id).where(EmailAccount.user_id == current_user.id)
    )
    account_ids = [row[0] for row in accounts_result.fetchall()]

    # Count recent emails (last 7 days)
    from datetime import timedelta

    week_ago = datetime.utcnow() - timedelta(days=7)

    recent_emails = 0
    if account_ids:
        emails_result = await db.execute(
            select(func.count(Email.id)).where(
                Email.account_id.in_(account_ids),
                Email.received_at >= week_ago,
            )
        )
        recent_emails = emails_result.scalar() or 0

    # Count recent meetings
    meetings_result = await db.execute(
        select(func.count(Meeting.id)).where(
            Meeting.user_id == current_user.id,
            Meeting.created_at >= week_ago,
        )
    )
    recent_meetings = meetings_result.scalar() or 0

    # Count indexed documents
    docs_result = await db.execute(
        select(func.count(Document.id)).where(
            Document.user_id == current_user.id,
            Document.indexed_at.isnot(None),
        )
    )
    indexed_documents = docs_result.scalar() or 0

    # Count active drafts
    drafts_result = await db.execute(
        select(func.count(Draft.id)).where(
            Draft.user_id == current_user.id,
            Draft.status == "pending",
        )
    )
    active_drafts = drafts_result.scalar() or 0

    return ChatContext(
        recent_emails=recent_emails,
        recent_meetings=recent_meetings,
        indexed_documents=indexed_documents,
        active_drafts=active_drafts,
    )
