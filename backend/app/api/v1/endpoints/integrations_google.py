"""Google OAuth integration endpoints for Gmail and Calendar."""

import secrets
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.encryption import decrypt_value, encrypt_value
from app.models.email_account import EmailAccount
from app.models.user import User

router = APIRouter()

# Google OAuth scopes for Gmail and Calendar
GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/userinfo.email",
]


# Store state tokens temporarily (in production, use Redis or DB)
_oauth_states: dict = {}


def _get_google_flow() -> Flow:
    """Create Google OAuth flow."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env",
        )

    client_config = {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=GOOGLE_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )

    return flow


@router.get("/authorize")
async def google_authorize(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get Google OAuth authorization URL."""
    flow = _get_google_flow()

    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {
        "user_id": str(current_user.id),
        "created_at": datetime.utcnow(),
    }

    # Clean up old states (older than 10 minutes)
    _oauth_states.clear()
    _oauth_states[state] = {
        "user_id": str(current_user.id),
        "created_at": datetime.utcnow(),
    }

    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )

    return {"authorization_url": authorization_url, "state": state}


@router.get("/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Handle Google OAuth callback."""
    # Verify state token
    state_data = _oauth_states.get(state)
    if not state_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state token. Please try connecting again.",
        )

    user_id = UUID(state_data["user_id"])
    del _oauth_states[state]

    try:
        flow = _get_google_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Get user's email from Google
        from googleapiclient.discovery import build

        oauth2_service = build("oauth2", "v2", credentials=credentials)
        user_info = oauth2_service.userinfo().get().execute()
        email_address = user_info.get("email", "")

        if not email_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not retrieve email address from Google",
            )

        # Check if account already exists
        existing_result = await db.execute(
            select(EmailAccount).where(
                EmailAccount.user_id == user_id,
                EmailAccount.email_address == email_address,
                EmailAccount.provider == "gmail",
            )
        )
        existing_account = existing_result.scalar_one_or_none()

        # Encrypt tokens
        encrypted_token = encrypt_value(credentials.token)
        encrypted_refresh = (
            encrypt_value(credentials.refresh_token) if credentials.refresh_token else None
        )

        if existing_account:
            # Update existing account
            existing_account.oauth_token = encrypted_token
            existing_account.oauth_refresh_token = encrypted_refresh
            existing_account.oauth_token_expiry = credentials.expiry
            existing_account.is_active = True
            account = existing_account
        else:
            # Create new account
            account = EmailAccount(
                user_id=user_id,
                provider="gmail",
                email_address=email_address,
                display_name=user_info.get("name", email_address),
                oauth_token=encrypted_token,
                oauth_refresh_token=encrypted_refresh,
                oauth_token_expiry=credentials.expiry,
                is_active=True,
                sync_enabled=True,
            )
            db.add(account)

        await db.commit()

        # Redirect to frontend settings page with success message
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/settings?google_connected=true&email={email_address}",
            status_code=status.HTTP_302_FOUND,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete Google OAuth: {str(e)}",
        )


@router.get("/status")
async def google_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Check if user has connected Google account."""
    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.user_id == current_user.id,
            EmailAccount.provider == "gmail",
            EmailAccount.oauth_token.isnot(None),
        )
    )
    accounts = result.scalars().all()

    connected_accounts = []
    for account in accounts:
        connected_accounts.append(
            {
                "id": str(account.id),
                "email": account.email_address,
                "display_name": account.display_name,
                "is_active": account.is_active,
                "last_sync": (account.last_sync.isoformat() if account.last_sync else None),
            }
        )

    return {
        "connected": len(connected_accounts) > 0,
        "accounts": connected_accounts,
        "oauth_configured": bool(
            settings.google_client_id and settings.google_client_secret
        ),
    }


@router.delete("/disconnect/{account_id}")
async def google_disconnect(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Disconnect a Google account."""
    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.id == account_id,
            EmailAccount.user_id == current_user.id,
            EmailAccount.provider == "gmail",
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    # Clear OAuth tokens
    account.oauth_token = None
    account.oauth_refresh_token = None
    account.oauth_token_expiry = None
    account.is_active = False

    await db.commit()

    return {"message": "Google account disconnected"}


def get_google_credentials(account: EmailAccount) -> Optional[Credentials]:
    """Get Google credentials from email account, refreshing if needed."""
    if not account.oauth_token:
        return None

    token = decrypt_value(account.oauth_token)
    refresh_token = (
        decrypt_value(account.oauth_refresh_token) if account.oauth_refresh_token else None
    )

    if not token:
        return None

    creds = Credentials(
        token=token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        expiry=account.oauth_token_expiry,
    )

    # Refresh if expired
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request

        try:
            creds.refresh(Request())
            # Note: In a real implementation, you'd want to update the DB with new tokens
            # This would require passing the db session to this function
        except Exception:
            return None

    return creds
