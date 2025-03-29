"""MusicBrainz-specific API error classes."""

from plexomatic.api.errors import (
    APIError,
    APIAuthenticationError,
    APIRequestError,
    APIRateLimitError,
    APINotFoundError,
)


class MusicBrainzError(APIError):
    """Base class for all MusicBrainz API errors."""

    pass


class MusicBrainzAuthenticationError(APIAuthenticationError, MusicBrainzError):
    """Raised when authentication with MusicBrainz API fails."""

    pass


class MusicBrainzRequestError(APIRequestError, MusicBrainzError):
    """Raised when a MusicBrainz API request fails."""

    pass


class MusicBrainzRateLimitError(APIRateLimitError, MusicBrainzError):
    """Raised when MusicBrainz API rate limit is exceeded."""

    pass


class MusicBrainzNotFoundError(APINotFoundError, MusicBrainzError):
    """Raised when a resource is not found on the MusicBrainz API."""

    pass


class MusicBrainzSearchError(MusicBrainzRequestError):
    """Raised when a search query to MusicBrainz fails."""

    def __init__(self, message: str, query: str = None, status_code: int = None):
        """Initialize the search error.

        Args:
            message: The error message.
            query: The search query that failed.
            status_code: Optional HTTP status code.
        """
        self.query = query
        super().__init__(message, status_code)
