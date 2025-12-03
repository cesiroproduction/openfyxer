"""Notification Celery tasks."""

import asyncio
from datetime import datetime, timedelta
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


@celery_app.task
def send_notification(user_id: str, notification_type: str, data: dict):
    """Send notification to user based on their preferences."""

    async def _send():
        from sqlalchemy import select

        from app.core.encryption import decrypt_value
        from app.models.user_settings import UserSettings
        from app.services.notification_service import NotificationService

        async with get_async_session() as db:
            # Get user settings
            result = await db.execute(
                select(UserSettings).where(UserSettings.user_id == UUID(user_id))
            )
            settings = result.scalar_one_or_none()

            if not settings:
                return {"status": "skipped", "message": "No settings configured"}

            # Check notification preferences
            prefs = settings.notification_preferences or {}
            if not prefs.get(notification_type, True):
                return {"status": "skipped", "message": "Notification disabled"}

            # Initialize notification service
            notification_service = NotificationService(
                slack_webhook_url=(
                    decrypt_value(settings.slack_webhook_url)
                    if settings.slack_webhook_url
                    else None
                ),
                sms_provider=settings.sms_provider,
                sms_api_key=(
                    decrypt_value(settings.sms_api_key)
                    if settings.sms_api_key
                    else None
                ),
                sms_phone_number=settings.sms_phone_number,
                notification_email=settings.notification_email,
            )

            sent_channels = []

            try:
                if notification_type == "new_email":
                    await notification_service.notify_new_email(
                        sender=data.get("sender", "Unknown"),
                        subject=data.get("subject", "No Subject"),
                        category=data.get("category", "fyi"),
                        preview=data.get("preview", ""),
                    )
                    sent_channels.append("slack")

                elif notification_type == "draft_ready":
                    await notification_service.notify_draft_ready(
                        email_subject=data.get("email_subject", ""),
                        draft_preview=data.get("draft_preview", ""),
                    )
                    sent_channels.append("slack")

                elif notification_type == "meeting_reminder":
                    await notification_service.notify_meeting_reminder(
                        title=data.get("title", ""),
                        start_time=data.get("start_time", ""),
                        location=data.get("location"),
                        meeting_link=data.get("meeting_link"),
                    )
                    sent_channels.extend(["slack", "sms"])

                elif notification_type == "transcription_complete":
                    await notification_service.notify_transcription_complete(
                        meeting_title=data.get("meeting_title", ""),
                        summary=data.get("summary"),
                    )
                    sent_channels.append("slack")

                elif notification_type == "error":
                    await notification_service.notify_error(
                        error_type=data.get("error_type", "Unknown"),
                        error_message=data.get("error_message", ""),
                        context=data.get("context"),
                    )
                    sent_channels.append("slack")

                return {
                    "status": "success",
                    "channels": sent_channels,
                }

            except Exception as e:
                return {
                    "status": "error",
                    "message": str(e),
                }

    return run_async(_send())


@celery_app.task
def send_meeting_reminder(meeting_id: str, user_id: str, minutes_before: int = 15):
    """Send meeting reminder notification."""

    async def _remind():
        from sqlalchemy import select

        from app.models.calendar_event import CalendarEvent

        async with get_async_session() as db:
            # Get meeting
            result = await db.execute(
                select(CalendarEvent).where(
                    CalendarEvent.id == UUID(meeting_id),
                    CalendarEvent.user_id == UUID(user_id),
                )
            )
            event = result.scalar_one_or_none()

            if not event:
                return {"status": "error", "message": "Event not found"}

            if event.status == "cancelled":
                return {"status": "skipped", "message": "Event cancelled"}

            # Send notification
            send_notification.delay(
                user_id,
                "meeting_reminder",
                {
                    "title": event.title,
                    "start_time": event.start_time.strftime("%H:%M"),
                    "location": event.location,
                    "meeting_link": event.meeting_link,
                },
            )

            return {"status": "success", "event_id": meeting_id}

    return run_async(_remind())


@celery_app.task
def schedule_meeting_reminders(user_id: str):
    """Schedule reminders for upcoming meetings."""

    async def _schedule():
        from sqlalchemy import select

        from app.models.calendar_event import CalendarEvent
        from app.models.user_settings import UserSettings

        async with get_async_session() as db:
            # Get user settings for default reminder time
            settings_result = await db.execute(
                select(UserSettings).where(UserSettings.user_id == UUID(user_id))
            )
            settings = settings_result.scalar_one_or_none()

            default_reminder = 15
            if settings and settings.meeting_buffer_minutes:
                default_reminder = settings.meeting_buffer_minutes

            # Get upcoming events in the next hour
            now = datetime.utcnow()
            one_hour_later = now + timedelta(hours=1)

            result = await db.execute(
                select(CalendarEvent).where(
                    CalendarEvent.user_id == UUID(user_id),
                    CalendarEvent.start_time >= now,
                    CalendarEvent.start_time <= one_hour_later,
                    CalendarEvent.status != "cancelled",
                )
            )
            events = result.scalars().all()

            scheduled = 0
            for event in events:
                reminder_minutes = event.reminder_minutes or default_reminder
                reminder_time = event.start_time - timedelta(minutes=reminder_minutes)

                if reminder_time > now:
                    # Schedule the reminder
                    delay_seconds = (reminder_time - now).total_seconds()
                    send_meeting_reminder.apply_async(
                        args=[str(event.id), user_id, reminder_minutes],
                        countdown=delay_seconds,
                    )
                    scheduled += 1

            return {"scheduled_reminders": scheduled}

    return run_async(_schedule())


