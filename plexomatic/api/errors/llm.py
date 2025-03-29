"""LLM-specific API error classes."""

from plexomatic.api.errors import (
    APIError,
    APIAuthenticationError,
    APIRequestError,
    APIRateLimitError,
    APINotFoundError,
    APIResourceNotAvailableError,
)


class LLMError(APIError):
    """Base class for all LLM API errors."""

    pass


class LLMAuthenticationError(APIAuthenticationError, LLMError):
    """Raised when authentication with LLM API fails."""

    pass


class LLMRequestError(APIRequestError, LLMError):
    """Raised when an LLM API request fails."""

    pass


class LLMRateLimitError(APIRateLimitError, LLMError):
    """Raised when LLM API rate limit is exceeded."""

    pass


class LLMNotFoundError(APINotFoundError, LLMError):
    """Raised when a resource is not found on the LLM API."""

    pass


class LLMModelNotAvailableError(APIResourceNotAvailableError, LLMError):
    """Raised when a specific LLM model is not available."""

    def __init__(self, message: str, model_name: str, status_code: int = None):
        """Initialize the model not available error.

        Args:
            message: The error message.
            model_name: Name of the model that is not available.
            status_code: Optional HTTP status code.
        """
        self.model_name = model_name
        super().__init__(message, status_code)


class LLMContentFilterError(LLMError):
    """Raised when content is flagged by the LLM's content filter."""

    def __init__(self, message: str, filtered_content: str = None, status_code: int = None):
        """Initialize the content filter error.

        Args:
            message: The error message.
            filtered_content: The content that was filtered.
            status_code: Optional HTTP status code.
        """
        self.filtered_content = filtered_content
        super().__init__(message, status_code)


class LLMContextLengthExceededError(LLMError):
    """Raised when the input context length exceeds the model's limit."""

    def __init__(self, message: str, max_tokens: int = None, status_code: int = None):
        """Initialize the context length exceeded error.

        Args:
            message: The error message.
            max_tokens: The maximum number of tokens allowed.
            status_code: Optional HTTP status code.
        """
        self.max_tokens = max_tokens
        super().__init__(message, status_code)
