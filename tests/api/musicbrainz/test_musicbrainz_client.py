"""Tests for the MusicBrainz API client basic functionality."""

import pytest
from pytest_mock import MockerFixture
import time
import requests

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

    def test_rate_limiting(self, mocker: MockerFixture) -> None:
        """Test rate limiting behavior."""
        # Mock time.sleep to avoid actual waiting
        mock_sleep = mocker.patch("time.sleep")
        
        # Mock successful response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"artists": []}
        mock_get.return_value = mock_response

        # Make two requests with different search terms to avoid caching
        self.client.search_artist("Test1")
        self.client.search_artist("Test2")

        # Verify rate limiting was enforced
        assert mock_get.call_count == 2
        calls = mock_get.call_args_list
        assert len(calls) == 2
        
        # Verify different search terms were used
        assert calls[0][1]["params"]["query"] == "Test1"
        assert calls[1][1]["params"]["query"] == "Test2"
        
        # Verify sleep was called due to rate limiting
        mock_sleep.assert_called()

    def test_rate_limit_error(self, mocker: MockerFixture) -> None:
        """Test rate limit error handling."""
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_get.return_value = mock_response

        with pytest.raises(MusicBrainzRateLimitError):
            self.client.search_artist("Test")

    def test_auto_retry_after_rate_limit(self, mocker: MockerFixture) -> None:
        """Test automatic retry after rate limit."""
        # Mock time.sleep to avoid actual waiting
        mocker.patch("time.sleep")
        
        # Create client with auto_retry enabled
        client = MusicBrainzClient(auto_retry=True)

        # Mock rate limit followed by success
        mock_get = mocker.patch("requests.get")
        mock_response1 = mocker.Mock()
        mock_response1.status_code = 429
        mock_response1.text = "Rate limit exceeded"

        mock_response2 = mocker.Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {"artists": []}

        mock_get.side_effect = [mock_response1, mock_response2]

        result = client.search_artist("Test")
        assert result == []
        assert mock_get.call_count == 2

    def test_request_error(self, mocker: MockerFixture) -> None:
        """Test request error handling."""
        mock_get = mocker.patch("requests.get")
        # Use a requests.RequestException instead of a generic Exception
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        with pytest.raises(MusicBrainzRequestError):
            self.client.search_artist("Test")

    def test_verify_music_file(self, mocker: MockerFixture) -> None:
        """Test music file verification."""
        # Mock artist and album searches
        mock_get = mocker.patch("requests.get")
        
        # First response: artist search
        mock_response1 = mocker.Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "artists": [
                {
                    "id": "123",
                    "name": "Test Artist",
                    "score": 95,
                }
            ]
        }
        
        # Second response: album search
        mock_response2 = mocker.Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "releases": [
                {
                    "id": "456",
                    "title": "Test Album",
                    "score": 90,
                    "date": "2020-01-01",
                }
            ]
        }
        
        mock_get.side_effect = [mock_response1, mock_response2]

        result, confidence = self.client.verify_music_file("Test Artist", "Test Album")
        
        assert result["artist_id"] == "123"
        assert result["album_id"] == "456"
        assert confidence >= 0.8  # Should be high confidence
        assert mock_get.call_count == 2 