@celery_app.task
def send_daily_digest(user_id: str):
    """Send daily digest email."""

    async def _digest():
        from sqlalchemy import func, select

        from app.models.calendar_event import CalendarEvent
        from app.models.draft import Draft
        from app.models.email import Email
        from app.models.email_account import EmailAccount
        from app.models.user_settings import UserSettings
        from app.services.notification_service import NotificationService

        async with get_async_session() as db:
            # Get user settings
            settings_result = await db.execute(
                select(UserSettings).where(UserSettings.user_id == UUID(user_id))
            )
            settings = settings_result.scalar_one_or_none()

            if not settings or not settings.notification_email:
                return {"status": "skipped", "message": "No notification email"}

            # Get today's stats
            today_start = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            tomorrow = today_start + timedelta(days=1)

            # Count emails received today
            accounts_result = await db.execute(
                select(EmailAccount.id).where(EmailAccount.user_id == UUID(user_id))
            )
            account_ids = [row[0] for row in accounts_result.fetchall()]

            emails_today = 0
            urgent_emails = 0
            if account_ids:
                emails_result = await db.execute(
                    select(func.count(Email.id)).where(
                        Email.account_id.in_(account_ids),
                        Email.received_at >= today_start,
                    )
                )
                emails_today = emails_result.scalar() or 0

                urgent_result = await db.execute(
                    select(func.count(Email.id)).where(
                        Email.account_id.in_(account_ids),
                        Email.received_at >= today_start,
                        Email.category == "urgent",
                    )
                )
                urgent_emails = urgent_result.scalar() or 0

            # Count pending drafts
            drafts_result = await db.execute(
                select(func.count(Draft.id)).where(
                    Draft.user_id == UUID(user_id),
                    Draft.status == "pending",
                )
            )
            pending_drafts = drafts_result.scalar() or 0

            # Count today's meetings
            meetings_result = await db.execute(
                select(func.count(CalendarEvent.id)).where(
                    CalendarEvent.user_id == UUID(user_id),
                    CalendarEvent.start_time >= today_start,
                    CalendarEvent.start_time < tomorrow,
                    CalendarEvent.status != "cancelled",
                )
            )
            meetings_today = meetings_result.scalar() or 0

            # Build digest message
            subject = f"OpenFyxer Daily Digest - {today_start.strftime('%B %d, %Y')}"
            body = f"""Good morning!

Here's your daily summary:

Emails:
- {emails_today} new emails received
- {urgent_emails} marked as urgent
- {pending_drafts} drafts awaiting review

Calendar:
- {meetings_today} meetings scheduled for today

Have a productive day!

---
OpenFyxer - Your AI Executive Assistant
"""

            # Send email
            notification_service = NotificationService(
                notification_email=settings.notification_email,
            )

            try:
                await notification_service.send_email(
                    subject=subject,
                    body=body,
                )
                return {"status": "success"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

    return run_async(_digest())


@celery_app.task
def send_follow_up_reminders(user_id: str):
    """Send reminders for emails needing follow-up."""

    async def _follow_up():
        from sqlalchemy import select

        from app.models.email import Email
        from app.models.email_account import EmailAccount
        from app.models.user_settings import UserSettings

        async with get_async_session() as db:
            # Get user settings
            settings_result = await db.execute(
                select(UserSettings).where(UserSettings.user_id == UUID(user_id))
            )
            settings = settings_result.scalar_one_or_none()

            follow_up_days = 3
            if settings and settings.follow_up_days:
                follow_up_days = settings.follow_up_days

            # Find emails needing follow-up
            cutoff = datetime.utcnow() - timedelta(days=follow_up_days)

            accounts_result = await db.execute(
                select(EmailAccount.id).where(EmailAccount.user_id == UUID(user_id))
            )
            account_ids = [row[0] for row in accounts_result.fetchall()]

            if not account_ids:
                return {"status": "skipped", "message": "No email accounts"}

            # Find emails marked as to_respond that are older than follow_up_days
            emails_result = await db.execute(
                select(Email)
                .where(
                    Email.account_id.in_(account_ids),
                    Email.category == "to_respond",
                    Email.received_at < cutoff,
                    Email.is_archived.is_(False),
                )
                .limit(10)
            )
            emails = emails_result.scalars().all()

            if emails:
                # Send notification
                send_notification.delay(
                    user_id,
                    "follow_up_reminder",
                    {
                        "count": len(emails),
                        "emails": [
                            {"subject": e.subject, "sender": e.sender}
                            for e in emails[:5]
                        ],
                    },
                )

            return {"status": "success", "emails_needing_followup": len(emails)}

    return run_async(_follow_up())
