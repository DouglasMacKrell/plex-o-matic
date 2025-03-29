import pytest
from pytest_mock import mocker
# Removed unittest.mock imports: Mock, patch

from plexomatic.api.tvdb_client import TVDBClient


class TestTVDBEpisodes:
    """Tests for TVDB episode-related functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = None  # Will be set up in each test
        
        # Mock responses for series data
        self.series_data = {
            "data": {
                "series": {
                    "id": 12345,
                    "name": "Test Show"
                },
                "seasons": [
                    {
                        "id": 1001,
                        "number": 1,
                        "type": {"name": "Aired Order"}
                    },
                    {
                        "id": 1002,
                        "number": 0,
                        "type": {"name": "Special"}
                    },
                    {
                        "id": 1003,
                        "number": 1,
                        "type": {"name": "Webisode"}
                    }
                ]
            }
        }
        
        # Mock responses for regular season episodes
        self.season1_episode_data = {
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
                    }
                ]
            }
        }
        
        # Mock responses for special episodes
        self.season0_episode_data = {
            "data": {
                "episodes": [
                    {
                        "id": 3,
                        "name": "Special 1",
                        "seasonNumber": 0,
                        "number": 1
                    }
                ]
            }
        }
        
        # Mock response for webisodes (empty)
        self.webisode_data = {
            "data": {
                "episodes": []
            }
        }
        
    def test_get_episodes_by_series_id(self, mocker):
        """Test getting episodes by series ID."""
        # Set up mock session and responses
        mock_session = mocker.Mock()
        
        # Create mock responses
        mock_series_response = mocker.Mock()
        mock_series_response.json.return_value = self.series_data
        
        mock_episode_response = mocker.Mock()
        mock_episode_response.json.return_value = self.season1_episode_data
        
        # Set up mock session
        mock_session.get.side_effect = [
            mock_series_response,
            mock_episode_response
        ]
        
        # Patch the session
        mocker.patch("requests.Session", return_value=mock_session)
        
        # Create client
        self.client = TVDBClient(api_key="test_key")
        self.client._token = "test_token"
        
        # Run test
        episodes = self.client.get_season_episodes(12345, 1)
        assert len(episodes) == 2
        assert episodes[0]["name"] == "Episode 1"
        assert episodes[1]["name"] == "Episode 2"
        
    def test_get_season_episodes(self, mocker):
        """Test getting episodes for a specific season."""
        # Set up mock session and responses
        mock_session = mocker.Mock()
        
        # Create mock responses
        mock_series_response = mocker.Mock()
        mock_series_response.json.return_value = self.series_data
        
        mock_episode_response = mocker.Mock()
        mock_episode_response.json.return_value = self.season1_episode_data
        
        # Set up mock session
        mock_session.get.side_effect = [
            mock_series_response,
            mock_episode_response
        ]
        
        # Patch the session
        mocker.patch("requests.Session", return_value=mock_session)
        
        # Create client
        self.client = TVDBClient(api_key="test_key")
        self.client._token = "test_token"
        
        # Run test
        episodes = self.client.get_season_episodes(12345, 1)
        assert len(episodes) == 2
        assert episodes[0]["name"] == "Episode 1"
        assert episodes[1]["name"] == "Episode 2"
        
    def test_get_season_episodes_with_type(self, mocker):
        """Test getting episodes for a specific season type."""
        # Set up mock session and responses
        mock_session = mocker.Mock()
        
        # Create mock responses
        mock_series_response = mocker.Mock()
        mock_series_response.json.return_value = self.series_data
        
        mock_episode_response = mocker.Mock()
        mock_episode_response.json.return_value = self.season0_episode_data
        
        # Set up mock session
        mock_session.get.side_effect = [
            mock_series_response,
            mock_episode_response
        ]
        
        # Patch the session
        mocker.patch("requests.Session", return_value=mock_session)
        
        # Create client
        self.client = TVDBClient(api_key="test_key")
        self.client._token = "test_token"
        
        # Run test
        episodes = self.client.get_season_episodes(12345, 0, "Special")
        assert len(episodes) == 1
        assert episodes[0]["name"] == "Special 1"
        
    def test_get_different_episode_types(self, mocker):
        """Test getting episodes of different types."""
        # Set up mock session and responses
        mock_session = mocker.Mock()
        
        # Create mock responses
        mock_series_response = mocker.Mock()
        mock_series_response.json.return_value = self.series_data
        
        mock_special_response = mocker.Mock()
        mock_special_response.json.return_value = self.season0_episode_data
        
        mock_webisode_response = mocker.Mock()
        mock_webisode_response.json.return_value = self.webisode_data
        
        # Set up mock session with different responses for multiple calls
        mock_session.get.side_effect = [
            mock_series_response,  # First call for specials
            mock_special_response,
            mock_series_response,  # Second call for webisodes
            mock_webisode_response
        ]
        
        # Patch the session
        mocker.patch("requests.Session", return_value=mock_session)
        
        # Create client
        self.client = TVDBClient(api_key="test_key")
        self.client._token = "test_token"
        
        # Get special episodes
        specials = self.client.get_season_episodes(12345, 0, "Special")
        assert len(specials) == 1
        assert specials[0]["name"] == "Special 1"
        
        # Get webisodes
        webisodes = self.client.get_season_episodes(12345, 1, "Webisode")
        assert len(webisodes) == 0  # No webisodes in mock data 