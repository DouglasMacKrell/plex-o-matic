"""Metadata fetchers for retrieving media information from various sources.

This module contains classes for fetching metadata from different sources like TVDB, TMDB, AniDB, and TVMaze.
"""

import logging
import re
import os
import sys
from functools import lru_cache

# Import standard library dependencies
from plexomatic.api.tvdb_client import TVDBClient
from plexomatic.api.tmdb_client import TMDBClient
from plexomatic.api.anidb_client import AniDBClient
from plexomatic.api.tvmaze_client import TVMazeClient

# Import consolidated MediaType
from plexomatic.core.constants import MediaType

# Define Python version
PY_VERSION = sys.version_info[:2]

# Import typing elements based on Python version
if PY_VERSION >= (3, 9):
    # Python 3.9+ has native support for these types
    from typing import Dict, List, Any, Optional, Type
else:
    # For Python 3.8 support
    try:
        from typing import Any, Optional
        from typing_extensions import Dict, List, Type
    except ImportError:
        # Fallback if typing_extensions is not available
        from typing import Dict, List, Any, Optional, Type

logger = logging.getLogger(__name__)

CACHE_SIZE = 100  # Default size for the LRU caches

# Default API keys and credentials from environment variables
DEFAULT_TVDB_API_KEY = os.environ.get("TVDB_API_KEY", "")
DEFAULT_TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
DEFAULT_ANIDB_USERNAME = os.environ.get("ANIDB_USERNAME", "")
DEFAULT_ANIDB_PASSWORD = os.environ.get("ANIDB_PASSWORD", "")


def safe_cast(obj: Any, target_type: Type) -> Optional[Any]:
    """Safely cast an object to the specified type, returning None if not possible."""
    return obj if isinstance(obj, target_type) else None


def extract_dict_list(data: Any) -> List[Dict[str, Any]]:
    """Extract a list of dictionaries from various data formats."""
    result: List[Dict[str, Any]] = []

    # Handle empty data
    if not data:
        return result

    # Check if data is a dict with a results key
    data_dict = safe_cast(data, dict)
    if data_dict is not None:
        results = data_dict.get("results")
        if results is not None:
            results_list = safe_cast(results, list)
            if results_list is not None:
                for item in results_list:
                    item_dict = safe_cast(item, dict)
                    if item_dict is not None:
                        result.append(item_dict)
                return result

    # Handle list of objects
    if isinstance(data, list):
        for item in data:
            item_dict = safe_cast(item, dict)
            if item_dict is not None:
                result.append(item_dict)

    return result


class MetadataResult:
    """Class representing metadata results from any source."""

    def __init__(
        self,
        id: str,
        title: str,
        overview: Optional[str] = None,
        media_type: MediaType = MediaType.UNKNOWN,
        source: str = "unknown",
        year: Optional[int] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
    ):
        """Initialize a metadata result.

        Args:
            id: Unique identifier for the result, prefixed with source (e.g., "tvdb:12345")
            title: Title of the media
            overview: Description or summary of the media
            media_type: Type of media (TV show, movie, anime, etc.)
            source: Source of the metadata (tvdb, tmdb, anidb, etc.)
            year: Release year if available
            extra_data: Additional data specific to the source
            confidence: Confidence score of the match (0.0 to 1.0)
        """
        self.id = id
        self.title = title
        self.overview = overview
        self.media_type = media_type
        self.source = source
        self.year = year
        self.extra_data = extra_data or {}
        self.confidence = confidence

    def __str__(self) -> str:
        """Return a string representation of the result."""
        return f"{self.title} ({self.year or 'Unknown Year'}) [{self.source}]"

    def __repr__(self) -> str:
        """Return a detailed string representation of the result."""
        return f"MetadataResult(id='{self.id}', title='{self.title}', media_type={self.media_type}, source='{self.source}')"


