"""Common error classes for API clients.

This module defines a hierarchy of exception classes that can be used by all API clients
to provide a consistent error handling experience.
"""

from typing import Optional


class APIError(Exception):
    """Base class for all API related errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        """Initialize the API error.

        Args:
            message: The error message.
            status_code: Optional HTTP status code associated with the error.
        """
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class APIConnectionError(APIError):
    """Raised when there is an error connecting to the API."""

    pass


class APITimeoutError(APIConnectionError):
    """Raised when an API request times out."""

    pass


class APIAuthenticationError(APIError):
    """Raised when authentication with an API fails."""

    pass


class APIRequestError(APIError):
    """Raised when an API request fails."""

    pass


class APIResponseError(APIError):
    """Raised when there is an error parsing the API response."""

    pass


class APIRateLimitError(APIError):
    """Raised when an API rate limit is exceeded."""

    def __init__(
        self, message: str, retry_after: Optional[int] = None, status_code: Optional[int] = 429
    ):
        """Initialize the rate limit error.

        Args:
            message: The error message.
            retry_after: Number of seconds to wait before retrying.
            status_code: HTTP status code (defaults to 429).
        """
        self.retry_after = retry_after
        super().__init__(message, status_code)


class APINotFoundError(APIRequestError):
    """Raised when a resource is not found on the API."""

    def __init__(
        self, message: str, resource_id: Optional[str] = None, status_code: Optional[int] = 404
    ):
        """Initialize the not found error.

        Args:
            message: The error message.
            resource_id: Optional ID of the resource that was not found.
            status_code: HTTP status code (defaults to 404).
        """
        self.resource_id = resource_id
        super().__init__(message, status_code)


class APIServerError(APIError):
    """Raised when the API server returns a 5XX error."""

    pass


class APIClientError(APIError):
    """Raised when there is a problem with the client configuration."""

    pass


class APIResourceNotAvailableError(APIError):
    """Raised when a requested resource (like a model) is not available."""

    pass
