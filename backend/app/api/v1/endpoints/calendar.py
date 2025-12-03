"""Calendar endpoints."""

import uuid
from datetime import datetime, timedelta
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Pagination, get_current_user, get_pagination
from app.core.encryption import decrypt_value
from app.core.exceptions import CalendarProviderError
from app.db.session import get_db
from app.models.calendar_event import CalendarEvent
from app.models.email_account import EmailAccount
from app.models.user import User
from app.models.user_settings import UserSettings
from app.schemas.calendar import (
    AvailableSlot,
    AvailableSlotsRequest,
    AvailableSlotsResponse,
    CalendarEventCreate,
    CalendarEventListResponse,
    CalendarEventResponse,
    CalendarEventUpdate,
    ConflictResponse,
    ScheduleMeetingRequest,
)
from app.services.calendar_service import CalendarService

router = APIRouter()


@router.get("/events", response_model=CalendarEventListResponse)
async def list_calendar_events(
    provider: Optional[str] = Query(None, pattern="^(google|outlook)$"),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    pagination: Pagination = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List calendar events."""
    query = select(CalendarEvent).where(CalendarEvent.user_id == current_user.id)
    count_query = select(func.count(CalendarEvent.id)).where(
        CalendarEvent.user_id == current_user.id
    )

    if provider:
        query = query.where(CalendarEvent.provider == provider)
        count_query = count_query.where(CalendarEvent.provider == provider)

    if date_from:
        query = query.where(CalendarEvent.start_time >= date_from)
        count_query = count_query.where(CalendarEvent.start_time >= date_from)

    if date_to:
        query = query.where(CalendarEvent.end_time <= date_to)
        count_query = count_query.where(CalendarEvent.end_time <= date_to)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.order_by(CalendarEvent.start_time.asc())
    query = query.offset(pagination.offset).limit(pagination.limit)

    result = await db.execute(query)
    events = result.scalars().all()

    total_pages = (total + pagination.page_size - 1) // pagination.page_size

    return CalendarEventListResponse(
        items=events,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.post(
    "/events", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED
)
async def create_calendar_event(
    event_in: CalendarEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new calendar event."""
    if event_in.end_time <= event_in.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time",
        )

    provider = event_in.provider

    # Auto-route local events to a connected provider when possible
    if provider == "local":
        connected_account = await db.execute(
            select(EmailAccount)
            .where(
                EmailAccount.user_id == current_user.id,
                EmailAccount.is_active == True,  # noqa: E712
                EmailAccount.sync_enabled == True,  # noqa: E712
            )
            .order_by(EmailAccount.created_at)
        )
        account = connected_account.scalar_one_or_none()
        if account:
            if account.provider == "gmail":
                provider = "google"
            elif account.provider == "outlook":
                provider = "outlook"

    event = CalendarEvent(
        user_id=current_user.id,
        provider=provider,
        title=event_in.title,
        description=event_in.description,
        start_time=event_in.start_time,
        end_time=event_in.end_time,
        timezone=event_in.timezone or current_user.timezone,
        location=event_in.location,
        meeting_link=event_in.meeting_link,
        attendees=event_in.attendees,
        is_all_day=event_in.is_all_day,
        reminder_minutes=event_in.reminder_minutes,
        status="confirmed",
    )

    db.add(event)
    await db.commit()
    await db.refresh(event)

    # Push newly created events to external providers when possible
    if provider == "google":
        account_query = await db.execute(
            select(EmailAccount)
            .where(
                EmailAccount.user_id == current_user.id,
                EmailAccount.provider == "gmail",
                EmailAccount.is_active == True,  # noqa: E712
                EmailAccount.sync_enabled == True,  # noqa: E712
            )
            .order_by(EmailAccount.created_at)
        )
        account = account_query.scalar_one_or_none()

        if account and account.oauth_token:
            calendar_service = CalendarService(db)
            external_id = await calendar_service.create_google_event(
                oauth_token=decrypt_value(account.oauth_token),
                refresh_token=(
                    decrypt_value(account.oauth_refresh_token)
                    if account.oauth_refresh_token
                    else None
                ),
                event=event,
            )

            if external_id:
                event.external_id = external_id
                event.calendar_id = "primary"
                await db.commit()
                await db.refresh(event)

    return event


@router.get("/events/{event_id}", response_model=CalendarEventResponse)
async def get_calendar_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get calendar event by ID."""
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == current_user.id,
        )
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar event not found",
        )

    return event


@router.put("/events/{event_id}", response_model=CalendarEventResponse)
async def update_calendar_event(
    event_id: uuid.UUID,
    event_in: CalendarEventUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update calendar event."""
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == current_user.id,
        )
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar event not found",
        )

    update_data = event_in.model_dump(exclude_unset=True)

    # Validate times if both are being updated
    start_time = update_data.get("start_time", event.start_time)
    end_time = update_data.get("end_time", event.end_time)

    if end_time <= start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time",
        )

    for field, value in update_data.items():
        setattr(event, field, value)

    await db.commit()
    await db.refresh(event)

    # TODO: Sync to external calendar provider

    return event


