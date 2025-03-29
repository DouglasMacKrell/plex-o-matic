"""TVMaze-specific API error classes."""

from plexomatic.api.errors import (
    APIError,
    APIAuthenticationError,
    APIRequestError,
    APIRateLimitError,
    APINotFoundError,
)


class TVMazeError(APIError):
    """Base class for all TVMaze API errors."""

    pass


class TVMazeAuthenticationError(APIAuthenticationError, TVMazeError):
    """Raised when authentication with TVMaze API fails."""

    pass


class TVMazeRequestError(APIRequestError, TVMazeError):
    """Raised when a TVMaze API request fails."""

    pass


class TVMazeRateLimitError(APIRateLimitError, TVMazeError):
    """Raised when TVMaze API rate limit is exceeded."""

    pass


class TVMazeNotFoundError(APINotFoundError, TVMazeError):
    """Raised when a resource is not found on the TVMaze API."""

    pass
