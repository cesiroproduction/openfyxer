"""Settings endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.encryption import encrypt_value
from app.db.session import get_db
from app.models.user import User
from app.models.user_settings import UserSettings
from app.schemas.settings import (
    NotificationTest,
    StyleAnalysisRequest,
    StyleAnalysisResponse,
    UserSettingsResponse,
    UserSettingsUpdate,
)

router = APIRouter()


def settings_to_response(settings: UserSettings) -> UserSettingsResponse:
    """Convert UserSettings model to response schema."""
    return UserSettingsResponse(
        id=settings.id,
        user_id=settings.user_id,
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
        has_openai_key=bool(settings.openai_api_key),
        has_gemini_key=bool(settings.gemini_api_key),
        has_claude_key=bool(settings.claude_api_key),
        has_cohere_key=bool(settings.cohere_api_key),
        allow_cloud_llm_for_sensitive=settings.allow_cloud_llm_for_sensitive,
        has_slack_webhook=bool(settings.slack_webhook_url),
        sms_provider=settings.sms_provider,
        has_sms_key=bool(settings.sms_api_key),
        sms_phone_number=settings.sms_phone_number,
        notification_email=settings.notification_email,
        notification_preferences=settings.notification_preferences,
        email_style=settings.email_style,
        email_signature=settings.email_signature,
        auto_categorize=settings.auto_categorize,
        auto_draft=settings.auto_draft,
        auto_send=settings.auto_send,
        follow_up_days=settings.follow_up_days,
        priority_contacts=settings.priority_contacts,
        working_hours_start=settings.working_hours_start,
        working_hours_end=settings.working_hours_end,
        working_days=settings.working_days,
        meeting_buffer_minutes=settings.meeting_buffer_minutes,
        default_meeting_duration=settings.default_meeting_duration,
        whisper_model=settings.whisper_model,
        theme=settings.theme,
        dashboard_widgets=settings.dashboard_widgets,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


@router.get("", response_model=UserSettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get current user settings."""
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    settings = result.scalar_one_or_none()

    if not settings:
        # Create default settings
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings_to_response(settings)


@router.put("", response_model=UserSettingsResponse)
async def update_settings(
    settings_in: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update user settings."""
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    settings = result.scalar_one_or_none()

    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)

    update_data = settings_in.model_dump(exclude_unset=True)

    # Encrypt sensitive fields
    sensitive_fields = [
        "openai_api_key",
        "gemini_api_key",
        "claude_api_key",
        "cohere_api_key",
        "sms_api_key",
        "slack_webhook_url",
    ]

    for field, value in update_data.items():
        if field in sensitive_fields and value:
            value = encrypt_value(value)
        setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)

    return settings_to_response(settings)


@router.post("/test-notification")
async def test_notification(
    test_in: NotificationTest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Test notification channel."""
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Settings not configured",
        )

    channel = test_in.channel

    if channel == "slack":
        if not settings.slack_webhook_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slack webhook not configured",
            )
        # TODO: Send test Slack message
        # webhook_url = decrypt_value(settings.slack_webhook_url)

    elif channel == "sms":
        if not settings.sms_api_key or not settings.sms_phone_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SMS not configured",
            )
        # TODO: Send test SMS

    elif channel == "email":
        if not settings.notification_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Notification email not configured",
            )
        # TODO: Send test email

    elif channel == "webhook":
        # TODO: Send test webhook
        pass

    return {"message": f"Test notification sent to {channel}"}


@router.post("/analyze-style", response_model=StyleAnalysisResponse)
async def analyze_email_style(
    request: StyleAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Analyze user's email writing style."""
    # TODO: Implement actual style analysis using sent emails
    # For now, return placeholder data

    return StyleAnalysisResponse(
        average_length=150,
        common_greetings=["Hi", "Hello", "Dear"],
        common_closings=["Best regards", "Thanks", "Best"],
        tone_profile={
            "formal": 0.3,
            "friendly": 0.5,
            "professional": 0.7,
            "concise": 0.6,
        },
        vocabulary_complexity="medium",
        formality_level="professional",
        analyzed_emails_count=0,
    )


@router.get("/llm-providers")
async def get_llm_providers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get available LLM providers and their status."""
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    settings = result.scalar_one_or_none()

    providers = [
        {
            "id": "local",
            "name": "Local LLM (Ollama)",
            "description": "Run models locally using Ollama",
            "configured": True,  # Always available
            "requires_api_key": False,
        },
        {
            "id": "openai",
            "name": "OpenAI",
            "description": "GPT-4, GPT-3.5-turbo",
            "configured": bool(settings and settings.openai_api_key),
            "requires_api_key": True,
        },
        {
            "id": "gemini",
            "name": "Google Gemini",
            "description": "Gemini Pro, Gemini Ultra",
            "configured": bool(settings and settings.gemini_api_key),
            "requires_api_key": True,
        },
        {
            "id": "claude",
            "name": "Anthropic Claude",
            "description": "Claude 3 Opus, Sonnet, Haiku",
            "configured": bool(settings and settings.claude_api_key),
            "requires_api_key": True,
        },
        {
            "id": "cohere",
            "name": "Cohere",
            "description": "Command, Command-Light",
            "configured": bool(settings and settings.cohere_api_key),
            "requires_api_key": True,
        },
    ]

    return {"providers": providers}


@router.get("/whisper-models")
async def get_whisper_models() -> Any:
    """Get available Whisper models."""
    models = [
        {
            "id": "tiny",
            "name": "Tiny",
            "description": "Fastest, lowest accuracy (~1GB VRAM)",
            "size_mb": 75,
        },
        {
            "id": "base",
            "name": "Base",
            "description": "Good balance of speed and accuracy (~1GB VRAM)",
            "size_mb": 142,
        },
        {
            "id": "small",
            "name": "Small",
            "description": "Better accuracy, slower (~2GB VRAM)",
            "size_mb": 466,
        },
        {
            "id": "medium",
            "name": "Medium",
            "description": "High accuracy (~5GB VRAM)",
            "size_mb": 1500,
        },
        {
            "id": "large",
            "name": "Large",
            "description": "Best accuracy, slowest (~10GB VRAM)",
            "size_mb": 2900,
        },
    ]

    return {"models": models}


@router.delete("/api-key/{provider}")
async def delete_api_key(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Delete an API key."""
    valid_providers = ["openai", "gemini", "claude", "cohere", "sms", "slack"]
    if provider not in valid_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider. Valid options: {valid_providers}",
        )

    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found",
        )

    field_map = {
        "openai": "openai_api_key",
        "gemini": "gemini_api_key",
        "claude": "claude_api_key",
        "cohere": "cohere_api_key",
        "sms": "sms_api_key",
        "slack": "slack_webhook_url",
    }

    field = field_map[provider]
    setattr(settings, field, None)

    await db.commit()

    return {"message": f"{provider} API key deleted"}
