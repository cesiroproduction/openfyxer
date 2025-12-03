"""Celery tasks module."""

from app.workers.tasks.email_tasks import (
    classify_email,
    generate_draft,
    send_draft,
    sync_all_accounts,
    sync_email_account,
)
from app.workers.tasks.notification_tasks import (
    send_meeting_reminder,
    send_notification,
)
from app.workers.tasks.rag_tasks import (
    index_document,
    index_email,
    index_meeting,
    reindex_all,
)
from app.workers.tasks.transcription_tasks import summarize_meeting, transcribe_meeting

__all__ = [
    "sync_email_account",
    "sync_all_accounts",
    "classify_email",
    "generate_draft",
    "send_draft",
    "transcribe_meeting",
    "summarize_meeting",
    "index_email",
    "index_document",
    "index_meeting",
    "reindex_all",
    "send_notification",
    "send_meeting_reminder",
]