@router.delete("/events/{event_id}")
async def delete_calendar_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Delete calendar event."""
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == current_user.id,
        )
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar event not found",
        )

    await db.delete(event)
    await db.commit()

    # TODO: Delete from external calendar provider

    return {"message": "Calendar event deleted successfully"}


@router.post("/events/{event_id}/check-conflicts", response_model=ConflictResponse)
async def check_conflicts(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Check for conflicts with other events."""
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == current_user.id,
        )
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar event not found",
        )

    # Find conflicting events
    conflicts_result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.user_id == current_user.id,
            CalendarEvent.id != event_id,
            CalendarEvent.status != "cancelled",
            or_(
                and_(
                    CalendarEvent.start_time < event.end_time,
                    CalendarEvent.end_time > event.start_time,
                ),
            ),
        )
    )
    conflicts = conflicts_result.scalars().all()

    # Find alternative slots if there are conflicts
    alternatives = []
    if conflicts:
        # Simple algorithm: suggest slots after the last conflict
        last_conflict_end = max(c.end_time for c in conflicts)
        duration = event.end_time - event.start_time

        for i in range(3):
            slot_start = last_conflict_end + timedelta(minutes=15 * (i + 1))
            slot_end = slot_start + duration
            alternatives.append(
                AvailableSlot(
                    start_time=slot_start,
                    end_time=slot_end,
                    duration_minutes=int(duration.total_seconds() / 60),
                )
            )

    return ConflictResponse(
        has_conflict=len(conflicts) > 0,
        conflicting_events=conflicts,
        suggested_alternatives=alternatives,
    )


@router.post("/available-slots", response_model=AvailableSlotsResponse)
async def get_available_slots(
    request: AvailableSlotsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get available time slots for scheduling."""
    # Get user settings for working hours
    settings_result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    user_settings = settings_result.scalar_one_or_none()

    working_start = "09:00"
    working_end = "17:00"
    working_days = [1, 2, 3, 4, 5]  # Monday to Friday
    buffer_minutes = 15

    if user_settings:
        working_start = user_settings.working_hours_start or working_start
        working_end = user_settings.working_hours_end or working_end
        working_days = user_settings.working_days or working_days
        buffer_minutes = user_settings.meeting_buffer_minutes or buffer_minutes

    # Get existing events in the date range
    events_result = await db.execute(
        select(CalendarEvent)
        .where(
            CalendarEvent.user_id == current_user.id,
            CalendarEvent.status != "cancelled",
            CalendarEvent.start_time >= request.date_from,
            CalendarEvent.end_time <= request.date_to,
        )
        .order_by(CalendarEvent.start_time)
    )
    existing_events = events_result.scalars().all()

    # Generate available slots
    slots = []
    current_date = request.date_from.date()
    end_date = request.date_to.date()

    while current_date <= end_date:
        # Check if it's a working day
        if current_date.isoweekday() in working_days:
            # Parse working hours
            start_hour, start_min = map(int, working_start.split(":"))
            end_hour, end_min = map(int, working_end.split(":"))

            day_start = datetime.combine(
                current_date,
                datetime.min.time().replace(hour=start_hour, minute=start_min),
            )
            day_end = datetime.combine(
                current_date,
                datetime.min.time().replace(hour=end_hour, minute=end_min),
            )

            if request.respect_working_hours:
                slot_start = max(day_start, request.date_from)
                slot_end = min(day_end, request.date_to)
            else:
                slot_start = datetime.combine(current_date, datetime.min.time())
                slot_end = datetime.combine(current_date, datetime.max.time())

            # Find free slots
            current_time = slot_start

            for event in existing_events:
                if event.start_time.date() != current_date:
                    continue

                # Check if there's a gap before this event
                if event.start_time > current_time:
                    gap_duration = (
                        event.start_time - current_time
                    ).total_seconds() / 60
                    if gap_duration >= request.duration_minutes:
                        slots.append(
                            AvailableSlot(
                                start_time=current_time,
                                end_time=current_time
                                + timedelta(minutes=request.duration_minutes),
                                duration_minutes=request.duration_minutes,
                            )
                        )

                current_time = event.end_time + timedelta(minutes=buffer_minutes)

            # Check for slot after last event
            if current_time < slot_end:
                remaining = (slot_end - current_time).total_seconds() / 60
                if remaining >= request.duration_minutes:
                    slots.append(
                        AvailableSlot(
                            start_time=current_time,
                            end_time=current_time
                            + timedelta(minutes=request.duration_minutes),
                            duration_minutes=request.duration_minutes,
                        )
                    )

        current_date += timedelta(days=1)

    return AvailableSlotsResponse(slots=slots[:20], total=len(slots))


@router.post("/schedule-meeting", response_model=CalendarEventResponse)
async def auto_schedule_meeting(
    request: ScheduleMeetingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Auto-schedule a meeting based on availability."""
    # Get available slots
    date_from = request.date_range_start or datetime.utcnow()
    date_to = request.date_range_end or (date_from + timedelta(days=7))

    slots_request = AvailableSlotsRequest(
        duration_minutes=request.duration_minutes,
        date_from=date_from,
        date_to=date_to,
        attendees=request.attendees,
        respect_working_hours=True,
    )

    slots_response = await get_available_slots(slots_request, current_user, db)

    if not slots_response.slots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No available slots found in the specified date range",
        )

    # Use first available slot or preferred time if specified
    selected_slot = slots_response.slots[0]

    if request.preferred_times:
        for preferred in request.preferred_times:
            for slot in slots_response.slots:
                if slot.start_time == preferred:
                    selected_slot = slot
                    break

    # Create the event
    event = CalendarEvent(
        user_id=current_user.id,
        provider="google",  # Default provider
        title=request.title,
        description=request.description,
        start_time=selected_slot.start_time,
        end_time=selected_slot.end_time,
        attendees=request.attendees,
        status="confirmed",
    )

    db.add(event)
    await db.commit()
    await db.refresh(event)

    # TODO: Send calendar invites if send_invites is True

    return event


