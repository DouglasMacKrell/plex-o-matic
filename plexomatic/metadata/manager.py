"""Metadata manager for aggregating and managing metadata from multiple sources.

This module provides a unified interface for searching, matching, and fetching metadata
from various sources like TVDB, TMDB, AniDB, and TVMaze.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Union, cast
from functools import lru_cache
from dataclasses import dataclass

from plexomatic.metadata.fetcher import (
    TVDBMetadataFetcher,
    TMDBMetadataFetcher,
    AniDBMetadataFetcher,
    TVMazeMetadataFetcher,
    MediaType,
)

logger = logging.getLogger(__name__)

# Constants
MATCH_THRESHOLD = 0.5  # Minimum confidence for a match
CACHE_SIZE = 100  # Size of LRU cache


@dataclass
class MetadataMatchResult:
    """Class representing the result of a metadata match operation."""

    matched: bool
    """Whether a valid match was found."""

    title: Optional[str] = None
    """The matched title, if any."""

    year: Optional[int] = None
    """The matched year, if any."""

    media_type: Optional[MediaType] = None
    """The type of media that was matched."""

    confidence: float = 0.0
    """The confidence level of the match (0.0 to 1.0)."""

    metadata: Optional[Dict[str, Any]] = None
    """The full metadata result if matched."""

    @property
    def id(self) -> Optional[str]:
        """Get the ID of the matched metadata, if any."""
        return self.metadata.get("id") if self.metadata else None

    @property
    def source(self) -> Optional[str]:
        """Get the source of the matched metadata, if any."""
        return self.metadata.get("source") if self.metadata else None


# Type for all fetcher types
FetcherType = Union[
    TVDBMetadataFetcher, TMDBMetadataFetcher, AniDBMetadataFetcher, TVMazeMetadataFetcher
]


class MetadataManager:
    """Manager for coordinating metadata operations across multiple sources."""

    def __init__(
        self,
        tvdb_fetcher: Optional[TVDBMetadataFetcher] = None,
        tmdb_fetcher: Optional[TMDBMetadataFetcher] = None,
        anidb_fetcher: Optional[AniDBMetadataFetcher] = None,
        tvmaze_fetcher: Optional[TVMazeMetadataFetcher] = None,
    ):
        """Initialize the metadata manager.

        Args:
            tvdb_fetcher: TVDBMetadataFetcher instance, or None to create a new one
            tmdb_fetcher: TMDBMetadataFetcher instance, or None to create a new one
            anidb_fetcher: AniDBMetadataFetcher instance, or None to create a new one
            tvmaze_fetcher: TVMazeMetadataFetcher instance, or None to create a new one
        """
        self.fetchers: Dict[str, FetcherType] = {}

        # Store fetchers if provided
        if tvdb_fetcher:
            self.fetchers["tvdb"] = tvdb_fetcher
        if tmdb_fetcher:
            self.fetchers["tmdb"] = tmdb_fetcher
        if anidb_fetcher:
            self.fetchers["anidb"] = anidb_fetcher
        if tvmaze_fetcher:
            self.fetchers["tvmaze"] = tvmaze_fetcher

        # Initialize cache (will be decorated with lru_cache below)
        self.cache: Dict[str, Any] = {}

    def _search_uncached(self, query: str, media_type: Optional[MediaType]) -> List[Dict[str, Any]]:
        """
        Search for media without caching.

        Args:
            query: The search term
            media_type: Type of media to search for (TV_SHOW, MOVIE, ANIME, or None for all)

        Returns:
            List of metadata results
        """
        results = []

        # Track errors for logging
        errors = []

        # Search TV shows
        if media_type is None or media_type == MediaType.TV_SHOW:
            for source, fetcher in self.fetchers.items():
                if hasattr(fetcher, "search_show"):
                    try:
                        show_results = fetcher.search_show(query)
                        results.extend(show_results)
                    except Exception as e:
                        errors.append(f"Error searching {source} for TV show '{query}': {str(e)}")

        # Search movies
        if media_type is None or media_type == MediaType.MOVIE:
            for source, fetcher in self.fetchers.items():
                if hasattr(fetcher, "search_movie"):
                    try:
                        movie_results = fetcher.search_movie(query)
                        results.extend(movie_results)
                    except Exception as e:
                        errors.append(f"Error searching {source} for movie '{query}': {str(e)}")

        # Search anime
        if media_type is None or media_type == MediaType.ANIME:
            for source, fetcher in self.fetchers.items():
                if hasattr(fetcher, "search_anime"):
                    try:
                        anime_results = fetcher.search_anime(query)
                        results.extend(anime_results)
                    except Exception as e:
                        errors.append(f"Error searching {source} for anime '{query}': {str(e)}")

        # Log any errors
        for error in errors:
            logger.warning(error)

        # Sort results by confidence if present
        results.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        return results

    @lru_cache(maxsize=CACHE_SIZE)
    def _cached_search(self, query: str, media_type_str: Optional[str]) -> List[Dict[str, Any]]:
        """Cached version of the search method.

        Args:
            query: Search query
            media_type_str: String representation of the media type

        Returns:
            List of metadata results
        """
        media_type = None
        if media_type_str:
            media_type = MediaType[media_type_str]
        return self._search_uncached(query, media_type)

    def search(self, query: str, media_type: Optional[MediaType] = None) -> List[Dict[str, Any]]:
        """
        Search for metadata across all configured sources.

        Args:
            query: The search term
            media_type: Type of media to search for (TV_SHOW, MOVIE, ANIME, or None for all)

        Returns:
            List of metadata results
        """
        # For testing purposes, allow direct patching of this method
        return self._search_uncached(query, media_type)

    def fetch_metadata(self, metadata_id: str) -> Dict[str, Any]:
        """Fetch metadata for a specific ID.

        Args:
            metadata_id: ID in the format "source:id" or "source-id" (e.g. "tvdb:12345" or "tvdb-12345")

        Returns:
            Metadata dictionary

        Raises:
            ValueError: If the source is not recognized
        """
        # Handle both "source:id" and "source-id" formats
        if ":" in metadata_id:
            source, source_id = metadata_id.split(":", 1)
        elif "-" in metadata_id:
            source, source_id = metadata_id.split("-", 1)
        else:
            raise ValueError(
                f"Invalid metadata ID format: {metadata_id}, expected source:id or source-id"
            )

        if source not in self.fetchers:
            raise ValueError(f"Unknown metadata source: {source}")

        fetcher = self.fetchers[source]

        # Call the appropriate method based on the source
        if source == "tvdb":
            if isinstance(fetcher, TVDBMetadataFetcher) and hasattr(fetcher, "get_show_details"):
                return cast(Dict[str, Any], fetcher.get_show_details(source_id))
        elif source == "tvmaze":
            if isinstance(fetcher, TVMazeMetadataFetcher) and hasattr(fetcher, "get_show_details"):
                return cast(Dict[str, Any], fetcher.get_show_details(source_id))
        elif source == "tmdb":
            if isinstance(fetcher, TMDBMetadataFetcher) and hasattr(fetcher, "get_movie_details"):
                return cast(Dict[str, Any], fetcher.get_movie_details(source_id))
        elif source == "anidb":
            if isinstance(fetcher, AniDBMetadataFetcher) and hasattr(fetcher, "get_anime_details"):
                return cast(Dict[str, Any], fetcher.get_anime_details(source_id))

        # If we get here, either the source is not supported or the method doesn't exist
        raise ValueError(f"No fetch method available for source: {source}")

    def fetch_episode_metadata(
        self, metadata_id: str, episode_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch metadata for specific episodes.

        Args:
            metadata_id: ID in the format "source:id" or "source-id" (e.g. "tvdb:12345" or "tvdb-12345")
            episode_info: Dictionary containing episode information:
                - For special episodes: {'special_type': str, 'special_number': Optional[int]}
                - For multi-episodes: {'episodes': List[int], 'season': Optional[int]}

        Returns:
            Metadata dictionary with episode-specific information

        Raises:
            ValueError: If the source is not recognized or doesn't support episode fetching
        """
        # Handle both "source:id" and "source-id" formats
        if ":" in metadata_id:
            source, source_id = metadata_id.split(":", 1)
        elif "-" in metadata_id:
            source, source_id = metadata_id.split("-", 1)
        else:
            raise ValueError(
                f"Invalid metadata ID format: {metadata_id}, expected source:id or source-id"
            )

        if source not in self.fetchers:
            raise ValueError(f"Unknown metadata source: {source}")

        fetcher = self.fetchers[source]

        # Only TVDB and TVMaze support episode fetching
        if source not in ["tvdb", "tvmaze"]:
            raise ValueError(f"Source {source} does not support episode fetching")

        # Get the base metadata first
        base_metadata = self.fetch_metadata(metadata_id)

        # Handle special episodes
        if "special_type" in episode_info:
            if source == "tvdb" and isinstance(fetcher, TVDBMetadataFetcher):
                # Check if the method exists
                if hasattr(fetcher, "get_special_episodes"):
                    # Get special episodes from TVDB
                    special_episodes = fetcher.get_special_episodes(int(source_id))

                    # Find the matching special episode
                    special_number = episode_info.get("special_number")
                    matching_episode = None

                    if special_number is not None:
                        # Find by number
                        for episode in special_episodes:
                            if episode.get("special_number") == special_number:
                                matching_episode = episode
                                break
                    elif special_episodes:
                        # Just take the first one if no number specified
                        matching_episode = special_episodes[0]

                    if matching_episode:
                        # Add the special episode info to the metadata
                        base_metadata["special_episode"] = matching_episode

            # Add the special type to the metadata
            base_metadata["special_type"] = episode_info["special_type"]

        # Handle multi-episodes
        elif "episodes" in episode_info:
            if source == "tvdb" and isinstance(fetcher, TVDBMetadataFetcher):
                # Check if the method exists
                if hasattr(fetcher, "get_episodes_by_numbers"):
                    # Get the episodes by their numbers
                    season = episode_info.get("season", 1)
                    episode_numbers = episode_info["episodes"]

                    episodes = fetcher.get_episodes_by_numbers(
                        int(source_id), episode_numbers, season
                    )

                    if episodes:
                        # Add the episodes to the metadata
                        base_metadata["multi_episodes"] = episodes

            # Add the episode numbers to the metadata
            base_metadata["episode_numbers"] = episode_info["episodes"]

        return base_metadata

    def match(self, filename: str, media_type: Optional[MediaType] = None) -> MetadataMatchResult:
        """
        Match a filename to the best metadata result.

        Args:
            filename: The filename to match
            media_type: Type of media to search for (TV_SHOW, MOVIE, ANIME, or None for all)

        Returns:
            MetadataMatchResult object
        """
        # Check for special episodes if it's a TV show
        if media_type == MediaType.TV_SHOW or media_type is None:
            from plexomatic.utils.episode_handler import (
                detect_special_episodes,
                detect_multi_episodes,
            )

            # Check for special episodes
            special_info = detect_special_episodes(filename)
            if special_info:
                # Extract title for the special episode
                title, _ = self._extract_title_and_year(filename)
                if title:
                    # Create a match result with special episode info
                    return MetadataMatchResult(
                        matched=True,
                        title=title,
                        media_type=MediaType.TV_SHOW,
                        confidence=0.9,  # High confidence for special episode detection
                        metadata={
                            "title": title,
                            "special_type": special_info["type"],
                            "special_number": special_info["number"],
                        },
                    )

            # Check for multi-episodes
            episodes = detect_multi_episodes(filename)
            if len(episodes) > 1:
                # Extract title for the multi-episode
                title, _ = self._extract_title_and_year(filename)
                if title:
                    # Create a match result with multi-episode info
                    return MetadataMatchResult(
                        matched=True,
                        title=title,
                        media_type=MediaType.TV_SHOW,
                        confidence=0.9,  # High confidence for multi-episode detection
                        metadata={"title": title, "episodes": episodes},
                    )

        # Extract title and year from filename
        title, year = self._extract_title_and_year(filename)

        if not title:
            logger.warning(f"Could not extract title from filename: {filename}")
            return MetadataMatchResult(matched=False, confidence=0.0)

        # Search for metadata
        results = self.search(title, media_type)

        if not results:
            logger.info(f"No metadata found for '{title}'")
            return MetadataMatchResult(matched=False, confidence=0.0)

        # Find the best match
        best_match = None
        best_confidence = 0.0

        for result in results:
            confidence = self._calculate_match_confidence(title, year, result)

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = result

        # Check if the best match exceeds the threshold
        if best_confidence >= MATCH_THRESHOLD and best_match:
            return MetadataMatchResult(
                matched=True,
                title=best_match.get("title"),
                year=best_match.get("year"),
                media_type=media_type,
                confidence=best_confidence,
                metadata=best_match,
            )
        else:
            return MetadataMatchResult(matched=False, confidence=best_confidence)

    def _extract_title_and_year(self, filename: str) -> Tuple[str, Optional[int]]:
        """
        Extract the title and year from a filename.

        Args:
            filename: The filename to process

        Returns:
            Tuple of (title, year)
        """
        # Remove file extension
        filename = re.sub(r"\.[^.]+$", "", filename)

        # Extract year if present
        year_match = re.search(r"(?:^|\D)(\d{4})(?:\D|$)", filename)
        year = int(year_match.group(1)) if year_match else None

        # Clean up the title
        title = filename

        # Remove year
        if year:
            title = re.sub(r"\.?\(?{}(?:\.\))?".format(year), "", title)

        # Remove season/episode info
        title = re.sub(r"S\d{1,2}E\d{1,2}.*", "", title, flags=re.IGNORECASE)
        title = re.sub(r"Season\s+\d+.*", "", title, flags=re.IGNORECASE)

        # Handle anime-style filenames
        title = re.sub(r"\[\w+\]", "", title)  # Remove [Group] tags
        title = re.sub(r"\s*-\s*\d+.*", "", title)  # Remove episode numbers
        title = re.sub(r"\[\d+p\]", "", title)  # Remove quality tags

        # Replace dots, underscores, dashes with spaces
        title = re.sub(r"[._-]", " ", title)

        # Remove extra spaces and trim
        title = re.sub(r"\s+", " ", title).strip()

        return title, year

    def _calculate_match_confidence(
        self, title: str, year: Optional[int], metadata: Dict[str, Any]
    ) -> float:
        """
        Calculate a confidence score for a metadata match.

        Args:
            title: The extracted title
            year: The extracted year
            metadata: The metadata dictionary

        Returns:
            Confidence score between 0 and 1
        """
        # Start with title similarity
        metadata_title = metadata.get("title", "")
        title_similarity = self._calculate_title_similarity(title, metadata_title)
        confidence = title_similarity * 0.8  # Base confidence from title similarity

        # Check year if available
        if year and metadata.get("year"):
            year_match = year == metadata["year"]
            if year_match:
                confidence += 0.3
            else:
                # Year mismatch slightly reduces confidence
                confidence -= 0.1

        # Cap at 1.0
        confidence = min(confidence, 1.0)

        return confidence

    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles.

        Args:
            title1: First title
            title2: Second title

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Simple case-insensitive exact match
        if title1.lower() == title2.lower():
            return 1.0

        # Normalize titles
        title1 = title1.lower()
        title2 = title2.lower()

        # Remove common words like 'the', 'a', 'an'
        common_words = {"the", "a", "an"}
        words1 = [w for w in title1.split() if w not in common_words]
        words2 = [w for w in title2.split() if w not in common_words]

        # Calculate word intersection
        intersection = set(words1) & set(words2)
        union = set(words1) | set(words2)

        if not union:
            return 0.0

        # Jaccard similarity
        similarity = len(intersection) / len(union)

        return similarity

    def clear_cache(self) -> None:
        """Clear the search cache."""
        self._cached_search.cache_clear()
        logger.info("Metadata search cache cleared")
