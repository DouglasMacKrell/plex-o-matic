import requests
from unittest.mock import patch, MagicMock, Mock
import pytest

from plexomatic.api.tvdb_client import TVDBClient, TVDBRateLimitError


class TestTVDBRateLimiting:
    """Tests for TVDB rate limiting and caching functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a clean client for each test
        self.client = TVDBClient(api_key="test_key", pin="test_pin")

        # Set token for authentication
        self.client._token = "test_token"

        # Create standard test data
        self.test_show_data = {"data": [{"name": "Test Show"}]}

    @patch("requests.Session")
    @patch("time.sleep")  # Patch sleep to avoid waiting
    def test_rate_limiting(self, mock_sleep, mock_session_class):
        """Test rate limiting and automatic retry functionality."""
        # Setup the mock session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Create response objects
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "1"}
        rate_limit_response.raise_for_status.side_effect = requests.HTTPError(
            "Rate limited", response=rate_limit_response
        )

        success_response = Mock()
        success_response.status_code = 200
        success_response.raise_for_status.return_value = None
        success_response.json.return_value = self.test_show_data

        # Set up mock to return rate limit first then success
        mock_session.get.side_effect = [rate_limit_response, success_response]

        # Create a client with our mock session
        client = TVDBClient(api_key="test_key", pin="test_pin")
        client._session = mock_session  # Replace the session
        client._token = "test_token"  # Set a token so it thinks it's authenticated
        client.auto_retry = True  # Enable auto retry

        # Clear the cache to ensure our test hits the API
        client.clear_cache()

        # Call the method
        result = client.get_series_by_name("Test Show")

        # Verify the results
        assert result[0]["name"] == "Test Show"
        assert mock_session.get.call_count == 2
        assert mock_sleep.called  # Should have called sleep due to rate limit

    @patch("plexomatic.api.tvdb_client.TVDBClient._get_cached_key")
    def test_cache_mechanism(self, mock_get_cached_key):
        """Test that caching works properly."""
        # Set up the mock to return test data
        mock_get_cached_key.return_value = self.test_show_data

        # First call should hit the mock
        result1 = self.client.get_series_by_name("Test Show")
        assert result1[0]["name"] == "Test Show"
        assert mock_get_cached_key.call_count == 1

        # Reset the mock to track the second call
        mock_get_cached_key.reset_mock()

        # Second call with same name should use the same cache key
        result2 = self.client.get_series_by_name("Test Show")
        assert result2[0]["name"] == "Test Show"

        # Verify the mock was called with the same cache key
        assert mock_get_cached_key.call_count == 1

    def test_cache_clearing(self):
        """Test that the cache can be cleared."""
        # Create a mock for the cache_clear method
        mock_cache_clear = Mock()

        # Replace the client's method with our mock
        original_get_cached_key = self.client._get_cached_key
        self.client._get_cached_key = Mock()
        self.client._get_cached_key.cache_clear = mock_cache_clear

        try:
            # Call the clear_cache method
            self.client.clear_cache()

            # Verify that cache_clear was called
            mock_cache_clear.assert_called_once()
        finally:
            # Restore the original method
            self.client._get_cached_key = original_get_cached_key

    @patch("plexomatic.api.tvdb_client.TVDBClient._get_cached_key")
    def test_different_cache_keys(self, mock_get_cached_key):
        """Test that different search terms use different cache keys."""
        # Set up the mock to return test data
        mock_get_cached_key.return_value = self.test_show_data

        # Call with first show name
        self.client.get_series_by_name("Show One")

        # Call with second show name
        self.client.get_series_by_name("Show Two")

        # Verify the mock was called twice with different URLs
        assert mock_get_cached_key.call_count == 2

        # Get the cache keys used
        call_args_list = mock_get_cached_key.call_args_list
        first_call_key = call_args_list[0][0][0]
        second_call_key = call_args_list[1][0][0]

        # Verify different cache keys were used
        assert first_call_key != second_call_key
        assert "Show%20One" in first_call_key
        assert "Show%20Two" in second_call_key

    @patch("plexomatic.api.tvdb_client.TVDBClient._get_cached_key")
    @patch("time.sleep")  # Patch sleep to avoid waiting
    def test_no_auto_retry(self, mock_sleep, mock_get_cached_key):
        """Test that rate limiting errors propagate when auto_retry is disabled."""
        # Set up the mock to raise rate limit error
        mock_get_cached_key.side_effect = TVDBRateLimitError("Rate limited")

        # Disable auto-retry
        self.client.auto_retry = False

        # Call should fail with rate limit error
        with pytest.raises(TVDBRateLimitError):
            self.client.get_series_by_name("Test Show")

        # Verify sleep was not called
        mock_sleep.assert_not_called()

    @patch("plexomatic.api.tvdb_client.TVDBClient._get_cached_key")
    def test_cache_hit(self, mock_get_cached_key):
        """Test that cache hit avoids additional API calls."""
        # Set up a simple mock cache
        test_cache = {}

        # Create a side effect that simulates a cache
        def cached_get(cache_key):
            if cache_key not in test_cache:
                test_cache[cache_key] = self.test_show_data
            return test_cache[cache_key]

        mock_get_cached_key.side_effect = cached_get

        # First call should add to cache
        result1 = self.client.get_series_by_name("Test Show")
        assert result1[0]["name"] == "Test Show"

        # Reset the mock to track second call
        mock_get_cached_key.reset_mock()

        # Second call with same parameters should still call _get_cached_key
        # (the real caching happens inside that method)
        result2 = self.client.get_series_by_name("Test Show")
        assert result2[0]["name"] == "Test Show"
        assert mock_get_cached_key.called
