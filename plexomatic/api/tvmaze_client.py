"""TVMaze API client for retrieving TV show metadata.

This module provides a client for interacting with the TVMaze API to retrieve TV show data.
"""
import logging
import time
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from functools import lru_cache
import requests

logger = logging.getLogger(__name__)

# TVMaze API endpoints
BASE_URL = "https://api.tvmaze.com"
SEARCH_SHOWS_URL = f"{BASE_URL}/search/shows"
SEARCH_PEOPLE_URL = f"{BASE_URL}/search/people"
LOOKUP_SHOWS_URL = f"{BASE_URL}/lookup/shows"
SHOW_URL = f"{BASE_URL}/shows"
CACHE_SIZE = 100
DEFAULT_RETRY_WAIT = 10  # seconds


class TVMazeRequestError(Exception):
    """Raised when a TVMaze API request fails."""
    pass


class TVMazeRateLimitError(TVMazeRequestError):
    """Raised when TVMaze API rate limit is exceeded."""
    pass


class TVMazeClient:
    """Client for interacting with the TVMaze API."""
    
    def __init__(self, cache_size: int = CACHE_SIZE):
        """Initialize the TVMaze client.
        
        Args:
            cache_size: Maximum number of responses to cache (default: 100).
        """
        self.cache_size = cache_size
        self.setup_cache()
    
    def setup_cache(self):
        """Set up the cache with the specified size."""
        # Apply the lru_cache decorator to the appropriate method
        self._request_cached = lru_cache(maxsize=self.cache_size)(self._request_uncached)
    
    def _request_uncached(self, url: str, params_str: str) -> Any:
        """Make an uncached request to the TVMaze API.
        
        Args:
            url: The URL to request.
            params_str: JSON string of query parameters.
            
        Returns:
            The JSON response data.
            
        Raises:
            TVMazeRequestError: For general API errors.
            TVMazeRateLimitError: When rate limited.
        """
        params = json.loads(params_str) if params_str != '{}' else None
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Resource not found at {url} with params {params}")
                raise TVMazeRequestError(f"Resource not found: {url}")
            elif response.status_code == 429:
                retry_after = response.headers.get('Retry-After', DEFAULT_RETRY_WAIT)
                logger.warning(f"Rate limit exceeded. Retry after {retry_after} seconds")
                raise TVMazeRateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds")
            else:
                logger.error(f"TVMaze API error: {response.status_code} - {response.text}")
                raise TVMazeRequestError(f"API error: {response.status_code} - {response.text}")
        
        except (requests.RequestException, json.JSONDecodeError) as e:
            logger.error(f"TVMaze request failed: {e}")
            raise TVMazeRequestError(f"Request failed: {e}")
    
    def _get(self, url: str, params: Optional[Dict] = None) -> Any:
        """Make a cached request to the TVMaze API.
        
        Args:
            url: The URL to request.
            params: Optional query parameters.
            
        Returns:
            The JSON response data.
            
        Raises:
            TVMazeRequestError: For general API errors.
            TVMazeRateLimitError: When rate limited.
        """
        # Convert params dict to a string for cache key
        params_str = json.dumps(params, sort_keys=True) if params else '{}'
        
        # Make the request, leveraging the cache
        try:
            return self._request_cached(url, params_str)
        except TVMazeRateLimitError:
            # Propagate rate limit errors
            raise
        except Exception as e:
            logger.error(f"Error in cached request: {e}")
            raise TVMazeRequestError(f"Request error: {e}")
    
    def clear_cache(self):
        """Clear the request cache."""
        self._request_cached.cache_clear()
        logger.info("TVMaze client cache cleared")
    
    def search_shows(self, query: str) -> List[Dict[str, Any]]:
        """Search for TV shows by name.
        
        Args:
            query: The show name to search for.
            
        Returns:
            A list of matching shows with scores.
        """
        params = {"q": query}
        return self._get(SEARCH_SHOWS_URL, params)
    
    def get_show_by_id(self, show_id: int) -> Dict[str, Any]:
        """Get detailed information about a show by ID.
        
        Args:
            show_id: The TVMaze show ID.
            
        Returns:
            Detailed show information.
            
        Raises:
            TVMazeRequestError: If the show is not found.
        """
        url = f"{SHOW_URL}/{show_id}"
        return self._get(url)
    
    def get_show_by_imdb_id(self, imdb_id: str) -> Dict[str, Any]:
        """Get show information using an IMDB ID.
        
        Args:
            imdb_id: The IMDB ID (e.g., "tt0903747").
            
        Returns:
            Show information.
            
        Raises:
            TVMazeRequestError: If the show is not found.
        """
        params = {"imdb": imdb_id}
        return self._get(LOOKUP_SHOWS_URL, params)
    
    def get_episodes(self, show_id: int) -> List[Dict[str, Any]]:
        """Get all episodes for a show.
        
        Args:
            show_id: The TVMaze show ID.
            
        Returns:
            A list of episodes.
            
        Raises:
            TVMazeRequestError: If the show is not found.
        """
        url = f"{SHOW_URL}/{show_id}/episodes"
        return self._get(url)
    
    def get_episode_by_number(self, show_id: int, season: int, episode: int) -> Dict[str, Any]:
        """Get a specific episode by season and episode number.
        
        Args:
            show_id: The TVMaze show ID.
            season: The season number.
            episode: The episode number.
            
        Returns:
            Episode information.
            
        Raises:
            TVMazeRequestError: If the episode is not found.
        """
        url = f"{SHOW_URL}/{show_id}/episodebynumber"
        params = {"season": season, "number": episode}
        return self._get(url, params)
    
    def search_people(self, query: str) -> List[Dict[str, Any]]:
        """Search for people by name.
        
        Args:
            query: The person's name to search for.
            
        Returns:
            A list of matching people with scores.
        """
        params = {"q": query}
        return self._get(SEARCH_PEOPLE_URL, params)
    
    def get_show_cast(self, show_id: int) -> List[Dict[str, Any]]:
        """Get the cast for a show.
        
        Args:
            show_id: The TVMaze show ID.
            
        Returns:
            A list of cast members with their characters.
            
        Raises:
            TVMazeRequestError: If the show is not found.
        """
        url = f"{SHOW_URL}/{show_id}/cast"
        return self._get(url) 