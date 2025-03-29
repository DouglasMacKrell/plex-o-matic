"""Test cases for the MusicBrainz-specific API error classes."""

from plexomatic.api.errors import (
    APIError,
    APIAuthenticationError,
    APIRequestError,
    APIRateLimitError,
    APINotFoundError,
)
from plexomatic.api.errors.musicbrainz import (
    MusicBrainzError,
    MusicBrainzAuthenticationError,
    MusicBrainzRequestError,
    MusicBrainzRateLimitError,
    MusicBrainzNotFoundError,
    MusicBrainzSearchError,
)


class TestMusicBrainzErrors:
    """Test cases for the MusicBrainz-specific API error classes."""

    def test_musicbrainz_error_base_class(self) -> None:
        """Test the base MusicBrainzError class."""
        error = MusicBrainzError("MusicBrainz error message")
        assert isinstance(error, APIError)
        assert str(error) == "MusicBrainz error message"
        assert error.message == "MusicBrainz error message"
        assert error.status_code is None

    def test_musicbrainz_authentication_error(self) -> None:
        """Test the MusicBrainzAuthenticationError class."""
        error = MusicBrainzAuthenticationError("Auth error", 401)
        assert isinstance(error, APIAuthenticationError)
        assert isinstance(error, MusicBrainzError)
        assert isinstance(error, APIError)
        assert str(error) == "Auth error"
        assert error.status_code == 401

    def test_musicbrainz_request_error(self) -> None:
        """Test the MusicBrainzRequestError class."""
        error = MusicBrainzRequestError("Request error", 400)
        assert isinstance(error, APIRequestError)
        assert isinstance(error, MusicBrainzError)
        assert isinstance(error, APIError)
        assert str(error) == "Request error"
        assert error.status_code == 400

    def test_musicbrainz_rate_limit_error(self) -> None:
        """Test the MusicBrainzRateLimitError class."""
        error = MusicBrainzRateLimitError("Rate limited", 30, 429)
        assert isinstance(error, APIRateLimitError)
        assert isinstance(error, MusicBrainzError)
        assert isinstance(error, APIError)
        assert str(error) == "Rate limited"
        assert error.status_code == 429
        assert error.retry_after == 30

    def test_musicbrainz_not_found_error(self) -> None:
        """Test the MusicBrainzNotFoundError class."""
        error = MusicBrainzNotFoundError("Album not found", "album-123")
        assert isinstance(error, APINotFoundError)
        assert isinstance(error, MusicBrainzError)
        assert isinstance(error, APIError)
        assert str(error) == "Album not found"
        assert error.status_code == 404
        assert error.resource_id == "album-123"

    def test_musicbrainz_search_error(self) -> None:
        """Test the MusicBrainzSearchError class."""
        error = MusicBrainzSearchError("Search failed")
        assert isinstance(error, MusicBrainzRequestError)
        assert isinstance(error, MusicBrainzError)
        assert isinstance(error, APIError)
        assert str(error) == "Search failed"
        assert error.query is None

        # With query
        error = MusicBrainzSearchError("Search failed", "artist:beyonce")
        assert error.query == "artist:beyonce"

        # With status code
        error = MusicBrainzSearchError("Search failed", "artist:beyonce", 400)
        assert error.status_code == 400

    def test_error_catch_as_parent(self) -> None:
        """Test catching MusicBrainz errors as their parent classes."""
        # Catch as MusicBrainzError
        try:
            raise MusicBrainzRateLimitError("Rate limited", 30)
        except MusicBrainzError as e:
            assert isinstance(e, MusicBrainzRateLimitError)
            assert e.retry_after == 30

        # Catch as APIRateLimitError
        try:
            raise MusicBrainzRateLimitError("Rate limited", 30)
        except APIRateLimitError as e:
            assert isinstance(e, MusicBrainzRateLimitError)
            assert e.retry_after == 30

        # Catch specific MusicBrainz errors
        try:
            raise MusicBrainzSearchError("Search failed", "artist:beyonce")
        except MusicBrainzRequestError as e:
            assert isinstance(e, MusicBrainzSearchError)
            assert e.query == "artist:beyonce"