@router.post("/sync")
async def sync_calendars(
    provider: Optional[str] = Query(None, pattern="^(google|outlook)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Sync calendars with external providers."""
    calendar_service = CalendarService(db)

    account_query = select(EmailAccount).where(
        EmailAccount.user_id == current_user.id,
        EmailAccount.is_active == True,  # noqa: E712
        EmailAccount.sync_enabled == True,  # noqa: E712
    )

    if provider == "google":
        account_query = account_query.where(EmailAccount.provider == "gmail")
    elif provider == "outlook":
        account_query = account_query.where(EmailAccount.provider == "outlook")

    result = await db.execute(account_query)
    accounts = result.scalars().all()

    if not accounts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No connected accounts available for calendar sync",
        )

    summary = []
    total_synced = 0

    try:
        for account in accounts:
            if account.provider == "gmail" and account.oauth_token:
                await calendar_service.push_local_google_events(
                    user_id=current_user.id,
                    oauth_token=decrypt_value(account.oauth_token),
                    refresh_token=(
                        decrypt_value(account.oauth_refresh_token)
                        if account.oauth_refresh_token
                        else None
                    ),
                    calendar_id="primary",
                )
                events = await calendar_service.sync_google_calendar(
                    user_id=current_user.id,
                    oauth_token=decrypt_value(account.oauth_token),
                    refresh_token=(
                        decrypt_value(account.oauth_refresh_token)
                        if account.oauth_refresh_token
                        else None
                    ),
                    calendar_id="primary",
                )
            elif account.provider == "outlook" and account.oauth_token:
                events = await calendar_service.sync_outlook_calendar(
                    user_id=current_user.id,
                    oauth_token=decrypt_value(account.oauth_token),
                )
            else:
                summary.append(
                    {
                        "account_id": str(account.id),
                        "provider": account.provider,
                        "synced_count": 0,
                        "status": "skipped_no_token",
                    }
                )
                continue

            account.last_sync = datetime.utcnow()
            await db.commit()

            summary.append(
                {
                    "account_id": str(account.id),
                    "provider": account.provider,
                    "synced_count": len(events),
                    "status": "success",
                }
            )
            total_synced += len(events)

        return {
            "message": "Calendar sync completed",
            "provider": provider or "all",
            "synced_events": total_synced,
            "accounts": summary,
        }

    except CalendarProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync calendars: {str(e)}",
        )


@router.get("/today", response_model=List[CalendarEventResponse])
async def get_today_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get today's calendar events."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    result = await db.execute(
        select(CalendarEvent)
        .where(
            CalendarEvent.user_id == current_user.id,
            CalendarEvent.start_time >= today_start,
            CalendarEvent.start_time < today_end,
            CalendarEvent.status != "cancelled",
        )
        .order_by(CalendarEvent.start_time)
    )
    events = result.scalars().all()

    return events


@router.get("/upcoming", response_model=List[CalendarEventResponse])
async def get_upcoming_events(
    days: int = Query(default=7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get upcoming calendar events."""
    now = datetime.utcnow()
    end_date = now + timedelta(days=days)

    result = await db.execute(
        select(CalendarEvent)
        .where(
            CalendarEvent.user_id == current_user.id,
            CalendarEvent.start_time >= now,
            CalendarEvent.start_time <= end_date,
            CalendarEvent.status != "cancelled",
        )
        .order_by(CalendarEvent.start_time)
        .limit(20)
    )
    events = result.scalars().all()

    return events
