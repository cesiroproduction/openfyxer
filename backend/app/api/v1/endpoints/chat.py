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
from app.models.email import Email
from app.models.email_account import EmailAccount
from app.models.meeting import Meeting
from app.models.draft import Draft
from app.models.user import User
from app.models.user_settings import UserSettings
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
chat_histories: dict = {}

# --- HARDCODED CONFIGURATION ---
FORCE_PROVIDER = "openai"
FORCE_MODEL = "gpt-3.5-turbo"
# Cheia ta OpenAI
FORCE_API_KEY = "YOUR API KEY"


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

    if user_id not in chat_histories:
        chat_histories[user_id] = []

    user_message = ChatMessageResponse(
        id=uuid.uuid4(),
        role="user",
        content=message_in.message,
        context_type=message_in.context_type,
        context_id=message_in.context_id,
        created_at=datetime.utcnow(),
    )
    chat_histories[user_id].append(user_message)

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

    system_prompt = (
        "You are OpenFyxer, an AI executive assistant. "
        "Be concise, helpful, and professional."
    )

    try:
        # FORCED OPENAI CONFIGURATION
        llm = LLMService(
            provider=FORCE_PROVIDER, 
            model=FORCE_MODEL, 
            api_key=FORCE_API_KEY
        )

        if context_text:
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

        logger.info(f"LLM response generated successfully using {FORCE_PROVIDER}")

    except Exception as e:
        logger.exception(f"LLM Error: {e}")
        response_text = f"Error generating response: {str(e)}"

    suggested_actions = []
    message_lower = message_in.message.lower()
    if "email" in message_lower:
        suggested_actions.append({"type": "action", "text": "View inbox", "action": "navigate", "target": "/inbox"})

    assistant_message = ChatMessageResponse(
        id=uuid.uuid4(),
        role="assistant",
        content=response_text,
        context_type=message_in.context_type,
        context_id=message_in.context_id,
        created_at=datetime.utcnow(),
    )
    chat_histories[user_id].append(assistant_message)

    if len(chat_histories[user_id]) > 100:
        chat_histories[user_id] = chat_histories[user_id][-100:]

    response_time_ms = int((time.time() - start_time) * 1000)

    return ChatResponse(
        message_id=assistant_message.id,
        response=response_text,
        sources=[],
        suggested_actions=suggested_actions,
        response_time_ms=response_time_ms,
        llm_provider=FORCE_PROVIDER,
        llm_model=FORCE_MODEL,
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
    return ChatHistory(messages=messages, total=len(chat_histories[user_id]))


@router.delete("/history")
async def clear_chat_history(current_user: User = Depends(get_current_user)) -> Any:
    user_id = str(current_user.id)
    if user_id in chat_histories:
        chat_histories[user_id] = []
    return {"message": "Chat history cleared"}


@router.get("/suggestions", response_model=List[ChatSuggestion])
async def get_chat_suggestions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    suggestions = [
        ChatSuggestion(text="Summarize my unread emails", type="question"),
        ChatSuggestion(text="What meetings do I have today?", type="question"),
    ]
    return suggestions


@router.get("/context", response_model=ChatContext)
async def get_chat_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return ChatContext(
        recent_emails=0,
        recent_meetings=0,
        indexed_documents=0,
        active_drafts=0,
    )
