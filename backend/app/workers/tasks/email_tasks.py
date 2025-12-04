"""Email-related Celery tasks."""

import asyncio
from datetime import datetime
from uuid import UUID
from app.workers.celery_app import celery_app
from app.workers.tasks.rag_tasks import index_email

# --- HARDCODED CONFIGURATION ---
FORCE_PROVIDER = "openai"
FORCE_MODEL = "gpt-3.5-turbo"
FORCE_API_KEY = "YOUR API_KEY"

def get_async_session():
    from app.db.session import async_session_maker
    return async_session_maker()

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# Keep sync_email_account and sync_all_accounts and classify_email as they were
# ... (omitted for brevity, assume standard implementation or paste from previous if needed) ...
# Let's focus on generate_draft which is the one needing update

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
                # Get email logic...
                accounts_result = await db.execute(select(EmailAccount.id).where(EmailAccount.user_id == UUID(user_id)))
                account_ids = [row[0] for row in accounts_result.fetchall()]
                result = await db.execute(select(Email).where(Email.id == UUID(email_id), Email.account_id.in_(account_ids)))
                email = result.scalar_one_or_none()
                
                if not email: return {"status": "error"}

                # Check existing...
                existing = await db.execute(select(Draft).where(Draft.email_id == UUID(email_id), Draft.status == "pending"))
                if existing.scalar_one_or_none(): return {"status": "skipped"}

                # --- GET USER SETTINGS & SIGNATURE ---
                settings_result = await db.execute(select(UserSettings).where(UserSettings.user_id == UUID(user_id)))
                user_settings = settings_result.scalar_one_or_none()

                user_style = {}
                if user_settings:
                    if user_settings.learned_style_profile:
                        user_style = user_settings.learned_style_profile
                    # THIS IS THE FIX: Explicitly add signature to style dict
                    if user_settings.email_signature:
                        user_style["signature"] = user_settings.email_signature
                # -------------------------------------

                start_time = time.time()
                llm_service = LLMService(provider=FORCE_PROVIDER, api_key=FORCE_API_KEY, model=FORCE_MODEL)
                
                content = await llm_service.generate_email_draft(
                    original_email={
                        "sender": email.sender,
                        "subject": email.subject,
                        "body": email.body_text,
                    },
                    user_style=user_style, # Now contains signature
                    tone=tone,
                    language=email.language or "en",
                )
                generation_time = int((time.time() - start_time) * 1000)

                draft = Draft(
                    email_id=UUID(email_id),
                    user_id=UUID(user_id),
                    subject=f"Re: {email.subject}",
                    content=content,
                    original_content=content,
                    status="pending",
                    llm_provider=FORCE_PROVIDER,
                    llm_model=FORCE_MODEL,
                    generation_time_ms=generation_time,
                    language=email.language or "en",
                    tone=tone,
                )
                db.add(draft)
                await db.commit()

                from app.workers.tasks.notification_tasks import send_notification
                send_notification.delay(user_id, "draft_ready", {"email_subject": email.subject})

                return {"status": "success", "draft_id": str(draft.id)}

            except Exception as e:
                print(f"Draft error: {e}")
                raise self.retry(exc=e, countdown=30)

    return run_async(_generate())

# ... (include other tasks like send_draft, etc if needed) ...
