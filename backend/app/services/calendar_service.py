import logging
import httpx
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CalendarProviderError
from app.models.calendar_event import CalendarEvent
from app.core.config import settings

# Logger setup
logger = logging.getLogger("google_calendar_fetch")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - [HTTP] - %(levelname)s - %(message)s'))
logger.addHandler(handler)

GOOGLE_API_BASE = "https://www.googleapis.com/calendar/v3"

class CalendarService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync_google_calendar(
        self,
        user_id: UUID,
        oauth_token: str,
        refresh_token: Optional[str] = None,
        calendar_id: str = "primary",
    ) -> List[CalendarEvent]:
        logger.info("Starting Sync...")
        
        # 1. Fetch events from Google
        url = f"{GOOGLE_API_BASE}/calendars/{calendar_id}/events"
        now = datetime.utcnow()
        params = {
            "timeMin": (now - timedelta(days=30)).isoformat() + "Z",
            "timeMax": (now + timedelta(days=90)).isoformat() + "Z",
            "singleEvents": "true",
            "orderBy": "startTime"
        }
        headers = {"Authorization": f"Bearer {oauth_token}"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)
                
            if response.status_code == 401:
                logger.error("Token expired!")
                raise CalendarProviderError("Google Token Expired")
            
            data = response.json()
            items = data.get("items", [])
            logger.info(f"Found {len(items)} events in Google.")
            
            # 2. Save to DB (Simplified logic)
            synced = []
            for item in items:
                # Logic simplificat de upsert
                ext_id = item.get("id")
                existing = await self.db.execute(select(CalendarEvent).where(
                    CalendarEvent.external_id == ext_id, 
                    CalendarEvent.user_id == user_id
                ))
                ev = existing.scalar_one_or_none()
                
                start_dt = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")
                end_dt = item.get("end", {}).get("dateTime") or item.get("end", {}).get("date")
                
                # Fix format date (scoate Z daca e cazul)
                if start_dt and 'T' in start_dt: start_dt = start_dt.replace('Z', '')
                if end_dt and 'T' in end_dt: end_dt = end_dt.replace('Z', '')

                if not ev:
                    ev = CalendarEvent(
                        user_id=user_id,
                        provider="google",
                        external_id=ext_id,
                        title=item.get("summary", "No Title"),
                        start_time=datetime.fromisoformat(start_dt),
                        end_time=datetime.fromisoformat(end_dt)
                    )
                    self.db.add(ev)
                else:
                    ev.title = item.get("summary", "No Title")
                
                synced.append(ev)
            
            await self.db.commit()
            return synced

        except Exception as e:
            logger.error(f"Sync Error: {e}")
            raise CalendarProviderError(f"Sync failed: {e}")

    async def create_google_event(self, oauth_token: str, refresh_token: str, event: CalendarEvent):
        url = f"{GOOGLE_API_BASE}/calendars/primary/events"
        headers = {"Authorization": f"Bearer {oauth_token}"}
        body = {
            "summary": event.title,
            "description": event.description,
            "start": {"dateTime": event.start_time.isoformat()},
            "end": {"dateTime": event.end_time.isoformat()}
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=body)
            if resp.status_code == 200:
                return resp.json().get("id")
            else:
                logger.error(f"Create Error: {resp.text}")
                return None
    
    # Placeholder methods for compatibility
    async def sync_outlook_calendar(self, *args, **kwargs): return []
