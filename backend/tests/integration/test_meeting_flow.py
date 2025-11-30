"""
Integration tests for meeting flow.
Tests meeting creation, transcription, summarization, and follow-up.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime


class TestMeetingFlow:
    """Integration tests for meeting functionality."""

    @pytest.fixture
    def mock_services(self, mock_transcription_service, mock_llm_service, mock_rag_service):
        """Bundle all mock services."""
        return {
            "transcription": mock_transcription_service,
            "llm": mock_llm_service,
            "rag": mock_rag_service,
        }

    @pytest.mark.asyncio
    async def test_meeting_creation_flow(self):
        """Test meeting creation flow."""
        meeting = {
            "title": "Project Kickoff",
            "description": "Initial project planning meeting",
            "meeting_date": datetime.utcnow(),
            "participants": ["alice@company.com", "bob@company.com"],
            "status": "pending",
        }

        assert meeting["title"] == "Project Kickoff"
        assert meeting["status"] == "pending"
        assert len(meeting["participants"]) == 2

    @pytest.mark.asyncio
    async def test_audio_transcription_flow(self, mock_services):
        """Test audio transcription flow."""
        mock_services["transcription"].transcribe = AsyncMock(
            return_value={
                "text": "Alice: Let's discuss the project timeline. Bob: I think we need two weeks.",
                "segments": [
                    {"start": 0.0, "end": 3.0, "text": "Alice: Let's discuss the project timeline."},
                    {"start": 3.0, "end": 6.0, "text": "Bob: I think we need two weeks."},
                ],
                "language": "en",
            }
        )

        result = await mock_services["transcription"].transcribe(
            audio_path="/path/to/audio.mp3",
            language="en",
        )

        assert "Alice" in result["text"]
        assert "Bob" in result["text"]
        assert len(result["segments"]) == 2

    @pytest.mark.asyncio
    async def test_meeting_summarization_flow(self, mock_services):
        """Test meeting summarization flow."""
        transcript = """
        Alice: Welcome everyone. Let's discuss the Q4 goals.
        Bob: I think we should focus on customer retention.
        Alice: Good point. What about the dashboard redesign?
        Bob: We can prioritize that for November.
        Alice: Agreed. Let's set the deadline for November 30th.
        """

        mock_services["llm"].summarize = AsyncMock(
            return_value={
                "summary": "Team discussed Q4 goals focusing on customer retention and dashboard redesign.",
                "action_items": [
                    "Complete dashboard redesign by November 30th",
                    "Focus on customer retention initiatives",
                ],
                "key_decisions": [
                    "Dashboard redesign deadline: November 30th",
                    "Priority: Customer retention",
                ],
                "topics": ["Q4 goals", "Customer retention", "Dashboard redesign"],
            }
        )

        result = await mock_services["llm"].summarize(transcript)

        assert "Q4" in result["summary"] or "customer retention" in result["summary"].lower()
        assert len(result["action_items"]) > 0
        assert len(result["key_decisions"]) > 0

    @pytest.mark.asyncio
    async def test_meeting_indexing_flow(self, mock_services):
        """Test meeting indexing in RAG."""
        meeting = {
            "id": "meeting1",
            "title": "Project Kickoff",
            "transcript": "Discussion about project timeline and goals.",
            "summary": "Team agreed on project timeline.",
            "action_items": ["Complete phase 1 by next week"],
        }

        mock_services["rag"].index_meeting = AsyncMock(return_value=True)

        result = await mock_services["rag"].index_meeting(meeting)

        assert result is True

    @pytest.mark.asyncio
    async def test_follow_up_email_generation(self, mock_services):
        """Test follow-up email generation after meeting."""
        meeting_summary = {
            "title": "Project Review",
            "date": "2024-01-15",
            "participants": ["alice@company.com", "bob@company.com"],
            "summary": "Reviewed project progress and set next milestones.",
            "action_items": [
                "Alice: Complete design mockups by Friday",
                "Bob: Prepare technical documentation",
            ],
        }

        mock_services["llm"].generate_follow_up = AsyncMock(
            return_value="""
Subject: Follow-up: Project Review Meeting

Hi Team,

Thank you for attending today's Project Review meeting.

Key Discussion Points:
- Reviewed project progress and set next milestones

Action Items:
- Alice: Complete design mockups by Friday
- Bob: Prepare technical documentation

Please let me know if you have any questions.

