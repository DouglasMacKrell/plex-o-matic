"""TVDB API client for retrieving TV show metadata."""
import os
import time
import requests
import logging
import json
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta, timezone
from functools import lru_cache

logger = logging.getLogger(__name__)

# TVDB API endpoints
BASE_URL = "https://api.thetvdb.com"
AUTH_URL = f"{BASE_URL}/login"
SEARCH_SERIES_URL = f"{BASE_URL}/search/series"
SERIES_URL = f"{BASE_URL}/series"
EPISODES_URL = f"{BASE_URL}/series/{{series_id}}/episodes"


class TVDBAuthenticationError(Exception):
    """Raised when authentication with TVDB API fails."""
    pass


class TVDBRequestError(Exception):
    """Raised when a TVDB API request fails."""
    pass


class TVDBRateLimitError(Exception):
    """Raised when TVDB API rate limit is exceeded."""
    pass


class TVDBClient:
    """Client for interacting with the TVDB API."""

    def __init__(self, api_key: str, cache_size: int = 100, auto_retry: bool = False):
        """Initialize the TVDB API client.
        
        Args:
            api_key: The TVDB API key.
            cache_size: Maximum number of responses to cache.
            auto_retry: Whether to automatically retry requests when rate limited.
        """
        self.api_key = api_key
        self.token = None
        self.token_expires_at = None
        self.auto_retry = auto_retry
        self.cache_size = cache_size
    
    def authenticate(self) -> None:
        """Authenticate with the TVDB API and get an access token."""
        payload = {"apikey": self.api_key}
        
        try:
            response = requests.post(AUTH_URL, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["data"]["token"]
                # Token expires after 24 hours
                self.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
                logger.info("Successfully authenticated with TVDB API")
            else:
                logger.error(f"TVDB authentication failed: {response.status_code} - {response.text}")
                raise TVDBAuthenticationError(f"Failed to authenticate: {response.status_code} - {response.text}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"TVDB authentication request failed: {e}")
            raise TVDBRequestError(f"Request failed: {e}")
    
    def _ensure_authenticated(self) -> None:
        """Ensure the client is authenticated, re-authenticating if necessary."""
        if self.token is None or (
            self.token_expires_at is not None and 
            datetime.now(timezone.utc) >= self.token_expires_at
        ):
            self.authenticate()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests including authorization token."""
        self._ensure_authenticated()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request to the TVDB API.
        
        Args:
            url: The URL to request.
            params: Optional query parameters.
            
        Returns:
            The JSON response data.
            
        Raises:
            TVDBAuthenticationError: If authentication fails.
            TVDBRateLimitError: If rate limited.
            TVDBRequestError: If the request fails.
        """
        self._ensure_authenticated()
        headers = self._get_headers()
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                # Token may have expired, try to re-authenticate
                self.token = None
                self._ensure_authenticated()
                # Retry with new token
                headers = self._get_headers()
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"TVDB request failed after re-auth: {response.status_code} - {response.text}")
                    raise TVDBRequestError(f"Request failed: {response.status_code} - {response.text}")
            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"TVDB rate limit exceeded, retry after {retry_after} seconds")
                
                if self.auto_retry:
                    logger.info(f"Waiting {retry_after} seconds before retrying...")
                    time.sleep(retry_after)
                    return self._get(url, params)
                else:
                    raise TVDBRateLimitError(f"Rate limit exceeded, retry after {retry_after} seconds")
            else:
                logger.error(f"TVDB request failed: {response.status_code} - {response.text}")
                raise TVDBRequestError(f"Request failed: {response.status_code} - {response.text}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"TVDB request failed: {e}")
            raise TVDBRequestError(f"Request failed: {e}")
    
    @lru_cache(maxsize=100)
    def _get_cached_key(self, cache_key: str) -> Dict[str, Any]:
        """A wrapper for _get that uses a string cache key instead of dict parameters.
        
        Args:
            cache_key: A string key representing the request URL and parameters.
            
        Returns:
            The cached response.
        """
        # Parse the cache_key to extract URL and params
        parts = cache_key.split('::')
        url = parts[0]
        params = json.loads(parts[1]) if len(parts) > 1 else None
        
        return self._get(url, params)
    
    def get_series_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Search for TV series by name.
        
        Args:
            name: The name of the series to search for.
            
        Returns:
            A list of matching series, or an empty list if none found.
        """
        params = {"name": name}
        cache_key = f"{SEARCH_SERIES_URL}::{json.dumps(params, sort_keys=True)}"
        
        try:
            response = self._get_cached_key(cache_key)
            return response.get("data", [])
        except TVDBRateLimitError:
            # If cached function raises rate limit error and auto_retry is enabled
            if self.auto_retry:
                # Clear the cache for this query
                self._get_cached_key.cache_clear()
                # Retry directly with non-cached method
                return self._get(SEARCH_SERIES_URL, params).get("data", [])
            else:
                raise
    
    def get_series_by_id(self, series_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific TV series.
        
        Args:
            series_id: The TVDB ID of the series.
            
        Returns:
            Detailed series information.
        """
        url = f"{SERIES_URL}/{series_id}"
        cache_key = url
        
        response = self._get_cached_key(cache_key)
        return response.get("data", {})
    
    def get_episodes_by_series_id(self, series_id: int) -> List[Dict[str, Any]]:
        """Get all episodes for a TV series.
        
        Args:
            series_id: The TVDB ID of the series.
            
        Returns:
            A list of episodes.
        """
        url = EPISODES_URL.format(series_id=series_id)
        cache_key = url
        
        response = self._get_cached_key(cache_key)
        return response.get("data", [])
    
    def clear_cache(self) -> None:
        """Clear the request cache."""
        self._get_cached_key.cache_clear()
        logger.info("TVDB API client cache cleared") 