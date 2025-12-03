"""RAG and Knowledge Base endpoints."""

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Pagination, get_current_user, get_pagination
from app.db.session import get_db
from app.models.document import Document
from app.models.email import Email
from app.models.email_account import EmailAccount
from app.models.meeting import Meeting
from app.models.user import User
from app.schemas.rag import (
    DocumentContent,
    DocumentListResponse,
    DocumentResponse,
    GraphQueryResponse,
    IndexingStatus,
    RAGQuery,
    RAGResponse,
    RAGSource,
)

router = APIRouter()


@router.post("/query", response_model=RAGResponse)
async def query_knowledge_base(
    query_in: RAGQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Query the knowledge base using RAG."""
    import time

    start_time = time.time()

    # TODO: Implement actual RAG query using LlamaIndex + Neo4j
    # For now, return a placeholder response

    sources = []

    # Search emails if included
    if query_in.include_emails:
        accounts_result = await db.execute(
            select(EmailAccount.id).where(EmailAccount.user_id == current_user.id)
        )
        account_ids = [row[0] for row in accounts_result.fetchall()]

        if account_ids:
            email_query = (
                select(Email)
                .where(
                    Email.account_id.in_(account_ids),
                    Email.body_text.ilike(f"%{query_in.query}%"),
                )
                .limit(query_in.max_results)
            )

            if query_in.date_from:
                email_query = email_query.where(Email.received_at >= query_in.date_from)
            if query_in.date_to:
                email_query = email_query.where(Email.received_at <= query_in.date_to)

            emails_result = await db.execute(email_query)
            emails = emails_result.scalars().all()

            for email in emails:
                sources.append(
                    RAGSource(
                        type="email",
                        id=email.id,
                        title=email.subject or "No Subject",
                        snippet=(email.snippet or email.body_text[:200] if email.body_text else ""),
                        relevance_score=0.8,
                        date=email.received_at,
                    )
                )

    # Search documents if included
    if query_in.include_documents:
        doc_query = (
            select(Document)
            .where(
                Document.user_id == current_user.id,
                Document.content_text.ilike(f"%{query_in.query}%"),
            )
            .limit(query_in.max_results)
        )

        if query_in.date_from:
            doc_query = doc_query.where(Document.created_at >= query_in.date_from)
        if query_in.date_to:
            doc_query = doc_query.where(Document.created_at <= query_in.date_to)

        docs_result = await db.execute(doc_query)
        docs = docs_result.scalars().all()

        for doc in docs:
            sources.append(
                RAGSource(
                    type="document",
                    id=doc.id,
                    title=doc.filename,
                    snippet=(
                        doc.content_summary or doc.content_text[:200] if doc.content_text else ""
                    ),
                    relevance_score=0.75,
                    date=doc.created_at,
                )
            )

    # Search meetings if included
    if query_in.include_meetings:
        meeting_query = (
            select(Meeting)
            .where(
                Meeting.user_id == current_user.id,
                Meeting.transcript.ilike(f"%{query_in.query}%"),
            )
            .limit(query_in.max_results)
        )

        if query_in.date_from:
            meeting_query = meeting_query.where(Meeting.meeting_date >= query_in.date_from)
        if query_in.date_to:
            meeting_query = meeting_query.where(Meeting.meeting_date <= query_in.date_to)

        meetings_result = await db.execute(meeting_query)
        meetings = meetings_result.scalars().all()

        for meeting in meetings:
            sources.append(
                RAGSource(
                    type="meeting",
                    id=meeting.id,
                    title=meeting.title,
                    snippet=(
                        meeting.summary or meeting.transcript[:200] if meeting.transcript else ""
                    ),
                    relevance_score=0.7,
                    date=meeting.meeting_date,
                )
            )

    # Sort sources by relevance
    sources.sort(key=lambda x: x.relevance_score, reverse=True)
    sources = sources[: query_in.max_results]

    # Generate answer (placeholder - would use LLM in production)
    if sources:
        answer = f"Based on {len(sources)} sources found in your knowledge base, here's what I found about '{query_in.query}':\n\n"
        for i, source in enumerate(sources[:3], 1):
            answer += f"{i}. From {source.type} '{source.title}': {source.snippet[:100]}...\n"
    else:
        answer = f"I couldn't find any relevant information about '{query_in.query}' in your knowledge base."

    query_time_ms = int((time.time() - start_time) * 1000)

    return RAGResponse(
        answer=answer,
        sources=sources,
        confidence=0.8 if sources else 0.2,
        query_time_ms=query_time_ms,
        llm_provider="placeholder",
        llm_model="placeholder",
    )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    source: Optional[str] = Query(None, pattern="^(upload|email_attachment|url)$"),
    file_type: Optional[str] = None,
    search: Optional[str] = None,
    pagination: Pagination = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all documents in knowledge base."""
    query = select(Document).where(Document.user_id == current_user.id)
    count_query = select(func.count(Document.id)).where(Document.user_id == current_user.id)

    if source:
        query = query.where(Document.source == source)
        count_query = count_query.where(Document.source == source)

    if file_type:
        query = query.where(Document.file_type == file_type)
        count_query = count_query.where(Document.file_type == file_type)

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (Document.filename.ilike(search_filter)) | (Document.content_text.ilike(search_filter))
        )
        count_query = count_query.where(
            (Document.filename.ilike(search_filter)) | (Document.content_text.ilike(search_filter))
        )

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.order_by(Document.created_at.desc())
    query = query.offset(pagination.offset).limit(pagination.limit)

    result = await db.execute(query)
    documents = result.scalars().all()

    total_pages = (total + pagination.page_size - 1) // pagination.page_size

    return DocumentListResponse(
        items=documents,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Upload a document to the knowledge base."""
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not allowed. Allowed types: PDF, DOCX, TXT",
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Determine file type
    file_type = "unknown"
    if file.content_type == "application/pdf":
        file_type = "pdf"
    elif (
        file.content_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        file_type = "docx"
    elif file.content_type == "text/plain":
        file_type = "txt"

    # Generate unique filename
    import hashlib

    file_hash = hashlib.md5(content).hexdigest()[:8]
    stored_filename = f"{current_user.id}_{file_hash}_{file.filename}"

    # TODO: Save file to storage (local or S3)
    file_path = f"/data/documents/{stored_filename}"

    # TODO: Extract text content from document
    content_text = None
    if file_type == "txt":
        content_text = content.decode("utf-8", errors="ignore")
    # For PDF and DOCX, would use pypdf and python-docx

    # Create document record
    document = Document(
        user_id=current_user.id,
        filename=stored_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_type=file_type,
        mime_type=file.content_type,
        file_size=file_size,
        content_text=content_text,
        source="upload",
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    # TODO: Trigger async indexing task

    return document


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get document by ID."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.get("/documents/{document_id}/content", response_model=DocumentContent)
async def get_document_content(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get document content."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return DocumentContent(
        id=document.id,
        filename=document.filename,
        content_text=document.content_text,
        content_summary=document.content_summary,
    )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Delete document from knowledge base."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # TODO: Delete file from storage
    # TODO: Remove from Neo4j index

    await db.delete(document)
    await db.commit()

    return {"message": "Document deleted successfully"}


@router.post("/documents/{document_id}/reindex")
async def reindex_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Reindex a document in the knowledge base."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # TODO: Trigger reindexing task

    return {"message": "Document reindexing started", "document_id": str(document_id)}


@router.get("/status", response_model=IndexingStatus)
async def get_indexing_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get knowledge base indexing status."""
    # Get email counts
    accounts_result = await db.execute(
        select(EmailAccount.id).where(EmailAccount.user_id == current_user.id)
    )
    account_ids = [row[0] for row in accounts_result.fetchall()]

    total_emails = 0
    indexed_emails = 0

    if account_ids:
        total_result = await db.execute(
            select(func.count(Email.id)).where(Email.account_id.in_(account_ids))
        )
        total_emails = total_result.scalar() or 0

        indexed_result = await db.execute(
            select(func.count(Email.id)).where(
                Email.account_id.in_(account_ids),
                Email.indexed_at.isnot(None),
            )
        )
        indexed_emails = indexed_result.scalar() or 0

    # Get document counts
    total_docs_result = await db.execute(
        select(func.count(Document.id)).where(Document.user_id == current_user.id)
    )
    total_documents = total_docs_result.scalar() or 0

    indexed_docs_result = await db.execute(
        select(func.count(Document.id)).where(
            Document.user_id == current_user.id,
            Document.indexed_at.isnot(None),
        )
    )
    indexed_documents = indexed_docs_result.scalar() or 0

    # Get meeting counts
    total_meetings_result = await db.execute(
        select(func.count(Meeting.id)).where(Meeting.user_id == current_user.id)
    )
    total_meetings = total_meetings_result.scalar() or 0

    indexed_meetings_result = await db.execute(
        select(func.count(Meeting.id)).where(
            Meeting.user_id == current_user.id,
            Meeting.neo4j_node_id.isnot(None),
        )
    )
    indexed_meetings = indexed_meetings_result.scalar() or 0

    # Get last index time
    last_index_result = await db.execute(
        select(func.max(Document.indexed_at)).where(Document.user_id == current_user.id)
    )
    last_index_time = last_index_result.scalar()

    return IndexingStatus(
        total_emails=total_emails,
        indexed_emails=indexed_emails,
        total_documents=total_documents,
        indexed_documents=indexed_documents,
        total_meetings=total_meetings,
        indexed_meetings=indexed_meetings,
        last_index_time=last_index_time,
        is_indexing=False,  # TODO: Check actual indexing status
    )


@router.post("/reindex-all")
async def reindex_all(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Trigger full reindexing of knowledge base."""
    # TODO: Trigger Celery task for full reindexing

    return {"message": "Full reindexing started"}


@router.get("/graph", response_model=GraphQueryResponse)
async def query_knowledge_graph(
    node_type: Optional[str] = Query(
        None, pattern="^(Person|Company|Project|Email|Document|Meeting|Topic)$"
    ),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Query the knowledge graph."""
    # TODO: Implement Neo4j graph query

    return GraphQueryResponse(
        nodes=[],
        relationships=[],
    )
