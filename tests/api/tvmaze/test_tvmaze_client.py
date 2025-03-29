"""
Test file for TVMaze client core functionality.
Tests for initialization, error handling, and caching.
"""

import pytest
from pytest_mock import MockerFixture
import requests
import json

from plexomatic.api.tvmaze_client import TVMazeClient, TVMazeRequestError, TVMazeRateLimitError


class TestTVMazeClient:
    """Tests for the TVMaze client core functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.client = TVMazeClient()

    def test_initialization(self) -> None:
        """Test client initialization with different parameters."""
        # Default initialization
        client = TVMazeClient()
        assert client.cache_size == 100

        # Custom initialization
        client = TVMazeClient(cache_size=200)
        assert client.cache_size == 200

    def test_request_exception(self, mocker: MockerFixture) -> None:
        """Test handling of request exceptions."""
        # Mock requests.get to raise an exception
        mock_get = mocker.patch("requests.get")
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        # Test request exception handling
        with pytest.raises(TVMazeRequestError) as excinfo:
            self.client._get("https://api.tvmaze.com/shows/1")

        # Verify error message
        assert "Connection error" in str(excinfo.value)

    def test_json_decode_error(self, mocker: MockerFixture) -> None:
        """Test handling of JSON decode errors."""
        # Mock requests.get to return invalid JSON
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response

        # Test JSON decode error handling
        with pytest.raises(TVMazeRequestError) as excinfo:
            self.client._get("https://api.tvmaze.com/shows/1")

        # Verify error message
        assert "Invalid JSON" in str(excinfo.value)

    def test_404_error(self, mocker: MockerFixture) -> None:
        """Test handling of 404 Not Found errors."""
        # Mock 404 response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Test 404 handling
        with pytest.raises(TVMazeRequestError) as excinfo:
            self.client._get("https://api.tvmaze.com/shows/99999")

        # Verify error message
        assert "Resource not found" in str(excinfo.value)

    def test_rate_limit_error(self, mocker: MockerFixture) -> None:
        """Test handling of rate limit errors."""
        # Mock rate limit response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "30"}
        mock_get.return_value = mock_response

        # Test rate limit error handling
        with pytest.raises(TVMazeRateLimitError) as excinfo:
            self.client._get("https://api.tvmaze.com/shows/1")

        # Verify error message contains the retry after value
        assert "Retry after" in str(excinfo.value)
        assert "30 seconds" in str(excinfo.value)

    def test_generic_error(self, mocker: MockerFixture) -> None:
        """Test handling of other HTTP errors."""
        # Mock generic error response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        # Test generic error handling
        with pytest.raises(TVMazeRequestError) as excinfo:
            self.client._get("https://api.tvmaze.com/shows/1")

        # Verify error message
        assert "500" in str(excinfo.value)
        assert "Internal Server Error" in str(excinfo.value)

    def test_caching(self, mocker: MockerFixture) -> None:
        """Test that responses are properly cached."""
        # Mock HTTP response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "name": "Breaking Bad"}
        mock_get.return_value = mock_response

        # First call should hit the API
        result1 = self.client._get("https://api.tvmaze.com/shows/1")
        assert mock_get.call_count == 1
        assert result1["name"] == "Breaking Bad"

        # Second call with same URL and params should use cache
        result2 = self.client._get("https://api.tvmaze.com/shows/1")
        assert mock_get.call_count == 1  # Still 1, not incremented
        assert result2["name"] == "Breaking Bad"

        # Different URL should hit the API again
        mock_response.json.return_value = {"id": 2, "name": "Better Call Saul"}
        result3 = self.client._get("https://api.tvmaze.com/shows/2")
        assert mock_get.call_count == 2
        assert result3["name"] == "Better Call Saul"

    def test_clear_cache(self, mocker: MockerFixture) -> None:
        """Test clearing the cache."""
        # Mock the cache_clear method
        mock_cache_clear = mocker.Mock()

        # Patch the _request_cached method to have our mock
        original_cache_clear = None
        try:
            if hasattr(self.client._request_cached, "cache_clear"):
                original_cache_clear = self.client._request_cached.cache_clear
                self.client._request_cached.cache_clear = mock_cache_clear

            # Call the method
            self.client.clear_cache()

            # Verify the cache clear was called
            mock_cache_clear.assert_called_once()
        finally:
            # Restore original method if needed
            if original_cache_clear:
                self.client._request_cached.cache_clear = original_cache_clear

    def test_setup_cache(self, mocker: MockerFixture) -> None:
        """Test setting up the cache."""
        # Create a new client with a mock for lru_cache
        lru_cache_mock = mocker.patch("plexomatic.api.tvmaze_client.lru_cache")

        # Set up the mock to return a simple caching function
        def mock_lru_cache(maxsize):
            def decorator(func):
                def wrapper(*args, **kwargs):
                    return func(*args, **kwargs)

                wrapper.cache_clear = lambda: None
                return wrapper

            return decorator

        lru_cache_mock.side_effect = mock_lru_cache

        # Create a new client which will use our mocked lru_cache
        TVMazeClient(cache_size=300)

        # Verify lru_cache was called with the right size
        lru_cache_mock.assert_called_once_with(maxsize=300)
