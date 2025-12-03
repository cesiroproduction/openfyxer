import asyncio
import os
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Ensure the FastAPI app and SQLAlchemy engine use the in-memory SQLite database during tests.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.security import create_access_token, get_password_hash
from app.models.calendar_event import CalendarEvent
from app.models.document import Document
from app.models.email import Email
from app.models.email_account import EmailAccount
from app.models.meeting import Meeting
from app.models.user import User


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def async_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user() -> dict:
    return {
        "id": str(uuid.uuid4()),
        "email": "test@example.com",
        "full_name": "Test User",
        "hashed_password": get_password_hash("testpassword123"),
        "is_active": True,
        "two_factor_enabled": False,
    }


@pytest.fixture
def test_user_token(test_user) -> str:
    return create_access_token(subject=test_user["id"])


@pytest.fixture
def auth_headers(test_user_token) -> dict:
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def sample_email() -> dict:
    return {
        "id": str(uuid.uuid4()),
        "message_id": "<test123@example.com>",
        "thread_id": "thread123",
        "subject": "Urgent: Project deadline tomorrow",
        "sender": "boss@company.com",
        "recipients": ["test@example.com"],
        "body_text": "Please complete the project by tomorrow. This is very important.",
        "body_html": "<p>Please complete the project by tomorrow. This is very important.</p>",
        "received_at": datetime.utcnow(),
        "is_read": False,
        "is_starred": False,
        "is_archived": False,
        "has_attachments": False,
    }


@pytest.fixture
def sample_calendar_event() -> dict:
    return {
        "id": str(uuid.uuid4()),
        "title": "Team Meeting",
        "description": "Weekly team sync",
        "start_time": datetime.utcnow() + timedelta(hours=1),
        "end_time": datetime.utcnow() + timedelta(hours=2),
        "timezone": "UTC",
        "location": "Conference Room A",
        "is_all_day": False,
        "is_recurring": False,
        "status": "confirmed",
    }


@pytest.fixture
def sample_meeting() -> dict:
    return {
        "id": str(uuid.uuid4()),
        "title": "Project Review",
        "description": "Review Q4 project progress",
        "meeting_date": datetime.utcnow(),
        "participants": ["alice@example.com", "bob@example.com"],
        "status": "pending",
    }


@pytest.fixture
def mock_llm_service():
    mock = MagicMock()
    mock.generate = AsyncMock(return_value="This is a generated response.")
    mock.classify_email = AsyncMock(return_value="urgent")
    mock.generate_draft = AsyncMock(
        return_value="Thank you for your email. I will complete the project by tomorrow."
    )
    mock.summarize = AsyncMock(
        return_value="Meeting summary: Discussed project progress and next steps."
    )
    return mock


@pytest.fixture
def mock_rag_service():
    mock = MagicMock()
    mock.query = AsyncMock(
        return_value={
            "answer": "Based on the documents, the project deadline is tomorrow.",
            "sources": [
                {
                    "type": "email",
                    "id": "123",
                    "title": "Project Update",
                    "snippet": "Deadline is tomorrow",
                    "relevance_score": 0.95,
                }
            ],
            "confidence": 0.9,
        }
    )
    mock.index_email = AsyncMock(return_value=True)
    mock.index_document = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_email_service():
    mock = MagicMock()
    mock.fetch_emails = AsyncMock(return_value=[])
    mock.send_email = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_calendar_service():
    mock = MagicMock()
    mock.get_events = AsyncMock(return_value=[])
    mock.create_event = AsyncMock(return_value={"id": "event123"})
    return mock


@pytest.fixture
def mock_transcription_service():
    mock = MagicMock()
    mock.transcribe = AsyncMock(
        return_value={
            "text": "This is the transcribed text from the meeting.",
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "This is the transcribed text"},
                {"start": 5.0, "end": 10.0, "text": "from the meeting."},
            ],
            "language": "en",
        }
    )
    return mock
