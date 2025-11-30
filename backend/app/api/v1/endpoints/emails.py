"""Email endpoints."""

import uuid
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_pagination, Pagination
from app.db.session import get_db
from app.models.email import Email
from app.models.email_account import EmailAccount
from app.models.user import User
from app.schemas.email import (
    EmailAccountCreate,
    EmailAccountResponse,
    EmailAccountUpdate,
    EmailCategoryUpdate,
    EmailListResponse,
    EmailResponse,
)

router = APIRouter()


# Email Account endpoints
@router.get("/accounts", response_model=List[EmailAccountResponse])
async def list_email_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all email accounts for current user."""
    result = await db.execute(
        select(EmailAccount)
        .where(EmailAccount.user_id == current_user.id)
        .order_by(EmailAccount.created_at.desc())
    )
    accounts = result.scalars().all()
    return accounts


@router.post("/accounts", response_model=EmailAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_email_account(
    account_in: EmailAccountCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new email account connection."""
    # Check if account already exists
    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.user_id == current_user.id,
            EmailAccount.email_address == account_in.email_address,
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email account already connected",
        )
    
    # Create account
    account = EmailAccount(
        user_id=current_user.id,
        provider=account_in.provider,
        email_address=account_in.email_address,
        display_name=account_in.display_name,
        imap_host=account_in.imap_host,
        imap_port=account_in.imap_port,
        smtp_host=account_in.smtp_host,
        smtp_port=account_in.smtp_port,
    )
    
    # Encrypt IMAP password if provided
    if account_in.imap_password:
        from app.core.encryption import encrypt_value
        account.imap_password = encrypt_value(account_in.imap_password)
    
    db.add(account)
    await db.commit()
    await db.refresh(account)
    
    return account


@router.get("/accounts/{account_id}", response_model=EmailAccountResponse)
async def get_email_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get email account by ID."""
    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.id == account_id,
            EmailAccount.user_id == current_user.id,
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email account not found",
        )
    
    return account


@router.put("/accounts/{account_id}", response_model=EmailAccountResponse)
async def update_email_account(
    account_id: uuid.UUID,
    account_in: EmailAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update email account."""
    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.id == account_id,
            EmailAccount.user_id == current_user.id,
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email account not found",
        )
    
    update_data = account_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)
    
    await db.commit()
    await db.refresh(account)
    
    return account


@router.delete("/accounts/{account_id}")
async def delete_email_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Delete email account."""
    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.id == account_id,
            EmailAccount.user_id == current_user.id,
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email account not found",
        )
    
    await db.delete(account)
    await db.commit()
    
    return {"message": "Email account deleted successfully"}


@router.post("/accounts/{account_id}/sync")
async def sync_email_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Trigger email sync for account."""
    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.id == account_id,
            EmailAccount.user_id == current_user.id,
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email account not found",
        )
    
    # TODO: Trigger Celery task for email sync
    # from app.workers.tasks import sync_emails
    # sync_emails.delay(str(account_id))
    
    return {"message": "Email sync started", "account_id": str(account_id)}


@router.get("/accounts/{account_id}/oauth/url")
async def get_oauth_url(
    account_id: uuid.UUID,
    provider: str = Query(..., pattern="^(gmail|outlook)$"),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get OAuth URL for email provider."""
    # TODO: Implement OAuth URL generation
    return {
        "url": f"https://oauth.example.com/{provider}/authorize",
        "provider": provider,
    }


@router.post("/accounts/{account_id}/oauth/callback")
async def oauth_callback(
    account_id: uuid.UUID,
    code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Handle OAuth callback and store tokens."""
    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.id == account_id,
            EmailAccount.user_id == current_user.id,
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email account not found",
        )
    
    # TODO: Exchange code for tokens and store encrypted
    
    return {"message": "OAuth tokens stored successfully"}


