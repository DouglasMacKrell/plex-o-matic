"""Test cases for the common API error classes."""

from plexomatic.api.errors import (
    APIError,
    APIConnectionError,
    APITimeoutError,
    APIAuthenticationError,
    APIRequestError,
    APIResponseError,
    APIRateLimitError,
    APINotFoundError,
    APIServerError,
    APIClientError,
    APIResourceNotAvailableError,
)


class TestAPIErrors:
    """Test cases for the common API error classes."""

    def test_api_error_base_class(self) -> None:
        """Test the base APIError class."""
        error = APIError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.status_code is None

        # With status code
        error = APIError("Error with status", 500)
        assert error.message == "Error with status"
        assert error.status_code == 500

    def test_api_connection_error(self) -> None:
        """Test the APIConnectionError class."""
        error = APIConnectionError("Connection error")
        assert isinstance(error, APIError)
        assert str(error) == "Connection error"
        assert error.status_code is None

    def test_api_timeout_error(self) -> None:
        """Test the APITimeoutError class."""
        error = APITimeoutError("Timeout error")
        assert isinstance(error, APIConnectionError)
        assert isinstance(error, APIError)
        assert str(error) == "Timeout error"

    def test_api_authentication_error(self) -> None:
        """Test the APIAuthenticationError class."""
        error = APIAuthenticationError("Auth error", 401)
        assert isinstance(error, APIError)
        assert str(error) == "Auth error"
        assert error.status_code == 401

    def test_api_request_error(self) -> None:
        """Test the APIRequestError class."""
        error = APIRequestError("Request error", 400)
        assert isinstance(error, APIError)
        assert str(error) == "Request error"
        assert error.status_code == 400

    def test_api_response_error(self) -> None:
        """Test the APIResponseError class."""
        error = APIResponseError("Response parsing error")
        assert isinstance(error, APIError)
        assert str(error) == "Response parsing error"

    def test_api_rate_limit_error(self) -> None:
        """Test the APIRateLimitError class."""
        error = APIRateLimitError("Rate limited", 30)
        assert isinstance(error, APIError)
        assert str(error) == "Rate limited"
        assert error.status_code == 429
        assert error.retry_after == 30

        # Without retry_after
        error = APIRateLimitError("Rate limited")
        assert error.retry_after is None
        assert error.status_code == 429

    def test_api_not_found_error(self) -> None:
        """Test the APINotFoundError class."""
        error = APINotFoundError("Resource not found", "resource-123")
        assert isinstance(error, APIRequestError)
        assert isinstance(error, APIError)
        assert str(error) == "Resource not found"
        assert error.status_code == 404
        assert error.resource_id == "resource-123"

        # Without resource_id
        error = APINotFoundError("Not found")
        assert error.resource_id is None
        assert error.status_code == 404

    def test_api_server_error(self) -> None:
        """Test the APIServerError class."""
        error = APIServerError("Server error", 500)
        assert isinstance(error, APIError)
        assert str(error) == "Server error"
        assert error.status_code == 500

    def test_api_client_error(self) -> None:
        """Test the APIClientError class."""
        error = APIClientError("Client configuration error")
        assert isinstance(error, APIError)
        assert str(error) == "Client configuration error"

    def test_api_resource_not_available_error(self) -> None:
        """Test the APIResourceNotAvailableError class."""
        error = APIResourceNotAvailableError("Model not available")
        assert isinstance(error, APIError)
        assert str(error) == "Model not available"

    def test_error_inheritance(self) -> None:
        """Test the inheritance hierarchy of error classes."""
        # Check exception handling based on inheritance
        try:
            raise APINotFoundError("Resource not found")
        except APIRequestError as e:
            assert isinstance(e, APIRequestError)
            assert str(e) == "Resource not found"

        # Check handling rate limit errors
        try:
            raise APIRateLimitError("Rate limited", 30)
        except APIError as e:
            assert isinstance(e, APIRateLimitError)
            assert e.retry_after == 30
