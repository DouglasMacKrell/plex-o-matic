"""TVDB API client for retrieving TV show metadata."""

import requests
import logging

try:
    # Python 3.9+ has native support for these types
    from typing import Dict, List, Optional, Any, cast
except ImportError:
    # For Python 3.8 support
    from typing_extensions import Dict, List, Optional, Any, cast
from datetime import datetime, timedelta, timezone
from functools import lru_cache

logger = logging.getLogger(__name__)

# TVDB API v4 endpoints
BASE_URL = "https://api4.thetvdb.com/v4"
AUTH_URL = f"{BASE_URL}/login"
SEARCH_SERIES_URL = f"{BASE_URL}/search"
SERIES_URL = f"{BASE_URL}/series"
EPISODES_URL = f"{BASE_URL}/series/{{series_id}}/episodes/default"
SERIES_EXTENDED_URL = f"{BASE_URL}/series/{{series_id}}/extended"
SEASONS_URL = f"{BASE_URL}/seasons"
SEASON_EPISODES_URL = f"{BASE_URL}/seasons/{{season_id}}/episodes"


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
    """Client for interacting with the TVDB API v4."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_size: int = 100,
        auto_retry: bool = False,
        pin: Optional[str] = None,
    ):
        """Initialize the TVDB API client.

        Args:
            api_key: The TVDB API key. If None, will attempt to load from config.
            cache_size: Maximum number of responses to cache.
            auto_retry: Whether to automatically retry requests when rate limited.
            pin: Optional subscriber PIN for v4 API (user-supported model)
        """
        # If no API key provided, try to load from config
        if api_key is None:
            from plexomatic.config.config_manager import ConfigManager

            config = ConfigManager()
            api_key = config.get("api", {}).get("tvdb", {}).get("api_key")
            pin = pin or config.get("api", {}).get("tvdb", {}).get("pin")
            if not api_key:
                raise TVDBAuthenticationError("No API key provided and none found in config")

        self.api_key = api_key
        self.pin = pin
        self.token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.auto_retry = auto_retry
        self.cache_size = cache_size

    def authenticate(self) -> None:
        """Authenticate with the TVDB API v4 and get an access token."""
        # Prepare authentication payload
        payload = {"apikey": self.api_key}

        # Include PIN if provided (for subscriber model)
        if self.pin:
            payload["pin"] = self.pin

        headers = {"Content-Type": "application/json"}

        # Make auth request
        try:
            response = requests.post(AUTH_URL, json=payload, headers=headers)
            response.raise_for_status()

            # Parse response
            data = response.json()

            # Extract token
            token_data = data.get("data", {})
            token = token_data.get("token")

            if not token:
                raise TVDBAuthenticationError("No token in authentication response")

            # Calculate token expiration (24 hours from now)
            self.token = token
            self.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

            logger.info("Successfully authenticated with TVDB API v4")
        except requests.RequestException as e:
            logger.error(f"TVDB authentication failed: {e}")
            raise TVDBAuthenticationError(f"Authentication failed: {e}")

    def is_authenticated(self) -> bool:
        """Check if the client has a valid token.

        Returns:
            True if the client has a valid token, False otherwise.
        """
        if not self.token or not self.token_expires_at:
            return False

        # Check if token is expired
        return datetime.now(timezone.utc) < self.token_expires_at

    def _ensure_authenticated(self) -> None:
        """Ensure client is authenticated, authenticating if needed."""
        if not self.is_authenticated():
            self.authenticate()

    @lru_cache(maxsize=100)
    def _get_cached_key(self, url: str) -> Dict[str, Any]:
        """Get a cached response for a URL, fetching if not cached.

        Args:
            url: The URL to fetch.

        Returns:
            The response JSON.
        """
        self._ensure_authenticated()

        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except requests.exceptions.HTTPError as e:
            logger.error(f"TVDB request failed: {e.response.status_code} - {e.response.text}")

            # Handle token expiration (401) or rate limiting (429)
            if e.response.status_code in (401, 429) and self.auto_retry:
                if e.response.status_code == 401:
                    logger.info("Token expired, re-authenticating")
                    self.authenticate()
                elif e.response.status_code == 429:
                    logger.info("Rate limited, retrying with new request")

                # Retry the request
                headers = {"Authorization": f"Bearer {self.token}"}
                try:
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                    return cast(Dict[str, Any], response.json())
                except Exception as retry_error:
                    logger.error(f"Retry failed: {retry_error}")

            # Return empty result based on URL type
            if "search" in url:
                return cast(Dict[str, Any], {"data": []})  # For search endpoints return empty list
            else:
                return cast(Dict[str, Any], {"status": "error", "message": str(e), "data": {}})
        except Exception as e:
            logger.error(f"TVDB request error: {e}")
            # Return empty result based on URL type
            if "search" in url:
                return cast(Dict[str, Any], {"data": []})  # For search endpoints return empty list
            else:
                return cast(Dict[str, Any], {"status": "error", "message": str(e), "data": {}})

    def _normalize_id(self, series_id: Any) -> int:
        """Normalize a series ID by removing any 'series-' prefix.

        Args:
            series_id: The series ID to normalize.

        Returns:
            The normalized series ID as an integer.
        """
        if isinstance(series_id, str) and series_id.startswith("series-"):
            return int(series_id[7:])
        return int(series_id)

    def get_series_by_name(self, series_name: str) -> List[Dict[str, Any]]:
        """Search for TV series by name.

        Args:
            series_name: The name of the series to search for.

        Returns:
            A list of search results.
        """
        url = f"{SEARCH_SERIES_URL}?query={series_name}&type=series"
        cache_key = url

        response = self._get_cached_key(cache_key)
        if "data" in response:
            return cast(List[Dict[str, Any]], response["data"])
        return cast(List[Dict[str, Any]], [])

    def get_series(self, series_id: Any) -> Dict[str, Any]:
        """Get TV series details by ID.

        Args:
            series_id: The TVDB ID of the series.

        Returns:
            Series details.
        """
        normalized_id = self._normalize_id(series_id)
        url = f"{SERIES_URL}/{normalized_id}"
        cache_key = url

        response = self._get_cached_key(cache_key)
        result = response.get("data", {})
        return cast(Dict[str, Any], result)

    def get_series_extended(self, series_id: Any) -> Dict[str, Any]:
        """Get extended TV series details by ID, including seasons info.

        Args:
            series_id: The TVDB ID of the series.

        Returns:
            Extended series details including seasons.
        """
        normalized_id = self._normalize_id(series_id)
        url = SERIES_EXTENDED_URL.format(series_id=normalized_id)
        cache_key = url

        response = self._get_cached_key(cache_key)
        result = response.get("data", {})
        return cast(Dict[str, Any], result)

    def get_series_seasons(self, series_id: Any) -> List[Dict[str, Any]]:
        """Get seasons for a TV series.

        Args:
            series_id: The TVDB ID of the series.

        Returns:
            A list of seasons.
        """
        normalized_id = self._normalize_id(series_id)
        url = SEASONS_URL.format(series_id=normalized_id)
        cache_key = url

        response = self._get_cached_key(cache_key)
        # Process the v4 API response
        if "data" in response:
            result = response["data"]
        else:
            result = []
        return cast(List[Dict[str, Any]], result)

    def get_episodes_by_series_id(self, series_id: Any) -> List[Dict[str, Any]]:
        """Get all episodes for a TV series using the default season order.

        Args:
            series_id: The TVDB ID of the series.

        Returns:
            A list of episodes.
        """
        normalized_id = self._normalize_id(series_id)
        url = EPISODES_URL.format(series_id=normalized_id)
        cache_key = url

        response = self._get_cached_key(cache_key)
        # v4 API nests episodes under data.episodes
        if "data" in response and "episodes" in response["data"]:
            result = response["data"]["episodes"]
        else:
            result = []
        return cast(List[Dict[str, Any]], result)

    def get_season_episodes(
        self, series_id: Any, season_number: int, season_type: str = "Aired Order"
    ) -> List[Dict[str, Any]]:
        """Get episodes for a specific season of a TV series.

        This method will:
        1. Get the series' seasons
        2. Find the season ID for the given season number and type
        3. Get episodes for that season

        Args:
            series_id: The TVDB ID of the series.
            season_number: The season number to get episodes for.
            season_type: The season type to retrieve (e.g., "Aired Order", "DVD Order", "Absolute Order").
                         Defaults to "Aired Order" if not specified.

        Returns:
            A list of episodes for the specified season.
        """
        normalized_id = self._normalize_id(series_id)

        # First get the series to find the default season type
        logger.debug(f"Fetching extended series data for {normalized_id}")
        series_extended = self.get_series_extended(normalized_id)

        # Get all seasons for the series
        seasons = series_extended.get("seasons", [])
        logger.debug(f"Extended series data has {len(seasons)} seasons")
        if not seasons:
            # Fall back to separate seasons API call if not in extended data
            logger.debug("No seasons in extended data, falling back to seasons API call")
            seasons = self.get_series_seasons(normalized_id)
            logger.debug(f"Found {len(seasons)} seasons from series_seasons API")

        logger.debug(f"Available seasons: {[s.get('number') for s in seasons if 'number' in s]}")

        # Find the season with the matching season number
        season_id = None
        matching_seasons = []

        for season in seasons:
            season_num = season.get("number")
            season_type_value = (
                season.get("type", {}).get("name")
                if isinstance(season.get("type"), dict)
                else season.get("type")
            )
            season_id_val = season.get("id")
            logger.debug(
                f"Checking season: number={season_num}, type={season_type_value}, id={season_id_val}"
            )

            if season_num == season_number:
                matching_seasons.append({"id": season_id_val, "type": season_type_value})

        # Prioritize seasons by type
        if matching_seasons:
            # First try to find the requested season type
            for s in matching_seasons:
                if s["type"] == season_type:
                    season_id = s["id"]
                    logger.debug(f"Found '{season_type}' season ID: {season_id}")
                    break

            # If requested type not found, fall back to "Aired Order" if different from requested type
            if not season_id and season_type != "Aired Order":
                for s in matching_seasons:
                    if s["type"] == "Aired Order":
                        season_id = s["id"]
                        logger.debug(
                            f"Requested type '{season_type}' not found, falling back to 'Aired Order' season ID: {season_id}"
                        )
                        break

            # If still no match, use the first one
            if not season_id:
                season_id = matching_seasons[0]["id"]
                logger.debug(
                    f"Neither '{season_type}' nor 'Aired Order' found, using first matching season ID: {season_id}"
                )

        if not season_id:
            logger.warning(f"Season {season_number} not found for series {normalized_id}")
            return []

        # Get episodes for the season
        url = SEASON_EPISODES_URL.format(season_id=season_id)
        logger.debug(f"Fetching episodes from URL: {url}")
        cache_key = url

        response = self._get_cached_key(cache_key)
        logger.debug(
            f"Season episodes response: {response.keys() if isinstance(response, dict) else 'Not a dict'}"
        )

        # v4 API response format
        if "data" in response and "episodes" in response["data"]:
            result = response["data"]["episodes"]
        elif "data" in response:
            result = response["data"]
        else:
            result = []

        logger.debug(
            f"Found {len(result)} episodes for season {season_number} of series {normalized_id}"
        )
        return cast(List[Dict[str, Any]], result)

    def clear_cache(self) -> None:
        """Clear the request cache."""
        self._get_cached_key.cache_clear()
        logger.info("TVDB API client cache cleared")

    def get_series_by_id(self, series_id: int) -> dict[str, Any]:
        """Get a TV series by ID."""
        url = f"{SERIES_URL}/{series_id}"
        try:
            result = self._get_cached_key(url)
            if not result:
                logger.warning(f"No series found for ID {series_id}")
                return {}
            return cast(dict[str, Any], result.get("data", {}))
        except Exception as e:
            logger.error(f"Error getting series by ID: {e}")
            return {}

    def get_season_by_id(self, season_id: int) -> dict[str, Any]:
        """Get a TV season by ID."""
        url = f"{SEASONS_URL}/{season_id}"
        try:
            result = self._get_cached_key(url)
            if not result:
                logger.warning(f"No season found for ID {season_id}")
                return {}
            return cast(dict[str, Any], result.get("data", {}))
        except Exception as e:
            logger.error(f"Error getting season by ID: {e}")
            return {}

    def get_episodes_by_season(self, season_id: int) -> list[dict[str, Any]]:
        """Get episodes by season ID."""
        url = f"{SEASONS_URL}/{season_id}/episodes"
        try:
            result = self._get_cached_key(url)
            if not result:
                logger.warning(f"No episodes found for season ID {season_id}")
                return []
            return cast(list[dict[str, Any]], result.get("data", []))
        except Exception as e:
            logger.error(f"Error getting episodes by season ID: {e}")
            return []
