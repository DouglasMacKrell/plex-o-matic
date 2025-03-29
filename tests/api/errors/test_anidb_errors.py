"""Test cases for the AniDB-specific API error classes."""

from plexomatic.api.errors import (
    APIError,
    APIAuthenticationError,
    APIRequestError,
    APIRateLimitError,
    APINotFoundError,
    APIConnectionError,
)
from plexomatic.api.errors.anidb import (
    AniDBError,
    AniDBAuthenticationError,
    AniDBRequestError,
    AniDBRateLimitError,
    AniDBNotFoundError,
    AniDBConnectionError,
    AniDBUDPError,
    AniDBBannedError,
    AniDBInvalidSessionError,
    AniDBServerError,
)


class TestAniDBErrors:
    """Test cases for the AniDB-specific API error classes."""

    def test_anidb_error_base_class(self) -> None:
        """Test the base AniDBError class."""
        error = AniDBError("AniDB error message")
        assert isinstance(error, APIError)
        assert str(error) == "AniDB error message"
        assert error.message == "AniDB error message"
        assert error.status_code is None

    def test_anidb_authentication_error(self) -> None:
        """Test the AniDBAuthenticationError class."""
        error = AniDBAuthenticationError("Auth error", 401)
        assert isinstance(error, APIAuthenticationError)
        assert isinstance(error, AniDBError)
        assert isinstance(error, APIError)
        assert str(error) == "Auth error"
        assert error.status_code == 401

    def test_anidb_request_error(self) -> None:
        """Test the AniDBRequestError class."""
        error = AniDBRequestError("Request error", 400)
        assert isinstance(error, APIRequestError)
        assert isinstance(error, AniDBError)
        assert isinstance(error, APIError)
        assert str(error) == "Request error"
        assert error.status_code == 400

    def test_anidb_rate_limit_error(self) -> None:
        """Test the AniDBRateLimitError class."""
        error = AniDBRateLimitError("Rate limited", 30, 429)
        assert isinstance(error, APIRateLimitError)
        assert isinstance(error, AniDBError)
        assert isinstance(error, APIError)
        assert str(error) == "Rate limited"
        assert error.status_code == 429
        assert error.retry_after == 30

    def test_anidb_not_found_error(self) -> None:
        """Test the AniDBNotFoundError class."""
        error = AniDBNotFoundError("Anime not found", "anime-123")
        assert isinstance(error, APINotFoundError)
        assert isinstance(error, AniDBError)
        assert isinstance(error, APIError)
        assert str(error) == "Anime not found"
        assert error.status_code == 404
        assert error.resource_id == "anime-123"

    def test_anidb_connection_error(self) -> None:
        """Test the AniDBConnectionError class."""
        error = AniDBConnectionError("Connection error")
        assert isinstance(error, APIConnectionError)
        assert isinstance(error, AniDBError)
        assert isinstance(error, APIError)
        assert str(error) == "Connection error"

    def test_anidb_udp_error(self) -> None:
        """Test the AniDBUDPError class."""
        error = AniDBUDPError("UDP error", 500)
        assert isinstance(error, AniDBError)
        assert isinstance(error, APIError)
        assert str(error) == "UDP error"
        assert error.code == 500
        assert error.status_code is None

        # With status code
        error = AniDBUDPError("UDP error", 500, 503)
        assert error.status_code == 503
        assert error.code == 500

    def test_anidb_banned_error(self) -> None:
        """Test the AniDBBannedError class."""
        error = AniDBBannedError("You are banned", 555)
        assert isinstance(error, AniDBUDPError)
        assert isinstance(error, AniDBError)
        assert isinstance(error, APIError)
        assert str(error) == "You are banned"
        assert error.code == 555

    def test_anidb_invalid_session_error(self) -> None:
        """Test the AniDBInvalidSessionError class."""
        error = AniDBInvalidSessionError("Invalid session", 501)
        assert isinstance(error, AniDBUDPError)
        assert isinstance(error, AniDBError)
        assert isinstance(error, APIError)
        assert str(error) == "Invalid session"
        assert error.code == 501

    def test_anidb_server_error(self) -> None:
        """Test the AniDBServerError class."""
        error = AniDBServerError("Server error", 600)
        assert isinstance(error, AniDBUDPError)
        assert isinstance(error, AniDBError)
        assert isinstance(error, APIError)
        assert str(error) == "Server error"
        assert error.code == 600

    def test_error_catch_as_parent(self) -> None:
        """Test catching AniDB errors as their parent classes."""
        # Catch as AniDBError
        try:
            raise AniDBRateLimitError("Rate limited", 30)
        except AniDBError as e:
            assert isinstance(e, AniDBRateLimitError)
            assert e.retry_after == 30

        # Catch as APIRateLimitError
        try:
            raise AniDBRateLimitError("Rate limited", 30)
        except APIRateLimitError as e:
            assert isinstance(e, AniDBRateLimitError)
            assert e.retry_after == 30

        # Catch UDP errors as AniDBError
        try:
            raise AniDBBannedError("You are banned", 555)
        except AniDBError as e:
            assert isinstance(e, AniDBBannedError)
            assert e.code == 555
