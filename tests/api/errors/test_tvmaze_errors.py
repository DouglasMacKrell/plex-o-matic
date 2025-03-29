"""Test cases for the TVMaze-specific API error classes."""

from plexomatic.api.errors import (
    APIError,
    APIAuthenticationError,
    APIRequestError,
    APIRateLimitError,
    APINotFoundError,
)
from plexomatic.api.errors.tvmaze import (
    TVMazeError,
    TVMazeAuthenticationError,
    TVMazeRequestError,
    TVMazeRateLimitError,
    TVMazeNotFoundError,
)


class TestTVMazeErrors:
    """Test cases for the TVMaze-specific API error classes."""

    def test_tvmaze_error_base_class(self) -> None:
        """Test the base TVMazeError class."""
        error = TVMazeError("TVMaze error message")
        assert isinstance(error, APIError)
        assert str(error) == "TVMaze error message"
        assert error.message == "TVMaze error message"
        assert error.status_code is None

    def test_tvmaze_authentication_error(self) -> None:
        """Test the TVMazeAuthenticationError class."""
        error = TVMazeAuthenticationError("Auth error", 401)
        assert isinstance(error, APIAuthenticationError)
        assert isinstance(error, TVMazeError)
        assert isinstance(error, APIError)
        assert str(error) == "Auth error"
        assert error.status_code == 401

    def test_tvmaze_request_error(self) -> None:
        """Test the TVMazeRequestError class."""
        error = TVMazeRequestError("Request error", 400)
        assert isinstance(error, APIRequestError)
        assert isinstance(error, TVMazeError)
        assert isinstance(error, APIError)
        assert str(error) == "Request error"
        assert error.status_code == 400

    def test_tvmaze_rate_limit_error(self) -> None:
        """Test the TVMazeRateLimitError class."""
        error = TVMazeRateLimitError("Rate limited", 30, 429)
        assert isinstance(error, APIRateLimitError)
        assert isinstance(error, TVMazeError)
        assert isinstance(error, APIError)
        assert str(error) == "Rate limited"
        assert error.status_code == 429
        assert error.retry_after == 30

    def test_tvmaze_not_found_error(self) -> None:
        """Test the TVMazeNotFoundError class."""
        error = TVMazeNotFoundError("Show not found", "show-123")
        assert isinstance(error, APINotFoundError)
        assert isinstance(error, TVMazeError)
        assert isinstance(error, APIError)
        assert str(error) == "Show not found"
        assert error.status_code == 404
        assert error.resource_id == "show-123"

    def test_error_catch_as_parent(self) -> None:
        """Test catching TVMaze errors as their parent classes."""
        # Catch as TVMazeError
        try:
            raise TVMazeRateLimitError("Rate limited", 30)
        except TVMazeError as e:
            assert isinstance(e, TVMazeRateLimitError)
            assert e.retry_after == 30

        # Catch as APIRateLimitError
        try:
            raise TVMazeRateLimitError("Rate limited", 30)
        except APIRateLimitError as e:
            assert isinstance(e, TVMazeRateLimitError)
            assert e.retry_after == 30

        # Catch as APIError
        try:
            raise TVMazeNotFoundError("Show not found", "show-123")
        except APIError as e:
            assert isinstance(e, TVMazeNotFoundError)
            assert e.resource_id == "show-123"
