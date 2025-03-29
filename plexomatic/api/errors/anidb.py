"""AniDB-specific API error classes."""

from plexomatic.api.errors import (
    APIError,
    APIAuthenticationError,
    APIRequestError,
    APIRateLimitError,
    APINotFoundError,
    APIConnectionError,
)


class AniDBError(APIError):
    """Base class for all AniDB API errors."""

    pass


class AniDBAuthenticationError(APIAuthenticationError, AniDBError):
    """Raised when authentication with AniDB API fails."""

    pass


class AniDBRequestError(APIRequestError, AniDBError):
    """Raised when an AniDB API request fails."""

    pass


class AniDBRateLimitError(APIRateLimitError, AniDBError):
    """Raised when AniDB API rate limit is exceeded."""

    pass


class AniDBNotFoundError(APINotFoundError, AniDBError):
    """Raised when a resource is not found on the AniDB API."""

    pass


class AniDBConnectionError(APIConnectionError, AniDBError):
    """Raised when there is a connection error with AniDB."""

    pass


# UDP Protocol specific errors
class AniDBUDPError(AniDBError):
    """Base class for UDP protocol specific errors."""

    def __init__(self, message: str, code: int, status_code: int = None):
        """Initialize the UDP error.

        Args:
            message: The error message.
            code: The UDP protocol error code.
            status_code: Optional HTTP status code equivalent.
        """
        self.code = code
        super().__init__(message, status_code)


class AniDBBannedError(AniDBUDPError):
    """Raised when the client is banned from AniDB."""

    pass


class AniDBInvalidSessionError(AniDBUDPError):
    """Raised when the session is invalid or expired."""

    pass


class AniDBServerError(AniDBUDPError):
    """Raised when AniDB server returns an error."""

    pass
