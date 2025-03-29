"""TVDB-specific API error classes."""

from plexomatic.api.errors import (
    APIError,
    APIAuthenticationError,
    APIRequestError,
    APIRateLimitError,
    APINotFoundError,
)


class TVDBError(APIError):
    """Base class for all TVDB API errors."""

    pass


class TVDBAuthenticationError(APIAuthenticationError, TVDBError):
    """Raised when authentication with TVDB API fails."""

    pass


class TVDBRequestError(APIRequestError, TVDBError):
    """Raised when a TVDB API request fails."""

    pass


class TVDBRateLimitError(APIRateLimitError, TVDBError):
    """Raised when TVDB API rate limit is exceeded."""

    pass


class TVDBNotFoundError(APINotFoundError, TVDBError):
    """Raised when a resource is not found on the TVDB API."""

    pass
