"""
Unit tests for prompt generation logic.
Tests the generation of prompts for LLM interactions.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestPromptGeneration:
    """Tests for prompt generation functionality."""

    @pytest.fixture
    def email_context(self):
        """Sample email context for draft generation."""
        return {
            "subject": "Question about project timeline",
            "sender": "client@customer.com",
            "sender_name": "John Smith",
            "body": "Hi, I wanted to follow up on our discussion. When will the project be completed?",
            "received_at": "2024-01-15 10:30:00",
            "thread_history": [
                {
                    "sender": "me@company.com",
                    "body": "We are working on it and will update you soon.",
                    "date": "2024-01-14 15:00:00",
                }
            ],
        }

    @pytest.fixture
    def user_style_profile(self):
        """Sample user writing style profile."""
        return {
            "tone": "professional",
            "formality": "formal",
            "greeting_style": "Dear [Name],",
            "closing_style": "Best regards,",
            "signature": "John Doe\nProject Manager",
            "typical_length": "medium",
            "language_preference": "en",
        }

    def test_draft_prompt_generation(self, email_context, user_style_profile):
        """Test generation of draft email prompt."""
        prompt = self._generate_draft_prompt(email_context, user_style_profile)

        assert "Question about project timeline" in prompt
        assert "client@customer.com" in prompt
        assert "professional" in prompt.lower() or "formal" in prompt.lower()
        assert len(prompt) > 100

    def _generate_draft_prompt(self, email_context: dict, style_profile: dict) -> str:
        """Generate a prompt for draft email generation."""
        prompt = f"""Generate a professional email reply based on the following context:

Original Email:
- Subject: {email_context['subject']}
- From: {email_context['sender']} ({email_context.get('sender_name', 'Unknown')})
- Received: {email_context['received_at']}
- Content: {email_context['body']}

Writing Style Guidelines:
- Tone: {style_profile['tone']}
- Formality: {style_profile['formality']}
- Greeting: {style_profile['greeting_style']}
- Closing: {style_profile['closing_style']}
- Typical Length: {style_profile['typical_length']}

Please generate a reply that:
1. Addresses the sender's question or concern
2. Maintains the specified tone and formality
3. Is concise but complete
4. Uses the appropriate greeting and closing

Reply:"""
        return prompt

    def test_classification_prompt_generation(self):
        """Test generation of email classification prompt."""
        email = {
            "subject": "URGENT: Server maintenance required",
            "body": "The server needs immediate attention. Please respond ASAP.",
            "sender": "ops@company.com",
        }

        prompt = self._generate_classification_prompt(email)

        assert "URGENT" in prompt
        assert "server" in prompt.lower()
        assert "urgent" in prompt.lower() or "to_respond" in prompt.lower()

    def _generate_classification_prompt(self, email: dict) -> str:
        """Generate a prompt for email classification."""
        prompt = f"""Classify the following email into one of these categories:
- urgent: Requires immediate attention or action
- to_respond: Requires a response but not urgent
- fyi: Informational, no response needed
- newsletter: Marketing or newsletter content
- spam: Unwanted or suspicious content

Email:
Subject: {email['subject']}
From: {email['sender']}
Body: {email['body']}

Classification (respond with only the category name):"""
        return prompt

    def test_summarization_prompt_generation(self):
        """Test generation of meeting summarization prompt."""
        transcript = """
        Alice: Let's discuss the Q4 goals.
        Bob: I think we should focus on customer retention.
        Alice: Good point. What about new features?
        Bob: We can prioritize the dashboard redesign.
        Alice: Agreed. Let's set the deadline for end of November.
        """

        prompt = self._generate_summarization_prompt(transcript)

        assert "Q4" in prompt or "goals" in prompt.lower()
        assert "summary" in prompt.lower() or "summarize" in prompt.lower()

    def _generate_summarization_prompt(self, transcript: str) -> str:
        """Generate a prompt for meeting summarization."""
        prompt = f"""Summarize the following meeting transcript. Include:
1. Executive Summary (2-3 sentences)
2. Key Discussion Points
3. Action Items (with assignees if mentioned)
4. Decisions Made
5. Next Steps

