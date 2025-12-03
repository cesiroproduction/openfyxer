"""Email-related Celery tasks."""

import asyncio
from datetime import datetime, timedelta
from uuid import UUID

from app.workers.celery_app import celery_app
from app.workers.tasks.rag_tasks import index_email


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


@celery_app.task(bind=True, max_retries=3)
def sync_email_account(self, account_id: str, user_id: str, max_emails: int = 100):
    """Sync emails for a specific account."""

    async def _sync():
        from sqlalchemy import select

        from app.models.audit_log import AuditLog
        from app.models.email_account import EmailAccount
        from app.services.email_service import EmailService

        async with get_async_session() as db:
            try:
                # Get account
                result = await db.execute(
                    select(EmailAccount).where(
                        EmailAccount.id == UUID(account_id),
                        EmailAccount.user_id == UUID(user_id),
                    )
                )
                account = result.scalar_one_or_none()

                if not account:
                    return {"status": "error", "message": "Account not found"}

                if not account.is_active or not account.sync_enabled:
                    return {"status": "skipped", "message": "Account sync disabled"}

                # Sync emails
                email_service = EmailService(db)
                emails = await email_service.sync_emails(account, max_emails)

                # Create audit log
                audit_log = AuditLog(
                    user_id=UUID(user_id),
                    action="email_sync",
                    entity_type="email_account",
                    entity_id=UUID(account_id),
                    details={"synced_count": len(emails)},
                    status="success",
                )
                db.add(audit_log)
                await db.commit()

                # Trigger classification and indexing for new emails
                for email in emails:
                    classify_email.delay(str(email.id), user_id)
                    index_email.delay(str(email.id), user_id)

                return {
                    "status": "success",
                    "synced_count": len(emails),
                    "account_id": account_id,
                }

            except Exception as e:
                # Log error
                audit_log = AuditLog(
                    user_id=UUID(user_id),
                    action="email_sync",
                    entity_type="email_account",
                    entity_id=UUID(account_id),
                    status="error",
                    error_message=str(e),
                )
                db.add(audit_log)
                await db.commit()

                raise self.retry(exc=e, countdown=60)

    return run_async(_sync())


@celery_app.task
def sync_all_accounts():
    """Sync all active email accounts."""

    async def _sync_all():
        from sqlalchemy import select

        from app.models.email_account import EmailAccount

        async with get_async_session() as db:
            result = await db.execute(
                select(EmailAccount).where(
                    EmailAccount.is_active,
                    EmailAccount.sync_enabled,
                )
            )
            accounts = result.scalars().all()

            for account in accounts:
                sync_email_account.delay(
                    str(account.id),
                    str(account.user_id),
                )

            return {"queued_accounts": len(accounts)}

    return run_async(_sync_all())


@celery_app.task
def sync_all_calendars():
    """Sync all calendars."""

    async def _sync_calendars():
        from sqlalchemy import select

        from app.models.user import User

        async with get_async_session() as db:
            result = await db.execute(select(User).where(User.is_active))
            users = result.scalars().all()

            # TODO: Implement calendar sync for each user
            return {"queued_users": len(users)}

    return run_async(_sync_calendars())


@celery_app.task(bind=True, max_retries=3)
def classify_email(self, email_id: str, user_id: str):
    """Classify an email using AI."""

    async def _classify():
        from sqlalchemy import select

        from app.models.email import Email
        from app.models.email_account import EmailAccount
        from app.services.llm_service import LLMService

        async with get_async_session() as db:
            try:
                # Get email
                accounts_result = await db.execute(
                    select(EmailAccount.id).where(EmailAccount.user_id == UUID(user_id))
                )
                account_ids = [row[0] for row in accounts_result.fetchall()]

                result = await db.execute(
                    select(Email).where(
                        Email.id == UUID(email_id),
                        Email.account_id.in_(account_ids),
                    )
                )
                email = result.scalar_one_or_none()

                if not email:
                    return {"status": "error", "message": "Email not found"}

                # Classify using LLM
                llm_service = LLMService()
                classification = await llm_service.classify_email(
                    subject=email.subject or "",
                    body=email.body_text or "",
                    sender=email.sender or "",
                )

                # Update email
                email.category = classification.get("category", "fyi")
                email.language = classification.get("language", "en")
                email.sentiment = classification.get("sentiment", "neutral")
                email.priority_score = classification.get("priority_score", 0.5)
                email.processed_at = datetime.utcnow()

                await db.commit()

                # Generate draft if needed
                if email.category in ["urgent", "to_respond"]:
                    generate_draft.delay(email_id, user_id)

                return {
                    "status": "success",
                    "email_id": email_id,
                    "category": email.category,
                }

            except Exception as e:
                raise self.retry(exc=e, countdown=30)

    return run_async(_classify())


