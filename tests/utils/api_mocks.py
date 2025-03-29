"""API mocking utilities for pytest.

This module provides pytest fixtures for mocking HTTP API responses
in tests, allowing for testing without making actual network requests.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import json
from typing import Dict, Any, Optional, Union, Callable


class MockResponse:
    """Utility for creating mock HTTP responses."""
    
    @staticmethod
    def success(data: Any, status_code: int = 200) -> Mock:
        """Create a successful mock response."""
        mock_resp = Mock()
        mock_resp.status_code = status_code
        mock_resp.ok = status_code < 400
        mock_resp.json.return_value = data
        mock_resp.text = json.dumps(data)
        mock_resp.content = json.dumps(data).encode('utf-8')
        mock_resp.raise_for_status = Mock()
        mock_resp.headers = {}
        return mock_resp
    
    @staticmethod
    def error(status_code: int = 404, error_msg: str = "Not Found") -> Mock:
        """Create an error mock response."""
        from requests.exceptions import HTTPError
        
        error_data = {"error": error_msg}
        mock_resp = Mock()
        mock_resp.status_code = status_code
        mock_resp.ok = False
        mock_resp.json.return_value = error_data
        mock_resp.text = json.dumps(error_data)
        mock_resp.content = json.dumps(error_data).encode('utf-8')
        mock_resp.headers = {}
        
        # Create a raise_for_status that raises an exception
        def raise_error(*args, **kwargs):
            raise HTTPError(f"{status_code} Error: {error_msg}", response=mock_resp)
        
        mock_resp.raise_for_status.side_effect = raise_error
        return mock_resp


class MockAPISession:
    """Mock session for API testing."""
    
    def __init__(self):
        """Initialize a MockAPISession."""
        self.responses = {}
        self.session = MagicMock()
        
        # Set up request methods
        for method in ['get', 'post', 'put', 'delete']:
            setattr(self.session, method, self._create_method_mock(method))
    
    def _create_method_mock(self, method: str) -> Callable:
        """Create a mock for a request method."""
        def method_mock(url, *args, **kwargs):
            # Find the response for this URL
            key = (method.lower(), url)
            if key in self.responses:
                response = self.responses[key]
                if callable(response):
                    return response(*args, **kwargs)
                return response
            
            # Default to 404 if no response is defined
            return MockResponse.error(
                status_code=404,
                error_msg=f"No mock response for {method.upper()} {url}"
            )
        
        return MagicMock(side_effect=method_mock)
    
    def add_response(self, method: str, url: str, response: Mock) -> None:
        """Add a response for a given method and URL."""
        self.responses[(method.lower(), url)] = response
    
    def add_json_response(self, method: str, url: str, data: Any) -> None:
        """Add a JSON response for a given method and URL."""
        self.responses[(method.lower(), url)] = MockResponse.success(data)


@pytest.fixture
def mock_api():
    """Pytest fixture that provides a MockAPISession object.
    
    Returns:
        MockAPISession: A configured mock API session
    """
    return MockAPISession()


@pytest.fixture
def mock_tvdb_client(mock_api, monkeypatch):
    """Pytest fixture that patches the TVDB client.
    
    Args:
        mock_api: The mock_api fixture
        monkeypatch: The pytest monkeypatch fixture
        
    Returns:
        tuple: (TVDBClient, MockAPISession) - the client and mock session
    """
    from plexomatic.api.tvdb_client import TVDBClient
    
    # Patch the requests.Session in tvdb_client
    monkeypatch.setattr(
        "plexomatic.api.tvdb_client.requests.Session", 
        lambda: mock_api.session
    )
    
    # Create and return the client
    client = TVDBClient(api_key="test_key")
    return client, mock_api 