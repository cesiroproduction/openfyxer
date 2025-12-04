import uuid
import traceback
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

# --- HELPER PENTRU LOGARE IN TERMINAL ---
def log_debug(msg):
    print(f"[CALENDAR_API_DEBUG] {msg}", flush=True)

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

    total_result = await db.execute(count_query)
    total = total_result.scalar()

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
    """Create a new calendar event with Google Sync."""
    log_debug(f"Received CREATE Request. Title: {event_in.title}, Provider: {event_in.provider}")
    
    if event_in.end_time <= event_in.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time",
        )

    # 1. Create local event
    event = CalendarEvent(
        user_id=current_user.id,
        provider=event_in.provider,
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

    # 2. Sync to Google logic
    log_debug(f"Checking sync condition: provider={event.provider}")
    
    if event.provider == "google":
        log_debug("Attempting Google Sync...")
        
        # Get Account
        account_result = await db.execute(
            select(EmailAccount).where(
                EmailAccount.user_id == current_user.id,
                EmailAccount.provider == "gmail",
                EmailAccount.is_active == True
            )
        )
        email_account = account_result.scalars().first()

        if email_account and email_account.oauth_token:
            log_debug(f"Found Google Account: {email_account.email_address}")
            try:
                service = CalendarService(db)
                token = decrypt_value(email_account.oauth_token)
                refresh = decrypt_value(email_account.oauth_refresh_token) if email_account.oauth_refresh_token else None
                
                log_debug("Calling service.create_google_event...")
                google_id = await service.create_google_event(
                    oauth_token=token,
                    refresh_token=refresh,
                    event=event
                )
                
                if google_id:
                    log_debug(f"SYNC SUCCESS! Google ID: {google_id}")
                    event.external_id = google_id
                    await db.commit()
                    await db.refresh(event)
                else:
                    log_debug("SYNC FAILED: Service returned None")
            except Exception as e:
                log_debug(f"SYNC EXCEPTION: {e}")
                traceback.print_exc()
        else:
            log_debug("SYNC FAILED: No active Google account found with tokens.")

    return event


@router.get("/events/{event_id}", response_model=CalendarEventResponse)
async def get_calendar_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
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

    return event


@router.delete("/events/{event_id}")
async def delete_calendar_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
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

    return {"message": "Calendar event deleted successfully"}


@router.post("/events/{event_id}/check-conflicts", response_model=ConflictResponse)
async def check_conflicts(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
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

    alternatives = []
    if conflicts:
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
    settings_result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    user_settings = settings_result.scalar_one_or_none()

    working_start = "09:00"
    working_end = "17:00"
    working_days = [1, 2, 3, 4, 5]
    buffer_minutes = 15

    if user_settings:
        working_start = user_settings.working_hours_start or working_start
        working_end = user_settings.working_hours_end or working_end
        working_days = user_settings.working_days or working_days
        buffer_minutes = user_settings.meeting_buffer_minutes or buffer_minutes

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

    slots = []
    current_date = request.date_from.date()
    end_date = request.date_to.date()

    while current_date <= end_date:
        if current_date.isoweekday() in working_days:
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

            current_time = slot_start

            for event in existing_events:
                if event.start_time.date() != current_date:
                    continue

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

    selected_slot = slots_response.slots[0]

    if request.preferred_times:
        for preferred in request.preferred_times:
            for slot in slots_response.slots:
                if slot.start_time == preferred:
                    selected_slot = slot
                    break

    event = CalendarEvent(
        user_id=current_user.id,
        provider="google",
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

    account_result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.user_id == current_user.id,
            EmailAccount.provider == "gmail",
            EmailAccount.is_active == True
        )
    )
    email_account = account_result.scalars().first()
    
    if email_account and email_account.oauth_token:
        try:
            service = CalendarService(db)
            token = decrypt_value(email_account.oauth_token)
            refresh = decrypt_value(email_account.oauth_refresh_token) if email_account.oauth_refresh_token else None
            
            google_id = await service.create_google_event(
                oauth_token=token,
                refresh_token=refresh,
                event=event
            )
            if google_id:
                event.external_id = google_id
                await db.commit()
        except Exception:
            pass

    return event


@router.post("/sync")
async def sync_calendars(
    provider: Optional[str] = Query(None, pattern="^(google|outlook)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Sync calendars with detailed debugging."""
    log_debug(f"Starting SYNC for user {current_user.id}")
    calendar_service = CalendarService(db)

    account_query = select(EmailAccount).where(
        EmailAccount.user_id == current_user.id,
        EmailAccount.is_active == True,
        EmailAccount.sync_enabled == True,
    )

    if provider == "google":
        account_query = account_query.where(EmailAccount.provider == "gmail")
    elif provider == "outlook":
        account_query = account_query.where(EmailAccount.provider == "outlook")

    result = await db.execute(account_query)
    accounts = result.scalars().all()
    
    log_debug(f"Found {len(accounts)} active accounts")

    if not accounts:
        log_debug("No accounts found, returning empty success.")
        return {"message": "No accounts to sync", "synced_events": 0, "accounts": []}

    summary = []
    total_synced = 0

    for account in accounts:
        log_debug(f"Processing account: {account.email_address}")
        try:
            if account.provider == "gmail" and account.oauth_token:
                token = decrypt_value(account.oauth_token)
                refresh = decrypt_value(account.oauth_refresh_token) if account.oauth_refresh_token else None
                
                log_debug("Calling sync_google_calendar...")
                events = await calendar_service.sync_google_calendar(
                    user_id=current_user.id,
                    oauth_token=token,
                    refresh_token=refresh,
                    calendar_id="primary",
                )
                log_debug(f"Sync returned {len(events)} events")
                
                account.last_sync = datetime.utcnow()
                await db.commit()
                
                count = len(events)
                total_synced += count
                summary.append({"account": account.email_address, "status": "success", "count": count})
            else:
                log_debug(f"Account {account.email_address} has no token or unsupported provider.")
                
        except Exception as e:
            log_debug(f"ERROR syncing account {account.email_address}: {e}")
            traceback.print_exc()
            summary.append({"account": account.email_address, "status": "failed", "error": str(e)})

    return {
        "message": "Sync attempt finished",
        "synced_events": total_synced,
        "details": summary,
    }


@router.get("/today", response_model=List[CalendarEventResponse])
async def get_today_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
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
