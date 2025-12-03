"""Calendar service for handling calendar operations."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import CalendarProviderError
from app.models.calendar_event import CalendarEvent
from app.models.user_settings import UserSettings


class CalendarService:
    """Service for calendar operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync_google_calendar(
        self,
        user_id: UUID,
        oauth_token: str,
        refresh_token: Optional[str] = None,
        calendar_id: str = "primary",
    ) -> List[CalendarEvent]:
        """Sync events from Google Calendar."""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            creds = Credentials(
                token=oauth_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
            )

            service = build("calendar", "v3", credentials=creds)

            # Get events from the last month to next 3 months
            now = datetime.utcnow()
            time_min = (now - timedelta(days=30)).isoformat() + "Z"
            time_max = (now + timedelta(days=90)).isoformat() + "Z"

            events_result = (
                service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=500,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            synced_events = []

            for event_data in events:
                event = await self._parse_google_event(user_id, event_data, calendar_id)
                if event:
                    synced_events.append(event)

            await self.db.commit()
            return synced_events

        except Exception as e:
            raise CalendarProviderError(f"Google Calendar sync failed: {str(e)}")

    async def sync_outlook_calendar(
        self,
        user_id: UUID,
        oauth_token: str,
    ) -> List[CalendarEvent]:
        """Sync events from Outlook Calendar."""
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {oauth_token}",
                "Content-Type": "application/json",
            }

            # Get events from the last month to next 3 months
            now = datetime.utcnow()
            time_min = (now - timedelta(days=30)).isoformat() + "Z"
            time_max = (now + timedelta(days=90)).isoformat() + "Z"

            url = f"https://graph.microsoft.com/v1.0/me/calendarView?startDateTime={time_min}&endDateTime={time_max}&$top=500"
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                raise CalendarProviderError(f"Outlook API error: {response.text}")

            events = response.json().get("value", [])
            synced_events = []

            for event_data in events:
                event = await self._parse_outlook_event(user_id, event_data)
                if event:
                    synced_events.append(event)

            await self.db.commit()
            return synced_events

        except Exception as e:
            raise CalendarProviderError(f"Outlook Calendar sync failed: {str(e)}")

    async def _parse_google_event(
        self,
        user_id: UUID,
        event_data: Dict[str, Any],
        calendar_id: str,
    ) -> Optional[CalendarEvent]:
        """Parse Google Calendar event into CalendarEvent model."""
        try:
            external_id = event_data.get("id", "")

            # Check if event already exists
            existing = await self.db.execute(
                select(CalendarEvent).where(
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.external_id == external_id,
                    CalendarEvent.provider == "google",
                )
            )
            existing_event = existing.scalar_one_or_none()

            # Parse start/end times
            start = event_data.get("start", {})
            end = event_data.get("end", {})

            is_all_day = "date" in start
            if is_all_day:
                start_time = datetime.fromisoformat(start["date"])
                end_time = datetime.fromisoformat(end["date"])
            else:
                start_time = datetime.fromisoformat(
                    start.get("dateTime", "").replace("Z", "+00:00")
                )
                end_time = datetime.fromisoformat(end.get("dateTime", "").replace("Z", "+00:00"))

            # Parse attendees
            attendees = [a.get("email", "") for a in event_data.get("attendees", [])]

            # Get meeting link
            meeting_link = None
            if event_data.get("hangoutLink"):
                meeting_link = event_data["hangoutLink"]
            elif event_data.get("conferenceData", {}).get("entryPoints"):
                for entry in event_data["conferenceData"]["entryPoints"]:
                    if entry.get("entryPointType") == "video":
                        meeting_link = entry.get("uri")
                        break

            if existing_event:
                # Update existing event
                existing_event.title = event_data.get("summary", "No Title")
                existing_event.description = event_data.get("description")
                existing_event.start_time = start_time
                existing_event.end_time = end_time
                existing_event.timezone = start.get("timeZone")
                existing_event.location = event_data.get("location")
                existing_event.meeting_link = meeting_link
                existing_event.attendees = attendees
                existing_event.organizer = event_data.get("organizer", {}).get("email")
                existing_event.is_all_day = is_all_day
                existing_event.is_recurring = bool(event_data.get("recurringEventId"))
                existing_event.status = event_data.get("status", "confirmed")
                return existing_event
            else:
                # Create new event
                event = CalendarEvent(
                    user_id=user_id,
                    provider="google",
                    external_id=external_id,
                    calendar_id=calendar_id,
                    title=event_data.get("summary", "No Title"),
                    description=event_data.get("description"),
                    start_time=start_time,
                    end_time=end_time,
                    timezone=start.get("timeZone"),
                    location=event_data.get("location"),
                    meeting_link=meeting_link,
                    attendees=attendees,
                    organizer=event_data.get("organizer", {}).get("email"),
                    is_all_day=is_all_day,
                    is_recurring=bool(event_data.get("recurringEventId")),
                    status=event_data.get("status", "confirmed"),
                    color=event_data.get("colorId"),
                )
                self.db.add(event)
                return event

        except Exception as e:
            print(f"Error parsing Google event: {e}")
            return None

    async def _parse_outlook_event(
        self,
        user_id: UUID,
        event_data: Dict[str, Any],
    ) -> Optional[CalendarEvent]:
        """Parse Outlook Calendar event into CalendarEvent model."""
        try:
            external_id = event_data.get("id", "")

            # Check if event already exists
            existing = await self.db.execute(
                select(CalendarEvent).where(
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.external_id == external_id,
                    CalendarEvent.provider == "outlook",
                )
            )
            existing_event = existing.scalar_one_or_none()

            # Parse times
            start = event_data.get("start", {})
            end = event_data.get("end", {})

            is_all_day = event_data.get("isAllDay", False)
            start_time = datetime.fromisoformat(
                start.get("dateTime", "").replace("Z", "+00:00")
            )
            end_time = datetime.fromisoformat(
                end.get("dateTime", "").replace("Z", "+00:00")
            )

            # Parse attendees
            attendees = [
                a.get("emailAddress", {}).get("address", "")
                for a in event_data.get("attendees", [])
            ]

            # Get meeting link
            meeting_link = event_data.get("onlineMeeting", {}).get("joinUrl")

            if existing_event:
                existing_event.title = event_data.get("subject", "No Title")
                existing_event.description = event_data.get("bodyPreview")
                existing_event.start_time = start_time
                existing_event.end_time = end_time
                existing_event.timezone = start.get("timeZone")
                existing_event.location = event_data.get("location", {}).get(
                    "displayName"
                )
                existing_event.meeting_link = meeting_link
                existing_event.attendees = attendees
                existing_event.organizer = (
                    event_data.get("organizer", {}).get("emailAddress", {}).get("address")
                )
                existing_event.is_all_day = is_all_day
                existing_event.is_recurring = event_data.get("type") == "occurrence"
                return existing_event
            else:
                event = CalendarEvent(
                    user_id=user_id,
                    provider="outlook",
                    external_id=external_id,
                    title=event_data.get("subject", "No Title"),
                    description=event_data.get("bodyPreview"),
                    start_time=start_time,
                    end_time=end_time,
                    timezone=start.get("timeZone"),
                    location=event_data.get("location", {}).get("displayName"),
                    meeting_link=meeting_link,
                    attendees=attendees,
                    organizer=event_data.get("organizer", {})
                    .get("emailAddress", {})
                    .get("address"),
                    is_all_day=is_all_day,
                    is_recurring=event_data.get("type") == "occurrence",
                    status="confirmed",
                )
                self.db.add(event)
                return event

        except Exception as e:
            print(f"Error parsing Outlook event: {e}")
            return None

    async def create_google_event(
        self,
        oauth_token: str,
        refresh_token: Optional[str],
        event: CalendarEvent,
    ) -> Optional[str]:
        """Create event in Google Calendar."""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            creds = Credentials(
                token=oauth_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
            )

            service = build("calendar", "v3", credentials=creds)

            event_body = {
                "summary": event.title,
                "description": event.description,
                "start": {
                    "dateTime": event.start_time.isoformat(),
                    "timeZone": event.timezone or "UTC",
                },
                "end": {
                    "dateTime": event.end_time.isoformat(),
                    "timeZone": event.timezone or "UTC",
                },
            }

            if event.location:
                event_body["location"] = event.location

            if event.attendees:
                event_body["attendees"] = [{"email": a} for a in event.attendees]

            if event.reminder_minutes:
                event_body["reminders"] = {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": event.reminder_minutes},
                    ],
                }

            result = (
                service.events()
                .insert(
                    calendarId="primary",
                    body=event_body,
                    sendUpdates="all" if event.attendees else "none",
                )
                .execute()
            )

            return result.get("id")

        except Exception as e:
            raise CalendarProviderError(f"Failed to create Google event: {str(e)}")

    async def create_outlook_event(
        self,
        oauth_token: str,
        event: CalendarEvent,
    ) -> Optional[str]:
        """Create event in Outlook Calendar."""
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {oauth_token}",
                "Content-Type": "application/json",
            }

            event_body = {
                "subject": event.title,
                "body": {
                    "contentType": "text",
                    "content": event.description or "",
                },
                "start": {
                    "dateTime": event.start_time.isoformat(),
                    "timeZone": event.timezone or "UTC",
                },
                "end": {
                    "dateTime": event.end_time.isoformat(),
                    "timeZone": event.timezone or "UTC",
                },
            }

            if event.location:
                event_body["location"] = {"displayName": event.location}

            if event.attendees:
                event_body["attendees"] = [
                    {"emailAddress": {"address": a}, "type": "required"} for a in event.attendees
                ]

            response = requests.post(
                "https://graph.microsoft.com/v1.0/me/events",
                headers=headers,
                json=event_body,
            )

            if response.status_code != 201:
                raise CalendarProviderError(f"Outlook API error: {response.text}")

            return response.json().get("id")

        except Exception as e:
            raise CalendarProviderError(f"Failed to create Outlook event: {str(e)}")

    async def find_available_slots(
        self,
        user_id: UUID,
        duration_minutes: int,
        date_from: datetime,
        date_to: datetime,
        respect_working_hours: bool = True,
    ) -> List[Dict[str, Any]]:
        """Find available time slots."""
        # Get user settings
        settings_result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
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

        # Get existing events
        events_result = await self.db.execute(
            select(CalendarEvent)
            .where(
                CalendarEvent.user_id == user_id,
                CalendarEvent.status != "cancelled",
                CalendarEvent.start_time >= date_from,
                CalendarEvent.end_time <= date_to,
            )
            .order_by(CalendarEvent.start_time)
        )
        existing_events = events_result.scalars().all()

        # Generate available slots
        slots = []
        current_date = date_from.date()
        end_date = date_to.date()

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

                if not respect_working_hours:
                    day_start = datetime.combine(
                        current_date, datetime.min.time().replace(hour=8)
                    )
                    day_end = datetime.combine(
                        current_date, datetime.min.time().replace(hour=20)
                    )

                current_time = max(day_start, date_from)
                day_events = [
                    e for e in existing_events if e.start_time.date() == current_date
                ]

                for event in day_events:
                    if event.start_time > current_time:
                        gap_minutes = (
                            event.start_time - current_time
                        ).total_seconds() / 60
                        if gap_minutes >= duration_minutes:
                            slots.append(
                                {
                                    "start_time": current_time,
                                    "end_time": current_time + timedelta(minutes=duration_minutes),
                                    "duration_minutes": duration_minutes,
                                }
                            )
                    current_time = event.end_time + timedelta(minutes=buffer_minutes)

                if current_time < min(day_end, date_to):
                    remaining = (
                        min(day_end, date_to) - current_time
                    ).total_seconds() / 60
                    if remaining >= duration_minutes:
                        slots.append(
                            {
                                "start_time": current_time,
                                "end_time": current_time + timedelta(minutes=duration_minutes),
                                "duration_minutes": duration_minutes,
                            }
                        )

            current_date += timedelta(days=1)

        return slots[:20]

    async def check_conflicts(
        self,
        user_id: UUID,
        start_time: datetime,
        end_time: datetime,
        exclude_event_id: Optional[UUID] = None,
    ) -> List[CalendarEvent]:
        """Check for conflicting events."""
        query = select(CalendarEvent).where(
            CalendarEvent.user_id == user_id,
            CalendarEvent.status != "cancelled",
            or_(
                and_(
                    CalendarEvent.start_time < end_time,
                    CalendarEvent.end_time > start_time,
                ),
            ),
        )

        if exclude_event_id:
            query = query.where(CalendarEvent.id != exclude_event_id)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_upcoming_events(
        self,
        user_id: UUID,
        days: int = 7,
        limit: int = 20,
    ) -> List[CalendarEvent]:
        """Get upcoming events."""
        now = datetime.utcnow()
        end_date = now + timedelta(days=days)

        result = await self.db.execute(
            select(CalendarEvent)
            .where(
                CalendarEvent.user_id == user_id,
                CalendarEvent.start_time >= now,
                CalendarEvent.start_time <= end_date,
                CalendarEvent.status != "cancelled",
            )
            .order_by(CalendarEvent.start_time)
            .limit(limit)
        )

        return result.scalars().all()

    async def get_today_events(
        self,
        user_id: UUID,
    ) -> List[CalendarEvent]:
        """Get today's events."""
        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_end = today_start + timedelta(days=1)

        result = await self.db.execute(
            select(CalendarEvent)
            .where(
                CalendarEvent.user_id == user_id,
                CalendarEvent.start_time >= today_start,
                CalendarEvent.start_time < today_end,
                CalendarEvent.status != "cancelled",
            )
            .order_by(CalendarEvent.start_time)
        )

        return result.scalars().all()
