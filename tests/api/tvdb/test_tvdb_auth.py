"""Tests for TVDB authentication functionality."""

import pytest
import requests

from plexomatic.api.tvdb_client import TVDBClient, TVDBAuthenticationError


class TestTVDBAuthentication:
    """Tests for TVDB authentication functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.api_key = "test_api_key"
        self.pin = "test_pin"

    def test_authentication_success(self, mocker) -> None:
        """Test successful authentication process."""
        # Set up the mock session
        mock_session = mocker.Mock()
        mocker.patch('plexomatic.api.tvdb_client.requests.Session', return_value=mock_session)
        
        # Create the client
        client = TVDBClient(api_key=self.api_key, pin=self.pin)
        
        # Test successful authentication
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"token": "mock_token"}}
        mock_session.post.return_value = mock_response

        client.authenticate()
        
        # Verify the post was called with correct headers (not json payload)
        mock_session.post.assert_called_once()
        args, kwargs = mock_session.post.call_args
        assert args[0] == "https://api4.thetvdb.com/v4/login"
        
        # Check that the headers contain the API key and PIN
        assert kwargs["headers"]["apikey"] == self.api_key
        assert kwargs["headers"]["pin"] == self.pin
        
        # Verify token is stored
        assert client._token == "mock_token"

    def test_authentication_v4(self, mocker) -> None:
        """Test that authenticate method correctly uses the v4 API."""
        # Set up the mock session
        mock_session = mocker.Mock()
        mocker.patch('plexomatic.api.tvdb_client.requests.Session', return_value=mock_session)
        
        # Create the client
        client = TVDBClient(api_key=self.api_key, pin=self.pin)
        
        # Setup mock response
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"token": "test_token"}}
        mock_session.post.return_value = mock_response

        # Call the authenticate method
        client.authenticate()

        # Verify correct endpoint and headers
        mock_session.post.assert_called_once()
        args, kwargs = mock_session.post.call_args

        # Verify the URL is v4
        assert args[0] == "https://api4.thetvdb.com/v4/login"

        # Verify the headers contain the API key and PIN
        assert kwargs["headers"]["apikey"] == self.api_key
        assert kwargs["headers"]["pin"] == self.pin

        # Verify token is stored
        assert client._token == "test_token"

    def test_authentication_no_pin(self, mocker) -> None:
        """Test authentication without a PIN."""
        # Set up the mock session
        mock_session = mocker.Mock()
        mocker.patch('plexomatic.api.tvdb_client.requests.Session', return_value=mock_session)
        
        # Create client without PIN
        client_no_pin = TVDBClient(api_key=self.api_key)
        client_no_pin._session = mock_session

        # Setup mock response
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"token": "test_token"}}
        mock_session.post.return_value = mock_response

        # Call the authenticate method
        client_no_pin.authenticate()

        # Verify headers only contains API key
        args, kwargs = mock_session.post.call_args
        assert kwargs["headers"]["apikey"] == self.api_key
        assert "pin" not in kwargs["headers"]

    def test_authentication_failure(self, mocker) -> None:
        """Test authentication failure."""
        # Set up the mock session
        mock_session = mocker.Mock()
        mocker.patch('plexomatic.api.tvdb_client.requests.Session', return_value=mock_session)
        
        # Create the client
        client = TVDBClient(api_key=self.api_key, pin=self.pin)
        client._session = mock_session

        # Create a response that raises an exception when raise_for_status is called
        mock_response = mocker.Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "401 Client Error: Unauthorized for url: https://api4.thetvdb.com/v4/login",
            response=mock_response
        )
        mock_response.text = "Invalid API key"
        mock_response.json.return_value = {"error": "Invalid credentials"}
        mock_session.post.return_value = mock_response

        with pytest.raises(TVDBAuthenticationError):
            client.authenticate()

    def test_is_authenticated(self) -> None:
        """Test the is_authenticated method."""
        # Create client without mocks since we're not making network calls
        client = TVDBClient(api_key=self.api_key)
        
        # Not authenticated
        client._token = None
        assert not client.is_authenticated()

        # With token
        client._token = "test_token"
        assert client.is_authenticated()
        
    def test_with_mock_fixture(self, mock_tvdb_client) -> None:
        """Test using the mock_tvdb_client fixture."""
        # Get the client and mock helper
        client, mock_api = mock_tvdb_client
        
        # Client should already have auth response mocked
        client.authenticate()
        
        # Verify token is set
        assert client._token == "test_token"