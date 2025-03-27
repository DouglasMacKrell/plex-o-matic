"""Tests for the MusicBrainz API client."""

import pytest
from unittest.mock import patch, MagicMock

from plexomatic.api.musicbrainz_client import (
    MusicBrainzClient,
    MusicBrainzRequestError,
    MusicBrainzRateLimitError,
)


class TestMusicBrainzClient:
    """Tests for the MusicBrainz API client."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.app_name = "Test App"
        self.app_version = "1.0"
        self.contact_email = "test@example.com"
        self.client = MusicBrainzClient(
            app_name=self.app_name,
            app_version=self.app_version,
            contact_email=self.contact_email,
        )

    def test_initialization(self) -> None:
        """Test client initialization with different parameters."""
        # Test with all parameters
        client = MusicBrainzClient(
            app_name="Test App",
            app_version="1.0",
            contact_email="test@example.com",
            cache_size=200,
            auto_retry=True,
        )
        assert client.app_name == "Test App"
        assert client.app_version == "1.0"
        assert client.contact_email == "test@example.com"
        assert client.cache_size == 200
        assert client.auto_retry is True
        assert "Test App/1.0 ( test@example.com )" in client.user_agent

        # Test with minimal parameters
        client = MusicBrainzClient()
        assert client.app_name == "Plex-o-matic"
        assert client.app_version == "1.0"
        assert client.contact_email == ""
        assert client.cache_size == 100
        assert client.auto_retry is False
        assert "Plex-o-matic/1.0" in client.user_agent

    @patch("plexomatic.api.musicbrainz_client.requests.get")
    def test_search_artist_success(self, mock_get: MagicMock) -> None:
        """Test successful artist search."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "artists": [
                {
                    "id": "123",
                    "name": "Test Artist",
                    "type": "Person",
                    "country": "US",
                }
            ]
        }
        mock_get.return_value = mock_response

        result = self.client.search_artist("Test Artist")
        assert len(result) == 1
        assert result[0]["name"] == "Test Artist"
        assert result[0]["id"] == "123"
        mock_get.assert_called_once()

    @patch("plexomatic.api.musicbrainz_client.requests.get")
    def test_search_artist_no_results(self, mock_get: MagicMock) -> None:
        """Test artist search with no results."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"artists": []}
        mock_get.return_value = mock_response

        result = self.client.search_artist("Nonexistent Artist")
        assert result == []
        mock_get.assert_called_once()

    @patch("plexomatic.api.musicbrainz_client.requests.get")
    def test_get_artist_success(self, mock_get: MagicMock) -> None:
        """Test successful artist retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123",
            "name": "Test Artist",
            "type": "Person",
            "country": "US",
            "life-span": {"begin": "1990", "end": None},
        }
        mock_get.return_value = mock_response

        result = self.client.get_artist("123")
        assert result["name"] == "Test Artist"
        assert result["id"] == "123"
        mock_get.assert_called_once()

    @patch("plexomatic.api.musicbrainz_client.requests.get")
    def test_get_artist_with_releases(self, mock_get: MagicMock) -> None:
        """Test artist retrieval with releases included."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123",
            "name": "Test Artist",
            "releases": [
                {
                    "id": "456",
                    "title": "Test Album",
                    "date": "2020-01-01",
                }
            ],
        }
        mock_get.return_value = mock_response

        result = self.client.get_artist("123", include_releases=True)
        assert result["name"] == "Test Artist"
        assert len(result["releases"]) == 1
        assert result["releases"][0]["title"] == "Test Album"
        mock_get.assert_called_once()

    @patch("plexomatic.api.musicbrainz_client.requests.get")
    def test_search_release_success(self, mock_get: MagicMock) -> None:
        """Test successful release search."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "releases": [
                {
                    "id": "456",
                    "title": "Test Album",
                    "date": "2020-01-01",
                    "artist-credit": [{"name": "Test Artist"}],
                }
            ]
        }
        mock_get.return_value = mock_response

        result = self.client.search_release("Test Album")
        assert len(result) == 1
        assert result[0]["title"] == "Test Album"
        assert result[0]["id"] == "456"
        mock_get.assert_called_once()

    @patch("plexomatic.api.musicbrainz_client.requests.get")
    def test_get_release_success(self, mock_get: MagicMock) -> None:
        """Test successful release retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "456",
            "title": "Test Album",
            "date": "2020-01-01",
            "artist-credit": [{"name": "Test Artist"}],
        }
        mock_get.return_value = mock_response

        result = self.client.get_release("456")
        assert result["title"] == "Test Album"
        assert result["id"] == "456"
        mock_get.assert_called_once()

    @patch("plexomatic.api.musicbrainz_client.requests.get")
    def test_get_release_with_recordings(self, mock_get: MagicMock) -> None:
        """Test release retrieval with recordings included."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "456",
            "title": "Test Album",
            "recordings": [
                {
                    "id": "789",
                    "title": "Test Track",
                    "length": 180000,
                }
            ],
        }
        mock_get.return_value = mock_response

        result = self.client.get_release("456", include_recordings=True)
        assert result["title"] == "Test Album"
        assert len(result["recordings"]) == 1
        assert result["recordings"][0]["title"] == "Test Track"
        mock_get.assert_called_once()

    @patch("plexomatic.api.musicbrainz_client.requests.get")
    def test_rate_limiting(self, mock_get: MagicMock) -> None:
        """Test rate limiting behavior."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"artists": []}
        mock_get.return_value = mock_response

        # Make two requests in quick succession
        self.client.search_artist("Test")
        self.client.search_artist("Test")

        # Verify rate limiting was enforced
        assert mock_get.call_count == 2
        # The second call should have been delayed by at least RATE_LIMIT seconds
        # This is handled by the _enforce_rate_limit method

    @patch("plexomatic.api.musicbrainz_client.requests.get")
    def test_rate_limit_error(self, mock_get: MagicMock) -> None:
        """Test rate limit error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_get.return_value = mock_response

        with pytest.raises(MusicBrainzRateLimitError):
            self.client.search_artist("Test")

    @patch("plexomatic.api.musicbrainz_client.requests.get")
    def test_auto_retry_after_rate_limit(self, mock_get: MagicMock) -> None:
        """Test automatic retry after rate limit."""
        # Create client with auto_retry enabled
        client = MusicBrainzClient(auto_retry=True)

        # Mock rate limit followed by success
        mock_response1 = MagicMock()
        mock_response1.status_code = 429
        mock_response1.text = "Rate limit exceeded"

        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {"artists": []}

        mock_get.side_effect = [mock_response1, mock_response2]

        result = client.search_artist("Test")
        assert result == []
        assert mock_get.call_count == 2

    @patch("plexomatic.api.musicbrainz_client.requests.get")
    def test_request_error(self, mock_get: MagicMock) -> None:
        """Test request error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_get.return_value = mock_response

        with pytest.raises(MusicBrainzRequestError):
            self.client.search_artist("Test")

    @patch("plexomatic.api.musicbrainz_client.requests.get")
    def test_verify_music_file(self, mock_get: MagicMock) -> None:
        """Test music file verification."""
        # Mock successful artist search
        mock_artist_response = MagicMock()
        mock_artist_response.status_code = 200
        mock_artist_response.json.return_value = {
            "artists": [
                {
                    "id": "123",
                    "name": "Test Artist",
                    "score": 100,
                }
            ]
        }

        # Mock successful release search
        mock_release_response = MagicMock()
        mock_release_response.status_code = 200
        mock_release_response.json.return_value = {
            "releases": [
                {
                    "id": "456",
                    "title": "Test Album",
                    "score": 100,
                }
            ]
        }

        # Mock successful recording search
        mock_recording_response = MagicMock()
        mock_recording_response.status_code = 200
        mock_recording_response.json.return_value = {
            "recordings": [
                {
                    "id": "789",
                    "title": "Test Track",
                    "score": 100,
                }
            ]
        }

        mock_get.side_effect = [
            mock_artist_response,
            mock_release_response,
            mock_recording_response,
        ]

        result, confidence = self.client.verify_music_file(
            artist="Test Artist",
            album="Test Album",
            track="Test Track",
        )

        assert result["artist"]["name"] == "Test Artist"
        assert result["release"]["title"] == "Test Album"
        assert result["recording"]["title"] == "Test Track"
        assert confidence > 0.8  # High confidence for exact matches
        assert mock_get.call_count == 3
