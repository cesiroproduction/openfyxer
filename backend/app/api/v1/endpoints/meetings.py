"""Meeting endpoints."""

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Pagination, get_current_user, get_pagination
from app.db.session import get_db
from app.models.calendar_event import CalendarEvent
from app.models.meeting import Meeting
from app.models.user import User
from app.schemas.meeting import (
    FollowUpEmailRequest,
    MeetingCreate,
    MeetingListResponse,
    MeetingResponse,
    MeetingUpdate,
    SummarizationRequest,
    TranscriptionProgress,
    TranscriptionRequest,
)

router = APIRouter()


@router.get("", response_model=MeetingListResponse)
async def list_meetings(
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        pattern="^(pending|transcribing|transcribed|summarized|error)$",
    ),
    search: Optional[str] = None,
    pagination: Pagination = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all meetings."""
    query = select(Meeting).where(Meeting.user_id == current_user.id)
    count_query = select(func.count(Meeting.id)).where(Meeting.user_id == current_user.id)

    if status_filter:
        query = query.where(Meeting.status == status_filter)
        count_query = count_query.where(Meeting.status == status_filter)

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (Meeting.title.ilike(search_filter))
            | (Meeting.transcript.ilike(search_filter))
            | (Meeting.summary.ilike(search_filter))
        )
        count_query = count_query.where(
            (Meeting.title.ilike(search_filter))
            | (Meeting.transcript.ilike(search_filter))
            | (Meeting.summary.ilike(search_filter))
        )

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.order_by(Meeting.created_at.desc())
    query = query.offset(pagination.offset).limit(pagination.limit)

    result = await db.execute(query)
    meetings = result.scalars().all()

    total_pages = (total + pagination.page_size - 1) // pagination.page_size

    return MeetingListResponse(
        items=meetings,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    meeting_in: MeetingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new meeting record."""
    # Verify calendar event if provided
    if meeting_in.calendar_event_id:
        event_result = await db.execute(
            select(CalendarEvent).where(
                CalendarEvent.id == meeting_in.calendar_event_id,
                CalendarEvent.user_id == current_user.id,
            )
        )
        event = event_result.scalar_one_or_none()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Calendar event not found",
            )

    meeting = Meeting(
        user_id=current_user.id,
        calendar_event_id=meeting_in.calendar_event_id,
        title=meeting_in.title,
        description=meeting_in.description,
        meeting_date=meeting_in.meeting_date,
        participants=meeting_in.participants,
        status="pending",
    )

    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)

    return meeting


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get meeting by ID."""
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == current_user.id,
        )
    )
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    return meeting


@router.put("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: uuid.UUID,
    meeting_in: MeetingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update meeting details."""
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == current_user.id,
        )
    )
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    update_data = meeting_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(meeting, field, value)

    await db.commit()
    await db.refresh(meeting)

    return meeting


@router.delete("/{meeting_id}")
async def delete_meeting(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Delete a meeting."""
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == current_user.id,
        )
    )
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    # TODO: Delete audio file if exists

    await db.delete(meeting)
    await db.commit()

    return {"message": "Meeting deleted successfully"}


@router.post("/{meeting_id}/upload-audio", response_model=MeetingResponse)
async def upload_meeting_audio(
    meeting_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Upload audio file for a meeting."""
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == current_user.id,
        )
    )
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    # Validate file type
    allowed_types = [
        "audio/mpeg",
        "audio/wav",
        "audio/mp4",
        "audio/x-m4a",
        "audio/webm",
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio format not supported. Allowed: MP3, WAV, M4A, WebM",
        )

    # Read file
    content = await file.read()

    # Determine format
    audio_format = "unknown"
    if file.content_type == "audio/mpeg":
        audio_format = "mp3"
    elif file.content_type == "audio/wav":
        audio_format = "wav"
    elif file.content_type in ["audio/mp4", "audio/x-m4a"]:
        audio_format = "m4a"
    elif file.content_type == "audio/webm":
        audio_format = "webm"

    # Generate unique filename
    import hashlib

    file_hash = hashlib.md5(content).hexdigest()[:8]
    stored_filename = f"{current_user.id}_{meeting_id}_{file_hash}.{audio_format}"

    # TODO: Save file to storage
    file_path = f"/data/audio/{stored_filename}"

    # TODO: Get audio duration
    audio_duration = None

    # Update meeting
    meeting.audio_file_path = file_path
    meeting.audio_format = audio_format
    meeting.audio_duration_seconds = audio_duration

    await db.commit()
    await db.refresh(meeting)

    return meeting


