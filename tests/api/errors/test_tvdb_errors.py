"""Test cases for the TVDB-specific API error classes."""

from plexomatic.api.errors import (
    APIError,
    APIAuthenticationError,
    APIRequestError,
    APIRateLimitError,
    APINotFoundError,
)
from plexomatic.api.errors.tvdb import (
    TVDBError,
    TVDBAuthenticationError,
    TVDBRequestError,
    TVDBRateLimitError,
    TVDBNotFoundError,
)


class TestTVDBErrors:
    """Test cases for the TVDB-specific API error classes."""

    def test_tvdb_error_base_class(self) -> None:
        """Test the base TVDBError class."""
        error = TVDBError("TVDB error message")
        assert isinstance(error, APIError)
        assert str(error) == "TVDB error message"
        assert error.message == "TVDB error message"
        assert error.status_code is None

    def test_tvdb_authentication_error(self) -> None:
        """Test the TVDBAuthenticationError class."""
        error = TVDBAuthenticationError("Auth error", 401)
        assert isinstance(error, APIAuthenticationError)
        assert isinstance(error, TVDBError)
        assert isinstance(error, APIError)
        assert str(error) == "Auth error"
        assert error.status_code == 401

    def test_tvdb_request_error(self) -> None:
        """Test the TVDBRequestError class."""
        error = TVDBRequestError("Request error", 400)
        assert isinstance(error, APIRequestError)
        assert isinstance(error, TVDBError)
        assert isinstance(error, APIError)
        assert str(error) == "Request error"
        assert error.status_code == 400

    def test_tvdb_rate_limit_error(self) -> None:
        """Test the TVDBRateLimitError class."""
        error = TVDBRateLimitError("Rate limited", 30, 429)
        assert isinstance(error, APIRateLimitError)
        assert isinstance(error, TVDBError)
        assert isinstance(error, APIError)
        assert str(error) == "Rate limited"
        assert error.status_code == 429
        assert error.retry_after == 30

    def test_tvdb_not_found_error(self) -> None:
        """Test the TVDBNotFoundError class."""
        error = TVDBNotFoundError("Show not found", "show-123")
        assert isinstance(error, APINotFoundError)
        assert isinstance(error, TVDBError)
        assert isinstance(error, APIError)
        assert str(error) == "Show not found"
        assert error.status_code == 404
        assert error.resource_id == "show-123"

    def test_error_catch_as_parent(self) -> None:
        """Test catching TVDB errors as their parent classes."""
        # Catch as TVDBError
        try:
            raise TVDBRateLimitError("Rate limited", 30)
        except TVDBError as e:
            assert isinstance(e, TVDBRateLimitError)
            assert e.retry_after == 30

        # Catch as APIRateLimitError
        try:
            raise TVDBRateLimitError("Rate limited", 30)
        except APIRateLimitError as e:
            assert isinstance(e, TVDBRateLimitError)
            assert e.retry_after == 30

        # Catch as APIError
        try:
            raise TVDBNotFoundError("Show not found", "show-123")
        except APIError as e:
            assert isinstance(e, TVDBNotFoundError)
            assert e.resource_id == "show-123"
