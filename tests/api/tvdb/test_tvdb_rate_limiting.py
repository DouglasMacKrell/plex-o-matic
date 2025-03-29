import requests
# Removed unittest.mock imports: patch, MagicMock, Mock
import time
import pytest

from plexomatic.api.tvdb_client import TVDBClient, TVDBRateLimitError


class TestTVDBRateLimiting:
    """Tests for TVDB rate limiting and caching functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.mock_auth_response = Mock()
        self.mock_auth_response.status_code = 200
        self.mock_auth_response.json.return_value = {"data": {"token": "test_token"}}

        self.mock_success_response = Mock()
        self.mock_success_response.status_code = 200
        self.mock_success_response.json.return_value = {
            "data": [{"name": "Test Show"}]
        }

        self.mock_rate_limit_response = Mock()
        self.mock_rate_limit_response.status_code = 429
        self.mock_rate_limit_response.headers = {"Retry-After": "1"}
        self.mock_rate_limit_response.raise_for_status = Mock(
            side_effect=requests.exceptions.HTTPError(
                "429 Client Error: Too Many Requests",
                response=self.mock_rate_limit_response
            )
        )

        with patch('requests.Session') as mock_session:
            mock_session.return_value.post.return_value = self.mock_auth_response
            mock_session.return_value.get.return_value = self.mock_success_response
            self.client = TVDBClient(api_key="test_key", pin="test_pin")

    def teardown_method(self):
        pass

    def test_rate_limiting(self):
        with patch('requests.Session') as mock_session:
            mock_session.return_value.post.return_value = self.mock_auth_response
            mock_session.return_value.get.side_effect = [
                self.mock_rate_limit_response,
                self.mock_success_response
            ]
            result = self.client.get_series_by_name("Test Show")
            assert result[0]["name"] == "Test Show"
            assert mock_session.return_value.get.call_count == 2

    def test_automatic_retry_after_rate_limit(self):
        with patch('requests.Session') as mock_session:
            mock_session.return_value.post.return_value = self.mock_auth_response
            mock_session.return_value.get.side_effect = [
                self.mock_rate_limit_response,
                self.mock_success_response
            ]
            start_time = time.time()
            result = self.client.get_series_by_name("Test Show")
            end_time = time.time()
            assert end_time - start_time >= 1  # Should have waited for Retry-After
            assert result[0]["name"] == "Test Show"
            assert mock_session.return_value.get.call_count == 2

    def test_cache_mechanism(self):
        with patch('requests.Session') as mock_session:
            mock_session.return_value.post.return_value = self.mock_auth_response
            mock_session.return_value.get.return_value = self.mock_success_response
            
            # First request should hit the API
            result1 = self.client.get_series_by_name("Test Show")
            assert result1[0]["name"] == "Test Show"
            assert mock_session.return_value.get.call_count == 1

            # Second request should use cache
            result2 = self.client.get_series_by_name("Test Show")
            assert result2[0]["name"] == "Test Show"
            assert mock_session.return_value.get.call_count == 1  # Count shouldn't increase

    def test_cache_invalidation(self):
        with patch('requests.Session') as mock_session:
            mock_session.return_value.post.return_value = self.mock_auth_response
            mock_session.return_value.get.return_value = self.mock_success_response
            
            # First request
            result1 = self.client.get_series_by_name("Test Show")
            assert mock_session.return_value.get.call_count == 1

            # Clear cache
            self.client.clear_cache()

            # Second request should hit API again
            result2 = self.client.get_series_by_name("Test Show")
            assert mock_session.return_value.get.call_count == 2

    def test_cache_size_limits(self):
        with patch('requests.Session') as mock_session:
            mock_session.return_value.post.return_value = self.mock_auth_response
            mock_session.return_value.get.return_value = self.mock_success_response
            
            # Make multiple unique requests to fill cache
            for i in range(10):
                self.client.get_series_by_name(f"Test Show {i}")

            # Verify cache size doesn't exceed limit
            assert len(self.client._cache) <= self.client._cache_size_limit

    def test_concurrent_rate_limiting(self):
        with patch('requests.Session') as mock_session:
            mock_session.return_value.post.return_value = self.mock_auth_response
            mock_session.return_value.get.side_effect = [
                self.mock_rate_limit_response,
                self.mock_success_response
            ] * 5  # For 5 concurrent requests
            
            self.client.clear_cache()
            results = []
            
            # Simulate concurrent requests
            for i in range(5):
                results.append(self.client.get_series_by_name(f"Test Show {i}"))
            
            # Verify all requests succeeded after retrying
            assert all(result[0]["name"] == "Test Show" for result in results)
            assert mock_session.return_value.get.call_count == 10  # Each request retried once 