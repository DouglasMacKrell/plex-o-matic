"""TMDB API client for retrieving movie and TV show metadata."""

import time
import json
import requests
import logging
from typing import Dict, List, Optional, Any, cast
from functools import lru_cache

logger = logging.getLogger(__name__)

# TMDB API endpoints
BASE_URL = "https://api.themoviedb.org/3"
CONFIGURATION_URL = f"{BASE_URL}/configuration"
SEARCH_MOVIE_URL = f"{BASE_URL}/search/movie"
SEARCH_TV_URL = f"{BASE_URL}/search/tv"
MOVIE_DETAILS_URL = f"{BASE_URL}/movie"
TV_DETAILS_URL = f"{BASE_URL}/tv"


class TMDBRequestError(Exception):
    """Raised when a TMDB API request fails."""

    pass


class TMDBRateLimitError(Exception):
    """Raised when TMDB API rate limit is exceeded."""

    pass


class TMDBClient:
    """Client for interacting with the TMDB API."""

    def __init__(self, api_key: str, cache_size: int = 100, auto_retry: bool = False):
        """Initialize the TMDB API client.

        Args:
            api_key: The TMDB API key.
            cache_size: Maximum number of responses to cache.
            auto_retry: Whether to automatically retry requests when rate limited.
        """
        self.api_key = api_key
        self.cache_size = cache_size
        self.auto_retry = auto_retry
        self._config: Optional[Dict[str, Any]] = None

    def _get_params(self, additional_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get base parameters for API requests including API key.

        Args:
            additional_params: Additional query parameters to include.

        Returns:
            Dict with API key and any additional parameters.
        """
        params = {"api_key": self.api_key}
        if additional_params:
            params.update(additional_params)
        return params

    def _get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request to the TMDB API.

        Args:
            url: The URL to request.
            params: Optional query parameters.

        Returns:
            The JSON response data.

        Raises:
            TMDBRateLimitError: If rate limited.
            TMDBRequestError: If the request fails.
        """
        full_params = self._get_params(params)

        try:
            response = requests.get(url, params=full_params)

            if response.status_code == 200:
                data = response.json()
                return cast(Dict[str, Any], data)
            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"TMDB rate limit exceeded, retry after {retry_after} seconds")

                if self.auto_retry:
                    logger.info(f"Waiting {retry_after} seconds before retrying...")
                    time.sleep(retry_after)
                    return self._get(url, params)
                else:
                    raise TMDBRateLimitError(
                        f"Rate limit exceeded, retry after {retry_after} seconds"
                    )
            else:
                logger.error(f"TMDB request failed: {response.status_code} - {response.text}")
                raise TMDBRequestError(f"Request failed: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            logger.error(f"TMDB request failed: {e}")
            raise TMDBRequestError(f"Request failed: {e}")

    @lru_cache(maxsize=100)
    def _get_cached_key(self, cache_key: str) -> Dict[str, Any]:
        """A wrapper for _get that uses a string cache key instead of dict parameters.

        Args:
            cache_key: A string key representing the request URL and parameters.

        Returns:
            The cached response.
        """
        # Parse the cache_key to extract URL and params
        parts = cache_key.split("::")
        url = parts[0]
        params = json.loads(parts[1]) if len(parts) > 1 else None

        return self._get(url, params)

    def get_configuration(self) -> Dict[str, Any]:
        """Get TMDB API configuration including image URLs and sizes.

        Returns:
            TMDB API configuration data.
        """
        if self._config is None:
            self._config = self._get(CONFIGURATION_URL)
        return self._config if self._config is not None else {}

    def search_movie(self, query: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for movies by title.

        Args:
            query: The movie title to search for.
            year: Optional release year to filter results.

        Returns:
            A list of matching movies, or an empty list if none found.
        """
        params: Dict[str, Any] = {"query": query}
        if year is not None:
            params["year"] = str(year)

        cache_key = f"{SEARCH_MOVIE_URL}::{json.dumps(params, sort_keys=True)}"

        try:
            response = self._get_cached_key(cache_key)
            results = response.get("results", [])
            return cast(List[Dict[str, Any]], results)
        except TMDBRateLimitError:
            if self.auto_retry:
                # Clear the cache for this query
                self._get_cached_key.cache_clear()
                # Retry directly with non-cached method
                response = self._get(SEARCH_MOVIE_URL, params)
                results = response.get("results", [])
                return cast(List[Dict[str, Any]], results)
            else:
                raise

    def search_tv(
        self, query: str, first_air_date_year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search for TV shows by name.

        Args:
            query: The TV show name to search for.
            first_air_date_year: Optional first air date year to filter results.

        Returns:
            A list of matching TV shows, or an empty list if none found.
        """
        params: Dict[str, Any] = {"query": query}
        if first_air_date_year is not None:
            params["first_air_date_year"] = str(first_air_date_year)

        cache_key = f"{SEARCH_TV_URL}::{json.dumps(params, sort_keys=True)}"

        try:
            response = self._get_cached_key(cache_key)
            results = response.get("results", [])
            return cast(List[Dict[str, Any]], results)
        except TMDBRateLimitError:
            if self.auto_retry:
                # Clear the cache for this query
                self._get_cached_key.cache_clear()
                # Retry directly with non-cached method
                response = self._get(SEARCH_TV_URL, params)
                results = response.get("results", [])
                return cast(List[Dict[str, Any]], results)
            else:
                raise

    def get_movie_details(
        self, movie_id: int, append_to_response: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed information about a specific movie.

        Args:
            movie_id: The TMDB ID of the movie.
            append_to_response: Optional comma-separated list of additional data to include.

        Returns:
            Detailed movie information.
        """
        url = f"{MOVIE_DETAILS_URL}/{movie_id}"
        params = {}
        if append_to_response:
            params["append_to_response"] = append_to_response

        cache_key = f"{url}::{json.dumps(params, sort_keys=True)}"

        return self._get_cached_key(cache_key)

    def get_tv_details(
        self, tv_id: int, append_to_response: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed information about a specific TV show.

        Args:
            tv_id: The TMDB ID of the TV show.
            append_to_response: Optional comma-separated list of additional data to include.

        Returns:
            Detailed TV show information.
        """
        url = f"{TV_DETAILS_URL}/{tv_id}"
        params = {}
        if append_to_response:
            params["append_to_response"] = append_to_response

        cache_key = f"{url}::{json.dumps(params, sort_keys=True)}"

        return self._get_cached_key(cache_key)

    def get_tv_season(self, tv_id: int, season_number: int) -> Dict[str, Any]:
        """Get detailed information about a specific TV show season.

        Args:
            tv_id: The TMDB ID of the TV show.
            season_number: The season number.

        Returns:
            Detailed season information including episodes.
        """
        url = f"{TV_DETAILS_URL}/{tv_id}/season/{season_number}"
        cache_key = url

        return self._get_cached_key(cache_key)

    def get_poster_url(self, poster_path: str, size: str = "original") -> str:
        """Get the full URL for a poster image.

        Args:
            poster_path: The poster path from TMDB (e.g., "/abc123.jpg").
            size: The size of the image (e.g., "original", "w500").

        Returns:
            The full URL to the poster image.
        """
        config = self.get_configuration()
        base_url = config.get("images", {}).get("secure_base_url", "")

        if not base_url:
            logger.warning("No secure base URL found in configuration, using default")
            base_url = "https://image.tmdb.org/t/p/"

        # If the poster path already includes the base URL, return it as is
        if poster_path.startswith(("http://", "https://")):
            return poster_path

        # Otherwise, construct the full URL
        return f"{base_url}{size}{poster_path}"

    def clear_cache(self) -> None:
        """Clear the request cache."""
        self._get_cached_key.cache_clear()
        logger.info("TMDB API client cache cleared")
