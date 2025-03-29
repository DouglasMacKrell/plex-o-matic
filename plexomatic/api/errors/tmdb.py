"""TMDB-specific API error classes."""

from plexomatic.api.errors import (
    APIError,
    APIAuthenticationError,
    APIRequestError,
    APIRateLimitError,
    APINotFoundError,
)


class TMDBError(APIError):
    """Base class for all TMDB API errors."""

    pass


class TMDBAuthenticationError(APIAuthenticationError, TMDBError):
    """Raised when authentication with TMDB API fails."""

    pass


class TMDBRequestError(APIRequestError, TMDBError):
    """Raised when a TMDB API request fails."""

    pass


class TMDBRateLimitError(APIRateLimitError, TMDBError):
    """Raised when TMDB API rate limit is exceeded."""

    pass


class TMDBNotFoundError(APINotFoundError, TMDBError):
    """Raised when a resource is not found on the TMDB API."""

    pass
