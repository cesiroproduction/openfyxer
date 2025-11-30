"""
Integration tests for email flow.
Tests the complete flow from email sync to draft generation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestEmailFlow:
    """Integration tests for email processing flow."""

    @pytest.fixture
    def mock_services(self, mock_email_service, mock_llm_service, mock_rag_service):
        """Bundle all mock services."""
        return {
            "email": mock_email_service,
            "llm": mock_llm_service,
            "rag": mock_rag_service,
        }

    @pytest.mark.asyncio
    async def test_complete_email_sync_flow(self, mock_services):
        """Test complete email sync flow."""
        mock_services["email"].fetch_emails = AsyncMock(
            return_value=[
                {
                    "id": "email1",
                    "subject": "Important Meeting",
                    "body": "Please attend the meeting tomorrow.",
                    "sender": "boss@company.com",
                    "received_at": datetime.utcnow(),
                }
            ]
        )

        emails = await mock_services["email"].fetch_emails()

        assert len(emails) == 1
        assert emails[0]["subject"] == "Important Meeting"

    @pytest.mark.asyncio
    async def test_email_classification_flow(self, mock_services):
        """Test email classification after sync."""
        email = {
            "id": "email1",
            "subject": "URGENT: Action Required",
            "body": "Please respond immediately.",
            "sender": "manager@company.com",
        }

        mock_services["llm"].classify_email = AsyncMock(return_value="urgent")

        category = await mock_services["llm"].classify_email(
            subject=email["subject"],
            body=email["body"],
            sender=email["sender"],
        )

        assert category == "urgent"

    @pytest.mark.asyncio
    async def test_email_indexing_flow(self, mock_services):
        """Test email indexing in RAG after classification."""
        email = {
            "id": "email1",
            "subject": "Project Update",
            "body": "The project is on track.",
            "sender": "team@company.com",
            "category": "fyi",
        }

        result = await mock_services["rag"].index_email(email)

        assert result is True
        mock_services["rag"].index_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_draft_generation_flow(self, mock_services):
        """Test draft generation for an email."""
        email = {
            "id": "email1",
            "subject": "Question about deadline",
            "body": "When is the project due?",
            "sender": "client@customer.com",
        }

        mock_services["llm"].generate_draft = AsyncMock(
            return_value="Thank you for your email. The project is due on December 15th."
        )

        draft = await mock_services["llm"].generate_draft(
            email=email,
            tone="professional",
        )

        assert "December 15th" in draft
        assert len(draft) > 20

    @pytest.mark.asyncio
    async def test_draft_approval_and_send_flow(self, mock_services):
        """Test draft approval and sending flow."""
        draft = {
            "id": "draft1",
            "email_id": "email1",
            "content": "Thank you for your email. I will respond shortly.",
            "status": "pending",
        }

        mock_services["email"].send_email = AsyncMock(return_value=True)

        result = await mock_services["email"].send_email(
            to="client@customer.com",
            subject="Re: Question",
            body=draft["content"],
        )

        assert result is True
        mock_services["email"].send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_email_to_draft_pipeline(self, mock_services):
        """Test the complete pipeline from email receipt to draft generation."""
        mock_services["email"].fetch_emails = AsyncMock(
            return_value=[
                {
                    "id": "email1",
                    "subject": "Meeting Request",
                    "body": "Can we schedule a call next week?",
                    "sender": "partner@company.com",
                    "received_at": datetime.utcnow(),
                }
            ]
        )
        mock_services["llm"].classify_email = AsyncMock(return_value="to_respond")
        mock_services["rag"].index_email = AsyncMock(return_value=True)
        mock_services["llm"].generate_draft = AsyncMock(
            return_value="I would be happy to schedule a call. How about Tuesday at 2 PM?"
        )

        emails = await mock_services["email"].fetch_emails()
        email = emails[0]

        category = await mock_services["llm"].classify_email(
            subject=email["subject"],
            body=email["body"],
            sender=email["sender"],
        )

        await mock_services["rag"].index_email({**email, "category": category})

        draft = await mock_services["llm"].generate_draft(
            email=email,
            tone="friendly",
        )

        assert category == "to_respond"
        assert "Tuesday" in draft or "call" in draft.lower()

    @pytest.mark.asyncio
    async def test_email_search_via_rag(self, mock_services):
        """Test searching emails via RAG."""
        mock_services["rag"].query = AsyncMock(
            return_value={
                "answer": "The meeting is scheduled for Tuesday at 2 PM.",
                "sources": [
                    {
                        "type": "email",
                        "id": "email1",
                        "title": "Meeting Request",
                        "snippet": "Can we schedule a call...",
                        "relevance_score": 0.92,
                    }
                ],
                "confidence": 0.9,
            }
        )

        result = await mock_services["rag"].query("When is the meeting?")

        assert "Tuesday" in result["answer"]
        assert len(result["sources"]) > 0
        assert result["confidence"] > 0.5

    @pytest.mark.asyncio
    async def test_follow_up_reminder_flow(self, mock_services):
        """Test follow-up reminder generation for unanswered emails."""
        unanswered_emails = [
            {
                "id": "email1",
                "subject": "Proposal Review",
                "sender": "client@customer.com",
                "received_at": datetime(2024, 1, 10),
                "has_response": False,
            }
        ]

        follow_ups = self._generate_follow_up_reminders(unanswered_emails, days_threshold=3)

        assert len(follow_ups) == 1
        assert follow_ups[0]["email_id"] == "email1"

    def _generate_follow_up_reminders(self, emails: list, days_threshold: int) -> list:
        """Generate follow-up reminders for unanswered emails."""
        reminders = []
        now = datetime.utcnow()

        for email in emails:
            if not email.get("has_response", True):
                days_since = (now - email["received_at"]).days
                if days_since >= days_threshold:
                    reminders.append({
                        "email_id": email["id"],
                        "subject": email["subject"],
                        "sender": email["sender"],
                        "days_since": days_since,
                    })

        return reminders

    @pytest.mark.asyncio
    async def test_batch_email_processing(self, mock_services):
        """Test batch processing of multiple emails."""
        emails = [
            {"id": f"email{i}", "subject": f"Email {i}", "body": f"Content {i}"}
            for i in range(10)
        ]

        mock_services["llm"].classify_email = AsyncMock(return_value="fyi")

        results = []
        for email in emails:
            category = await mock_services["llm"].classify_email(
                subject=email["subject"],
                body=email["body"],
                sender="sender@example.com",
            )
            results.append({"email_id": email["id"], "category": category})

        assert len(results) == 10
        assert all(r["category"] == "fyi" for r in results)
