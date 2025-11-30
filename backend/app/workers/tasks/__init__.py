"""Celery tasks module."""

from app.workers.tasks.email_tasks import (
    sync_email_account,
    sync_all_accounts,
    classify_email,
    generate_draft,
    send_draft,
)
from app.workers.tasks.transcription_tasks import (
    transcribe_meeting,
    summarize_meeting,
)
from app.workers.tasks.rag_tasks import (
    index_email,
    index_document,
    index_meeting,
    reindex_all,
)
from app.workers.tasks.notification_tasks import (
    send_notification,
    send_meeting_reminder,
)

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
