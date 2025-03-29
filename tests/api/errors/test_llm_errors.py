"""Test cases for the LLM-specific API error classes."""

from plexomatic.api.errors import (
    APIError,
    APIAuthenticationError,
    APIRequestError,
    APIRateLimitError,
    APINotFoundError,
    APIResourceNotAvailableError,
)
from plexomatic.api.errors.llm import (
    LLMError,
    LLMAuthenticationError,
    LLMRequestError,
    LLMRateLimitError,
    LLMNotFoundError,
    LLMModelNotAvailableError,
    LLMContentFilterError,
    LLMContextLengthExceededError,
)


class TestLLMErrors:
    """Test cases for the LLM-specific API error classes."""

    def test_llm_error_base_class(self) -> None:
        """Test the base LLMError class."""
        error = LLMError("LLM error message")
        assert isinstance(error, APIError)
        assert str(error) == "LLM error message"
        assert error.message == "LLM error message"
        assert error.status_code is None

    def test_llm_authentication_error(self) -> None:
        """Test the LLMAuthenticationError class."""
        error = LLMAuthenticationError("Auth error", 401)
        assert isinstance(error, APIAuthenticationError)
        assert isinstance(error, LLMError)
        assert isinstance(error, APIError)
        assert str(error) == "Auth error"
        assert error.status_code == 401

    def test_llm_request_error(self) -> None:
        """Test the LLMRequestError class."""
        error = LLMRequestError("Request error", 400)
        assert isinstance(error, APIRequestError)
        assert isinstance(error, LLMError)
        assert isinstance(error, APIError)
        assert str(error) == "Request error"
        assert error.status_code == 400

    def test_llm_rate_limit_error(self) -> None:
        """Test the LLMRateLimitError class."""
        error = LLMRateLimitError("Rate limited", 30, 429)
        assert isinstance(error, APIRateLimitError)
        assert isinstance(error, LLMError)
        assert isinstance(error, APIError)
        assert str(error) == "Rate limited"
        assert error.status_code == 429
        assert error.retry_after == 30

    def test_llm_not_found_error(self) -> None:
        """Test the LLMNotFoundError class."""
        error = LLMNotFoundError("Resource not found", "resource-123")
        assert isinstance(error, APINotFoundError)
        assert isinstance(error, LLMError)
        assert isinstance(error, APIError)
        assert str(error) == "Resource not found"
        assert error.status_code == 404
        assert error.resource_id == "resource-123"

    def test_llm_model_not_available_error(self) -> None:
        """Test the LLMModelNotAvailableError class."""
        error = LLMModelNotAvailableError("Model not available", "gpt-5")
        assert isinstance(error, APIResourceNotAvailableError)
        assert isinstance(error, LLMError)
        assert isinstance(error, APIError)
        assert str(error) == "Model not available"
        assert error.model_name == "gpt-5"
        assert error.status_code is None

        # With status code
        error = LLMModelNotAvailableError("Model not available", "gpt-5", 404)
        assert error.status_code == 404

    def test_llm_content_filter_error(self) -> None:
        """Test the LLMContentFilterError class."""
        error = LLMContentFilterError("Content filtered")
        assert isinstance(error, LLMError)
        assert isinstance(error, APIError)
        assert str(error) == "Content filtered"
        assert error.filtered_content is None

        # With filtered content
        error = LLMContentFilterError("Content filtered", "inappropriate content")
        assert error.filtered_content == "inappropriate content"

    def test_llm_context_length_exceeded_error(self) -> None:
        """Test the LLMContextLengthExceededError class."""
        error = LLMContextLengthExceededError("Context length exceeded")
        assert isinstance(error, LLMError)
        assert isinstance(error, APIError)
        assert str(error) == "Context length exceeded"
        assert error.max_tokens is None

        # With max tokens
        error = LLMContextLengthExceededError("Context length exceeded", 4096)
        assert error.max_tokens == 4096

    def test_error_catch_as_parent(self) -> None:
        """Test catching LLM errors as their parent classes."""
        # Catch as LLMError
        try:
            raise LLMRateLimitError("Rate limited", 30)
        except LLMError as e:
            assert isinstance(e, LLMRateLimitError)
            assert e.retry_after == 30

        # Catch as APIRateLimitError
        try:
            raise LLMRateLimitError("Rate limited", 30)
        except APIRateLimitError as e:
            assert isinstance(e, LLMRateLimitError)
            assert e.retry_after == 30

        # Catch specific LLM errors
        try:
            raise LLMModelNotAvailableError("Model not available", "gpt-5")
        except LLMModelNotAvailableError as e:
            assert e.model_name == "gpt-5"
