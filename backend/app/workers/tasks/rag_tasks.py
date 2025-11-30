"""RAG and indexing Celery tasks."""

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


@celery_app.task(bind=True, max_retries=3)
def index_email(self, email_id: str, user_id: str):
    """Index an email in the knowledge graph."""
    async def _index():
        from sqlalchemy import select
        from app.models.email import Email
        from app.models.email_account import EmailAccount
        from app.services.rag_service import RAGService

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

                if email.indexed_at:
                    return {"status": "skipped", "message": "Already indexed"}

                # Index email
                rag_service = RAGService(db)
                success = await rag_service.index_email(email, UUID(user_id))
                await rag_service.close()

                if success:
                    return {
                        "status": "success",
                        "email_id": email_id,
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Indexing failed",
                    }

            except Exception as e:
                raise self.retry(exc=e, countdown=30)

    return run_async(_index())


@celery_app.task(bind=True, max_retries=3)
def index_document(self, document_id: str, user_id: str):
    """Index a document in the knowledge graph."""
    async def _index():
        from sqlalchemy import select
        from app.models.document import Document
        from app.services.rag_service import RAGService

        async with get_async_session() as db:
            try:
                # Get document
                result = await db.execute(
                    select(Document).where(
                        Document.id == UUID(document_id),
                        Document.user_id == UUID(user_id),
                    )
                )
                document = result.scalar_one_or_none()

                if not document:
                    return {"status": "error", "message": "Document not found"}

                if document.indexed_at:
                    return {"status": "skipped", "message": "Already indexed"}

                # Index document
                rag_service = RAGService(db)
                success = await rag_service.index_document(document, UUID(user_id))
                await rag_service.close()

                if success:
                    return {
                        "status": "success",
                        "document_id": document_id,
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Indexing failed",
                    }

            except Exception as e:
                raise self.retry(exc=e, countdown=30)

    return run_async(_index())


@celery_app.task(bind=True, max_retries=3)
def index_meeting(self, meeting_id: str, user_id: str):
    """Index a meeting in the knowledge graph."""
    async def _index():
        from sqlalchemy import select
        from app.models.meeting import Meeting
        from app.services.rag_service import RAGService

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

                if meeting.neo4j_node_id:
                    return {"status": "skipped", "message": "Already indexed"}

                # Index meeting
                rag_service = RAGService(db)
                success = await rag_service.index_meeting(meeting, UUID(user_id))
                await rag_service.close()

                if success:
                    return {
                        "status": "success",
                        "meeting_id": meeting_id,
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Indexing failed",
                    }

            except Exception as e:
                raise self.retry(exc=e, countdown=30)

    return run_async(_index())


@celery_app.task
def reindex_all(user_id: str):
    """Reindex all content for a user."""
    async def _reindex():
        from sqlalchemy import select
        from app.models.email import Email
        from app.models.email_account import EmailAccount
        from app.models.document import Document
        from app.models.meeting import Meeting

        async with get_async_session() as db:
            queued = {"emails": 0, "documents": 0, "meetings": 0}

            # Queue emails
            accounts_result = await db.execute(
                select(EmailAccount.id).where(EmailAccount.user_id == UUID(user_id))
            )
            account_ids = [row[0] for row in accounts_result.fetchall()]

            if account_ids:
                emails_result = await db.execute(
                    select(Email.id).where(Email.account_id.in_(account_ids))
                )
                for row in emails_result.fetchall():
                    index_email.delay(str(row[0]), user_id)
                    queued["emails"] += 1

            # Queue documents
            docs_result = await db.execute(
                select(Document.id).where(Document.user_id == UUID(user_id))
            )
            for row in docs_result.fetchall():
                index_document.delay(str(row[0]), user_id)
                queued["documents"] += 1

            # Queue meetings
            meetings_result = await db.execute(
                select(Meeting.id).where(Meeting.user_id == UUID(user_id))
            )
            for row in meetings_result.fetchall():
                index_meeting.delay(str(row[0]), user_id)
                queued["meetings"] += 1

            return queued

    return run_async(_reindex())


@celery_app.task
def extract_document_content(document_id: str, user_id: str):
    """Extract text content from a document."""
    async def _extract():
        from sqlalchemy import select
        from app.models.document import Document
        import os

        async with get_async_session() as db:
            # Get document
            result = await db.execute(
                select(Document).where(
                    Document.id == UUID(document_id),
                    Document.user_id == UUID(user_id),
                )
            )
            document = result.scalar_one_or_none()

            if not document:
                return {"status": "error", "message": "Document not found"}

            if not document.file_path or not os.path.exists(document.file_path):
                return {"status": "error", "message": "File not found"}

            content_text = None

            # Extract based on file type
            if document.file_type == "pdf":
                try:
                    import pypdf
                    with open(document.file_path, "rb") as f:
                        reader = pypdf.PdfReader(f)
                        content_text = ""
                        for page in reader.pages:
                            content_text += page.extract_text() + "\n"
                        document.page_count = len(reader.pages)
                except Exception as e:
                    return {"status": "error", "message": f"PDF extraction failed: {e}"}

            elif document.file_type == "docx":
                try:
                    from docx import Document as DocxDocument
                    doc = DocxDocument(document.file_path)
                    content_text = "\n".join([p.text for p in doc.paragraphs])
                except Exception as e:
                    return {"status": "error", "message": f"DOCX extraction failed: {e}"}

            elif document.file_type == "txt":
                try:
                    with open(document.file_path, "r", encoding="utf-8") as f:
                        content_text = f.read()
                except Exception as e:
                    return {"status": "error", "message": f"TXT extraction failed: {e}"}

            if content_text:
                document.content_text = content_text
                document.word_count = len(content_text.split())

                # Generate summary using LLM
                from app.services.llm_service import LLMService
                llm_service = LLMService()

                try:
                    summary = await llm_service.generate(
                        prompt=f"Summarize this document in 2-3 sentences:\n\n{content_text[:3000]}",
                        max_tokens=200,
                    )
                    document.content_summary = summary
                except Exception:
                    pass

                await db.commit()

                # Trigger indexing
                index_document.delay(document_id, user_id)

                return {
                    "status": "success",
                    "document_id": document_id,
                    "word_count": document.word_count,
                }

            return {"status": "error", "message": "No content extracted"}

    return run_async(_extract())
