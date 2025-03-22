"""Utilities for handling file names and path manipulation."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Union

from plexomatic.core.constants import MediaType
from plexomatic.utils.name_parser import ParsedMediaName, parse_media_name
from plexomatic.utils.default_formatters import format_tv_show, format_movie, format_anime
from plexomatic.utils.multi_episode_formatter import ensure_episode_list


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters.

    Args:
        filename: The filename to sanitize

    Returns:
        str: Sanitized filename
    """
    # Replace characters that are invalid in filenames with underscore
    invalid_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
    sanitized = filename
    for char in invalid_chars:
        sanitized = sanitized.replace(char, "_")
    return sanitized


def extract_show_info(filename: str) -> Dict[str, Optional[str]]:
    """Extract show information from a filename.

    Note: This function is being deprecated in favor of parse_media_name.

    Args:
        filename: The filename to parse

    Returns:
        dict: Extracted information (show_name, season, episode, etc.)
    """
    # Use parse_media_name to get structured data
    parsed = parse_media_name(filename)

    # Convert the parsed object to the old-style dictionary for backward compatibility
    result: Dict[str, Optional[str]] = {}

    if parsed.media_type in (MediaType.TV_SHOW, MediaType.ANIME):
        result["show_name"] = parsed.title
        result["season"] = str(parsed.season) if parsed.season is not None else None
        if parsed.episodes and isinstance(parsed.episodes, list) and len(parsed.episodes) > 0:
            result["episode"] = str(parsed.episodes[0])
        else:
            result["episode"] = None
        result["title"] = parsed.episode_title

    elif parsed.media_type == MediaType.MOVIE:
        result["movie_name"] = parsed.title
        result["year"] = str(parsed.year) if parsed.year is not None else None

    return result


def detect_multi_episodes_simple(filename: str) -> List[int]:
    """Detect multiple episodes in a filename using a simple regex pattern.

    This is a simplified version that doesn't rely on the episode_handler module.

    Args:
        filename: The filename to parse for episodes

    Returns:
        List of episode numbers
    """
    # Pattern for S01E01E02 or S01E01-E02 format
    pattern = r"[sS]\d+[eE](\d+)(?:[eE](\d+))*"
    matches = re.findall(pattern, filename)

    episodes = []
    if matches:
        # First match: tuple of episode numbers (first in group 0, rest in subsequent groups)
        for ep_match in matches[0]:
            if ep_match:  # Skip empty matches
                episodes.append(int(ep_match))

    # Sort episodes and remove duplicates
    return sorted(list(set(episodes)))


def generate_tv_filename(
    show_name: str,
    season: int,
    episode: Union[int, List[int]],
    title: Optional[str] = None,
    extension: str = ".mp4",
) -> str:
    """Generate a standardized TV show filename.

    Args:
        show_name: Name of the show
        season: Season number
        episode: Episode number (int) or list of episode numbers
        title: Episode title (optional)
        extension: File extension (including dot)

    Returns:
        str: Standardized filename
    """
    # Create a ParsedMediaName object
    parsed = ParsedMediaName(
        media_type=MediaType.TV_SHOW,
        title=show_name,
        season=season,
        episodes=ensure_episode_list(episode),
        episode_title=title,
        extension=extension.lstrip("."),
    )

    # Apply the default TV show formatter
    return format_tv_show(parsed)


def generate_movie_filename(movie_name: str, year: int, extension: str = ".mp4") -> str:
    """Generate a standardized movie filename.

    Args:
        movie_name: Name of the movie
        year: Release year
        extension: File extension (including dot)

    Returns:
        str: Standardized filename
    """
    # Create a ParsedMediaName object
    parsed = ParsedMediaName(
        media_type=MediaType.MOVIE,
        title=movie_name,
        year=year,
        extension=extension.lstrip("."),
    )

    # Apply the default movie formatter
    return format_movie(parsed)


def get_preview_rename(
    path: Path,
    name: Optional[str] = None,
    season: Optional[int] = None,
    episode: Optional[Union[int, str, List[int]]] = None,
    title: Optional[str] = None,
    concatenated: bool = False,
) -> Dict[str, str]:
    """Generate a preview of a proposed rename based on the original file path.

    Args:
        path: Original file path
        name: New name for the show/movie (if None, uses existing)
        season: New season number (if None, uses existing)
        episode: New episode number or list of episode numbers (if None, uses existing)
        title: New episode title (if None, uses existing)
        concatenated: Whether to format multi-episodes as concatenated

    Returns:
        dict: Contains 'original_name', 'new_name', 'original_path', 'new_path'
    """
    original_name = path.name

    # Parse the original name to get structured data
    parsed = parse_media_name(original_name)

    # Apply overrides if provided
    if name is not None:
        parsed.title = name

    if season is not None:
        parsed.season = season
        # For movies, the season parameter is used as the year
        if parsed.media_type == MediaType.MOVIE:
            parsed.year = season

    if episode is not None:
        parsed.episodes = ensure_episode_list(episode)
    elif parsed.media_type in (MediaType.TV_SHOW, MediaType.ANIME) and not parsed.episodes:
        # Try to detect multi-episodes using a simpler method
        detected_episodes = detect_multi_episodes_simple(original_name)
        if detected_episodes:
            parsed.episodes = detected_episodes
        else:
            # Default to episode 1 if no episodes detected
            parsed.episodes = [1]

    if title is not None:
        parsed.episode_title = title

    # Generate new name based on media type
    if parsed.media_type == MediaType.TV_SHOW:
        new_name = format_tv_show(parsed)
    elif parsed.media_type == MediaType.MOVIE:
        new_name = format_movie(parsed)
    elif parsed.media_type == MediaType.ANIME:
        new_name = format_anime(parsed)
    else:
        # If we can't determine the type, don't rename
        new_name = original_name

    return {
        "original_name": original_name,
        "new_name": new_name,
        "original_path": str(path),
        "new_path": str(path.parent / new_name),
    }
