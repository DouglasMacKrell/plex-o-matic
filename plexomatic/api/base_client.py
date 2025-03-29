"""Base API client with common functionality for all API clients."""

import time
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Type, TypeVar, Union
from functools import lru_cache

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

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
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="BaseAPIClient")
ResponseType = Union[Dict[str, Any], List[Dict[str, Any]], List[Any]]


class BaseAPIClient(ABC):
    """Base class for all API clients with common functionality."""

    def __init__(
        self,
        base_url: str,
        cache_size: int = 100,
        auto_retry: bool = False,
        timeout: int = 10,
    ):
        """Initialize the base API client.

        Args:
            base_url: The base URL for the API.
            cache_size: Maximum number of responses to cache.
            auto_retry: Whether to automatically retry requests when rate limited.
            timeout: Timeout for API requests in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.cache_size = cache_size
        self.auto_retry = auto_retry
        self.timeout = timeout
        self._session = requests.Session()
        self._setup_cache()

    def _setup_cache(self) -> None:
        """Set up the cache with the specified size."""
        # Apply the lru_cache decorator to the appropriate method
        self._request_cached = lru_cache(maxsize=self.cache_size)(self._request_uncached)

    def clear_cache(self) -> None:
        """Clear the request cache."""
        self._request_cached.cache_clear()
        logger.info(f"{self.__class__.__name__} cache cleared")

    def _get_headers(self) -> Dict[str, str]:
        """Get the headers to use for API requests.

        This method should be overridden by subclasses if they need
        to add authentication headers or other custom headers.

        Returns:
            A dictionary of HTTP headers.
        """
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _handle_response_error(
        self, response: requests.Response, url: str, error_class: Type[APIError] = APIRequestError
    ) -> None:
        """Handle error responses from the API.

        Args:
            response: The HTTP response object.
            url: The URL that was requested.
            error_class: The error class to use for the exception.

        Raises:
            APINotFoundError: For 404 responses.
            APIRateLimitError: For 429 responses.
            APIAuthenticationError: For 401 and 403 responses.
            APIServerError: For 5XX responses.
            APIResponseError: For other error responses.
        """
        if response.status_code == 404:
            logger.warning(f"Resource not found at {url}")
            raise APINotFoundError(f"Resource not found: {url}")

        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_seconds = int(retry_after) if retry_after and retry_after.isdigit() else 60
            logger.warning(f"Rate limit exceeded. Retry after {retry_seconds} seconds")

            if self.auto_retry:
                logger.info("Auto-retrying after rate limit cooldown")
                time.sleep(retry_seconds)
                # Note: The caller needs to retry the request
                return

            raise APIRateLimitError(
                f"Rate limit exceeded. Retry after {retry_seconds} seconds",
                retry_after=retry_seconds,
            )

        elif response.status_code in (401, 403):
            logger.error(f"Authentication error: {response.status_code} - {response.text}")
            raise APIAuthenticationError(
                f"Authentication error: {response.status_code} - {response.text}",
                status_code=response.status_code,
            )

        elif 500 <= response.status_code < 600:
            logger.error(f"Server error: {response.status_code} - {response.text}")
            raise APIServerError(
                f"Server error: {response.status_code} - {response.text}",
                status_code=response.status_code,
            )

        else:
            logger.error(f"API error: {response.status_code} - {response.text}")
            raise error_class(
                f"API error: {response.status_code} - {response.text}",
                status_code=response.status_code,
            )

    def _request_uncached(
        self, method: str, url: str, params_str: str, data_str: str, headers_str: str
    ) -> Any:
        """Make an uncached request to the API.

        Args:
            method: HTTP method (GET, POST, etc.).
            url: The URL to request.
            params_str: JSON string of query parameters.
            data_str: JSON string of request body.
            headers_str: JSON string of additional headers.

        Returns:
            The JSON response data.

        Raises:
            APIConnectionError: For connection errors.
            APITimeoutError: For timeout errors.
            APIResponseError: For JSON parsing errors.
            APIRequestError: For other request errors.
        """
        params = json.loads(params_str) if params_str != "{}" else None
        data = json.loads(data_str) if data_str != "{}" else None
        additional_headers = json.loads(headers_str) if headers_str != "{}" else {}

        # Combine default headers with additional headers
        headers = self._get_headers()
        headers.update(additional_headers)

        try:
            response = self._session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    raise APIResponseError(f"Failed to parse JSON response: {e}")

            self._handle_response_error(response, url)

            # If _handle_response_error doesn't raise an exception (e.g., auto_retry is True for rate limiting)
            # then we need to retry the request - this would typically be handled by the caller
            return None

        except Timeout as e:
            logger.error(f"Request timeout: {e}")
            raise APITimeoutError(f"Request timed out: {e}")

        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise APIConnectionError(f"Connection error: {e}")

        except RequestException as e:
            logger.error(f"Request failed: {e}")
            raise APIRequestError(f"Request failed: {e}")

    def _request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        additional_headers: Optional[Dict[str, str]] = None,
        use_cache: bool = True,
    ) -> Any:
        """Make a request to the API, with optional caching.

        Args:
            method: HTTP method (GET, POST, etc.).
            url: The URL to request.
            params: Optional query parameters.
            data: Optional request body.
            additional_headers: Optional additional headers.
            use_cache: Whether to use the cache (only for GET requests).

        Returns:
            The JSON response data.

        Raises:
            APIError: For any API errors.
        """
        # Only cache GET requests
        if method != "GET":
            use_cache = False

        # Convert dictionaries to strings for cache key
        params_str = json.dumps(params, sort_keys=True) if params else "{}"
        data_str = json.dumps(data, sort_keys=True) if data else "{}"
        headers_str = json.dumps(additional_headers, sort_keys=True) if additional_headers else "{}"

        # Make the request, leveraging the cache if appropriate
        try:
            if use_cache:
                result = self._request_cached(method, url, params_str, data_str, headers_str)
            else:
                result = self._request_uncached(method, url, params_str, data_str, headers_str)

            # For auto_retry with rate limiting - the result will be None if we need to retry
            if result is None and self.auto_retry:
                # Retry the request - will use the same parameters
                return self._request_uncached(method, url, params_str, data_str, headers_str)

            return result

        except (
            APIError,
            APIConnectionError,
            APITimeoutError,
            APIAuthenticationError,
            APIRequestError,
            APIResponseError,
            APIRateLimitError,
            APINotFoundError,
            APIServerError,
        ):
            # Propagate all specific API errors
            raise

        except Exception as e:
            # Catch-all for unexpected errors only
            logger.error(f"Unexpected error in API request: {e}")
            raise APIRequestError(f"Unexpected error: {e}")

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        additional_headers: Optional[Dict[str, str]] = None,
        use_cache: bool = True,
    ) -> Any:
        """Make a GET request to the API.

        Args:
            endpoint: The API endpoint (will be appended to base_url).
            params: Optional query parameters.
            additional_headers: Optional additional headers.
            use_cache: Whether to use the cache.

        Returns:
            The JSON response data.

        Raises:
            APIError: For any API errors.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return self._request("GET", url, params, None, additional_headers, use_cache)

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        additional_headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make a POST request to the API.

        Args:
            endpoint: The API endpoint (will be appended to base_url).
            data: Optional request body.
            params: Optional query parameters.
            additional_headers: Optional additional headers.

        Returns:
            The JSON response data.

        Raises:
            APIError: For any API errors.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return self._request("POST", url, params, data, additional_headers, use_cache=False)

    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        additional_headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make a PUT request to the API.

        Args:
            endpoint: The API endpoint (will be appended to base_url).
            data: Optional request body.
            params: Optional query parameters.
            additional_headers: Optional additional headers.

        Returns:
            The JSON response data.

        Raises:
            APIError: For any API errors.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return self._request("PUT", url, params, data, additional_headers, use_cache=False)

    def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        additional_headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make a DELETE request to the API.

        Args:
            endpoint: The API endpoint (will be appended to base_url).
            params: Optional query parameters.
            additional_headers: Optional additional headers.

        Returns:
            The JSON response data.

        Raises:
            APIError: For any API errors.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return self._request("DELETE", url, params, None, additional_headers, use_cache=False)

    @abstractmethod
    def authenticate(self) -> None:
        """Authenticate with the API.

        This method should be implemented by subclasses to handle API-specific
        authentication. It should set up any necessary authentication state
        (e.g., tokens) that will be used by _get_headers().

        Raises:
            APIAuthenticationError: If authentication fails.
        """
        pass