@router.post("/{meeting_id}/transcribe", response_model=MeetingResponse)
async def transcribe_meeting(
    meeting_id: uuid.UUID,
    request: Optional[TranscriptionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Start transcription of meeting audio."""
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == current_user.id,
        )
    )
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    if not meeting.audio_file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No audio file uploaded for this meeting",
        )

    if meeting.status == "transcribing":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcription already in progress",
        )

    # Update status
    meeting.status = "transcribing"

    # Set transcription parameters
    language = "auto"
    model = "base"
    if request:
        language = request.language or language
        model = request.model or model

    meeting.transcription_model = f"whisper-{model}"

    await db.commit()
    await db.refresh(meeting)

    # TODO: Trigger Celery task for transcription
    # from app.workers.tasks import transcribe_audio
    # transcribe_audio.delay(str(meeting_id), language, model)

    return meeting


@router.get(
    "/{meeting_id}/transcription-progress", response_model=TranscriptionProgress
)
async def get_transcription_progress(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get transcription progress."""
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == current_user.id,
        )
    )
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    # TODO: Get actual progress from Celery task
    progress = 0.0
    estimated_time = None

    if meeting.status == "transcribed" or meeting.status == "summarized":
        progress = 100.0
    elif meeting.status == "transcribing":
        progress = 50.0  # Placeholder
        estimated_time = 60  # Placeholder

    return TranscriptionProgress(
        meeting_id=meeting_id,
        status=meeting.status,
        progress_percent=progress,
        estimated_time_remaining_seconds=estimated_time,
        error_message=None,
    )


@router.post("/{meeting_id}/summarize", response_model=MeetingResponse)
async def summarize_meeting(
    meeting_id: uuid.UUID,
    request: Optional[SummarizationRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Generate summary from meeting transcript."""
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == current_user.id,
        )
    )
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    if not meeting.transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting has no transcript. Please transcribe first.",
        )

    # TODO: Call LLM to generate summary
    # For now, create placeholder
    meeting.summary = f"Summary of meeting: {meeting.title}\n\nThis is a placeholder summary."

    if request and request.include_action_items:
        meeting.action_items = [
            "Action item 1 (placeholder)",
            "Action item 2 (placeholder)",
        ]

    if request and request.include_key_decisions:
        meeting.key_decisions = ["Key decision 1 (placeholder)"]

    if request and request.include_topics:
        meeting.topics = ["Topic 1", "Topic 2"]

    meeting.status = "summarized"
    meeting.summarized_at = datetime.utcnow()

    await db.commit()
    await db.refresh(meeting)

    return meeting


@router.post("/{meeting_id}/generate-follow-up")
async def generate_follow_up_email(
    meeting_id: uuid.UUID,
    request: FollowUpEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Generate follow-up email from meeting."""
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == current_user.id,
        )
    )
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    if not meeting.summary and not meeting.transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting has no summary or transcript",
        )

    # TODO: Generate follow-up email using LLM
    # For now, return placeholder

    email_content = f"""Subject: Follow-up: {meeting.title}

Hi,

Thank you for attending the meeting "{meeting.title}".

"""

    if request.include_summary and meeting.summary:
        email_content += f"Summary:\n{meeting.summary}\n\n"

    if request.include_action_items and meeting.action_items:
        email_content += "Action Items:\n"
        for item in meeting.action_items:
            email_content += f"- {item}\n"
        email_content += "\n"

    if request.include_key_decisions and meeting.key_decisions:
        email_content += "Key Decisions:\n"
        for decision in meeting.key_decisions:
            email_content += f"- {decision}\n"
        email_content += "\n"

    if request.additional_notes:
        email_content += f"Additional Notes:\n{request.additional_notes}\n\n"

    email_content += "Best regards"

    return {
        "subject": f"Follow-up: {meeting.title}",
        "recipients": request.recipients,
        "content": email_content,
        "meeting_id": str(meeting_id),
    }


@router.post("/{meeting_id}/send-follow-up")
async def send_follow_up_email(
    meeting_id: uuid.UUID,
    request: FollowUpEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Send follow-up email for meeting."""
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == current_user.id,
        )
    )
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    # Generate email content
    await generate_follow_up_email(meeting_id, request, current_user, db)

    # TODO: Actually send the email

    # Update meeting
    meeting.follow_up_email_sent = True
    await db.commit()

    return {
        "message": "Follow-up email sent successfully",
        "recipients": request.recipients,
    }
