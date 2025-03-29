"""
Example file demonstrating how to effectively mock the MusicBrainz client for testing.

This includes examples of:
- Mocking the MusicBrainzClient directly
- Mocking the requests module used by MusicBrainzClient
- Setting up mock responses for different API calls
"""

import pytest
from pytest_mock import MockerFixture
import time

from plexomatic.api.musicbrainz_client import (
    MusicBrainzClient,
    MusicBrainzRequestError,
    MusicBrainzRateLimitError,
)


# Sample response data for mock tests
ARTIST_SEARCH_RESPONSE = {
    "artists": [
        {
            "id": "123",
            "name": "Test Artist",
            "type": "Person",
            "country": "US",
            "score": 100,
        }
    ]
}

ARTIST_DETAIL_RESPONSE = {
    "id": "123",
    "name": "Test Artist",
    "type": "Person",
    "country": "US",
    "life-span": {"begin": "1990", "end": None},
}

RELEASE_SEARCH_RESPONSE = {
    "releases": [
        {
            "id": "456",
            "title": "Test Album",
            "date": "2020-01-01",
            "artist-credit": [{"name": "Test Artist"}],
            "score": 95,
        }
    ]
}

RELEASE_DETAIL_RESPONSE = {
    "id": "456",
    "title": "Test Album",
    "date": "2020-01-01",
    "artist-credit": [{"name": "Test Artist", "id": "123"}],
    "status": "Official",
    "country": "US",
}


class TestMusicBrainzMocking:
    """Examples of how to mock the MusicBrainz client for testing."""

    def test_mock_client_directly(self, mocker: MockerFixture) -> None:
        """Demo mocking the entire MusicBrainz client."""
        # Create a mock MusicBrainzClient
        mock_client = mocker.Mock(spec=MusicBrainzClient)
        
        # Configure mock to return sample data for different methods
        mock_client.search_artist.return_value = ARTIST_SEARCH_RESPONSE["artists"]
        mock_client.get_artist.return_value = ARTIST_DETAIL_RESPONSE
        mock_client.search_release.return_value = RELEASE_SEARCH_RESPONSE["releases"]
        mock_client.get_release.return_value = RELEASE_DETAIL_RESPONSE
        
        # Now use the mock client in your tests
        artists = mock_client.search_artist("Test Artist")
        assert len(artists) == 1
        assert artists[0]["name"] == "Test Artist"
        mock_client.search_artist.assert_called_once_with("Test Artist")
        
        artist = mock_client.get_artist("123")
        assert artist["name"] == "Test Artist"
        assert artist["type"] == "Person"
        mock_client.get_artist.assert_called_once_with("123")
        
        releases = mock_client.search_release("Test Album")
        assert len(releases) == 1
        assert releases[0]["title"] == "Test Album"
        mock_client.search_release.assert_called_once_with("Test Album")
        
        release = mock_client.get_release("456")
        assert release["title"] == "Test Album"
        assert release["date"] == "2020-01-01"
        mock_client.get_release.assert_called_once_with("456")

    def test_mock_requests(self, mocker: MockerFixture) -> None:
        """Demo mocking the requests module used by MusicBrainzClient."""
        # Mock requests.get
        mock_get = mocker.patch("requests.get")
        
        # Create a sample response for artist search
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = ARTIST_SEARCH_RESPONSE
        mock_get.return_value = mock_response
        
        # Create a real client that will use the mocked requests
        client = MusicBrainzClient(
            app_name="Test App",
            app_version="1.0",
        )
        
        # Mock time.sleep to avoid actual waiting during rate limiting
        mocker.patch("time.sleep")
        
        # Test artist search
        artists = client.search_artist("Test Artist")
        assert len(artists) == 1
        assert artists[0]["name"] == "Test Artist"
        assert artists[0]["id"] == "123"
        
        # Verify the request was correct
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "https://musicbrainz.org/ws/2/artist" in args[0]
        assert kwargs["params"]["query"] == "Test Artist"
        assert kwargs["params"]["fmt"] == "json"
        assert "User-Agent" in kwargs["headers"]

    def test_simulate_rate_limit(self, mocker: MockerFixture) -> None:
        """Demo simulating rate limiting and error handling."""
        # Mock requests.get
        mock_get = mocker.patch("requests.get")
        
        # Create rate limit error response
        mock_rate_limit_response = mocker.Mock()
        mock_rate_limit_response.status_code = 429
        mock_rate_limit_response.text = "Rate limit exceeded"
        
        # Create success response to return after rate limit
        mock_success_response = mocker.Mock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = ARTIST_SEARCH_RESPONSE
        
        # Set up mock to return rate limit then success
        mock_get.side_effect = [mock_rate_limit_response, mock_success_response]
        
        # Create client with auto retry enabled
        client = MusicBrainzClient(auto_retry=True)
        
        # Mock time.sleep to avoid actual waiting
        mocker.patch("time.sleep")
        
        # Test search with auto retry after rate limit
        artists = client.search_artist("Test Artist")
        assert len(artists) == 1
        assert artists[0]["name"] == "Test Artist"
        
        # Verify two requests were made
        assert mock_get.call_count == 2

    def test_mock_music_file_verification(self, mocker: MockerFixture) -> None:
        """Demo mocking music file verification."""
        # Mock requests.get
        mock_get = mocker.patch("requests.get")
        
        # Create responses for artist and release searches
        artist_response = mocker.Mock()
        artist_response.status_code = 200
        artist_response.json.return_value = ARTIST_SEARCH_RESPONSE
        
        release_response = mocker.Mock()
        release_response.status_code = 200
        release_response.json.return_value = RELEASE_SEARCH_RESPONSE
        
        # Set up mock to return different responses
        mock_get.side_effect = [artist_response, release_response]
        
        # Create client
        client = MusicBrainzClient()
        
        # Mock time.sleep to avoid actual waiting
        mocker.patch("time.sleep")
        
        # Test music file verification
        result, confidence = client.verify_music_file("Test Artist", "Test Album")
        
        # Verify the result structure - Check actual output keys from the implementation
        assert "artist" in result
        assert "artist_id" in result
        assert "album" in result
        assert "album_id" in result
        
        # Verify the actual values
        assert result["artist"] == "Test Artist"
        assert result["artist_id"] == "123"
        assert result["album"] == "Test Album"
        assert result["album_id"] == "456"
        assert result["year"] == "2020"  # From the date field in RELEASE_SEARCH_RESPONSE
        
        # Verify confidence level is high
        assert confidence >= 0.8
        
        # Verify the correct number of requests were made
        assert mock_get.call_count == 2 