class MetadataFetcher:
    """Base class for metadata fetchers."""

    def __init__(self, cache_size: int = CACHE_SIZE):
        """Initialize the metadata fetcher.

        Args:
            cache_size: Size of the LRU cache for metadata results
        """
        self.cache_size = cache_size
        self.cache: Dict[str, Any] = {}  # Initialize an empty cache dictionary
        self._setup_cache()

    def _setup_cache(self) -> None:
        """Set up the cache with the specified size."""
        # Apply the lru_cache decorator to the appropriate method
        self._fetch_metadata_cached = lru_cache(maxsize=self.cache_size)(
            self._fetch_metadata_uncached
        )

    def _fetch_metadata_uncached(self, id: str, media_type: MediaType) -> MetadataResult:
        """Fetch metadata without caching. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _fetch_metadata_uncached")

    def fetch_metadata(self, id: str, media_type: MediaType) -> MetadataResult:
        """Fetch metadata with caching.

        Args:
            id: Identifier for the media
            media_type: Type of media (TV show, movie, anime, etc.)

        Returns:
            Metadata result object
        """
        return self._fetch_metadata_cached(id, media_type)

    def search(self, query: str, media_type: MediaType) -> List[MetadataResult]:
        """Search for media by name.

        Args:
            query: Search query
            media_type: Type of media to search for

        Returns:
            List of metadata results
        """
        raise NotImplementedError("Subclasses must implement search")

    def clear_cache(self) -> None:
        """Clear the metadata cache."""
        self._fetch_metadata_cached.cache_clear()
        logger.info(f"{self.__class__.__name__} cache cleared")


class TVDBMetadataFetcher(MetadataFetcher):
    """Metadata fetcher for TVDB."""

    def __init__(
        self,
        client: Optional[TVDBClient] = None,
        api_key: str = DEFAULT_TVDB_API_KEY,
        cache_size: int = CACHE_SIZE,
    ):
        """Initialize the TVDB metadata fetcher.

        Args:
            client: TVDBClient instance, or None to create a new one
            api_key: TVDB API key (defaults to environment variable)
            cache_size: Size of the LRU cache for metadata results
        """
        super().__init__(cache_size=cache_size)
        self.client = client or TVDBClient(api_key=api_key)

        # Extract ID from prefixed ID (e.g., "tvdb:12345" -> 12345)
        self._extract_id = lambda id: int(id.split(":")[1]) if ":" in id else int(id)

    def _fetch_metadata_uncached(self, id: str, media_type: MediaType) -> MetadataResult:
        """Fetch metadata from TVDB without caching.

        Args:
            id: TVDB ID (either "tvdb:12345" or "12345")
            media_type: Type of media (only TV_SHOW is supported)

        Returns:
            Metadata result object

        Raises:
            ValueError: If media_type is not TV_SHOW
        """
        if media_type != MediaType.TV_SHOW:
            raise ValueError("TVDB only supports TV shows")

        series_id = self._extract_id(id)

        try:
            # Get series details
            series = self.client.get_series_by_id(series_id=series_id)

            # Extract year from first aired date if available
            year = None
            if "firstAired" in series and series["firstAired"]:
                year_match = re.match(r"(\d{4})", series["firstAired"])
                if year_match:
                    year = int(year_match.group(1))

            # Get episodes
            episodes = self.client.get_episodes_by_series_id(series_id=series_id)

            # Process episodes into a standardized format
            formatted_episodes = []
            for episode in episodes:
                formatted_episodes.append(
                    {
                        "id": episode.get("id"),
                        "title": episode.get("episodeName"),
                        "overview": episode.get("overview"),
                        "season": episode.get("airedSeason"),
                        "episode": episode.get("airedEpisodeNumber"),
                        "air_date": episode.get("firstAired"),
                    }
                )

            # Create extra data dictionary
            extra_data = {
                "network": series.get("network"),
                "first_aired": series.get("firstAired"),
                "status": series.get("status"),
                "episodes": formatted_episodes,
            }

            return MetadataResult(
                id=f"tvdb:{series_id}",
                title=series.get("seriesName", "Unknown"),
                overview=series.get("overview"),
                media_type=MediaType.TV_SHOW,
                source="tvdb",
                year=year,
                extra_data=extra_data,
            )

        except Exception as e:
            logger.error(f"Error fetching TVDB metadata for ID {id}: {e}")
            raise

    def get_special_episodes(self, series_id: int) -> List[Dict[str, Any]]:
        """Get special episodes (season 0) for a series.

        Args:
            series_id: TVDB series ID

        Returns:
            List of special episodes
        """
        try:
            # Get all episodes
            all_episodes = self.client.get_episodes_by_series_id(series_id=series_id)

            # Filter for special episodes (season 0)
            special_episodes = [
                episode for episode in all_episodes if episode.get("airedSeason") == 0
            ]

            # Format the special episodes
            formatted_specials = []
            for episode in special_episodes:
                formatted_specials.append(
                    {
                        "id": episode.get("id"),
                        "title": episode.get("episodeName"),
                        "overview": episode.get("overview"),
                        "special_number": episode.get("airedEpisodeNumber"),
                        "air_date": episode.get("firstAired"),
                    }
                )

            return formatted_specials

        except Exception as e:
            logger.error(f"Error fetching special episodes for series {series_id}: {e}")
            return []

    def get_episodes_by_numbers(
        self, series_id: int, episode_numbers: List[int], season: int = 1
    ) -> List[Dict[str, Any]]:
        """Get specific episodes by their numbers.

        Args:
            series_id: TVDB series ID
            episode_numbers: List of episode numbers to fetch
            season: Season number (default: 1)

        Returns:
            List of episodes matching the specified numbers
        """
        try:
            # Get all episodes
            all_episodes = self.client.get_episodes_by_series_id(series_id=series_id)

            # Filter for the requested episodes
            matching_episodes = [
                episode
                for episode in all_episodes
                if episode.get("airedSeason") == season
                and episode.get("airedEpisodeNumber") in episode_numbers
            ]

            # Format the episodes
            formatted_episodes = []
            for episode in matching_episodes:
                formatted_episodes.append(
                    {
                        "id": episode.get("id"),
                        "title": episode.get("episodeName"),
                        "overview": episode.get("overview"),
                        "season": episode.get("airedSeason"),
                        "episode": episode.get("airedEpisodeNumber"),
                        "air_date": episode.get("firstAired"),
                    }
                )

            return formatted_episodes

        except Exception as e:
            logger.error(f"Error fetching episodes {episode_numbers} for series {series_id}: {e}")
            return []

    def search(self, query: str, media_type: MediaType) -> List[MetadataResult]:
        """Search for TV shows by name.

        Args:
            query: Search query
            media_type: Type of media to search for (only TV_SHOW is supported)

        Returns:
            List of metadata results

        Raises:
            ValueError: If media_type is not TV_SHOW
        """
        if media_type != MediaType.TV_SHOW:
            raise ValueError("TVDB only supports TV shows")

        try:
            results = self.client.get_series_by_name(name=query)

            metadata_results = []
            for result in results:
                series_id = result.get("id")

                # Extract year from first aired date if available
                year = None
                if "firstAired" in result and result["firstAired"]:
                    year_match = re.match(r"(\d{4})", result["firstAired"])
                    if year_match:
                        year = int(year_match.group(1))

                metadata_results.append(
                    MetadataResult(
                        id=f"tvdb:{series_id}",
                        title=result.get("seriesName", "Unknown"),
                        overview=result.get("overview"),
                        media_type=MediaType.TV_SHOW,
                        source="tvdb",
                        year=year,
                        extra_data={
                            "network": result.get("network"),
                            "first_aired": result.get("firstAired"),
                            "status": result.get("status"),
                        },
                    )
                )

            return metadata_results

        except Exception as e:
            logger.error(f"Error searching TVDB for '{query}': {e}")
            return []


class TMDBMetadataFetcher(MetadataFetcher):
    """Metadata fetcher for TMDB."""

    def __init__(
        self,
        client: Optional[TMDBClient] = None,
        api_key: str = DEFAULT_TMDB_API_KEY,
        cache_size: int = CACHE_SIZE,
    ):
        """Initialize the TMDB metadata fetcher.

        Args:
            client: TMDBClient instance, or None to create a new one
            api_key: TMDB API key (defaults to environment variable)
            cache_size: Size of the LRU cache for metadata results
        """
        super().__init__(cache_size=cache_size)
        self.client = client or TMDBClient(api_key=api_key)

        # Extract ID from prefixed ID (e.g., "tmdb:12345" -> 12345)
        self._extract_id = lambda id: int(id.split(":")[1]) if ":" in id else int(id)

    def _fetch_metadata_uncached(self, id: str, media_type: MediaType) -> MetadataResult:
        """Fetch metadata from TMDB without caching.

        Args:
            id: TMDB ID (either "tmdb:12345" or "12345")
            media_type: Type of media (TV_SHOW or MOVIE)

        Returns:
            Metadata result object

        Raises:
            ValueError: If media_type is not supported
        """
        tmdb_id = self._extract_id(id)

        try:
            if media_type == MediaType.MOVIE:
                # Get movie details
                movie = self.client.get_movie_details(movie_id=tmdb_id)

                # Extract year from release date
                year = None
                if "release_date" in movie and movie["release_date"]:
                    year_match = re.match(r"(\d{4})", movie["release_date"])
                    if year_match:
                        year = int(year_match.group(1))

                # Process genres into a list of names
                genres = []
                if "genres" in movie and isinstance(movie["genres"], list):
                    genres = [genre["name"] for genre in movie["genres"]]

                return MetadataResult(
                    id=f"tmdb:{tmdb_id}",
                    title=movie.get("title", "Unknown"),
                    overview=movie.get("overview"),
                    media_type=MediaType.MOVIE,
                    source="tmdb",
                    year=year,
                    extra_data={
                        "release_date": movie.get("release_date"),
                        "runtime": movie.get("runtime"),
                        "genres": genres,
                        "vote_average": movie.get("vote_average"),
                        "original_language": movie.get("original_language"),
                    },
                )

            elif media_type == MediaType.TV_SHOW:
                # Get TV show details
                tv_show = self.client.get_tv_details(tv_id=tmdb_id)

                # Extract year from first air date
                year = None
                if "first_air_date" in tv_show and tv_show["first_air_date"]:
                    year_match = re.match(r"(\d{4})", tv_show["first_air_date"])
                    if year_match:
                        year = int(year_match.group(1))

                # Process genres into a list of names
                genres = []
                if "genres" in tv_show and isinstance(tv_show["genres"], list):
                    genres = [genre["name"] for genre in tv_show["genres"]]

                # Process seasons and episodes
                seasons = []
                if "number_of_seasons" in tv_show and tv_show["number_of_seasons"] > 0:
                    for season_number in range(1, tv_show["number_of_seasons"] + 1):
                        try:
                            season_data = self.client.get_tv_season(
                                tv_id=tmdb_id, season_number=season_number
                            )

                            formatted_episodes = []
                            if "episodes" in season_data:
                                for episode in season_data["episodes"]:
                                    formatted_episodes.append(
                                        {
                                            "id": episode.get("id"),
                                            "name": episode.get("name"),
                                            "overview": episode.get("overview"),
                                            "episode_number": episode.get("episode_number"),
                                            "air_date": episode.get("air_date"),
                                        }
                                    )

                            seasons.append(
                                {"season_number": season_number, "episodes": formatted_episodes}
                            )
                        except Exception as e:
                            logger.warning(
                                f"Error fetching season {season_number} for TV show {tmdb_id}: {e}"
                            )

                return MetadataResult(
                    id=f"tmdb:{tmdb_id}",
                    title=tv_show.get("name", "Unknown"),
                    overview=tv_show.get("overview"),
                    media_type=MediaType.TV_SHOW,
                    source="tmdb",
                    year=year,
                    extra_data={
                        "first_air_date": tv_show.get("first_air_date"),
                        "last_air_date": tv_show.get("last_air_date"),
                        "number_of_seasons": tv_show.get("number_of_seasons"),
                        "number_of_episodes": tv_show.get("number_of_episodes"),
                        "genres": genres,
                        "vote_average": tv_show.get("vote_average"),
                        "seasons": seasons,
                    },
                )

            else:
                raise ValueError(f"Unsupported media type: {media_type}")

        except Exception as e:
            logger.error(f"Error fetching TMDB metadata for ID {id}: {e}")
            raise

    def search(self, query: str, media_type: MediaType) -> List[MetadataResult]:
        """Search for movies or TV shows by name.

        Args:
            query: Search query
            media_type: Type of media to search for (TV_SHOW or MOVIE)

        Returns:
            List of metadata results

        Raises:
            ValueError: If media_type is not supported
        """
        try:
            if media_type == MediaType.MOVIE:
                # Search for movies
                search_results = self.client.search_movie(query=query)
                movie_results = extract_dict_list(search_results)

                metadata_results: List[MetadataResult] = []
                for result in movie_results:
                    movie_id = result.get("id")

                    # Extract year from release date
                    year = None
                    release_date = result.get("release_date")
                    if isinstance(release_date, str):
                        year_match = re.match(r"(\d{4})", release_date)
                        if year_match:
                            year = int(year_match.group(1))

                    metadata_results.append(
                        MetadataResult(
                            id=f"tmdb:{movie_id}",
                            title=result.get("title", "Unknown"),
                            overview=result.get("overview"),
                            media_type=MediaType.MOVIE,
                            source="tmdb",
                            year=year,
                            extra_data={
                                "release_date": result.get("release_date"),
                                "vote_average": result.get("vote_average"),
                                "original_language": result.get("original_language"),
                            },
                        )
                    )

                return metadata_results

            elif media_type == MediaType.TV_SHOW:
                # Search for TV shows
                search_results = self.client.search_tv(query=query)
                tv_results = extract_dict_list(search_results)

                tv_metadata_results: List[MetadataResult] = []
                for result in tv_results:
                    tv_id = result.get("id")

                    # Extract year from first air date
                    year = None
                    first_air_date = result.get("first_air_date")
                    if isinstance(first_air_date, str):
                        year_match = re.match(r"(\d{4})", first_air_date)
                        if year_match:
                            year = int(year_match.group(1))

                    tv_metadata_results.append(
                        MetadataResult(
                            id=f"tmdb:{tv_id}",
                            title=result.get("name", "Unknown"),
                            overview=result.get("overview"),
                            media_type=MediaType.TV_SHOW,
                            source="tmdb",
                            year=year,
                            extra_data={
                                "first_air_date": result.get("first_air_date"),
                                "vote_average": result.get("vote_average"),
                                "original_language": result.get("original_language"),
                            },
                        )
                    )

                return tv_metadata_results

            else:
                raise ValueError(f"Unsupported media type: {media_type}")

        except Exception as e:
            logger.error(f"Error searching TMDB for '{query}': {e}")
            return []


class AniDBMetadataFetcher(MetadataFetcher):
    """Metadata fetcher for AniDB."""

    def __init__(
        self,
        client: Optional[AniDBClient] = None,
        username: str = DEFAULT_ANIDB_USERNAME,
        password: str = DEFAULT_ANIDB_PASSWORD,
        cache_size: int = CACHE_SIZE,
    ):
        """Initialize the AniDB metadata fetcher.

        Args:
            client: AniDBClient instance, or None to create a new one
            username: AniDB username (defaults to environment variable)
            password: AniDB password (defaults to environment variable)
            cache_size: Size of the LRU cache for metadata results
        """
        super().__init__(cache_size=cache_size)
        self.client = client or AniDBClient(username=username, password=password)

        # Extract ID from prefixed ID (e.g., "anidb:12345" -> 12345)
        self._extract_id = lambda id: int(id.split(":")[1]) if ":" in id else int(id)

    def _fetch_metadata_uncached(self, id: str, media_type: MediaType) -> MetadataResult:
        """Fetch metadata from AniDB without caching.

        Args:
            id: AniDB ID (either "anidb:12345" or "12345")
            media_type: Type of media (only ANIME is supported)

        Returns:
            Metadata result object

        Raises:
            ValueError: If media_type is not ANIME
        """
        if media_type != MediaType.ANIME:
            raise ValueError("AniDB only supports anime")

        anime_id = self._extract_id(id)

        try:
            # Get anime details
            anime = self.client.get_anime_details(anime_id=anime_id)

            # Get episodes
            episodes = self.client.get_episodes_with_titles(anime_id=anime_id)

            # Process episodes into a standardized format
            formatted_episodes = []
            for episode in episodes:
                formatted_episodes.append(
                    {
                        "id": episode.get("id"),
                        "title": episode.get("title"),
                        "number": episode.get("epno"),
                        "length": episode.get("length"),
                    }
                )

            # Extract year from start date if available
            year = None
            if "startdate" in anime and anime["startdate"]:
                year_match = re.match(r"(\d{4})", anime["startdate"])
                if year_match:
                    year = int(year_match.group(1))

            return MetadataResult(
                id=f"anidb:{anime_id}",
                title=anime.get("title", "Unknown"),
                overview=anime.get("description"),
                media_type=MediaType.ANIME,
                source="anidb",
                year=year,
                extra_data={
                    "type": anime.get("type"),
                    "episodes_count": anime.get("episodes"),
                    "start_date": anime.get("startdate"),
                    "end_date": anime.get("enddate"),
                    "episodes": formatted_episodes,
                },
            )

        except Exception as e:
            logger.error(f"Error fetching AniDB metadata for ID {id}: {e}")
            raise

    def search(self, query: str, media_type: MediaType) -> List[MetadataResult]:
        """Search for anime by name.

        Args:
            query: Search query
            media_type: Type of media to search for (only ANIME is supported)

        Returns:
            List of metadata results

        Raises:
            ValueError: If media_type is not ANIME
        """
        if media_type != MediaType.ANIME:
            raise ValueError("AniDB only supports anime")

        try:
            # Get anime results and ensure they're the right type
            raw_results = self.client.get_anime_by_name(name=query)
            anime_results = extract_dict_list(raw_results)

            if not anime_results:
                logger.warning(f"No valid anime results found for query: {query}")
                return []

            anime_metadata_results: List[MetadataResult] = []

            # Process results
            for result in anime_results:
                anime_id = result.get("aid")

                # Extract year from start date if available
                year = None
                start_date = result.get("startdate")
                if isinstance(start_date, str):
                    year_match = re.match(r"(\d{4})", start_date)
                    if year_match:
                        year = int(year_match.group(1))

                anime_metadata_results.append(
                    MetadataResult(
                        id=f"anidb:{anime_id}",
                        title=result.get("title", "Unknown"),
                        overview=result.get("description"),
                        media_type=MediaType.ANIME,
                        source="anidb",
                        year=year,
                        extra_data={"type": result.get("type"), "episodes": result.get("episodes")},
                    )
                )

            return anime_metadata_results

        except Exception as e:
            logger.error(f"Error searching AniDB for '{query}': {e}")
            return []


class TVMazeMetadataFetcher(MetadataFetcher):
    """Metadata fetcher for TVMaze."""

    def __init__(self, client: Optional[TVMazeClient] = None, cache_size: int = CACHE_SIZE):
        """Initialize the TVMaze metadata fetcher.

        Args:
            client: TVMazeClient instance, or None to create a new one
            cache_size: Size of the LRU cache for metadata results
        """
        super().__init__(cache_size=cache_size)
        self.client = client or TVMazeClient()

        # Extract ID from prefixed ID (e.g., "tvmaze:12345" -> 12345)
        self._extract_id = lambda id: int(id.split(":")[1]) if ":" in id else int(id)

    def _fetch_metadata_uncached(self, id: str, media_type: MediaType) -> MetadataResult:
        """Fetch metadata from TVMaze without caching.

        Args:
            id: TVMaze ID (either "tvmaze:12345" or "12345")
            media_type: Type of media (only TV_SHOW is supported)

        Returns:
            Metadata result object

        Raises:
            ValueError: If media_type is not TV_SHOW
        """
        if media_type != MediaType.TV_SHOW:
            raise ValueError("TVMaze only supports TV shows")

        tvmaze_id = self._extract_id(id)

        try:
            # Get show details
            show = self.client.get_show_by_id(show_id=tvmaze_id)

            # Remove HTML tags from summary
            summary = show.get("summary", "")
            if summary:
                summary = re.sub(r"<.*?>", "", summary)

            # Get episodes
            episodes = self.client.get_episodes(show_id=tvmaze_id)

            # Get show cast
            cast = self.client.get_show_cast(show_id=tvmaze_id)

            # Process episodes into a standardized format
            formatted_episodes = []
            for episode in episodes:
                # Remove HTML tags from episode summary
                episode_summary = episode.get("summary", "")
                if episode_summary:
                    episode_summary = re.sub(r"<.*?>", "", episode_summary)

                formatted_episodes.append(
                    {
                        "id": episode.get("id"),
                        "title": episode.get("name"),
                        "overview": episode_summary,
                        "season": episode.get("season"),
                        "episode": episode.get("number"),
                        "air_date": episode.get("airdate"),
                    }
                )

            # Process cast into a standardized format
            formatted_cast = []
            for cast_member in cast:
                formatted_cast.append(
                    {
                        "actor": cast_member.get("person", {}).get("name"),
                        "character": cast_member.get("character", {}).get("name"),
                    }
                )

            # Extract year from premiered date if available
            year = None
            if "premiered" in show and show["premiered"]:
                year_match = re.match(r"(\d{4})", show["premiered"])
                if year_match:
                    year = int(year_match.group(1))

            # Extract network name
            network = None
            if "network" in show and isinstance(show["network"], dict):
                network = show["network"].get("name")

            return MetadataResult(
                id=f"tvmaze:{tvmaze_id}",
                title=show.get("name", "Unknown"),
                overview=summary,
                media_type=MediaType.TV_SHOW,
                source="tvmaze",
                year=year,
                extra_data={
                    "premiered": show.get("premiered"),
                    "ended": show.get("ended"),
                    "status": show.get("status"),
                    "network": network,
                    "episodes": formatted_episodes,
                    "cast": formatted_cast,
                },
            )

        except Exception as e:
            logger.error(f"Error fetching TVMaze metadata for ID {id}: {e}")
            raise

    def search(self, query: str, media_type: MediaType) -> List[MetadataResult]:
        """Search for TV shows by name.

        Args:
            query: Search query
            media_type: Type of media to search for (only TV_SHOW is supported)

        Returns:
            List of metadata results

        Raises:
            ValueError: If media_type is not TV_SHOW
        """
        if media_type != MediaType.TV_SHOW:
            raise ValueError("TVMaze only supports TV shows")

        try:
            results = self.client.search_shows(query=query)

            metadata_results = []
            for result in results:
                # TVMaze search returns results in a specific format
                if "show" not in result:
                    continue

                show = result["show"]
                score = result.get("score", 0.0)
                tvmaze_id = show.get("id")

                # Remove HTML tags from summary
                summary = show.get("summary", "")
                if summary:
                    summary = re.sub(r"<.*?>", "", summary)

                # Extract year from premiered date if available
                year = None
                if "premiered" in show and show["premiered"]:
                    year_match = re.match(r"(\d{4})", show["premiered"])
                    if year_match:
                        year = int(year_match.group(1))

                # Extract network name
                network = None
                if "network" in show and isinstance(show["network"], dict):
                    network = show["network"].get("name")

                metadata_results.append(
                    MetadataResult(
                        id=f"tvmaze:{tvmaze_id}",
                        title=show.get("name", "Unknown"),
                        overview=summary,
                        media_type=MediaType.TV_SHOW,
                        source="tvmaze",
                        year=year,
                        extra_data={
                            "premiered": show.get("premiered"),
                            "status": show.get("status"),
                            "network": network,
                            "score": score,
                        },
                        confidence=score,
                    )
                )

            return metadata_results

        except Exception as e:
            logger.error(f"Error searching TVMaze for '{query}': {e}")
            return []
