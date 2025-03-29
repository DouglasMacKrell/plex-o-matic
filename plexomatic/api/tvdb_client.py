"""TVDB API client for retrieving TV show metadata."""

import requests
import logging
from urllib.parse import quote
import time
from requests.exceptions import RequestException

try:
    # Python 3.9+ has native support for these types
    from typing import Dict, List, Optional, Any, cast
except ImportError:
    # For Python 3.8 support
    from typing_extensions import Dict, List, Optional, Any, cast
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
SEASON_EPISODES_URL = f"{BASE_URL}/seasons/{{season_id}}/extended"


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
        self.auto_retry = auto_retry
        self.cache_size = cache_size
        self._token: Optional[str] = None
        self._session = requests.Session()
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_size_limit = cache_size

    def authenticate(self) -> None:
        """Authenticate with the TVDB API v4 and get an access token."""
        try:
            headers = {"apikey": self.api_key}
            if self.pin:
                headers["pin"] = self.pin

            response = self._session.post(AUTH_URL, headers=headers)
            response.raise_for_status()
            self._token = response.json()["data"]["token"]
            logger.info("Successfully authenticated with TVDB API v4")
        except RequestException as e:
            logger.error(f"TVDB authentication failed: {e}")
            raise TVDBAuthenticationError(f"Authentication failed: {e}")

    def is_authenticated(self) -> bool:
        """Check if the client has a valid token.

        Returns:
            True if the client has a valid token, False otherwise.
        """
        return self._token is not None

    def _ensure_authenticated(self) -> None:
        """Ensure client is authenticated, authenticating if needed."""
        if not self.is_authenticated():
            self.authenticate()

    @lru_cache(maxsize=100)
    def _get_cached_key(self, cache_key: str) -> Dict[str, Any]:
        """Get a cached response or make a new request."""
        if cache_key in self._cache:
            return self._cache[cache_key]

        if not self.is_authenticated():
            self.authenticate()

        try:
            response = self._session.get(
                f"{BASE_URL}/{cache_key}", headers={"Authorization": f"Bearer {self._token}"}
            )
            response.raise_for_status()
            result = response.json()
            self._cache[cache_key] = result
            if len(self._cache) > self._cache_size_limit:
                self._cache.popitem()
            return result
        except RequestException as e:
            if hasattr(e, "response") and e.response is not None:
                if e.response.status_code == 429 and self.auto_retry:
                    retry_after = int(e.response.headers.get("Retry-After", "1"))
                    logger.info(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    return self._get_cached_key(cache_key)
                elif e.response.status_code == 401:
                    logger.info("Token expired, re-authenticating...")
                    self._token = None
                    self.authenticate()
                    return self._get_cached_key(cache_key)
            if "search" in cache_key:
                return cast(Dict[str, Any], {"data": []})
            raise

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
            A list of matching series.
        """
        # URL encode the series name for the query
        encoded_name = quote(series_name)
        url = f"{SEARCH_SERIES_URL}?query={encoded_name}&type=series"
        cache_key = url

        logger.debug(f"Searching for series by name: '{series_name}' (URL: {url})")
        response = self._get_cached_key(cache_key)

        if "data" in response:
            results = response["data"]
            logger.debug(f"Found {len(results)} series matching '{series_name}'")

            if results:
                # Log the top results for debugging
                for i, result in enumerate(results[:3]):  # Show top 3 matches
                    logger.debug(
                        f"Match {i+1}: {result.get('name', 'Unknown')} (ID: {result.get('id', 'Unknown')})"
                    )
            else:
                # Try alternative search patterns if no results
                logger.debug(f"No results found for '{series_name}', trying alternative search...")

                # Try with just the main title part (before any colon)
                if ":" in series_name:
                    main_title = series_name.split(":", 1)[0].strip()
                    logger.debug(f"Trying with main title only: '{main_title}'")
                    return self.get_series_by_name(main_title)

            return cast(List[Dict[str, Any]], results)

        logger.warning(f"No valid response data for series search: '{series_name}'")
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
        logger.info(
            f"Getting episodes for series ID {normalized_id}, season {season_number}, type '{season_type}'"
        )

        # First get the series to find the default season type
        logger.debug(f"Fetching extended series data for {normalized_id}")
        try:
            series_extended = self.get_series_extended(normalized_id)
            # Log some basic info about the series
            series_name = series_extended.get("name", "Unknown")
            logger.debug(f"Found series: {series_name} (ID: {normalized_id})")
        except Exception as e:
            logger.error(f"Failed to get extended series data: {e}")
            return []

        # Get all seasons for the series
        seasons = series_extended.get("seasons", [])
        logger.debug(f"Extended series data has {len(seasons)} seasons")

        # Log all season types to help diagnose issues
        season_info: Dict[Optional[int], List[Optional[str]]] = {}
        for season in seasons:
            num = season.get("number")
            type_val = (
                season.get("type", {}).get("name")
                if isinstance(season.get("type"), dict)
                else season.get("type")
            )
            if num not in season_info:
                season_info[num] = []
            season_info[num].append(type_val)

        logger.debug(f"Season types by number: {season_info}")

        if not seasons:
            # Fall back to separate seasons API call if not in extended data
            logger.debug("No seasons in extended data, falling back to seasons API call")
            try:
                seasons = self.get_series_seasons(normalized_id)
                logger.debug(f"Found {len(seasons)} seasons from series_seasons API")
            except Exception as e:
                logger.error(f"Failed to get series seasons: {e}")
                return []

        # Get available season numbers for logging
        available_seasons = [s.get("number") for s in seasons if "number" in s]
        logger.debug(f"Available season numbers: {available_seasons}")

        if season_number not in available_seasons:
            logger.warning(
                f"Season {season_number} not found in available seasons {available_seasons}"
            )

            # Try to offer a helpful message about available seasons
            if available_seasons:
                logger.info(f"Available seasons for {series_name}: {sorted(available_seasons)}")
                # If they asked for season 1 but only season 0 exists, suggest that
                if season_number == 1 and 0 in available_seasons:
                    logger.info("Note: This series may only have a 'Specials' season (season 0)")

            # Skip directly to fallback mechanism
            logger.info(
                f"Season {season_number} not found, falling back to get_episodes_by_series_id"
            )
            return self._fallback_episode_retrieval(normalized_id, season_number, series_name)

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

            if season_num == season_number:
                logger.debug(
                    f"Found matching season: number={season_num}, type={season_type_value}, id={season_id_val}"
                )
                matching_seasons.append(
                    {"id": season_id_val, "type": season_type_value, "typeId": season.get("typeId")}
                )

        # Show all matching seasons for debugging
        if matching_seasons:
            logger.debug(f"All matching seasons for number {season_number}: {matching_seasons}")
        else:
            logger.warning(f"No matching seasons found for number {season_number}")
            return self._fallback_episode_retrieval(normalized_id, season_number, series_name)

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

            # If still no match, try "Official" or "Default" types
            if not season_id:
                for s in matching_seasons:
                    if s["type"] in ["Official", "Default"]:
                        season_id = s["id"]
                        logger.debug(f"Using '{s['type']}' season order with ID: {season_id}")
                        break

            # If still no match, use the first one
            if not season_id and matching_seasons:
                season_id = matching_seasons[0]["id"]
                logger.debug(
                    f"No preferred season type found, using first matching season ID: {season_id} (type: {matching_seasons[0]['type']})"
                )

        if not season_id:
            logger.warning(f"Season {season_number} not found for series {normalized_id}")
            return self._fallback_episode_retrieval(normalized_id, season_number, series_name)

        # Get episodes for the season
        # First try using the direct season/episodes endpoint
        try:
            # Try with the standard endpoint first
            url = SEASON_EPISODES_URL.format(season_id=season_id)
            logger.debug(f"Fetching episodes from URL: {url}")

            response = self._get_cached_key(url)
            logger.debug(
                f"Season episodes response: {response.keys() if isinstance(response, dict) else 'Not a dict'}"
            )

            # V4 API response format for the extended endpoint
            if "data" in response:
                if "episodes" in response["data"]:
                    result = response["data"]["episodes"]
                    logger.debug(
                        f"Found {len(result)} episodes for season {season_number} in extended data"
                    )
                    return cast(List[Dict[str, Any]], result)
                else:
                    logger.warning("No 'episodes' key in response 'data'")
            else:
                logger.warning(f"No 'data' in response for season episodes: {response}")

            # If we get here, the extended endpoint failed, so try alternate endpoints
            if "status" in response and response.get("status") == "error":
                logger.warning(
                    f"Error response from season episodes endpoint: {response.get('message')}"
                )
                # Continue to fallback below

        except Exception as e:
            logger.error(f"Error fetching episodes for season ID {season_id}: {e}")
            # Continue to fallback

        # Fall back to filtering all episodes
        logger.info(
            f"Falling back to retrieving all episodes and filtering for season {season_number}"
        )
        return self._fallback_episode_retrieval(normalized_id, season_number, series_name)

    def _fallback_episode_retrieval(
        self, series_id: int, season_number: int, series_name: str = "Unknown"
    ) -> List[Dict[str, Any]]:
        """Fallback method to retrieve episodes when season-specific API calls fail.

        Args:
            series_id: The normalized series ID
            season_number: The season number to filter for
            series_name: The name of the series for logging

        Returns:
            A list of episodes for the specified season
        """
        try:
            logger.debug(f"Retrieving all episodes for series {series_id}")
            all_episodes = self.get_episodes_by_series_id(series_id)

            if not all_episodes:
                logger.warning(f"No episodes found for '{series_name}' (ID: {series_id})")
                return []

            logger.info(f"Retrieved {len(all_episodes)} total episodes for '{series_name}'")

            # Count episodes by season for debugging
            season_counts: Dict[Optional[int], int] = {}
            for ep in all_episodes:
                ep_season = ep.get("seasonNumber") or ep.get("airedSeason")
                if ep_season is not None:
                    season_counts[ep_season] = season_counts.get(ep_season, 0) + 1

            logger.debug(f"Episode count by season: {season_counts}")

            # Filter episodes for the given season
            season_episodes = [
                episode
                for episode in all_episodes
                if (
                    episode.get("seasonNumber") == season_number
                    or episode.get("airedSeason") == season_number
                )
            ]

            if season_episodes:
                logger.info(
                    f"Found {len(season_episodes)} episodes for '{series_name}' season {season_number} after filtering"
                )
                return season_episodes
            else:
                logger.warning(
                    f"No episodes found for '{series_name}' season {season_number} after filtering"
                )
                return []

        except Exception as e:
            logger.error(f"Error in fallback episode retrieval: {e}")
            return []

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
