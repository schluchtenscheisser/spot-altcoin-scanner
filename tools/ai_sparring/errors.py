from __future__ import annotations


class SparringError(Exception):
    """Base class for ai_sparring runtime errors."""


class PreflightValidationError(SparringError):
    """Raised when required configuration/context checks fail before runtime."""


class FatalProviderError(SparringError):
    """Raised for non-retryable provider failures."""


class TransientProviderError(SparringError):
    """Raised for retryable provider failures."""
