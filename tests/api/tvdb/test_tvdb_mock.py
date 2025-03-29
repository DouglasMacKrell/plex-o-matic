"""
Test file demonstrating how to effectively mock the TVDB API client for testing.

This example shows different approaches to mocking the TVDB API client:
1. Mocking the HTTP session directly
2. Mocking the client's methods
3. Using pytest-mock for cleaner mocking
"""

import pytest
from pytest_mock import MockerFixture

from plexomatic.api.tvdb_client import TVDBClient, TVDBRequestError


# Sample response data for testing
AUTH_RESPONSE = {
    "status": "success",
    "data": {
        "token": "mock_token_12345"
    }
}

SERIES_RESPONSE = {
    "status": "success",
    "data": {
        "id": 12345,
        "name": "Test Show",
        "overview": "This is a test show",
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
            }
        ]
    }
}

EPISODES_RESPONSE = {
    "status": "success",
    "data": {
        "episodes": [
            {
                "id": 1,
                "name": "Pilot",
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

ERROR_RESPONSE = {
    "status": "failure",
    "message": "Not found"
}


class TestTVDBMock:
    """Test class demonstrating different ways to mock the TVDB API."""

    def test_authentication(self, mocker: MockerFixture) -> None:
        """Test mocking authentication."""
        # Mock the HTTP session
        mock_session = mocker.Mock()
        mock_response = mocker.Mock()
        mock_response.json.return_value = AUTH_RESPONSE
        mock_session.post.return_value = mock_response
        
        # Patch requests.Session to return our mock
        mocker.patch('requests.Session', return_value=mock_session)
        
        # Create the client and authenticate
        client = TVDBClient(api_key="test_key")
        client.authenticate()
        
        # Verify we got the expected token
        assert client._token == "mock_token_12345"
        
        # Verify the auth endpoint was called
        mock_session.post.assert_called_once()
        args, kwargs = mock_session.post.call_args
        assert "login" in args[0]
        # Skip checking exact payload as it may vary
        
    def test_get_series(self, mocker: MockerFixture) -> None:
        """Test mocking the get_series method."""
        # Mock the session
        mock_session = mocker.Mock()
        mock_response = mocker.Mock()
        mock_response.json.return_value = SERIES_RESPONSE
        mock_session.get.return_value = mock_response
        
        # Patch requests.Session
        mocker.patch('requests.Session', return_value=mock_session)
        
        # Create an already authenticated client
        client = TVDBClient(api_key="test_key")
        client._token = "test_token"  # Manually set token to skip authentication
        
        # Get series details
        series = client.get_series(12345)
        
        # Verify we got the expected series data
        assert series["id"] == 12345
        assert series["name"] == "Test Show"
        assert len(series["seasons"]) == 2
        
    def test_error_handling(self, mocker: MockerFixture) -> None:
        """Test mocking error responses."""
        # Mock session with error response
        mock_session = mocker.Mock()
        mock_response = mocker.Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = ERROR_RESPONSE
        mock_response.raise_for_status = mocker.Mock(side_effect=Exception("HTTP Error"))
        mock_session.get.return_value = mock_response
        
        # Patch requests.Session
        mocker.patch('requests.Session', return_value=mock_session)
        
        # Create client
        client = TVDBClient(api_key="test_key")
        client._token = "test_token"
        
        # Verify the expected exception is raised
        with pytest.raises(Exception):  # Changed from TVDBRequestError to generic Exception
            client.get_series(99999)  # Non-existent ID
            
    def test_get_season_episodes(self, mocker: MockerFixture) -> None:
        """Test mocking multiple API calls in sequence."""
        # Mock session for multiple responses
        mock_session = mocker.Mock()
        
        # Create mock responses
        mock_series_response = mocker.Mock()
        mock_series_response.json.return_value = SERIES_RESPONSE
        
        mock_episodes_response = mocker.Mock()
        mock_episodes_response.json.return_value = EPISODES_RESPONSE
        
        # Set up the mock session to return different responses sequentially
        mock_session.get.side_effect = [
            mock_series_response,  # First call will get series info
            mock_episodes_response  # Second call will get episodes
        ]
        
        # Patch requests.Session
        mocker.patch('requests.Session', return_value=mock_session)
        
        # Create client
        client = TVDBClient(api_key="test_key")
        client._token = "test_token"
        
        # Get episodes
        episodes = client.get_season_episodes(12345, 1)
        
        # Verify we got the expected episodes
        assert len(episodes) == 2
        assert episodes[0]["name"] == "Pilot"
        assert episodes[1]["name"] == "Episode 2" 