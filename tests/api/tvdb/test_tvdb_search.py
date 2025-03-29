from unittest.mock import patch, Mock

from plexomatic.api.tvdb_client import TVDBClient


class TestTVDBSearch:
    """Tests for TVDB search functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a client for each test
        self.client = TVDBClient(api_key="test_key")
        self.client._token = "test_token"  # Manually set token to avoid authentication calls

        # Create a mock session for each test
        self.mock_session = Mock()

        # Replace the client's session with our mock
        self.client._session = self.mock_session

    @patch("requests.Session")
    def test_search_with_special_characters(self, mock_session_class) -> None:
        """Test search with special characters in the query."""
        # Configure mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
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

        # Set up the mock session to return our mock response
        self.client._session.get.return_value = mock_response

        # Test search with special characters
        result = self.client.get_series_by_name("Test Show: The Sequel")

        # Verify the result
        assert len(result) == 1
        assert result[0]["id"] == 12345
        assert result[0]["name"] == "Test Show: The Sequel"

        # Verify URL encoding in the API call
        self.client._session.get.assert_called_once()
        args, _ = self.client._session.get.call_args
        assert "Test%20Show%3A%20The%20Sequel" in args[0]

    @patch("requests.Session")
    def test_search_with_partial_matches(self, mock_session_class) -> None:
        """Test search with partial matches."""
        # Configure mock response with multiple results
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
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

        # Set up the mock session to return our mock response
        self.client._session.get.return_value = mock_response

        # Test search with partial match
        result = self.client.get_series_by_name("Test")

        # Verify the results
        assert len(result) == 2
        assert any(show["id"] == 12345 for show in result)
        assert any(show["id"] == 12346 for show in result)

    @patch("requests.Session")
    def test_search_with_empty_results(self, mock_session_class) -> None:
        """Test search with no results found."""
        # Configure mock empty response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": []}

        # Set up the mock session to return our mock response
        self.client._session.get.return_value = mock_response

        # Test search with no results
        result = self.client.get_series_by_name("Nonexistent Show")

        # Verify empty results
        assert result == []

    @patch("requests.Session")
    def test_search_with_alternative_patterns(self, mock_session_class) -> None:
        """Test search with alternative patterns when no results found."""
        # Configure first mock response with no results
        mock_empty_response = Mock()
        mock_empty_response.status_code = 200
        mock_empty_response.raise_for_status.return_value = None
        mock_empty_response.json.return_value = {"data": []}

        # Configure second mock response with results
        mock_success_response = Mock()
        mock_success_response.status_code = 200
        mock_success_response.raise_for_status.return_value = None
        mock_success_response.json.return_value = {"data": [{"id": 1, "name": "Test Show"}]}

        # Set up the mock session to return empty then success
        self.client._session.get.side_effect = [mock_empty_response, mock_success_response]

        # Test search with colon in title
        result = self.client.get_series_by_name("Test Show: The Sequel")

        # Verify result
        assert result[0]["id"] == 1
        assert result[0]["name"] == "Test Show"

        # Verify both queries were attempted
        assert self.client._session.get.call_count == 2
        urls = [call[0][0] for call in self.client._session.get.call_args_list]
        assert any("Test%20Show%3A%20The%20Sequel" in url for url in urls)
        assert any("Test%20Show" in url for url in urls)

    @patch("requests.Session")
    def test_search_with_missing_data(self, mock_session_class) -> None:
        """Test handling of missing or incomplete data in search results."""
        # Configure mock response with incomplete data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "data": [
                {
                    "id": 12345,
                    # Missing 'name' field
                    "status": "Continuing",
                    # Missing 'firstAired' field
                    "network": "Test Network",
                }
            ]
        }

        # Set up the mock session to return our mock response
        self.client._session.get.return_value = mock_response

        # Test that missing data is handled gracefully
        result = self.client.get_series_by_name("Test Show")

        # Verify result
        assert len(result) == 1
        assert result[0]["id"] == 12345
        assert "name" not in result[0]  # Field should be missing
        assert "firstAired" not in result[0]  # Field should be missing
        assert result[0]["network"] == "Test Network"
