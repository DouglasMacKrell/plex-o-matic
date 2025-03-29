import pytest
# Removed unittest.mock imports: Mock, patch, MagicMock

from plexomatic
.api.tvdb_client import TVDBClient


class TestTVDBUtils:
    """Tests for TVDB client utility methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TVDBClient(api_key="test_key")
        self.client._token = "test_token"
        
    def test_normalize_id(self):
        """Test ID normalization logic."""
        # Test with numeric ID
        assert self.client._normalize_id(12345) == 12345
        
        # Test with string ID
        assert self.client._normalize_id("12345") == 12345
        
        # Test with prefixed ID
        assert self.client._normalize_id("series-12345") == 12345
        
    def test_ensure_authenticated(self):
        """Test ensure_authenticated method."""
        # Test when already authenticated
        self.client._token = "valid_token"
        with patch.object(self.client, 'authenticate') as mock_auth:
            self.client._ensure_authenticated()
            mock_auth.assert_not_called()
        
        # Test when not authenticated
        self.client._token = None
        with patch.object(self.client, 'authenticate') as mock_auth:
            self.client._ensure_authenticated()
            mock_auth.assert_called_once()
            
    # Converted from @patch("plexomatic.api.tvdb_client.TVDBClient.clear_cache")
    def test_clear_cache(self, mock_clear_cache):
        """Test cache clearing functionality."""
        # Create a mock for the cache_clear method
        mock_cache_clear = Mock()
        
        # Temporarily replace the _get_cached_key method with one that has a cache_clear attribute
        original_get_cached_key = self.client._get_cached_key
        self.client._get_cached_key = Mock()
        self.client._get_cached_key.cache_clear = mock_cache_clear
        
        try:
            # Call the method
            self.client.clear_cache()
            
            # Verify cache_clear was called
            mock_cache_clear.assert_called_once()
        finally:
            # Restore the original method
            self.client._get_cached_key = original_get_cached_key
            
    # Converted from @patch("plexomatic.api.tvdb_client.requests.Session")
    def test_get_cached_key(self, mock_session_class):
        """Test the caching mechanism."""
        # Setup session mock
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"result": "test_data"}}
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        # Patch authenticate to avoid real API calls
        with patch.object(self.client, 'authenticate'):
            # First call should hit the API
            result1 = self.client._get_cached_key("test/endpoint")
            assert result1 == {"data": {"result": "test_data"}}
            mock_session.get.assert_called_once()
            
            # Second call with same key should use cache
            mock_session.get.reset_mock()
            result2 = self.client._get_cached_key("test/endpoint")
            assert result2 == {"data": {"result": "test_data"}}
            mock_session.get.assert_not_called()
            
            # Different key should hit API again
            result3 = self.client._get_cached_key("another/endpoint")
            assert result3 == {"data": {"result": "test_data"}}
            mock_session.get.assert_called_once()
        
    # Converted from @patch("plexomatic.api.tvdb_client.requests.Session")
    def test_cache_size_limit(self, mock_session_class):
        """Test that cache size is limited properly."""
        # Set a very small cache for testing
        self.client.cache_size = 2
        self.client._cache_size_limit = 2
        
        # Setup session mock
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"result": "test_data"}}
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        # Patch authenticate to avoid real API calls
        with patch.object(self.client, 'authenticate'):
            # Fill the cache beyond its limit
            for i in range(3):
                self.client._get_cached_key(f"endpoint{i}")
                
            # Assert only the most recent 2 entries are in cache
            assert len(self.client._cache) <= 2
        
    def test_get_series_by_id_forwards_to_get_series(self):
        """Test that get_series_by_id forwards to get_series."""
        # Create a proper mock for get_series
        self.client.get_series = Mock(return_value={"id": 12345, "name": "Test Show"})
        
        # Call the method
        result = self.client.get_series_by_id(12345)
        
        # Verify the mock was called
        self.client.get_series.assert_called_once_with(12345)
        assert result == {"id": 12345, "name": "Test Show"} 