# Email endpoints
@router.get("", response_model=EmailListResponse)
async def list_emails(
    account_id: Optional[uuid.UUID] = None,
    category: Optional[str] = Query(None, pattern="^(urgent|to_respond|fyi|newsletter|spam|archived)$"),
    is_read: Optional[bool] = None,
    is_starred: Optional[bool] = None,
    search: Optional[str] = None,
    pagination: Pagination = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List emails with filters."""
    # Get user's account IDs
    accounts_result = await db.execute(
        select(EmailAccount.id).where(EmailAccount.user_id == current_user.id)
    )
    account_ids = [row[0] for row in accounts_result.fetchall()]
    
    if not account_ids:
        return EmailListResponse(
            items=[],
            total=0,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=0,
        )
    
    # Build query
    query = select(Email).where(Email.account_id.in_(account_ids))
    count_query = select(func.count(Email.id)).where(Email.account_id.in_(account_ids))
    
    if account_id:
        if account_id not in account_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this email account",
            )
        query = query.where(Email.account_id == account_id)
        count_query = count_query.where(Email.account_id == account_id)
    
    if category:
        query = query.where(Email.category == category)
        count_query = count_query.where(Email.category == category)
    
    if is_read is not None:
        query = query.where(Email.is_read == is_read)
        count_query = count_query.where(Email.is_read == is_read)
    
    if is_starred is not None:
        query = query.where(Email.is_starred == is_starred)
        count_query = count_query.where(Email.is_starred == is_starred)
    
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (Email.subject.ilike(search_filter)) |
            (Email.body_text.ilike(search_filter)) |
            (Email.sender.ilike(search_filter))
        )
        count_query = count_query.where(
            (Email.subject.ilike(search_filter)) |
            (Email.body_text.ilike(search_filter)) |
            (Email.sender.ilike(search_filter))
        )
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get paginated results
    query = query.order_by(Email.received_at.desc())
    query = query.offset(pagination.offset).limit(pagination.limit)
    
    result = await db.execute(query)
    emails = result.scalars().all()
    
    # Calculate total pages
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return EmailListResponse(
        items=emails,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.get("/{email_id}", response_model=EmailResponse)
async def get_email(
    email_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get email by ID."""
    # Get user's account IDs
    accounts_result = await db.execute(
        select(EmailAccount.id).where(EmailAccount.user_id == current_user.id)
    )
    account_ids = [row[0] for row in accounts_result.fetchall()]
    
    result = await db.execute(
        select(Email).where(
            Email.id == email_id,
            Email.account_id.in_(account_ids),
        )
    )
    email = result.scalar_one_or_none()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found",
        )
    
    return email


@router.put("/{email_id}/category")
async def update_email_category(
    email_id: uuid.UUID,
    category_in: EmailCategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update email category."""
    # Get user's account IDs
    accounts_result = await db.execute(
        select(EmailAccount.id).where(EmailAccount.user_id == current_user.id)
    )
    account_ids = [row[0] for row in accounts_result.fetchall()]
    
    result = await db.execute(
        select(Email).where(
            Email.id == email_id,
            Email.account_id.in_(account_ids),
        )
    )
    email = result.scalar_one_or_none()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found",
        )
    
    email.category = category_in.category
    await db.commit()
    
    return {"message": "Category updated", "category": category_in.category}


@router.put("/{email_id}/read")
async def mark_email_read(
    email_id: uuid.UUID,
    is_read: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Mark email as read/unread."""
    # Get user's account IDs
    accounts_result = await db.execute(
        select(EmailAccount.id).where(EmailAccount.user_id == current_user.id)
    )
    account_ids = [row[0] for row in accounts_result.fetchall()]
    
    result = await db.execute(
        select(Email).where(
            Email.id == email_id,
            Email.account_id.in_(account_ids),
        )
    )
    email = result.scalar_one_or_none()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found",
        )
    
    email.is_read = is_read
    await db.commit()
    
    return {"message": "Email marked as read" if is_read else "Email marked as unread"}


@router.put("/{email_id}/star")
async def star_email(
    email_id: uuid.UUID,
    is_starred: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Star/unstar email."""
    # Get user's account IDs
    accounts_result = await db.execute(
        select(EmailAccount.id).where(EmailAccount.user_id == current_user.id)
    )
    account_ids = [row[0] for row in accounts_result.fetchall()]
    
    result = await db.execute(
        select(Email).where(
            Email.id == email_id,
            Email.account_id.in_(account_ids),
        )
    )
    email = result.scalar_one_or_none()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found",
        )
    
    email.is_starred = is_starred
    await db.commit()
    
    return {"message": "Email starred" if is_starred else "Email unstarred"}


@router.put("/{email_id}/archive")
async def archive_email(
    email_id: uuid.UUID,
    is_archived: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Archive/unarchive email."""
    # Get user's account IDs
    accounts_result = await db.execute(
        select(EmailAccount.id).where(EmailAccount.user_id == current_user.id)
    )
    account_ids = [row[0] for row in accounts_result.fetchall()]
    
    result = await db.execute(
        select(Email).where(
            Email.id == email_id,
            Email.account_id.in_(account_ids),
        )
    )
    email = result.scalar_one_or_none()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found",
        )
    
    email.is_archived = is_archived
    await db.commit()
    
    return {"message": "Email archived" if is_archived else "Email unarchived"}