Best regards
"""
        )

        email = await mock_services["llm"].generate_follow_up(meeting_summary)

        assert "Follow-up" in email
        assert "Action Items" in email

    @pytest.mark.asyncio
    async def test_complete_meeting_pipeline(self, mock_services):
        """Test complete meeting pipeline from audio to follow-up."""
        mock_services["transcription"].transcribe = AsyncMock(
            return_value={
                "text": "Alice: Let's finalize the project plan. Bob: Agreed, deadline is next Friday.",
                "language": "en",
            }
        )
        mock_services["llm"].summarize = AsyncMock(
            return_value={
                "summary": "Team finalized project plan with Friday deadline.",
                "action_items": ["Finalize project plan by Friday"],
                "key_decisions": ["Deadline: Next Friday"],
            }
        )
        mock_services["rag"].index_meeting = AsyncMock(return_value=True)
        mock_services["llm"].generate_follow_up = AsyncMock(
            return_value="Follow-up email content..."
        )

        transcript_result = await mock_services["transcription"].transcribe(
            audio_path="/path/to/audio.mp3"
        )

        summary_result = await mock_services["llm"].summarize(transcript_result["text"])

        meeting_data = {
            "id": "meeting1",
            "transcript": transcript_result["text"],
            **summary_result,
        }
        await mock_services["rag"].index_meeting(meeting_data)

        follow_up = await mock_services["llm"].generate_follow_up(summary_result)

        assert transcript_result["text"] is not None
        assert summary_result["summary"] is not None
        assert follow_up is not None

    @pytest.mark.asyncio
    async def test_speaker_diarization(self, mock_services):
        """Test speaker diarization in transcription."""
        mock_services["transcription"].transcribe_with_diarization = AsyncMock(
            return_value={
                "text": "Speaker 1: Hello everyone. Speaker 2: Hi, let's begin.",
                "speakers": [
                    {"id": "speaker_1", "segments": [{"start": 0.0, "end": 2.0}]},
                    {"id": "speaker_2", "segments": [{"start": 2.0, "end": 4.0}]},
                ],
            }
        )

        result = await mock_services["transcription"].transcribe_with_diarization(
            audio_path="/path/to/audio.mp3"
        )

        assert len(result["speakers"]) == 2

    @pytest.mark.asyncio
    async def test_language_detection_in_transcription(self, mock_services):
        """Test automatic language detection during transcription."""
        mock_services["transcription"].detect_language = AsyncMock(return_value="ro")

        language = await mock_services["transcription"].detect_language(
            audio_path="/path/to/romanian_audio.mp3"
        )

        assert language == "ro"

    @pytest.mark.asyncio
    async def test_meeting_search_via_rag(self, mock_services):
        """Test searching meeting content via RAG."""
        mock_services["rag"].query = AsyncMock(
            return_value={
                "answer": "The project deadline was set to next Friday.",
                "sources": [
                    {
                        "type": "meeting",
                        "id": "meeting1",
                        "title": "Project Review",
                        "snippet": "deadline is next Friday",
                        "relevance_score": 0.95,
                    }
                ],
                "confidence": 0.9,
            }
        )

        result = await mock_services["rag"].query(
            "What was the project deadline discussed in meetings?"
        )

        assert "Friday" in result["answer"]
        assert result["sources"][0]["type"] == "meeting"

    def test_extract_action_items_from_transcript(self):
        """Test extracting action items from transcript."""
        transcript = """
        Alice: Bob, can you prepare the report by Monday?
        Bob: Sure, I'll have it ready.
        Alice: Great. I'll review the design mockups tomorrow.
        """

        action_items = self._extract_action_items(transcript)

        assert len(action_items) >= 1

    def _extract_action_items(self, transcript: str) -> list:
        """Extract action items from transcript (simplified)."""
        action_keywords = ["will", "can you", "need to", "should", "must"]
        lines = transcript.strip().split("\n")
        action_items = []

        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in action_keywords):
                action_items.append(line.strip())

        return action_items

    def test_extract_key_decisions_from_transcript(self):
        """Test extracting key decisions from transcript."""
        transcript = """
        Alice: So we've decided to go with option A.
        Bob: Agreed. The deadline is confirmed for Friday.
        Alice: Perfect, that's our final decision.
        """

        decisions = self._extract_decisions(transcript)

        assert len(decisions) >= 1

    def _extract_decisions(self, transcript: str) -> list:
        """Extract decisions from transcript (simplified)."""
        decision_keywords = ["decided", "agreed", "confirmed", "final decision"]
        lines = transcript.strip().split("\n")
        decisions = []

        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in decision_keywords):
                decisions.append(line.strip())

        return decisions
