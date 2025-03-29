import pytest
# Removed unittest.mock imports: Mock, patch, MagicMock

from plexomatic.api.tvdb_client import TVDBClient


class TestTVDBSeasons:
    """Tests for TVDB season-related functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Set up the client with authentication patched
        with patch('plexomatic.api.tvdb_client.requests.Session'):
            self.client = TVDBClient(api_key="test_key")
            self.client._token = "test_token"
        
        # Mock responses for season data
        self.season_data = {
            "data": {
                "id": 2001,
                "seriesId": 12345,
                "number": 1,
                "name": "Season 1",
                "type": {
                    "id": 1,
                    "name": "Aired Order"
                }
            }
        }
        
        # Mock responses for season episodes
        self.season_episodes_data = {
            "data": [
                {
                    "id": 1,
                    "name": "Episode 1",
                    "seasonNumber": 1,
                    "number": 1
                },
                {
                    "id": 2,
                    "name": "Episode 2",
                    "seasonNumber": 1,
                    "number": 2
                }
            ]
        }
        
        # Create mock responses
        self.mock_season_response = Mock()
        self.mock_season_response.json.return_value = self.season_data
        
        self.mock_episodes_response = Mock()
        self.mock_episodes_response.json.return_value = self.season_episodes_data
        
    # Converted from @patch("plexomatic.api.tvdb_client.requests.Session")
    def test_get_season_by_id(self, mock_session_class: MagicMock) -> None:
        """Test retrieving a season by ID."""
        # Setup session mock
        mock_session = Mock()
        mock_session.get.return_value = self.mock_season_response
        mock_session_class.return_value = mock_session
        
        # Patch authenticate to avoid real API calls
        with patch.object(self.client, 'authenticate'):
            # Make the API call
            season = self.client.get_season_by_id(2001)
            
            # Verify the result
            assert season["id"] == 2001
            assert season["number"] == 1
            assert season["name"] == "Season 1"
            assert season["type"]["name"] == "Aired Order"
            
            # Verify API call
            mock_session.get.assert_called_once_with(
                "https://api4.thetvdb.com/v4/seasons/2001",
                headers={"Authorization": "Bearer test_token"}
            )
        
    # Converted from @patch("plexomatic.api.tvdb_client.requests.Session")
    def test_get_episodes_by_season(self, mock_session_class: MagicMock) -> None:
        """Test retrieving episodes by season ID."""
        # Setup session mock
        mock_session = Mock()
        mock_session.get.return_value = self.mock_episodes_response
        mock_session_class.return_value = mock_session
        
        # Patch authenticate to avoid real API calls
        with patch.object(self.client, 'authenticate'):
            # Make the API call
            episodes = self.client.get_episodes_by_season(2001)
            
            # Verify the result
            assert len(episodes) == 2
            assert episodes[0]["name"] == "Episode 1"
            assert episodes[1]["name"] == "Episode 2"
            
            # Verify API call
            mock_session.get.assert_called_once_with(
                "https://api4.thetvdb.com/v4/seasons/2001/episodes",
                headers={"Authorization": "Bearer test_token"}
            )
        
    # Converted from @patch("plexomatic.api.tvdb_client.requests.Session")
    def test_get_episodes_by_season_empty(self, mock_session_class: MagicMock) -> None:
        """Test retrieving episodes when none are found."""
        # Setup session mock
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        # Patch authenticate to avoid real API calls
        with patch.object(self.client, 'authenticate'):
            # Make the API call
            episodes = self.client.get_episodes_by_season(9999)
            
            # Verify the result is an empty list
            assert episodes == []
        
    # Converted from @patch("plexomatic.api.tvdb_client.requests.Session")
    def test_get_episodes_by_season_error(self, mock_session_class: MagicMock) -> None:
        """Test error handling when retrieving episodes by season ID."""
        # Setup session mock
        mock_session = Mock()
        mock_session.get.side_effect = Exception("API error")
        mock_session_class.return_value = mock_session
        
        # Patch authenticate to avoid real API calls
        with patch.object(self.client, 'authenticate'):
            # Make the API call - should handle the exception gracefully
            episodes = self.client.get_episodes_by_season(2001)
            
            # Verify the result is an empty list on error
            assert episodes == [] 