Transcript:
{transcript}

Summary:"""
        return prompt

    def test_rag_query_prompt_generation(self):
        """Test generation of RAG query prompt."""
        query = "What was discussed about the project deadline?"
        context_docs = [
            {"title": "Email: Project Update", "content": "The deadline is set for November 30."},
            {"title": "Meeting Notes", "content": "Team agreed to extend deadline by one week."},
        ]

        prompt = self._generate_rag_prompt(query, context_docs)

        assert "project deadline" in prompt.lower()
        assert "November 30" in prompt
        assert "context" in prompt.lower() or "documents" in prompt.lower()

    def _generate_rag_prompt(self, query: str, context_docs: list) -> str:
        """Generate a prompt for RAG-based Q&A."""
        context_text = "\n\n".join(
            f"Document: {doc['title']}\nContent: {doc['content']}"
            for doc in context_docs
        )

        prompt = f"""Answer the following question based on the provided context documents.
If the answer cannot be found in the context, say "I don't have enough information to answer this question."

Context Documents:
{context_text}

Question: {query}

Answer:"""
        return prompt

    def test_follow_up_email_prompt_generation(self):
        """Test generation of follow-up email prompt."""
        meeting_summary = {
            "title": "Project Review Meeting",
            "date": "2024-01-15",
            "participants": ["alice@company.com", "bob@company.com"],
            "summary": "Discussed Q4 goals and set deadline for November 30.",
            "action_items": [
                "Alice: Complete dashboard redesign",
                "Bob: Prepare customer retention report",
            ],
        }

        prompt = self._generate_follow_up_prompt(meeting_summary)

        assert "Project Review Meeting" in prompt
        assert "action items" in prompt.lower()
        assert "November 30" in prompt or "deadline" in prompt.lower()

    def _generate_follow_up_prompt(self, meeting_summary: dict) -> str:
        """Generate a prompt for follow-up email after meeting."""
        action_items_text = "\n".join(f"- {item}" for item in meeting_summary["action_items"])

        prompt = f"""Generate a professional follow-up email for the following meeting:

Meeting: {meeting_summary['title']}
Date: {meeting_summary['date']}
Participants: {', '.join(meeting_summary['participants'])}

Summary: {meeting_summary['summary']}

Action Items:
{action_items_text}

The email should:
1. Thank participants for attending
2. Summarize key discussion points
3. List action items with owners
4. Mention next steps or follow-up meeting if applicable

Follow-up Email:"""
        return prompt

    def test_prompt_language_adaptation(self):
        """Test that prompts can be adapted for different languages."""
        email_ro = {
            "subject": "Întrebare despre proiect",
            "body": "Bună ziua, când va fi gata proiectul?",
            "sender": "client@customer.ro",
        }

        prompt_en = self._generate_draft_prompt_with_language(email_ro, "en")
        prompt_ro = self._generate_draft_prompt_with_language(email_ro, "ro")

        assert "English" in prompt_en or "en" in prompt_en.lower()
        assert "Romanian" in prompt_ro or "ro" in prompt_ro.lower()

    def _generate_draft_prompt_with_language(self, email: dict, language: str) -> str:
        """Generate a draft prompt with language specification."""
        lang_name = "English" if language == "en" else "Romanian"
        prompt = f"""Generate a reply to the following email in {lang_name}:

Subject: {email['subject']}
From: {email['sender']}
Body: {email['body']}

Reply in {lang_name}:"""
        return prompt

    def test_tone_variations(self):
        """Test prompt generation with different tone settings."""
        base_email = {
            "subject": "Meeting request",
            "body": "Can we schedule a call?",
            "sender": "partner@company.com",
        }

        tones = ["formal", "friendly", "professional", "concise"]

        for tone in tones:
            prompt = self._generate_draft_prompt_with_tone(base_email, tone)
            assert tone in prompt.lower()

    def _generate_draft_prompt_with_tone(self, email: dict, tone: str) -> str:
        """Generate a draft prompt with specific tone."""
        prompt = f"""Generate a {tone} reply to:

Subject: {email['subject']}
Body: {email['body']}

Use a {tone} tone in your response.

Reply:"""
        return prompt
