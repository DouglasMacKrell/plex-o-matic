"""
Test file for TMDB client initialization and error handling functionality.
"""

import pytest
from pytest_mock import MockerFixture
import requests
import json

from plexomatic.api.tmdb_client import TMDBClient, TMDBRequestError, TMDBRateLimitError


class TestTMDBClient:
    """Tests for the TMDB client initialization and error handling."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.api_key = "test_api_key"
        self.client = TMDBClient(api_key=self.api_key)

    def test_initialization(self) -> None:
        """Test client initialization with different parameters."""
        # Default initialization
        client = TMDBClient(api_key=self.api_key)
        assert client.api_key == self.api_key
        assert client.cache_size == 100
        assert client.auto_retry is False
        assert client._config is None

        # Custom initialization
        client = TMDBClient(api_key=self.api_key, cache_size=200, auto_retry=True)
        assert client.api_key == self.api_key
        assert client.cache_size == 200
        assert client.auto_retry is True
        assert client._config is None

    def test_get_params(self) -> None:
        """Test creation of request parameters."""
        # Test with no additional params
        params = self.client._get_params()
        assert params == {"api_key": self.api_key}

        # Test with additional params
        additional_params = {"query": "test", "year": "2020"}
        params = self.client._get_params(additional_params)
        assert params == {"api_key": self.api_key, "query": "test", "year": "2020"}

    def test_clear_cache(self, mocker: MockerFixture) -> None:
        """Test clearing the cache."""
        # Mock the internal _get_cached_key.cache_clear method
        try:
            # Create a mock for the cache_clear method
            mock_cache_clear = mocker.Mock()
            
            # Store the original method
            original_cache_clear = None
            if hasattr(self.client._get_cached_key, 'cache_clear'):
                original_cache_clear = self.client._get_cached_key.cache_clear
                
            # Patch the _get_cached_key method with a version that has a mock cache_clear
            patched_get_cached_key = mocker.patch.object(
                self.client, 
                '_get_cached_key', 
                return_value={},
                cache_clear=mock_cache_clear
            )

            # Call the method
            self.client.clear_cache()

            # Verify the cache clear was called
            mock_cache_clear.assert_called_once()
        finally:
            # No need to restore the original method since we used patch.object
            pass

    def test_request_exception(self, mocker: MockerFixture) -> None:
        """Test handling of request exceptions."""
        # Mock requests.get to raise an exception
        mock_get = mocker.patch("requests.get")
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        # Test exception handling
        with pytest.raises(TMDBRequestError) as excinfo:
            self.client._get("https://api.themoviedb.org/3/movie/12345")

        # Verify error message
        assert "Connection error" in str(excinfo.value)

    def test_response_error(self, mocker: MockerFixture) -> None:
        """Test handling of error responses."""
        # Mock HTTP response with error
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response

        # Test error response handling
        with pytest.raises(TMDBRequestError) as excinfo:
            self.client._get("https://api.themoviedb.org/3/movie/99999")

        # Verify error message
        assert "404" in str(excinfo.value)
        assert "Not Found" in str(excinfo.value)

    def test_rate_limit_error(self, mocker: MockerFixture) -> None:
        """Test handling of rate limit errors."""
        # Mock rate limit response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "30"}
        mock_get.return_value = mock_response

        # Test rate limit error (without auto-retry)
        with pytest.raises(TMDBRateLimitError) as excinfo:
            self.client._get("https://api.themoviedb.org/3/movie/12345")

        # Verify error message
        assert "Rate limit exceeded" in str(excinfo.value)
        assert "30 seconds" in str(excinfo.value)

    def test_auto_retry(self, mocker: MockerFixture) -> None:
        """Test auto-retry functionality."""
        # Mock time.sleep
        mock_sleep = mocker.patch("time.sleep")
        
        # Mock requests.get to return rate limit then success
        mock_get = mocker.patch("requests.get")
        rate_limit_response = mocker.Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "10"}
        
        success_response = mocker.Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"id": 12345, "title": "Test Movie"}
        
        mock_get.side_effect = [rate_limit_response, success_response]

        # Enable auto-retry
        self.client.auto_retry = True

        # Call the method
        result = self.client._get("https://api.themoviedb.org/3/movie/12345")

        # Verify the client waited and retried
        mock_sleep.assert_called_once_with(10)
        assert mock_get.call_count == 2
        assert result["id"] == 12345 