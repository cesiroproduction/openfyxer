"""Custom exceptions for OpenFyxer."""

from typing import Any, Dict, Optional


class OpenFyxerException(Exception):
    """Base exception for OpenFyxer."""

    def __init__(
        self,
        message: str = "An error occurred",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(OpenFyxerException):
    """Authentication related errors."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class AuthorizationError(OpenFyxerException):
    """Authorization related errors."""

    def __init__(self, message: str = "Not authorized"):
        super().__init__(message)


class ValidationError(OpenFyxerException):
    """Validation related errors."""

    def __init__(
        self, message: str = "Validation failed", details: Optional[Dict] = None
    ):
        super().__init__(message, details)


class NotFoundError(OpenFyxerException):
    """Resource not found errors."""

    def __init__(self, resource: str = "Resource", identifier: str = ""):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} '{identifier}' not found"
        super().__init__(message)


class EmailProviderError(OpenFyxerException):
    """Email provider related errors."""

    def __init__(self, provider: str, message: str = "Email provider error"):
        super().__init__(f"{provider}: {message}")


class CalendarProviderError(OpenFyxerException):
    """Calendar provider related errors."""

    def __init__(self, provider: str, message: str = "Calendar provider error"):
        super().__init__(f"{provider}: {message}")


class LLMError(OpenFyxerException):
    """LLM related errors."""

    def __init__(self, provider: str, message: str = "LLM error"):
        super().__init__(f"{provider}: {message}")


class RAGError(OpenFyxerException):
    """RAG/Knowledge base related errors."""

    def __init__(self, message: str = "RAG error"):
        super().__init__(message)


class TranscriptionError(OpenFyxerException):
    """Speech-to-text transcription errors."""

    def __init__(self, message: str = "Transcription failed"):
        super().__init__(message)


class NotificationError(OpenFyxerException):
    """Notification delivery errors."""

    def __init__(self, channel: str, message: str = "Notification failed"):
        super().__init__(f"{channel}: {message}")


class RateLimitError(OpenFyxerException):
    """Rate limit exceeded errors."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message)


class ConfigurationError(OpenFyxerException):
    """Configuration related errors."""

    def __init__(self, message: str = "Configuration error"):
        super().__init__(message)
