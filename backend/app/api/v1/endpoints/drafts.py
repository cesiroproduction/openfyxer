"""Draft endpoints."""

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_pagination, Pagination
from app.db.session import get_db
from app.models.draft import Draft
from app.models.email import Email
from app.models.email_account import EmailAccount
from app.models.user import User
from app.schemas.draft import (
    DraftCreate,
    DraftListResponse,
    DraftRegenerate,
    DraftResponse,
    DraftSend,
    DraftUpdate,
)

router = APIRouter()


@router.get("", response_model=DraftListResponse)
async def list_drafts(
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(pending|approved|sent|rejected)$"),
    pagination: Pagination = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all drafts for current user."""
    query = select(Draft).where(Draft.user_id == current_user.id)
    count_query = select(func.count(Draft.id)).where(Draft.user_id == current_user.id)
    
    if status_filter:
        query = query.where(Draft.status == status_filter)
        count_query = count_query.where(Draft.status == status_filter)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get paginated results
    query = query.order_by(Draft.created_at.desc())
    query = query.offset(pagination.offset).limit(pagination.limit)
    
    result = await db.execute(query)
    drafts = result.scalars().all()
    
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return DraftListResponse(
        items=drafts,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=DraftResponse, status_code=status.HTTP_201_CREATED)
async def create_draft(
    draft_in: DraftCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new draft (AI-generated or manual)."""
    # Verify email exists and belongs to user
    accounts_result = await db.execute(
        select(EmailAccount.id).where(EmailAccount.user_id == current_user.id)
    )
    account_ids = [row[0] for row in accounts_result.fetchall()]
    
    email_result = await db.execute(
        select(Email).where(
            Email.id == draft_in.email_id,
            Email.account_id.in_(account_ids),
        )
    )
    email = email_result.scalar_one_or_none()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found",
        )
    
    # Check if draft already exists for this email
    existing_result = await db.execute(
        select(Draft).where(
            Draft.email_id == draft_in.email_id,
            Draft.user_id == current_user.id,
            Draft.status == "pending",
        )
    )
    existing_draft = existing_result.scalar_one_or_none()
    
    if existing_draft:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A pending draft already exists for this email",
        )
    
    # Generate draft content if not provided
    content = draft_in.content
    llm_provider = None
    llm_model = None
    generation_time_ms = None
    
    if not content:
        # TODO: Call LLM service to generate draft
        # For now, create a placeholder
        content = f"[AI-generated response to: {email.subject or 'No Subject'}]"
        llm_provider = "placeholder"
        llm_model = "placeholder"
        generation_time_ms = 0
    
    # Detect language from email or use specified
    language = draft_in.language or email.language or "en"
    
    draft = Draft(
        email_id=draft_in.email_id,
        user_id=current_user.id,
        subject=f"Re: {email.subject}" if email.subject else "Re:",
        content=content,
        original_content=content,
        status="pending",
        llm_provider=llm_provider,
        llm_model=llm_model,
        generation_time_ms=generation_time_ms,
        language=language,
        tone=draft_in.tone or "professional",
    )
    
    db.add(draft)
    await db.commit()
    await db.refresh(draft)
    
    return draft


@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft(
    draft_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get draft by ID."""
    result = await db.execute(
        select(Draft).where(
            Draft.id == draft_id,
            Draft.user_id == current_user.id,
        )
    )
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )
    
    return draft


@router.put("/{draft_id}", response_model=DraftResponse)
async def update_draft(
    draft_id: uuid.UUID,
    draft_in: DraftUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update draft content."""
    result = await db.execute(
        select(Draft).where(
            Draft.id == draft_id,
            Draft.user_id == current_user.id,
        )
    )
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )
    
    if draft.status == "sent":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a sent draft",
        )
    
    update_data = draft_in.model_dump(exclude_unset=True)
    
    if update_data:
        draft.edited_by_user = True
        for field, value in update_data.items():
            setattr(draft, field, value)
    
    await db.commit()
    await db.refresh(draft)
    
    return draft


@router.delete("/{draft_id}")
async def delete_draft(
    draft_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Delete a draft."""
    result = await db.execute(
        select(Draft).where(
            Draft.id == draft_id,
            Draft.user_id == current_user.id,
        )
    )
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )
    
    await db.delete(draft)
    await db.commit()
    
    return {"message": "Draft deleted successfully"}


@router.post("/{draft_id}/approve", response_model=DraftResponse)
async def approve_draft(
    draft_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Approve a draft for sending."""
    result = await db.execute(
        select(Draft).where(
            Draft.id == draft_id,
            Draft.user_id == current_user.id,
        )
    )
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )
    
    if draft.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve draft with status: {draft.status}",
        )
    
    draft.status = "approved"
    await db.commit()
    await db.refresh(draft)
    
    return draft


@router.post("/{draft_id}/reject", response_model=DraftResponse)
async def reject_draft(
    draft_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Reject a draft."""
    result = await db.execute(
        select(Draft).where(
            Draft.id == draft_id,
            Draft.user_id == current_user.id,
        )
    )
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )
    
    if draft.status == "sent":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reject a sent draft",
        )
    
    draft.status = "rejected"
    await db.commit()
    await db.refresh(draft)
    
    return draft


@router.post("/{draft_id}/send")
async def send_draft(
    draft_id: uuid.UUID,
    send_in: Optional[DraftSend] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Send a draft as email."""
    result = await db.execute(
        select(Draft).where(
            Draft.id == draft_id,
            Draft.user_id == current_user.id,
        )
    )
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )
    
    if draft.status == "sent":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Draft already sent",
        )
    
    # Apply overrides if provided
    if send_in:
        if send_in.subject:
            draft.subject = send_in.subject
        if send_in.content:
            draft.content = send_in.content
            draft.edited_by_user = True
    
    # TODO: Actually send the email via email service
    # For now, just mark as sent
    
    draft.status = "sent"
    draft.sent_at = datetime.utcnow()
    await db.commit()
    await db.refresh(draft)
    
    return {"message": "Draft sent successfully", "draft_id": str(draft_id)}


@router.post("/{draft_id}/regenerate", response_model=DraftResponse)
async def regenerate_draft(
    draft_id: uuid.UUID,
    regen_in: Optional[DraftRegenerate] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Regenerate draft content using AI."""
    result = await db.execute(
        select(Draft).where(
            Draft.id == draft_id,
            Draft.user_id == current_user.id,
        )
    )
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )
    
    if draft.status == "sent":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot regenerate a sent draft",
        )
    
    # Get the original email
    email_result = await db.execute(select(Email).where(Email.id == draft.email_id))
    email = email_result.scalar_one_or_none()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original email not found",
        )
    
    # TODO: Call LLM service to regenerate draft with new parameters
    # For now, create a placeholder
    new_content = f"[Regenerated AI response to: {email.subject or 'No Subject'}]"
    if regen_in and regen_in.instructions:
        new_content += f"\n[Instructions: {regen_in.instructions}]"
    
    draft.content = new_content
    draft.original_content = new_content
    draft.edited_by_user = False
    draft.status = "pending"
    
    if regen_in:
        if regen_in.tone:
            draft.tone = regen_in.tone
        if regen_in.language:
            draft.language = regen_in.language
    
    await db.commit()
    await db.refresh(draft)
    
    return draft
