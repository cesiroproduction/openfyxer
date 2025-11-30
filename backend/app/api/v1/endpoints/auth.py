"""Authentication endpoints."""

import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_client_ip,
    get_current_user,
    get_user_agent,
)
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_totp_qr_code,
    generate_totp_secret,
    get_password_hash,
    get_totp_uri,
    verify_password,
    verify_totp,
)
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.models.user_settings import UserSettings
from app.schemas.user import (
    Token,
    TwoFactorSetup,
    TwoFactorVerify,
    UserCreate,
    UserLogin,
    UserResponse,
)

router = APIRouter()


async def create_audit_log(
    db: AsyncSession,
    user_id: uuid.UUID,
    action: str,
    request: Request,
    status: str = "success",
    details: dict = None,
    error_message: str = None,
) -> None:
    """Create an audit log entry."""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        status=status,
        details=details,
        error_message=error_message,
    )
    db.add(audit_log)
    await db.commit()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Register a new user."""
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        language=user_in.language,
        timezone=user_in.timezone,
    )
    db.add(user)
    await db.flush()
    
    # Create default user settings
    user_settings = UserSettings(user_id=user.id)
    db.add(user_settings)
    
    await db.commit()
    await db.refresh(user)
    
    # Create audit log
    await create_audit_log(
        db=db,
        user_id=user.id,
        action="user_registered",
        request=request,
        details={"email": user.email},
    )
    
    return user


@router.post("/login", response_model=Token)
async def login(
    user_in: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Login and get access token."""
    # Find user
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    # Check 2FA if enabled
    if user.is_2fa_enabled:
        if not user_in.totp_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA code required",
            )
        
        if not user.totp_secret or not verify_totp(user.totp_secret, user_in.totp_code):
            await create_audit_log(
                db=db,
                user_id=user.id,
                action="login_failed",
                request=request,
                status="failure",
                error_message="Invalid 2FA code",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code",
            )
    
    # Create tokens
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    
    # Create audit log
    await create_audit_log(
        db=db,
        user_id=user.id,
        action="login",
        request=request,
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Refresh access token using refresh token."""
    payload = decode_token(refresh_token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    # Verify user exists and is active
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    # Create new tokens
    new_access_token = create_access_token(subject=str(user.id))
    new_refresh_token = create_refresh_token(subject=str(user.id))
    
    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Logout user (invalidate token on client side)."""
    # Create audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="logout",
        request=request,
    )
    
    return {"message": "Successfully logged out"}


@router.post("/2fa/setup", response_model=TwoFactorSetup)
async def setup_2fa(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Setup 2FA for user."""
    if current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled",
        )
    
    # Generate new TOTP secret
    secret = generate_totp_secret()
    uri = get_totp_uri(secret, current_user.email, settings.APP_NAME)
    qr_code = generate_totp_qr_code(uri)
    
    # Store secret temporarily (not enabled yet)
    current_user.totp_secret = secret
    await db.commit()
    
    return TwoFactorSetup(
        secret=secret,
        qr_code=qr_code,
        uri=uri,
    )


@router.post("/2fa/verify")
async def verify_2fa(
    verify_in: TwoFactorVerify,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Verify and enable 2FA."""
    if current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled",
        )
    
    if not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA setup not initiated. Call /2fa/setup first.",
        )
    
    if not verify_totp(current_user.totp_secret, verify_in.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )
    
    # Enable 2FA
    current_user.is_2fa_enabled = True
    await db.commit()
    
    # Create audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="2fa_enabled",
        request=request,
    )
    
    return {"message": "2FA enabled successfully"}


@router.post("/2fa/disable")
async def disable_2fa(
    verify_in: TwoFactorVerify,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Disable 2FA."""
    if not current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled",
        )
    
    if not current_user.totp_secret or not verify_totp(
        current_user.totp_secret, verify_in.code
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )
    
    # Disable 2FA
    current_user.is_2fa_enabled = False
    current_user.totp_secret = None
    await db.commit()
    
    # Create audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="2fa_disabled",
        request=request,
    )
    
    return {"message": "2FA disabled successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get current user information."""
    return current_user
