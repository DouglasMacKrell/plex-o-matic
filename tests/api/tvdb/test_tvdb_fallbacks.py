import pytest
# Removed unittest.mock imports: Mock, patch, MagicMock

from plexomatic.api.tvdb_client import TVDBClient


class TestTVDBFallbacks:
    """Tests for TVDB client fallback methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = None  # Will be initialized in each test
        
        # Mock responses for all episodes
        self.all_episodes_data = {
            "data": {
                "episodes": [
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
                    },
                    {
                        "id": 3,
                        "name": "Special 1",
                        "seasonNumber": 0,
                        "number": 1
                    },
                    {
                        "id": 4,
                        "name": "Episode 1",
                        "seasonNumber": 2,
                        "number": 1
                    }
                ]
            }
        }
        
    def test_fallback_episode_retrieval(self, mocker) -> None:
        """Test the fallback episode retrieval method."""
        # Setup session mock
        mock_session = mocker.Mock()
        mock_response = mocker.Mock()
        mock_response.json.return_value = self.all_episodes_data
        mock_session.get.return_value = mock_response
        
        # Patch requests.Session
        mocker.patch('requests.Session', return_value=mock_session)
        
        # Create the client instance
        client = TVDBClient(api_key="test_key")
        client._token = "test_token"
        
        # Run the test
        episodes = client._fallback_episode_retrieval(12345, 1, "Test Show")
        
        # Verify correct episodes were filtered
        assert len(episodes) == 2
        assert episodes[0]["name"] == "Episode 1" and episodes[0]["seasonNumber"] == 1
        assert episodes[1]["name"] == "Episode 2" and episodes[1]["seasonNumber"] == 1
        
    def test_fallback_episode_retrieval_season_0(self, mocker) -> None:
        """Test fallback retrieval for specials (season 0)."""
        # Setup session mock
        mock_session = mocker.Mock()
        mock_response = mocker.Mock()
        mock_response.json.return_value = self.all_episodes_data
        mock_session.get.return_value = mock_response
        mocker.patch('requests.Session', return_value=mock_session)
        
        # Create the client
        self.client = TVDBClient(api_key="test_key")
        self.client._token = "test_token"
        
        # Patch authenticate to avoid real API calls
        mocker.patch.object(self.client, 'authenticate')
        
        # Test fallback for season 0 (specials)
        episodes = self.client._fallback_episode_retrieval(12345, 0, "Test Show")
        
        # Verify correct episodes were filtered
        assert len(episodes) == 1
        assert episodes[0]["name"] == "Special 1" and episodes[0]["seasonNumber"] == 0
        
    def test_fallback_episode_retrieval_nonexistent_season(self, mocker) -> None:
        """Test fallback retrieval for a season that doesn't exist."""
        # Setup session mock
        mock_session = mocker.Mock()
        mock_response = mocker.Mock()
        mock_response.json.return_value = self.all_episodes_data
        mock_session.get.return_value = mock_response
        mocker.patch('requests.Session', return_value=mock_session)
        
        # Create the client
        self.client = TVDBClient(api_key="test_key")
        self.client._token = "test_token"
        
        # Patch authenticate to avoid real API calls
        mocker.patch.object(self.client, 'authenticate')
        
        # Test fallback for season 3 (doesn't exist)
        episodes = self.client._fallback_episode_retrieval(12345, 3, "Test Show")
        
        # Verify empty list is returned
        assert episodes == []
        
    def test_fallback_episode_retrieval_error(self, mocker) -> None:
        """Test error handling in fallback episode retrieval."""
        # Setup session mock that raises an exception
        mock_session = mocker.Mock()
        mock_session.get.side_effect = Exception("API error")
        mocker.patch('requests.Session', return_value=mock_session)
        
        # Create the client
        self.client = TVDBClient(api_key="test_key")
        self.client._token = "test_token"
        
        # Patch authenticate to avoid real API calls
        mocker.patch.object(self.client, 'authenticate')
        
        # Test fallback with error
        episodes = self.client._fallback_episode_retrieval(12345, 1, "Test Show")
        
        # Verify empty list is returned on error
        assert episodes == []
        
    def test_get_season_episodes_using_fallback(self, mocker) -> None:
        """Test that get_season_episodes uses the fallback when needed."""
        # Setup mocks
        mock_session = mocker.Mock()
        
        # First response is for series extended info
        mock_series_response = mocker.Mock()
        mock_series_response.json.return_value = {
            "data": {
                "name": "Test Show",
                "seasons": [
                    {
                        "id": 1001,
                        "number": 1,
                        "type": {"name": "Aired Order"}
                    }
                ]
            }
        }
        
        # Second response is for season episodes (with error)
        mock_season_error_response = mocker.Mock()
        mock_season_error_response.json.return_value = {
            "status": "error",
            "message": "Not found"
        }
        
        # Third response is for all episodes
        mock_all_episodes_response = mocker.Mock()
        mock_all_episodes_response.json.return_value = self.all_episodes_data
        
        # Set up the sequence of responses
        mock_session.get.side_effect = [
            mock_series_response,
            mock_season_error_response,
            mock_all_episodes_response
        ]
        mocker.patch('requests.Session', return_value=mock_session)
        
        # Create the client
        self.client = TVDBClient(api_key="test_key")
        self.client._token = "test_token"
        
        # Patch authenticate to avoid real API calls
        mocker.patch.object(self.client, 'authenticate')
        
        # Mock the fallback method
        mock_fallback = mocker.patch.object(self.client, '_fallback_episode_retrieval')
        mock_fallback.return_value = [{"name": "Fallback Episode"}]
        
        # Call the method
        episodes = self.client.get_season_episodes(12345, 1)
        
        # Verify fallback was called
        mock_fallback.assert_called_once_with(12345, 1, "Test Show") 