@celery_app.task(bind=True, max_retries=3)
def generate_draft(self, email_id: str, user_id: str, tone: str = "professional"):
    """Generate a draft response for an email."""

    async def _generate():
        import time

        from sqlalchemy import select

        from app.models.draft import Draft
        from app.models.email import Email
        from app.models.email_account import EmailAccount
        from app.models.user_settings import UserSettings
        from app.services.llm_service import LLMService

        async with get_async_session() as db:
            try:
                # Get email
                accounts_result = await db.execute(
                    select(EmailAccount.id).where(EmailAccount.user_id == UUID(user_id))
                )
                account_ids = [row[0] for row in accounts_result.fetchall()]

                result = await db.execute(
                    select(Email).where(
                        Email.id == UUID(email_id),
                        Email.account_id.in_(account_ids),
                    )
                )
                email = result.scalar_one_or_none()

                if not email:
                    return {"status": "error", "message": "Email not found"}

                # Check if draft already exists
                existing = await db.execute(
                    select(Draft).where(
                        Draft.email_id == UUID(email_id),
                        Draft.user_id == UUID(user_id),
                        Draft.status == "pending",
                    )
                )
                if existing.scalar_one_or_none():
                    return {"status": "skipped", "message": "Draft already exists"}

                # Get user settings for style
                settings_result = await db.execute(
                    select(UserSettings).where(UserSettings.user_id == UUID(user_id))
                )
                user_settings = settings_result.scalar_one_or_none()

                user_style = None
                if user_settings and user_settings.learned_style_profile:
                    user_style = user_settings.learned_style_profile

                # Generate draft
                start_time = time.time()
                llm_service = LLMService()
                content = await llm_service.generate_email_draft(
                    original_email={
                        "sender": email.sender,
                        "subject": email.subject,
                        "body": email.body_text,
                    },
                    user_style=user_style,
                    tone=tone,
                    language=email.language or "en",
                )
                generation_time = int((time.time() - start_time) * 1000)

                # Create draft
                draft = Draft(
                    email_id=UUID(email_id),
                    user_id=UUID(user_id),
                    subject=f"Re: {email.subject}" if email.subject else "Re:",
                    content=content,
                    original_content=content,
                    status="pending",
                    llm_provider="local",
                    llm_model="default",
                    generation_time_ms=generation_time,
                    language=email.language or "en",
                    tone=tone,
                )
                db.add(draft)
                await db.commit()

                # Send notification
                from app.workers.tasks.notification_tasks import send_notification

                send_notification.delay(
                    user_id,
                    "draft_ready",
                    {
                        "email_subject": email.subject,
                        "draft_preview": content[:200],
                    },
                )

                return {
                    "status": "success",
                    "draft_id": str(draft.id),
                    "generation_time_ms": generation_time,
                }

            except Exception as e:
                raise self.retry(exc=e, countdown=30)

    return run_async(_generate())


@celery_app.task(bind=True, max_retries=3)
def send_draft(self, draft_id: str, user_id: str):
    """Send a draft as email."""

    async def _send():
        from sqlalchemy import select

        from app.models.draft import Draft
        from app.models.email import Email
        from app.models.email_account import EmailAccount
        from app.services.email_service import EmailService

        async with get_async_session() as db:
            try:
                # Get draft
                result = await db.execute(
                    select(Draft).where(
                        Draft.id == UUID(draft_id),
                        Draft.user_id == UUID(user_id),
                    )
                )
                draft = result.scalar_one_or_none()

                if not draft:
                    return {"status": "error", "message": "Draft not found"}

                if draft.status == "sent":
                    return {"status": "skipped", "message": "Draft already sent"}

                # Get original email
                email_result = await db.execute(
                    select(Email).where(Email.id == draft.email_id)
                )
                email = email_result.scalar_one_or_none()

                if not email:
                    return {"status": "error", "message": "Original email not found"}

                # Get email account
                account_result = await db.execute(
                    select(EmailAccount).where(EmailAccount.id == email.account_id)
                )
                account = account_result.scalar_one_or_none()

                if not account:
                    return {"status": "error", "message": "Email account not found"}

                # Send email
                email_service = EmailService(db)
                await email_service.send_email(
                    account=account,
                    to=[email.sender],
                    subject=draft.subject,
                    body=draft.content,
                )

                # Update draft status
                draft.status = "sent"
                draft.sent_at = datetime.utcnow()
                await db.commit()

                return {
                    "status": "success",
                    "draft_id": draft_id,
                }

            except Exception as e:
                raise self.retry(exc=e, countdown=60)

    return run_async(_send())


@celery_app.task
def cleanup_old_audit_logs():
    """Clean up audit logs older than 90 days."""

    async def _cleanup():
        from sqlalchemy import delete

        from app.models.audit_log import AuditLog

        async with get_async_session() as db:
            cutoff = datetime.utcnow() - timedelta(days=90)

            result = await db.execute(
                delete(AuditLog).where(AuditLog.created_at < cutoff)
            )
            await db.commit()

            return {"deleted_count": result.rowcount}

    return run_async(_cleanup())
