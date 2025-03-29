"""Test cases for the TMDB-specific API error classes."""

from plexomatic.api.errors import (
    APIError,
    APIAuthenticationError,
    APIRequestError,
    APIRateLimitError,
    APINotFoundError,
)
from plexomatic.api.errors.tmdb import (
    TMDBError,
    TMDBAuthenticationError,
    TMDBRequestError,
    TMDBRateLimitError,
    TMDBNotFoundError,
)


class TestTMDBErrors:
    """Test cases for the TMDB-specific API error classes."""

    def test_tmdb_error_base_class(self) -> None:
        """Test the base TMDBError class."""
        error = TMDBError("TMDB error message")
        assert isinstance(error, APIError)
        assert str(error) == "TMDB error message"
        assert error.message == "TMDB error message"
        assert error.status_code is None

    def test_tmdb_authentication_error(self) -> None:
        """Test the TMDBAuthenticationError class."""
        error = TMDBAuthenticationError("Auth error", 401)
        assert isinstance(error, APIAuthenticationError)
        assert isinstance(error, TMDBError)
        assert isinstance(error, APIError)
        assert str(error) == "Auth error"
        assert error.status_code == 401

    def test_tmdb_request_error(self) -> None:
        """Test the TMDBRequestError class."""
        error = TMDBRequestError("Request error", 400)
        assert isinstance(error, APIRequestError)
        assert isinstance(error, TMDBError)
        assert isinstance(error, APIError)
        assert str(error) == "Request error"
        assert error.status_code == 400

    def test_tmdb_rate_limit_error(self) -> None:
        """Test the TMDBRateLimitError class."""
        error = TMDBRateLimitError("Rate limited", 30, 429)
        assert isinstance(error, APIRateLimitError)
        assert isinstance(error, TMDBError)
        assert isinstance(error, APIError)
        assert str(error) == "Rate limited"
        assert error.status_code == 429
        assert error.retry_after == 30

    def test_tmdb_not_found_error(self) -> None:
        """Test the TMDBNotFoundError class."""
        error = TMDBNotFoundError("Movie not found", "movie-123")
        assert isinstance(error, APINotFoundError)
        assert isinstance(error, TMDBError)
        assert isinstance(error, APIError)
        assert str(error) == "Movie not found"
        assert error.status_code == 404
        assert error.resource_id == "movie-123"

    def test_error_catch_as_parent(self) -> None:
        """Test catching TMDB errors as their parent classes."""
        # Catch as TMDBError
        try:
            raise TMDBRateLimitError("Rate limited", 30)
        except TMDBError as e:
            assert isinstance(e, TMDBRateLimitError)
            assert e.retry_after == 30

        # Catch as APIRateLimitError
        try:
            raise TMDBRateLimitError("Rate limited", 30)
        except APIRateLimitError as e:
            assert isinstance(e, TMDBRateLimitError)
            assert e.retry_after == 30

        # Catch as APIError
        try:
            raise TMDBNotFoundError("Movie not found", "movie-123")
        except APIError as e:
            assert isinstance(e, TMDBNotFoundError)
            assert e.resource_id == "movie-123"
