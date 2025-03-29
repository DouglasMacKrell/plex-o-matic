"""Test cases for the BaseAPIClient class."""

import pytest
from pytest_mock import MockerFixture
import requests
import json
from typing import Dict, Optional

from plexomatic.api.base_client import BaseAPIClient
from plexomatic.api.errors import (
    APIConnectionError,
    APITimeoutError,
    APIAuthenticationError,
    APIRequestError,
    APIResponseError,
    APIRateLimitError,
    APINotFoundError,
    APIServerError,
)


class MockAPIClient(BaseAPIClient):
    """Mock API client for testing."""

    def __init__(
        self,
        base_url: str = "https://api.example.com",
        cache_size: int = 100,
        auto_retry: bool = False,
        timeout: int = 10,
    ):
        """Initialize the mock API client."""
        super().__init__(base_url, cache_size, auto_retry, timeout)
        self.auth_token: Optional[str] = None

    def authenticate(self) -> None:
        """Mock authentication implementation."""
        self.auth_token = "mock_token"

    def _get_headers(self) -> Dict[str, str]:
        """Add authentication token to headers."""
        headers = super()._get_headers()
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers


class TestBaseAPIClient:
    """Test cases for the BaseAPIClient class."""

    def setup_method(self) -> None:
        """Set up the test case."""
        self.client = MockAPIClient()

    def test_initialization(self) -> None:
        """Test client initialization."""
        client = MockAPIClient()
        assert client.base_url == "https://api.example.com"
        assert client.cache_size == 100
        assert client.auto_retry is False
        assert client.timeout == 10

        # Custom initialization
        client = MockAPIClient(
            base_url="https://custom.api.com",
            cache_size=200,
            auto_retry=True,
            timeout=20,
        )
        assert client.base_url == "https://custom.api.com"
        assert client.cache_size == 200
        assert client.auto_retry is True
        assert client.timeout == 20

    def test_get_headers(self) -> None:
        """Test header generation."""
        # Default headers
        headers = self.client._get_headers()
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
        assert "Authorization" not in headers

        # With auth token
        self.client.authenticate()
        headers = self.client._get_headers()
        assert headers["Authorization"] == "Bearer mock_token"

    def test_successful_get_request(self, mocker: MockerFixture) -> None:
        """Test a successful GET request."""
        # Mock the session request method
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}

        mock_request = mocker.patch.object(self.client._session, "request")
        mock_request.return_value = mock_response

        # Make the request
        result = self.client.get("test")

        # Verify the result
        assert result == {"key": "value"}

        # Verify the request was made correctly
        mock_request.assert_called_once_with(
            method="GET",
            url="https://api.example.com/test",
            params=None,
            json=None,
            headers=self.client._get_headers(),
            timeout=10,
        )

    def test_successful_post_request(self, mocker: MockerFixture) -> None:
        """Test a successful POST request."""
        # Mock the session request method
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 123}

        mock_request = mocker.patch.object(self.client._session, "request")
        mock_request.return_value = mock_response

        # Make the request
        data = {"name": "test"}
        result = self.client.post("items", data=data)

        # Verify the result
        assert result == {"id": 123}

        # Verify the request was made correctly
        mock_request.assert_called_once_with(
            method="POST",
            url="https://api.example.com/items",
            params=None,
            json=data,
            headers=self.client._get_headers(),
            timeout=10,
        )

    def test_successful_put_request(self, mocker: MockerFixture) -> None:
        """Test a successful PUT request."""
        # Mock the session request method
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"updated": True}

        mock_request = mocker.patch.object(self.client._session, "request")
        mock_request.return_value = mock_response

        # Make the request
        data = {"name": "updated"}
        result = self.client.put("items/123", data=data)

        # Verify the result
        assert result == {"updated": True}

        # Verify the request was made correctly
        mock_request.assert_called_once_with(
            method="PUT",
            url="https://api.example.com/items/123",
            params=None,
            json=data,
            headers=self.client._get_headers(),
            timeout=10,
        )

    def test_successful_delete_request(self, mocker: MockerFixture) -> None:
        """Test a successful DELETE request."""
        # Mock the session request method
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"deleted": True}

        mock_request = mocker.patch.object(self.client._session, "request")
        mock_request.return_value = mock_response

        # Make the request
        result = self.client.delete("items/123")

        # Verify the result
        assert result == {"deleted": True}

        # Verify the request was made correctly
        mock_request.assert_called_once_with(
            method="DELETE",
            url="https://api.example.com/items/123",
            params=None,
            json=None,
            headers=self.client._get_headers(),
            timeout=10,
        )

    def test_caching(self, mocker: MockerFixture) -> None:
        """Test caching of GET requests."""
        # Mock the session request method
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}

        mock_request = mocker.patch.object(self.client._session, "request")
        mock_request.return_value = mock_response

        # Make the same request twice
        result1 = self.client.get("test")
        result2 = self.client.get("test")

        # Verify both calls returned the same result
        assert result1 == {"key": "value"}
        assert result2 == {"key": "value"}

        # Verify only one actual request was made
        assert mock_request.call_count == 1

        # Making a different request should make a new call
        self.client.get("different")
        assert mock_request.call_count == 2

    def test_clear_cache(self, mocker: MockerFixture) -> None:
        """Test cache clearing."""
        # Mock the cache_clear method on the cached request method
        mock_cache_clear = mocker.Mock()
        self.client._request_cached.cache_clear = mock_cache_clear

        # Clear the cache
        self.client.clear_cache()

        # Verify the cache was cleared
        mock_cache_clear.assert_called_once()

    def test_not_found_error(self, mocker: MockerFixture) -> None:
        """Test 404 response handling."""
        # Mock a 404 response
        mock_response = mocker.Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        mock_request = mocker.patch.object(self.client._session, "request")
        mock_request.return_value = mock_response

        # Make a request and verify it raises the correct error
        with pytest.raises(APINotFoundError) as excinfo:
            self.client.get("missing")

        assert "Resource not found" in str(excinfo.value)
        assert excinfo.value.status_code == 404

    def test_rate_limit_error(self, mocker: MockerFixture) -> None:
        """Test rate limit handling."""
        # Mock a 429 response
        mock_response = mocker.Mock()
        mock_response.status_code = 429
        mock_response.text = "Too Many Requests"
        mock_response.headers = {"Retry-After": "30"}

        mock_request = mocker.patch.object(self.client._session, "request")
        mock_request.return_value = mock_response

        # Make a request and verify it raises the correct error
        with pytest.raises(APIRateLimitError) as excinfo:
            self.client.get("rate-limited")

        assert "Rate limit" in str(excinfo.value)
        assert excinfo.value.status_code == 429
        assert excinfo.value.retry_after == 30

    def test_rate_limit_with_auto_retry(self, mocker: MockerFixture) -> None:
        """Test rate limit handling with auto-retry enabled."""
        # Create a client with auto_retry=True
        client = MockAPIClient(auto_retry=True)

        # Mock time.sleep to not actually sleep
        mock_sleep = mocker.patch("time.sleep")

        # Set up the mock responses - first 429, then 200
        mock_response_1 = mocker.Mock()
        mock_response_1.status_code = 429
        mock_response_1.text = "Too Many Requests"
        mock_response_1.headers = {"Retry-After": "2"}

        mock_response_2 = mocker.Mock()
        mock_response_2.status_code = 200
        mock_response_2.json.return_value = {"success": True}

        mock_request = mocker.patch.object(client._session, "request")
        # First call returns rate limit, second returns success
        mock_request.side_effect = [mock_response_1, mock_response_2]

        # Make the request
        result = client.get("test")

        # Verify the sleep was called
        mock_sleep.assert_called_once_with(2)

        # Verify two requests were made
        assert mock_request.call_count == 2

        # Verify the final result
        assert result == {"success": True}

    def test_authentication_error(self, mocker: MockerFixture) -> None:
        """Test authentication error handling."""
        # Mock a 401 response
        mock_response = mocker.Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        mock_request = mocker.patch.object(self.client._session, "request")
        mock_request.return_value = mock_response

        # Make a request and verify it raises the correct error
        with pytest.raises(APIAuthenticationError) as excinfo:
            self.client.get("protected")

        assert "Authentication error" in str(excinfo.value)
        assert excinfo.value.status_code == 401

    def test_server_error(self, mocker: MockerFixture) -> None:
        """Test server error handling."""
        # Mock a 500 response
        mock_response = mocker.Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_request = mocker.patch.object(self.client._session, "request")
        mock_request.return_value = mock_response

        # Make a request and verify it raises the correct error
        with pytest.raises(APIServerError) as excinfo:
            self.client.get("error")

        assert "Server error" in str(excinfo.value)
        assert excinfo.value.status_code == 500

    def test_connection_error(self, mocker: MockerFixture) -> None:
        """Test connection error handling."""
        # Mock a connection error
        mock_request = mocker.patch.object(self.client._session, "request")
        mock_request.side_effect = requests.ConnectionError("Connection refused")

        # Make a request and verify it raises the correct error
        with pytest.raises(APIConnectionError) as excinfo:
            self.client.get("unreachable")

        assert "Connection error" in str(excinfo.value)
        assert "Connection refused" in str(excinfo.value)

    def test_timeout_error(self, mocker: MockerFixture) -> None:
        """Test timeout error handling."""
        # Mock a timeout error
        mock_request = mocker.patch.object(self.client._session, "request")
        mock_request.side_effect = requests.Timeout("Request timed out")

        # Make a request and verify it raises the correct error
        with pytest.raises(APITimeoutError) as excinfo:
            self.client.get("slow")

        assert "timed out" in str(excinfo.value)

    def test_json_decode_error(self, mocker: MockerFixture) -> None:
        """Test JSON decode error handling."""
        # Mock a response with invalid JSON
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        mock_request = mocker.patch.object(self.client._session, "request")
        mock_request.return_value = mock_response

        # Make a request and verify it raises the correct error
        with pytest.raises(APIResponseError) as excinfo:
            self.client.get("bad-json")

        assert "JSON" in str(excinfo.value)

    def test_unexpected_error(self, mocker: MockerFixture) -> None:
        """Test handling of unexpected errors."""
        # Mock an unexpected error
        mock_request = mocker.patch.object(self.client._session, "request")
        mock_request.side_effect = Exception("Unexpected error")

        # Make a request and verify it raises the correct error
        with pytest.raises(APIRequestError) as excinfo:
            self.client.get("error")

        assert "Unexpected error" in str(excinfo.value)

    def test_additional_headers(self, mocker: MockerFixture) -> None:
        """Test adding additional headers to a request."""
        # Mock a successful response
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}

        mock_request = mocker.patch.object(self.client._session, "request")
        mock_request.return_value = mock_response

        # Make a request with additional headers
        additional_headers = {"X-Custom-Header": "value"}
        self.client.get("test", additional_headers=additional_headers)

        # Verify the additional headers were merged with the default headers
        called_headers = mock_request.call_args.kwargs["headers"]
        assert called_headers["X-Custom-Header"] == "value"
        assert called_headers["Content-Type"] == "application/json"  # Default header
