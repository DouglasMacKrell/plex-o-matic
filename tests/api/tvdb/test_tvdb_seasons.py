from unittest.mock import Mock

from plexomatic.api.tvdb_client import TVDBClient


class TestTVDBSeasons:
    """Tests for TVDB season-related functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create client with authentication already set
        self.client = TVDBClient(api_key="test_key")
        self.client._token = "test_token"  # Set token directly to avoid auth

        # Create mock session that we'll use in each test
        self.mock_session = Mock()

        # Replace the client's session with our mock
        self.client._session = self.mock_session

        # Create standard test data for seasons
        self.season_data = {
            "data": {
                "id": 2001,
                "seriesId": 12345,
                "number": 1,
                "name": "Season 1",
                "type": {"id": 1, "name": "Aired Order"},
            }
        }

        # Create standard test data for episodes
        self.season_episodes_data = {
            "data": [
                {"id": 1, "name": "Episode 1", "seasonNumber": 1, "number": 1},
                {"id": 2, "name": "Episode 2", "seasonNumber": 1, "number": 2},
            ]
        }

    def test_get_season_by_id(self) -> None:
        """Test retrieving a season by ID."""
        # Create mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = self.season_data

        # Configure the session mock to return our response
        self.client._session.get.return_value = mock_response

        # Make the API call
        season = self.client.get_season_by_id(2001)

        # Verify the result
        assert season["id"] == 2001
        assert season["number"] == 1
        assert season["name"] == "Season 1"
        assert season["type"]["name"] == "Aired Order"

        # Verify API call was made with correct parameters
        self.client._session.get.assert_called_once()
        url_arg = self.client._session.get.call_args[0][0]
        assert "seasons/2001" in url_arg

    def test_get_episodes_by_season(self) -> None:
        """Test retrieving episodes by season ID."""
        # Create mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = self.season_episodes_data

        # Configure the session mock to return our response
        self.client._session.get.return_value = mock_response

        # Make the API call
        episodes = self.client.get_episodes_by_season(2001)

        # Verify the result
        assert len(episodes) == 2
        assert episodes[0]["name"] == "Episode 1"
        assert episodes[1]["name"] == "Episode 2"

        # Verify API call was made with correct parameters
        self.client._session.get.assert_called_once()
        url_arg = self.client._session.get.call_args[0][0]
        assert "seasons/2001/episodes" in url_arg

    def test_get_episodes_by_season_empty(self) -> None:
        """Test retrieving episodes when none are found."""
        # Create mock response with empty data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": []}

        # Configure the session mock to return our response
        self.client._session.get.return_value = mock_response

        # Make the API call
        episodes = self.client.get_episodes_by_season(9999)

        # Verify the result is an empty list
        assert episodes == []

    def test_get_episodes_by_season_error(self) -> None:
        """Test error handling when retrieving episodes by season ID."""
        # Configure the session mock to raise an exception
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("API error")

        # Configure the session mock to return our error response
        self.client._session.get.return_value = mock_response

        # Make the API call - should handle the exception gracefully
        episodes = self.client.get_episodes_by_season(2001)

        # Verify the result is an empty list on error
        assert episodes == []
