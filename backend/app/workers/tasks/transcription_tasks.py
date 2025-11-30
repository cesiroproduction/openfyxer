"""Transcription-related Celery tasks."""

import asyncio
from datetime import datetime
from uuid import UUID

from app.workers.celery_app import celery_app


def get_async_session():
    """Get async database session for tasks."""
    from app.db.session import async_session_maker
    return async_session_maker()


def run_async(coro):
    """Run async function in sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=2)
def transcribe_meeting(
    self,
    meeting_id: str,
    user_id: str,
    language: str = "auto",
    model: str = "base",
):
    """Transcribe meeting audio."""
    async def _transcribe():
        from sqlalchemy import select
        from app.models.meeting import Meeting
        from app.models.audit_log import AuditLog
        from app.services.transcription_service import TranscriptionService

        async with get_async_session() as db:
            try:
                # Get meeting
                result = await db.execute(
                    select(Meeting).where(
                        Meeting.id == UUID(meeting_id),
                        Meeting.user_id == UUID(user_id),
                    )
                )
                meeting = result.scalar_one_or_none()

                if not meeting:
                    return {"status": "error", "message": "Meeting not found"}

                if not meeting.audio_file_path:
                    return {"status": "error", "message": "No audio file"}

                # Update status
                meeting.status = "transcribing"
                await db.commit()

                # Transcribe
                transcription_service = TranscriptionService(model_size=model)
                result = await transcription_service.transcribe(
                    meeting.audio_file_path,
                    language=language if language != "auto" else None,
                )

                # Update meeting
                meeting.transcript = result["text"]
                meeting.transcript_language = result["language"]
                meeting.transcription_model = f"whisper-{model}"
                meeting.transcription_time_seconds = result["transcription_time_seconds"]
                meeting.audio_duration_seconds = result["duration_seconds"]
                meeting.status = "transcribed"
                meeting.transcribed_at = datetime.utcnow()

                # Create audit log
                audit_log = AuditLog(
                    user_id=UUID(user_id),
                    action="meeting_transcription",
                    entity_type="meeting",
                    entity_id=UUID(meeting_id),
                    details={
                        "language": result["language"],
                        "duration_seconds": result["duration_seconds"],
                        "transcription_time_seconds": result["transcription_time_seconds"],
                    },
                    status="success",
                )
                db.add(audit_log)
                await db.commit()

                # Trigger summarization
                summarize_meeting.delay(meeting_id, user_id)

                # Trigger indexing
                from app.workers.tasks.rag_tasks import index_meeting
                index_meeting.delay(meeting_id, user_id)

                # Send notification
                from app.workers.tasks.notification_tasks import send_notification
                send_notification.delay(
                    user_id,
                    "transcription_complete",
                    {
                        "meeting_title": meeting.title,
                    },
                )

                return {
                    "status": "success",
                    "meeting_id": meeting_id,
                    "language": result["language"],
                    "duration_seconds": result["duration_seconds"],
                }

            except Exception as e:
                # Update status to error
                if meeting:
                    meeting.status = "error"
                    await db.commit()

                # Log error
                audit_log = AuditLog(
                    user_id=UUID(user_id),
                    action="meeting_transcription",
                    entity_type="meeting",
                    entity_id=UUID(meeting_id),
                    status="error",
                    error_message=str(e),
                )
                db.add(audit_log)
                await db.commit()

                raise self.retry(exc=e, countdown=120)

    return run_async(_transcribe())


@celery_app.task(bind=True, max_retries=2)
def summarize_meeting(self, meeting_id: str, user_id: str, language: str = None):
    """Summarize meeting transcript."""
    async def _summarize():
        from sqlalchemy import select
        from app.models.meeting import Meeting
        from app.models.audit_log import AuditLog
        from app.services.llm_service import LLMService

        async with get_async_session() as db:
            try:
                # Get meeting
                result = await db.execute(
                    select(Meeting).where(
                        Meeting.id == UUID(meeting_id),
                        Meeting.user_id == UUID(user_id),
                    )
                )
                meeting = result.scalar_one_or_none()

                if not meeting:
                    return {"status": "error", "message": "Meeting not found"}

                if not meeting.transcript:
                    return {"status": "error", "message": "No transcript available"}

                # Summarize using LLM
                llm_service = LLMService()
                summary_result = await llm_service.summarize_meeting(
                    transcript=meeting.transcript,
                    language=language or meeting.transcript_language or "en",
                )

                # Update meeting
                meeting.summary = summary_result.get("summary", "")
                meeting.action_items = summary_result.get("action_items", [])
                meeting.key_decisions = summary_result.get("key_decisions", [])
                meeting.topics = summary_result.get("topics", [])
                meeting.status = "summarized"
                meeting.summarized_at = datetime.utcnow()

                # Create audit log
                audit_log = AuditLog(
                    user_id=UUID(user_id),
                    action="meeting_summarization",
                    entity_type="meeting",
                    entity_id=UUID(meeting_id),
                    details={
                        "action_items_count": len(meeting.action_items or []),
                        "key_decisions_count": len(meeting.key_decisions or []),
                    },
                    status="success",
                )
                db.add(audit_log)
                await db.commit()

                # Send notification
                from app.workers.tasks.notification_tasks import send_notification
                send_notification.delay(
                    user_id,
                    "transcription_complete",
                    {
                        "meeting_title": meeting.title,
                        "summary": meeting.summary[:300] if meeting.summary else None,
                    },
                )

                return {
                    "status": "success",
                    "meeting_id": meeting_id,
                    "action_items_count": len(meeting.action_items or []),
                }

            except Exception as e:
                # Log error
                audit_log = AuditLog(
                    user_id=UUID(user_id),
                    action="meeting_summarization",
                    entity_type="meeting",
                    entity_id=UUID(meeting_id),
                    status="error",
                    error_message=str(e),
                )
                db.add(audit_log)
                await db.commit()

                raise self.retry(exc=e, countdown=60)

    return run_async(_summarize())


@celery_app.task
def batch_transcribe_meetings(user_id: str, meeting_ids: list):
    """Batch transcribe multiple meetings."""
    for meeting_id in meeting_ids:
        transcribe_meeting.delay(meeting_id, user_id)

    return {"queued_meetings": len(meeting_ids)}
