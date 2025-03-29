"""Test fixtures for TVDB client tests."""

import pytest
import json

from plexomatic.api.tvdb_client import TVDBClient


@pytest.fixture
def mock_response():
    """Utility fixture for creating mock HTTP responses."""
    
    class MockResponseFactory:
        """Factory for creating mock HTTP responses."""
        
        @staticmethod
        def success(data, status_code=200):
            """Create a successful mock response."""
            def create_mock(mocker):
                mock_resp = mocker.Mock()
                mock_resp.status_code = status_code
                mock_resp.ok = status_code < 400
                mock_resp.json.return_value = data
                mock_resp.text = json.dumps(data)
                mock_resp.content = json.dumps(data).encode('utf-8')
                mock_resp.raise_for_status = mocker.Mock()
                mock_resp.headers = {}
                return mock_resp
            return create_mock
        
        @staticmethod
        def error(status_code=404, error_msg="Not Found"):
            """Create an error mock response."""
            def create_mock(mocker):
                from requests.exceptions import HTTPError
                
                error_data = {"error": error_msg}
                mock_resp = mocker.Mock()
                mock_resp.status_code = status_code
                mock_resp.ok = False
                mock_resp.json.return_value = error_data
                mock_resp.text = json.dumps(error_data)
                mock_resp.content = json.dumps(error_data).encode('utf-8')
                mock_resp.headers = {}
                
                # Create a raise_for_status that raises an exception
                http_error = HTTPError(f"{status_code} Error: {error_msg}", response=mock_resp)
                mock_resp.raise_for_status.side_effect = http_error
                return mock_resp
            return create_mock
    
    return MockResponseFactory


@pytest.fixture
def mock_api(mocker):
    """Pytest fixture that provides a mocked API setup.
    
    This fixture creates a simpler mocking structure using pytest-mock,
    which is more reliable than trying to mock requests.Session directly.
    
    Args:
        mocker: The pytest-mock fixture
        
    Returns:
        object: A simple API mock object with methods to set up responses
    """
    # Create a class to manage mock responses
    class APITestHelper:
        def __init__(self):
            self.responses = {}
            self.session = mocker.Mock()
            
            # Set up mock post and get methods
            self.post_mock = mocker.Mock(side_effect=self._mock_request('post'))
            self.get_mock = mocker.Mock(side_effect=self._mock_request('get'))
            
            self.session.post = self.post_mock
            self.session.get = self.get_mock
            
            # Patch requests.Session
            mocker.patch('requests.Session', return_value=self.session)
        
        def _mock_request(self, method):
            def request_func(url, *args, **kwargs):
                key = (method, url)
                if key in self.responses:
                    return self.responses[key]
                # Create a mock error response
                from requests.exceptions import HTTPError
                error_data = {"error": f"No mock response for {method.upper()} {url}"}
                mock_resp = mocker.Mock()
                mock_resp.status_code = 404
                mock_resp.ok = False
                mock_resp.json.return_value = error_data
                mock_resp.text = json.dumps(error_data)
                mock_resp.content = json.dumps(error_data).encode('utf-8')
                http_error = HTTPError(f"404 Error: Not Found", response=mock_resp)
                mock_resp.raise_for_status.side_effect = http_error
                return mock_resp
            return request_func
        
        def add_response(self, method, url, response):
            """Add a mock response for a specific method and URL."""
            self.responses[(method, url)] = response
        
        def add_json_response(self, method, url, data):
            """Add a JSON response for a specific method and URL."""
            # Create a success response
            mock_resp = mocker.Mock()
            mock_resp.status_code = 200
            mock_resp.ok = True
            mock_resp.json.return_value = data
            mock_resp.text = json.dumps(data)
            mock_resp.content = json.dumps(data).encode('utf-8')
            mock_resp.raise_for_status = mocker.Mock()
            mock_resp.headers = {}
            self.responses[(method, url)] = mock_resp
    
    # Create and return the helper
    return APITestHelper()


@pytest.fixture
def mock_tvdb_client(mock_api):
    """Pytest fixture that provides a pre-configured TVDBClient.
    
    Args:
        mock_api: The mock_api fixture
        
    Returns:
        tuple: (TVDBClient, APITestHelper) - the client and mock API helper
    """
    # Set up default authentication response
    mock_api.add_json_response(
        "post", 
        "https://api4.thetvdb.com/v4/login", 
        {"data": {"token": "test_token"}}
    )
    
    # Create the client
    client = TVDBClient(api_key="test_key")
    
    # Return the client and the mock API helper
    return client, mock_api 