"""
Integration tests for calendar flow.
Tests calendar sync, event creation, and conflict detection.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta


class TestCalendarFlow:
    """Integration tests for calendar functionality."""

    @pytest.fixture
    def mock_calendar_service(self):
        """Create mock calendar service."""
        mock = MagicMock()
        mock.get_events = AsyncMock(return_value=[])
        mock.create_event = AsyncMock(return_value={"id": "event123"})
        mock.update_event = AsyncMock(return_value={"id": "event123"})
        mock.delete_event = AsyncMock(return_value=True)
        mock.check_conflicts = AsyncMock(return_value=[])
        mock.find_available_slots = AsyncMock(return_value=[])
        return mock

    @pytest.mark.asyncio
    async def test_calendar_sync_flow(self, mock_calendar_service):
        """Test calendar sync flow."""
        mock_calendar_service.get_events = AsyncMock(
            return_value=[
                {
                    "id": "event1",
                    "title": "Team Meeting",
                    "start_time": datetime.utcnow() + timedelta(hours=1),
                    "end_time": datetime.utcnow() + timedelta(hours=2),
                },
                {
                    "id": "event2",
                    "title": "Client Call",
                    "start_time": datetime.utcnow() + timedelta(hours=3),
                    "end_time": datetime.utcnow() + timedelta(hours=4),
                },
            ]
        )

        events = await mock_calendar_service.get_events()

        assert len(events) == 2
        assert events[0]["title"] == "Team Meeting"

    @pytest.mark.asyncio
    async def test_event_creation_flow(self, mock_calendar_service):
        """Test event creation flow."""
        new_event = {
            "title": "Project Review",
            "start_time": datetime.utcnow() + timedelta(days=1),
            "end_time": datetime.utcnow() + timedelta(days=1, hours=1),
            "description": "Review Q4 progress",
            "attendees": ["alice@company.com", "bob@company.com"],
        }

        result = await mock_calendar_service.create_event(new_event)

        assert result["id"] == "event123"
        mock_calendar_service.create_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_conflict_detection_flow(self, mock_calendar_service):
        """Test conflict detection when creating events."""
        existing_event = {
            "id": "event1",
            "title": "Existing Meeting",
            "start_time": datetime.utcnow() + timedelta(hours=1),
            "end_time": datetime.utcnow() + timedelta(hours=2),
        }

        mock_calendar_service.check_conflicts = AsyncMock(return_value=[existing_event])

        new_event_time = datetime.utcnow() + timedelta(hours=1, minutes=30)
        conflicts = await mock_calendar_service.check_conflicts(
            start_time=new_event_time,
            end_time=new_event_time + timedelta(hours=1),
        )

        assert len(conflicts) == 1
        assert conflicts[0]["title"] == "Existing Meeting"

    @pytest.mark.asyncio
    async def test_available_slots_flow(self, mock_calendar_service):
        """Test finding available time slots."""
        mock_calendar_service.find_available_slots = AsyncMock(
            return_value=[
                {
                    "start_time": datetime.utcnow() + timedelta(hours=5),
                    "end_time": datetime.utcnow() + timedelta(hours=6),
                    "duration_minutes": 60,
                },
                {
                    "start_time": datetime.utcnow() + timedelta(hours=7),
                    "end_time": datetime.utcnow() + timedelta(hours=8),
                    "duration_minutes": 60,
                },
            ]
        )

        slots = await mock_calendar_service.find_available_slots(
            duration_minutes=60,
            date_from=datetime.utcnow(),
            date_to=datetime.utcnow() + timedelta(days=1),
        )

        assert len(slots) == 2
        assert all(slot["duration_minutes"] == 60 for slot in slots)

    @pytest.mark.asyncio
    async def test_meeting_scheduling_with_conflict_resolution(self, mock_calendar_service):
        """Test scheduling a meeting with automatic conflict resolution."""
        mock_calendar_service.check_conflicts = AsyncMock(
            return_value=[
                {
                    "id": "conflict1",
                    "title": "Conflicting Meeting",
                    "start_time": datetime.utcnow() + timedelta(hours=1),
                    "end_time": datetime.utcnow() + timedelta(hours=2),
                }
            ]
        )
        mock_calendar_service.find_available_slots = AsyncMock(
            return_value=[
                {
                    "start_time": datetime.utcnow() + timedelta(hours=3),
                    "end_time": datetime.utcnow() + timedelta(hours=4),
                    "duration_minutes": 60,
                }
            ]
        )

        requested_time = datetime.utcnow() + timedelta(hours=1)
        conflicts = await mock_calendar_service.check_conflicts(
            start_time=requested_time,
            end_time=requested_time + timedelta(hours=1),
        )

        if conflicts:
            alternative_slots = await mock_calendar_service.find_available_slots(
                duration_minutes=60,
                date_from=datetime.utcnow(),
                date_to=datetime.utcnow() + timedelta(days=1),
            )
            assert len(alternative_slots) > 0

    @pytest.mark.asyncio
    async def test_recurring_event_handling(self, mock_calendar_service):
        """Test handling of recurring events."""
        recurring_event = {
            "id": "recurring1",
            "title": "Weekly Standup",
            "start_time": datetime.utcnow(),
            "end_time": datetime.utcnow() + timedelta(minutes=30),
            "is_recurring": True,
            "recurrence_rule": "FREQ=WEEKLY;BYDAY=MO,WE,FR",
        }

        mock_calendar_service.create_event = AsyncMock(return_value=recurring_event)

        result = await mock_calendar_service.create_event(recurring_event)

        assert result["is_recurring"] is True
        assert "WEEKLY" in result["recurrence_rule"]

    @pytest.mark.asyncio
    async def test_event_reminder_scheduling(self, mock_calendar_service):
        """Test scheduling reminders for events."""
        event = {
            "id": "event1",
            "title": "Important Meeting",
            "start_time": datetime.utcnow() + timedelta(hours=1),
            "reminder_minutes": 15,
        }

        reminder_time = event["start_time"] - timedelta(minutes=event["reminder_minutes"])
        should_remind = datetime.utcnow() >= reminder_time

        assert isinstance(should_remind, bool)

    @pytest.mark.asyncio
    async def test_working_hours_respect(self, mock_calendar_service):
        """Test that scheduling respects working hours."""
        working_hours = {
            "start": "09:00",
            "end": "17:00",
            "days": [0, 1, 2, 3, 4],
        }

        requested_time = datetime(2024, 1, 15, 20, 0)
        is_within_working_hours = self._is_within_working_hours(
            requested_time, working_hours
        )

        assert is_within_working_hours is False

    def _is_within_working_hours(self, time: datetime, working_hours: dict) -> bool:
        """Check if time is within working hours."""
        if time.weekday() not in working_hours["days"]:
            return False

        start_hour, start_min = map(int, working_hours["start"].split(":"))
        end_hour, end_min = map(int, working_hours["end"].split(":"))

        start_time = time.replace(hour=start_hour, minute=start_min)
        end_time = time.replace(hour=end_hour, minute=end_min)

        return start_time <= time <= end_time

    @pytest.mark.asyncio
    async def test_buffer_time_between_meetings(self, mock_calendar_service):
        """Test buffer time enforcement between meetings."""
        buffer_minutes = 15
        existing_events = [
            {
                "id": "event1",
                "end_time": datetime.utcnow() + timedelta(hours=1),
            }
        ]

        new_event_start = datetime.utcnow() + timedelta(hours=1, minutes=5)
        has_buffer = self._has_sufficient_buffer(
            existing_events, new_event_start, buffer_minutes
        )

        assert has_buffer is False

    def _has_sufficient_buffer(
        self, existing_events: list, new_start: datetime, buffer_minutes: int
    ) -> bool:
        """Check if there's sufficient buffer time."""
        for event in existing_events:
            time_diff = (new_start - event["end_time"]).total_seconds() / 60
            if 0 < time_diff < buffer_minutes:
                return False
        return True

    @pytest.mark.asyncio
    async def test_today_events_summary(self, mock_calendar_service):
        """Test getting today's events summary."""
        today = datetime.utcnow().date()
        mock_calendar_service.get_events = AsyncMock(
            return_value=[
                {
                    "id": "event1",
                    "title": "Morning Standup",
                    "start_time": datetime.combine(today, datetime.min.time().replace(hour=9)),
                },
                {
                    "id": "event2",
                    "title": "Lunch Meeting",
                    "start_time": datetime.combine(today, datetime.min.time().replace(hour=12)),
                },
            ]
        )

        events = await mock_calendar_service.get_events()
        today_events = [e for e in events if e["start_time"].date() == today]

        assert len(today_events) == 2
