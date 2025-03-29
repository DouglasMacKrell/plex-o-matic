import pytest
# Removed unittest.mock imports: patch, MagicMock, Mock

from plexomatic.api.tvdb_client import TVDBClient


class TestTVDBSearch:
    """Tests for TVDB search functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.client = TVDBClient(api_key="test_key")
        self.client.token = "test_token"
        
        # Mock authentication response
        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.json.return_value = {"data": {"token": "test_token"}}
        
        # Mock search data
        self.search_data = {
            "data": [
                {
                    "id": 1,
                    "name": "Test Show",
                    "status": "Continuing",
                    "type": "Scripted",
                    "year": 2020
                }
            ]
        }
        
        search_response = Mock()
        search_response.status_code = 200
        search_response.json.return_value = self.search_data
        
        # Set up the mock for requests
        self.mock_patcher = patch('plexomatic.api.tvdb_client.requests')
        self.mock_requests = self.mock_patcher.start()
        self.mock_requests.post.return_value = auth_response
        self.mock_requests.get.return_value = search_response

    def teardown_method(self):
        self.mock_patcher.stop()

    # Converted from @patch("plexomatic.api.tvdb_client.requests.get")
    def test_search_with_special_characters(self, mock_get: MagicMock) -> None:
        """Test search with special characters in the query."""
        # Mock successful search response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": 12345,
                    "name": "Test Show: The Sequel",
                    "status": "Continuing",
                    "firstAired": "2020-01-01",
                    "network": "Test Network",
                }
            ]
        }
        mock_get.return_value = mock_response

        # Test search with special characters
        result = self.client.get_series_by_name("Test Show: The Sequel")

        assert result[0]["id"] == 12345
        assert result[0]["name"] == "Test Show: The Sequel"

        # Verify URL encoding
        mock_get.assert_called_once()
        args, _ = mock_get.call_args
        assert "Test%20Show%3A%20The%20Sequel" in args[0]

    # Converted from @patch("plexomatic.api.tvdb_client.requests.get")
    def test_search_with_partial_matches(self, mock_get: MagicMock) -> None:
        """Test search with partial matches."""
        # Mock successful search response with multiple matches
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": 12345,
                    "name": "Test Show",
                    "status": "Continuing",
                    "firstAired": "2020-01-01",
                    "network": "Test Network",
                },
                {
                    "id": 12346,
                    "name": "Test Show: The Sequel",
                    "status": "Continuing",
                    "firstAired": "2021-01-01",
                    "network": "Test Network",
                },
            ]
        }
        mock_get.return_value = mock_response

        # Test search with partial match
        result = self.client.get_series_by_name("Test")

        assert len(result) == 2
        assert any(show["id"] == 12345 for show in result)
        assert any(show["id"] == 12346 for show in result)

    # Converted from @patch("plexomatic.api.tvdb_client.requests.get")
    def test_search_with_empty_results(self, mock_get: MagicMock) -> None:
        """Test search with no results found."""
        # Mock empty search response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        # Test search with no results
        result = self.client.get_series_by_name("Nonexistent Show")
        assert result == []

    # Converted from @patch("plexomatic.api.tvdb_client.requests.get")
    def test_search_with_alternative_patterns(self, mock_get: MagicMock) -> None:
        """Test search with alternative patterns when no results found."""
        # Mock first response with no results
        mock_empty_response = MagicMock()
        mock_empty_response.status_code = 200
        mock_empty_response.json.return_value = {"data": []}

        # Mock second response with results for main title
        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {
            "data": [{"id": 1, "name": "Test Show"}]
        }

        # Configure mock to return empty then success
        mock_get.side_effect = [mock_empty_response, mock_success_response]

        # Test search with colon in title
        result = self.client.get_series_by_name("Test Show: The Sequel")
        assert result[0]["id"] == 1
        assert result[0]["name"] == "Test Show"

        # Verify both URLs were tried
        assert mock_get.call_count == 2
        urls = [call[0][0] for call in mock_get.call_args_list]
        assert any("Test%20Show%3A%20The%20Sequel" in url for url in urls)
        assert any("Test%20Show" in url for url in urls)

    # Converted from @patch("plexomatic.api.tvdb_client.requests.get")
    def test_search_with_missing_data(self, mock_get: MagicMock) -> None:
        """Test handling of missing or incomplete data in search results."""
        # Mock response with missing fields
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": 12345,
                    # Missing seriesName
                    "status": "Continuing",
                    # Missing firstAired
                    "network": "Test Network",
                }
            ]
        }
        mock_get.return_value = mock_response

        # Test that missing data is handled gracefully
        result = self.client.get_series_by_name("Test Show")
        assert len(result) == 1
        assert result[0]["id"] == 12345
        assert "seriesName" not in result[0]
        assert "firstAired" not in result[0]
        assert result[0]["network"] == "Test Network" 