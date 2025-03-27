"""Functions for processing episodes, including anthology episode handling."""

import os
import logging
from enum import Enum, auto
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import functions from other modules
from plexomatic.utils.episode.parser import extract_show_info
from plexomatic.utils.episode.detector import (
    filter_segments,
    detect_segments_from_file,
    detect_special_episodes,
)


class EpisodeType(Enum):
    """Type of episode based on content and structure."""

    STANDARD = auto()  # Single episode
    MULTI_EPISODE = auto()  # Multiple episodes back-to-back
    ANTHOLOGY = auto()  # Multiple segments as single episode


def determine_episode_type(
    file_info: Dict[str, Any], segments: Optional[List[str]] = None, anthology_mode: bool = False
) -> EpisodeType:
    """
    Determine the type of episode based on the file information and segments.

    Args:
        file_info: Information about the episode file
        segments: List of segment titles if available
        anthology_mode: Whether anthology mode is enabled

    Returns:
        The episode type
    """
    # Check for multi-episodes by looking for episode_numbers or multi_episodes keys
    if "multi_episodes" in file_info and len(file_info["multi_episodes"]) > 1:
        return EpisodeType.MULTI_EPISODE

    if "episode_numbers" in file_info and len(file_info["episode_numbers"]) > 1:
        return EpisodeType.MULTI_EPISODE

    # Check for anthology episodes when segments are provided
    if segments and len(segments) > 1:
        return EpisodeType.ANTHOLOGY

    # Otherwise, it's a standard episode
    return EpisodeType.STANDARD


def detect_segments_with_llm(title_part: str, max_segments: int = 10) -> List[str]:
    """
    Use LLM to detect segments in an episode title.

    Args:
        title_part: The title part of the episode filename
        max_segments: Maximum number of segments to detect

    Returns:
        List of detected segments
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Detecting segments with LLM in: {title_part}")

    try:
        from plexomatic.api.llm_client import LLMClient

        client = LLMClient()

        if not client.check_model_available():
            logger.warning("LLM model not available for segment detection")
            return []

        # Prepare the prompt for segment detection
        prompt = f"""
        Analyze this text and split it into distinct anthology segments or short stories.
        Each segment should be a separate title. Only return the separated titles, one per line.
        Maximum {max_segments} segments.

        Text: {title_part}
        """

        # Get the response from the LLM - using generate_text instead of get_completion
        response = client.generate_text(prompt)

        if not response:
            logger.warning("No response from LLM for segment detection")
            return []

        # Process the response
        segments = [segment.strip() for segment in response.split("\n") if segment.strip()]

        # Filter out any segments that are not valid titles
        segments = filter_segments(segments)

        # Limit the number of segments
        segments = segments[:max_segments]

        logger.debug(f"LLM detected segments: {segments}")
        return segments

    except ImportError:
        logger.warning("LLM client not available for segment detection")
        return []
    except Exception as e:
        logger.error(f"Error in LLM segment detection: {str(e)}")
        return []


def process_anthology_episode(
    original_path: str, use_llm: bool = False, anthology_mode: bool = True, max_segments: int = 10
) -> Optional[Dict[str, Any]]:
    """
    Process an anthology episode, identifying segments and assigning episode numbers.

    Args:
        original_path: Path to the episode file
        use_llm: Whether to use LLM for segment detection
        anthology_mode: Whether anthology mode is enabled
        max_segments: Maximum number of segments to detect

    Returns:
        Dictionary with episode information, segments, and episode numbers
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Processing anthology episode: {original_path}")

    # Extract basic show information
    info = extract_show_info(original_path)
    if not info:
        logger.warning(f"Could not extract show info from: {original_path}")
        return None

    # Get the base episode number
    base_episode = info.get("episode", 1)

    # Initialize result
    result = {
        "show_name": info.get("show_name", ""),
        "season": info.get("season", 1),
        "episode_numbers": [base_episode],
        "segments": [],
        "is_anthology": False,
    }

    # If anthology mode is disabled, just return the basic info
    if not anthology_mode:
        return result

    # Detect segments
    segments = detect_segments_from_file(original_path, use_llm=use_llm, max_segments=max_segments)

    # If we have segments, process as an anthology episode
    if segments and len(segments) > 1:
        result["segments"] = segments
        result["episode_numbers"] = [base_episode + i for i in range(len(segments))]
        result["is_anthology"] = True

    return result


