"""User schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    language: str = Field(default="en", pattern="^(en|ro)$")
    timezone: str = Field(default="UTC")


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    email: Optional[EmailStr] = None
    language: Optional[str] = Field(default=None, pattern="^(en|ro)$")
    timezone: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user response."""

    id: UUID
    email: str
    is_active: bool
    is_2fa_enabled: bool
    language: str
    timezone: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str
    totp_code: Optional[str] = Field(default=None, min_length=6, max_length=6)


class Token(BaseModel):
    """Schema for JWT tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""

    sub: str
    exp: int
    type: str


class TwoFactorSetup(BaseModel):
    """Schema for 2FA setup response."""

    secret: str
    qr_code: str  # Base64 encoded QR code image
    uri: str


class TwoFactorVerify(BaseModel):
    """Schema for 2FA verification."""

    code: str = Field(..., min_length=6, max_length=6)


class PasswordChange(BaseModel):
    """Schema for password change."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordReset(BaseModel):
    """Schema for password reset."""

    email: EmailStr
