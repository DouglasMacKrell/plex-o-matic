import pytest
from unittest.mock import patch, MagicMock
import time
import os
from datetime import datetime, timezone, timedelta

from plexomatic.api.tvdb_client import TVDBClient, TVDBAuthenticationError, TVDBRateLimitError, TVDBRequestError


class TestTVDBClient:
    """Tests for the TVDB API client."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.api_key = "test_api_key"
        self.client = TVDBClient(api_key=self.api_key)
        # Pre-set a token to avoid automatic authentication
        self.client.token = "pre_auth_token"
        self.client.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    @patch('plexomatic.api.tvdb_client.requests.post')
    def test_authentication(self, mock_post):
        """Test the authentication process."""
        # Reset the token for authentication testing
        self.client.token = None
        self.client.token_expires_at = None
        
        # Mock successful authentication response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "token": "mock_token"
            }
        }
        mock_post.return_value = mock_response
        
        # Test successful authentication
        self.client.authenticate()
        assert self.client.token == "mock_token"
        assert self.client.token_expires_at is not None
        mock_post.assert_called_once()
        
        # Test authentication failure
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Invalid credentials"}
        mock_post.reset_mock()
        self.client.token = None
        with pytest.raises(TVDBAuthenticationError):
            self.client.authenticate()
    
    @patch('plexomatic.api.tvdb_client.requests.get')
    def test_get_series_by_name(self, mock_get):
        """Test retrieving series by name."""
        # Mock successful series search response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": 12345,
                    "seriesName": "Test Show",
                    "status": "Continuing",
                    "firstAired": "2020-01-01",
                    "network": "Test Network"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Test successful series search
        result = self.client.get_series_by_name("Test Show")
        assert result[0]["id"] == 12345
        assert result[0]["seriesName"] == "Test Show"
        mock_get.assert_called_once()
        
        # Test series not found
        mock_response.json.return_value = {"data": []}
        mock_get.reset_mock()
        self.client.clear_cache()  # Clear cache to ensure the mock is called again
        result = self.client.get_series_by_name("Nonexistent Show")
        assert result == []
    
    @patch('plexomatic.api.tvdb_client.requests.get')
    def test_get_series_by_id(self, mock_get):
        """Test retrieving series details by ID."""
        # Mock successful series details response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": 12345,
                "seriesName": "Test Show",
                "status": "Continuing",
                "firstAired": "2020-01-01",
                "network": "Test Network",
                "overview": "Test overview"
            }
        }
        mock_get.return_value = mock_response
        
        # Test successful series details retrieval
        result = self.client.get_series_by_id(12345)
        assert result["id"] == 12345
        assert result["seriesName"] == "Test Show"
        assert result["overview"] == "Test overview"
        mock_get.assert_called_once()
        
        # Test series not found
        mock_response.status_code = 404
        mock_get.reset_mock()
        self.client.clear_cache()  # Clear cache to ensure the mock is called again
        with pytest.raises(TVDBRequestError):
            self.client.get_series_by_id(99999)
    
    @patch('plexomatic.api.tvdb_client.requests.get')
    def test_get_episodes_by_series_id(self, mock_get):
        """Test retrieving episodes for a series."""
        # Mock successful episodes response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": 1001,
                    "airedSeason": 1,
                    "airedEpisodeNumber": 1,
                    "episodeName": "Pilot",
                    "firstAired": "2020-01-01"
                },
                {
                    "id": 1002,
                    "airedSeason": 1,
                    "airedEpisodeNumber": 2,
                    "episodeName": "Episode 2",
                    "firstAired": "2020-01-08"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Test successful episodes retrieval
        result = self.client.get_episodes_by_series_id(12345)
        assert len(result) == 2
        assert result[0]["id"] == 1001
        assert result[1]["airedEpisodeNumber"] == 2
        mock_get.assert_called_once()
    
    @patch('plexomatic.api.tvdb_client.requests.get')
    def test_rate_limiting(self, mock_get):
        """Test handling of rate limiting."""
        # Mock rate limit exceeded response
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response
        
        # Test rate limit handling
        with pytest.raises(TVDBRateLimitError):
            self.client.get_series_by_name("Test Show")
    
    @patch('plexomatic.api.tvdb_client.requests.get')
    @patch('time.sleep')
    def test_automatic_retry_after_rate_limit(self, mock_sleep, mock_get):
        """Test automatic retry after rate limit with backoff."""
        # Setup mock responses for rate limit then success
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "5"}
        
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "data": [{"id": 12345, "seriesName": "Test Show"}]
        }
        
        # Return rate limit on first call, success on second
        mock_get.side_effect = [rate_limit_response, success_response]
        
        # Test with auto_retry=True
        self.client.auto_retry = True
        self.client.clear_cache()  # Clear cache to ensure the mock is called
        result = self.client.get_series_by_name("Test Show")
        
        # Verify the client respected the retry-after header
        mock_sleep.assert_called_once_with(5)
        assert len(mock_get.call_args_list) == 2
        assert result[0]["id"] == 12345
    
    @patch('plexomatic.api.tvdb_client.requests.get')
    def test_cache_mechanism(self, mock_get):
        """Test that responses are properly cached."""
        # Setup mock for first call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"id": 12345, "seriesName": "Test Show"}]
        }
        mock_get.return_value = mock_response
        
        # Clear the cache before starting the test
        self.client.clear_cache()
        
        # First call should hit the API
        result1 = self.client.get_series_by_name("Test Show")
        assert mock_get.call_count == 1
        
        # Second call with same params should use cache
        result2 = self.client.get_series_by_name("Test Show")
        # Verify mock wasn't called again
        assert mock_get.call_count == 1
        
        # Results should be identical
        assert result1 == result2
        
        # Different query should hit the API again
        mock_response.json.return_value = {
            "data": [{"id": 67890, "seriesName": "Another Show"}]
        }
        result3 = self.client.get_series_by_name("Another Show")
        assert mock_get.call_count == 2
        assert result3[0]["id"] == 67890 