def process_episode(
    original_path: str, use_llm: bool = False, anthology_mode: bool = False, max_segments: int = 10
) -> Optional[Dict[str, Any]]:
    """
    Process an episode file, determining its type and extracting relevant information.

    Args:
        original_path: Path to the episode file
        use_llm: Whether to use LLM for assistance
        anthology_mode: Whether anthology mode is enabled
        max_segments: Maximum number of segments to detect

    Returns:
        Dictionary with episode information or None if processing fails
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Processing episode: {original_path}")

    # Extract basic information
    info = extract_show_info(original_path)
    if not info:
        logger.warning(f"Could not extract show info from: {original_path}")
        return None

    # Determine episode type
    episode_type = determine_episode_type(info, segments=None, anthology_mode=anthology_mode)

    # Handle different episode types
    if episode_type == EpisodeType.ANTHOLOGY:
        result = process_anthology_episode(
            original_path=original_path, use_llm=use_llm, max_segments=max_segments
        )
        return result
    elif episode_type == EpisodeType.MULTI_EPISODE:
        # Return info with multi_episodes data
        return {
            "show_name": info.get("show_name", ""),
            "season": info.get("season", 1),
            "episode": info.get("episode", 1),
            "title": info.get("title", ""),
            "multi_episodes": info.get("multi_episodes", []),
        }
    else:  # Standard episode
        return {
            "show_name": info.get("show_name", ""),
            "season": info.get("season", 1),
            "episode": info.get("episode", 1),
            "title": info.get("title", ""),
        }


def match_episode_titles(
    segment_titles: List[str], show_id: str, season_number: int
) -> Dict[str, Dict[str, Any]]:
    """
    Match segment titles to episode numbers using TVDb API.

    Args:
        segment_titles: List of segment titles to match
        show_id: The TVDb ID of the show
        season_number: The season number

    Returns:
        Dictionary mapping segment titles to episode data
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Matching segment titles with TVDb API: {season_number}")

    # Initialize the returned mapping
    matches: Dict[str, Dict[str, Any]] = {}

    try:
        # Import here to avoid circular imports
        from plexomatic.api.tvdb_client import TVDBClient
        from plexomatic.config.config_manager import ConfigManager
        import difflib

        # Get API key from environment or config
        config = ConfigManager()
        api_key = os.environ.get("TVDB_API_KEY") or config.get("tvdb_api_key")

        if not api_key:
            logger.warning("No TVDB API key found in environment or config")
            return {}

        # Initialize TVDb client
        client = TVDBClient(api_key=api_key)

        # Get episodes for the season
        all_episodes = client.get_episodes_by_series_id(show_id)
        if not all_episodes:
            logger.warning(f"No episodes found for series {show_id}")
            return {}

        # Filter episodes for the specified season
        episodes = [ep for ep in all_episodes if ep.get("airedSeason") == season_number]
        if not episodes:
            logger.warning(f"No episodes found for series {show_id}, season {season_number}")
            return {}

        logger.debug(f"Found {len(episodes)} episodes for Season {season_number}")

        # Create a mapping of normalized titles to episode data for fuzzy matching
        normalized_title_map = {}
        for episode in episodes:
            episode_title = episode.get("name", "")
            episode_number = episode.get("number")

            if episode_title and episode_number is not None:
                # Normalize the title for better matching
                normalized_title = episode_title.lower().strip()
                normalized_title_map[normalized_title] = {
                    "title": episode_title,
                    "episode_number": episode_number,
                }

        # Match each segment title to the closest episode title
        for segment_title in segment_titles:
            normalized_segment = segment_title.lower().strip()

            # Try exact match first
            if normalized_segment in normalized_title_map:
                matches[segment_title] = normalized_title_map[normalized_segment]
                continue

            # Try fuzzy matching
            best_score: float = 0.0
            best_match = None

            for api_title, episode_data in normalized_title_map.items():
                # Skip titles that were already matched
                if any(
                    data["episode_number"] == episode_data["episode_number"]
                    for data in matches.values()
                ):
                    continue

                # Calculate similarity score
                score = difflib.SequenceMatcher(None, normalized_segment, api_title).ratio()

                # If it's a good enough match and better than previous matches
                if score > 0.8 and score > best_score:
                    best_score = score
                    best_match = (api_title, episode_data)

            # If we found a good match, use it
            if best_match:
                matches[segment_title] = best_match[1]
                logger.debug(
                    f"Matched '{segment_title}' to '{best_match[0]}' (E{best_match[1]['episode_number']}) with score {best_score:.2f}"
                )

    except Exception as e:
        logger.error(f"Error matching episode titles: {e}")
        if logger.isEnabledFor(logging.DEBUG):
            logger.exception(e)

    # Return the mapping, which may be empty if no matches were found
    return matches


def split_title_by_separators(title: str) -> List[str]:
    """Split a title by common separators like '&', ',', '+', etc.

    Args:
        title: The title to split

    Returns:
        List of title segments
    """

    # Define the separators to split on
    separators = [" & ", ", ", " + ", " - ", " and "]

    # Check if any separators are in the title
    for sep in separators:
        if sep in title:
            return [segment.strip() for segment in title.split(sep)]

    # If no separators found, return the title as a single segment
    return [title]


def match_episode_titles_with_data(
    segments: List[str], api_data: List[Dict[str, Any]]
) -> Dict[str, Optional[int]]:
    """Match episode titles with API data.

    Args:
        segments: List of segment titles
        api_data: API data containing episode information

    Returns:
        Dictionary mapping segment titles to episode numbers
    """
    matches: Dict[str, Optional[int]] = {}

    # If either segments or API data is empty, return empty matches
    if not segments or not api_data:
        return matches

    # Create a dictionary of API data episode titles
    api_episodes = {episode.get("name", ""): episode.get("episode_number") for episode in api_data}

    # Try to match segments with API data
    for segment in segments:
        # Try exact match first
        if segment in api_episodes:
            matches[segment] = api_episodes[segment]
            continue

        # Try partial match (segment is contained in API title)
        for api_title, episode_number in api_episodes.items():
            if segment.lower() in api_title.lower():
                matches[segment] = episode_number
                break

    return matches


def organize_season_pack(files: List[Path]) -> Dict[str, List[Path]]:
    """Organize files from a season pack into seasons.

    Args:
        files: List of file paths

    Returns:
        Dictionary mapping season names to lists of files
    """
    result: Dict[str, List[Path]] = {"Season 1": [], "Season 2": [], "Specials": [], "Unknown": []}

    for file in files:
        filename = file.name

        # Check for special episodes
        if detect_special_episodes(filename):
            result["Specials"].append(file)
            continue

        # Extract show info
        info = extract_show_info(filename)

        # Organize by season
        if info is not None and "season" in info:
            season_key = f"Season {info['season']}"
            if season_key not in result:
                result[season_key] = []
            result[season_key].append(file)
        else:
            # Unknown files
            result["Unknown"].append(file)

    return result
