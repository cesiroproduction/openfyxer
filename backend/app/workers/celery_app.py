"""Celery application configuration."""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "openfyxer",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.tasks.email_tasks",
        "app.workers.tasks.transcription_tasks",
        "app.workers.tasks.rag_tasks",
        "app.workers.tasks.notification_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    result_expires=86400,  # Results expire after 24 hours
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Task routing
celery_app.conf.task_routes = {
    "app.workers.tasks.email_tasks.*": {"queue": "email"},
    "app.workers.tasks.transcription_tasks.*": {"queue": "transcription"},
    "app.workers.tasks.rag_tasks.*": {"queue": "rag"},
    "app.workers.tasks.notification_tasks.*": {"queue": "notifications"},
}

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "sync-all-emails-every-5-minutes": {
        "task": "app.workers.tasks.email_tasks.sync_all_accounts",
        "schedule": 300.0,  # 5 minutes
    },
    "sync-all-calendars-every-15-minutes": {
        "task": "app.workers.tasks.email_tasks.sync_all_calendars",
        "schedule": 900.0,  # 15 minutes
    },
    "cleanup-old-audit-logs-daily": {
        "task": "app.workers.tasks.email_tasks.cleanup_old_audit_logs",
        "schedule": 86400.0,  # 24 hours
    },
}
