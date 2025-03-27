"""MusicBrainz API client for retrieving music metadata."""

import logging
import time
from datetime import datetime
from functools import lru_cache
from typing import Dict, List, Optional, Any, Tuple

import requests
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger(__name__)


class MusicBrainzRequestError(Exception):
    """Raised when a MusicBrainz API request fails."""

    pass


class MusicBrainzRateLimitError(Exception):
    """Raised when MusicBrainz API rate limit is exceeded."""

    pass


class MusicBrainzClient:
    """Client for interacting with the MusicBrainz API."""

    BASE_URL = "https://musicbrainz.org/ws/2"
    # MusicBrainz requests 1 second between requests
    # https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting
    RATE_LIMIT = 1.0  # seconds between requests

    def __init__(
        self,
        app_name: str = "Plex-o-matic",
        app_version: str = "1.0",
        contact_email: str = "",
        cache_size: int = 100,
        auto_retry: bool = False,
    ):
        """Initialize the MusicBrainz API client.

        Args:
            app_name: Name of the application making the requests
            app_version: Version of the application
            contact_email: Contact email for the application
            cache_size: Maximum number of responses to cache
            auto_retry: Whether to automatically retry requests when rate limited
        """
        self.app_name = app_name
        self.app_version = app_version
        self.contact_email = contact_email
        self.cache_size = cache_size
        self.auto_retry = auto_retry
        self.last_request_time: Optional[datetime] = None

        # Format user agent according to MusicBrainz guidelines
        # https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting#Provide_meaningful_User-Agent_strings
        self.user_agent = f"{app_name}/{app_version}"
        if contact_email:
            self.user_agent += f" ( {contact_email} )"

        self.headers = {"User-Agent": self.user_agent}
        logger.debug(f"Initialized MusicBrainz client with user-agent: {self.user_agent}")

    def _enforce_rate_limit(self) -> None:
        """Enforce the MusicBrainz API rate limit by sleeping if necessary."""
        if self.last_request_time is None:
            self.last_request_time = datetime.now()
            return

        now = datetime.now()
        time_since_last_request = (now - self.last_request_time).total_seconds()

        if time_since_last_request < self.RATE_LIMIT:
            sleep_time = self.RATE_LIMIT - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = datetime.now()

    def _make_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a request to the MusicBrainz API with rate limiting.

        Args:
            endpoint: API endpoint to request
            params: Query parameters to include

        Returns:
            API response as dictionary

        Raises:
            MusicBrainzRequestError: When the request fails
            MusicBrainzRateLimitError: When rate limit is exceeded
        """
        url = f"{self.BASE_URL}/{endpoint}"

        # Ensure fmt=json is in params
        if params is None:
            params = {"fmt": "json"}
        else:
            params["fmt"] = "json"

        # Enforce rate limiting
        self._enforce_rate_limit()

        try:
            logger.debug(f"Making request to {url} with params {params}")
            response = requests.get(url, headers=self.headers, params=params)

            # Handle rate limiting
            if response.status_code == 429:
                logger.warning("MusicBrainz rate limit exceeded")
                if self.auto_retry:
                    logger.info("Auto-retrying after rate limit cooldown")
                    time.sleep(2)  # Wait for rate limit reset
                    self._enforce_rate_limit()
                    return self._make_request(endpoint, params)
                else:
                    raise MusicBrainzRateLimitError("Rate limit exceeded")

            # Handle other errors
            if response.status_code != 200:
                logger.error(f"MusicBrainz API error: {response.status_code} - {response.text}")
                raise MusicBrainzRequestError(
                    f"API request failed with status {response.status_code}: {response.text}"
                )

            return response.json()

        except Timeout:
            logger.error("MusicBrainz API request timed out")
            raise MusicBrainzRequestError("Request timed out")
        except RequestException as e:
            logger.error(f"MusicBrainz API request error: {str(e)}")
            raise MusicBrainzRequestError(f"Request failed: {str(e)}")

    @lru_cache(maxsize=100)
    def search_artist(self, query: str) -> List[Dict[str, Any]]:
        """Search for an artist by name.

        Args:
            query: Artist name to search for

        Returns:
            List of matching artists
        """
        params = {"query": query}
        response = self._make_request("artist", params)
        return response.get("artists", [])

    @lru_cache(maxsize=100)
    def get_artist(self, mbid: str, include_releases: bool = False) -> Dict[str, Any]:
        """Get artist details by MusicBrainz ID.

        Args:
            mbid: MusicBrainz ID
            include_releases: Whether to include releases in the response

        Returns:
            Artist details
        """
        params = {}
        if include_releases:
            params["inc"] = "releases"

        return self._make_request(f"artist/{mbid}", params)

    @lru_cache(maxsize=100)
    def search_release(self, query: str) -> List[Dict[str, Any]]:
        """Search for a release (album) by name.

        Args:
            query: Release name to search for

        Returns:
            List of matching releases
        """
        params = {"query": query}
        response = self._make_request("release", params)
        return response.get("releases", [])

    @lru_cache(maxsize=100)
    def get_release(self, mbid: str, include_recordings: bool = False) -> Dict[str, Any]:
        """Get release details by MusicBrainz ID.

        Args:
            mbid: MusicBrainz ID
            include_recordings: Whether to include recordings (tracks) in the response

        Returns:
            Release details
        """
        params = {}
        if include_recordings:
            params["inc"] = "recordings"

        return self._make_request(f"release/{mbid}", params)

    @lru_cache(maxsize=100)
    def search_track(self, query: str) -> List[Dict[str, Any]]:
        """Search for a track (recording) by name.

        Args:
            query: Track name to search for

        Returns:
            List of matching tracks
        """
        params = {"query": query}
        response = self._make_request("recording", params)
        return response.get("recordings", [])

    @lru_cache(maxsize=100)
    def get_track(self, mbid: str) -> Dict[str, Any]:
        """Get track details by MusicBrainz ID.

        Args:
            mbid: MusicBrainz ID

        Returns:
            Track details
        """
        return self._make_request(f"recording/{mbid}")

    def verify_music_file(
        self, artist: str, album: Optional[str] = None, track: Optional[str] = None
    ) -> Tuple[Dict[str, Any], float]:
        """Verify a music file by searching for the artist, album, and track.

        Args:
            artist: Artist name
            album: Album name (optional)
            track: Track name (optional)

        Returns:
            Tuple of (best match metadata, confidence score)
        """
        # Start with artist search
        artists = self.search_artist(artist)
        if not artists:
            logger.warning(f"No artists found matching '{artist}'")
            return {}, 0.0

        # Simple matching for now - first result
        best_artist = artists[0]
        artist_score = 0.8  # Default confidence

        result = {
            "artist": best_artist["name"],
            "artist_id": best_artist["id"],
            "artist_score": artist_score,
        }

        # If album provided, search for it
        if album:
            # Build query with artist to improve results
            query = f"release:{album} AND artist:{best_artist['name']}"
            releases = self.search_release(query)

            if releases:
                best_release = releases[0]
                album_score = 0.8  # Default confidence

                result.update(
                    {
                        "album": best_release["title"],
                        "album_id": best_release["id"],
                        "album_score": album_score,
                        "year": (
                            best_release.get("date", "").split("-")[0]
                            if "date" in best_release
                            else None
                        ),
                    }
                )

                # If track provided, search for it within this release
                if track and "id" in best_release:
                    release_details = self.get_release(best_release["id"], include_recordings=True)
                    if "media" in release_details:
                        for medium in release_details["media"]:
                            for track_info in medium.get("tracks", []):
                                if track.lower() in track_info["title"].lower():
                                    track_score = 0.8  # Default confidence

                                    result.update(
                                        {
                                            "track": track_info["title"],
                                            "track_id": track_info["id"],
                                            "track_score": track_score,
                                            "track_number": track_info["number"],
                                            "disc_number": medium["position"],
                                        }
                                    )
                                    break

        # Calculate overall confidence score
        confidence = artist_score
        if "album_score" in result:
            confidence = (confidence + result["album_score"]) / 2
        if "track_score" in result:
            confidence = (confidence + result["track_score"]) / 3

        return result, confidence
