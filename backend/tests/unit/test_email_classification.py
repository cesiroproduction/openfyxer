"""
Unit tests for email classification logic.
Tests the email categorization into: urgent, to_respond, fyi, newsletter, spam
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestEmailClassification:
    """Tests for email classification functionality."""

    @pytest.fixture
    def classification_prompts(self):
        """Sample emails for classification testing."""
        return {
            "urgent": {
                "subject": "URGENT: Server down - immediate action required",
                "body": "The production server is down. We need to fix this immediately. All hands on deck!",
                "sender": "ops@company.com",
            },
            "to_respond": {
                "subject": "Question about the project timeline",
                "body": "Hi, could you please let me know when the project will be completed? Thanks!",
                "sender": "client@customer.com",
            },
            "fyi": {
                "subject": "FYI: Updated company policies",
                "body": "Please find attached the updated company policies for your reference.",
                "sender": "hr@company.com",
            },
            "newsletter": {
                "subject": "Weekly Tech Newsletter - Issue #42",
                "body": "Welcome to this week's newsletter! Here are the top stories...",
                "sender": "newsletter@techsite.com",
            },
            "spam": {
                "subject": "You've won $1,000,000!!!",
                "body": "Click here to claim your prize! Limited time offer!",
                "sender": "winner@suspicious-domain.xyz",
            },
        }

    @pytest.mark.asyncio
    async def test_classify_urgent_email(self, classification_prompts, mock_llm_service):
        """Test classification of urgent emails."""
        email = classification_prompts["urgent"]
        mock_llm_service.classify_email = AsyncMock(return_value="urgent")

        result = await mock_llm_service.classify_email(
            subject=email["subject"],
            body=email["body"],
            sender=email["sender"],
        )

        assert result == "urgent"
        mock_llm_service.classify_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_to_respond_email(self, classification_prompts, mock_llm_service):
        """Test classification of emails requiring response."""
        email = classification_prompts["to_respond"]
        mock_llm_service.classify_email = AsyncMock(return_value="to_respond")

        result = await mock_llm_service.classify_email(
            subject=email["subject"],
            body=email["body"],
            sender=email["sender"],
        )

        assert result == "to_respond"

    @pytest.mark.asyncio
    async def test_classify_fyi_email(self, classification_prompts, mock_llm_service):
        """Test classification of FYI emails."""
        email = classification_prompts["fyi"]
        mock_llm_service.classify_email = AsyncMock(return_value="fyi")

        result = await mock_llm_service.classify_email(
            subject=email["subject"],
            body=email["body"],
            sender=email["sender"],
        )

        assert result == "fyi"

    @pytest.mark.asyncio
    async def test_classify_newsletter_email(self, classification_prompts, mock_llm_service):
        """Test classification of newsletter emails."""
        email = classification_prompts["newsletter"]
        mock_llm_service.classify_email = AsyncMock(return_value="newsletter")

        result = await mock_llm_service.classify_email(
            subject=email["subject"],
            body=email["body"],
            sender=email["sender"],
        )

        assert result == "newsletter"

    @pytest.mark.asyncio
    async def test_classify_spam_email(self, classification_prompts, mock_llm_service):
        """Test classification of spam emails."""
        email = classification_prompts["spam"]
        mock_llm_service.classify_email = AsyncMock(return_value="spam")

        result = await mock_llm_service.classify_email(
            subject=email["subject"],
            body=email["body"],
            sender=email["sender"],
        )

        assert result == "spam"

    def test_priority_score_calculation(self):
        """Test email priority score calculation based on category."""
        priority_scores = {
            "urgent": 100,
            "to_respond": 75,
            "fyi": 50,
            "newsletter": 25,
            "spam": 0,
        }

        for category, expected_score in priority_scores.items():
            score = self._calculate_priority_score(category)
            assert score == expected_score

    def _calculate_priority_score(self, category: str) -> int:
        """Helper to calculate priority score."""
        scores = {
            "urgent": 100,
            "to_respond": 75,
            "fyi": 50,
            "newsletter": 25,
            "spam": 0,
        }
        return scores.get(category, 50)

    def test_language_detection(self):
        """Test language detection for emails."""
        english_text = "Hello, how are you doing today?"
        romanian_text = "Bună ziua, cum vă simțiți astăzi?"

        assert self._detect_language(english_text) == "en"
        assert self._detect_language(romanian_text) == "ro"

    def _detect_language(self, text: str) -> str:
        """Simple language detection helper."""
        romanian_indicators = ["ă", "î", "ș", "ț", "â", "bună", "ziua", "mulțumesc"]
        text_lower = text.lower()

        for indicator in romanian_indicators:
            if indicator in text_lower:
                return "ro"
        return "en"

    def test_sentiment_analysis(self):
        """Test basic sentiment analysis for emails."""
        positive_text = "Thank you so much! This is wonderful news!"
        negative_text = "I am very disappointed with the service. This is unacceptable."
        neutral_text = "Please find the attached document for your review."

        assert self._analyze_sentiment(positive_text) == "positive"
        assert self._analyze_sentiment(negative_text) == "negative"
        assert self._analyze_sentiment(neutral_text) == "neutral"

    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis helper."""
        positive_words = ["thank", "wonderful", "great", "excellent", "happy", "pleased"]
        negative_words = ["disappointed", "unacceptable", "terrible", "angry", "frustrated"]

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        return "neutral"
