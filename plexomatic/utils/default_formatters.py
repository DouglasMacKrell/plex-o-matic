"""Default formatters for media file renaming.

This module provides default formatters for each media type,
which are used when no custom template is specified.
"""

from typing import Callable, Dict, Optional
import logging

from plexomatic.utils.name_parser import ParsedMediaName
from plexomatic.utils.template_types import TemplateType
from plexomatic.utils.multi_episode_formatter import get_formatted_episodes, ensure_episode_list

logger = logging.getLogger(__name__)


def format_tv_show(parsed: ParsedMediaName) -> str:
    """Format a TV show using the default format.

    Args:
        parsed: A ParsedMediaName object.

    Returns:
        A formatted file name string.
    """
    # Get basic components
    title = parsed.title.replace(" ", ".")
    season = f"S{parsed.season:02d}" if parsed.season is not None else ""
    episodes = get_formatted_episodes(parsed)

    # Build the filename
    parts = [title, f"{season}{episodes}"]

    # Add episode title if available
    if parsed.episode_title:
        parts.append(parsed.episode_title.replace(" ", "."))

    # Add quality if available
    if parsed.quality:
        parts.append(parsed.quality)

    # Join parts and add extension
    return ".".join(filter(None, parts)) + parsed.extension


def format_movie(parsed: ParsedMediaName) -> str:
    """Format a movie using the default format.

    Args:
        parsed: A ParsedMediaName object.

    Returns:
        A formatted file name string.
    """
    # Get basic components
    title = parsed.title.replace(" ", ".")
    year = str(parsed.year) if parsed.year is not None else ""

    # Build the filename
    parts = [title, year]

    # Add quality if available
    if parsed.quality:
        parts.append(parsed.quality)

    # Join parts and add extension
    return ".".join(filter(None, parts)) + parsed.extension


def format_anime(parsed: ParsedMediaName) -> str:
    """Format anime using the default format.

    Args:
        parsed: A ParsedMediaName object.

    Returns:
        A formatted file name string.
    """
    # Determine if this is a special
    is_special = parsed.media_type and "SPECIAL" in str(parsed.media_type)

    # Handle anime special formatting
    if is_special and parsed.special_type and parsed.special_number is not None:
        episode_text = f"{parsed.special_type}{parsed.special_number}"
    else:
        # Format episodes with a different format for anime (no E prefix)
        episodes = ensure_episode_list(parsed.episodes)
        if not episodes:
            episode_text = ""
        elif len(episodes) == 1:
            episode_text = f"{episodes[0]:02d}"
        else:
            # Format a range of episodes (e.g., 01-03)
            episode_text = f"{episodes[0]:02d}-{episodes[-1]:02d}"

    # Format with or without group
    if parsed.group:
        result = f"[{parsed.group}] {parsed.title} - {episode_text}"
        if parsed.quality:
            result += f" [{parsed.quality}]"
    else:
        # No group, use dot format
        title = parsed.title.replace(" ", ".")
        result = f"{title}.E{episode_text}"
        if parsed.quality:
            result += f".{parsed.quality}"

    return result + parsed.extension


# Map of media types to formatter functions
DEFAULT_FORMATTERS: Dict[TemplateType, Callable[[ParsedMediaName], str]] = {
    TemplateType.TV_SHOW: format_tv_show,
    TemplateType.MOVIE: format_movie,
    TemplateType.ANIME: format_anime,
    TemplateType.CUSTOM: format_tv_show,  # Default to TV show formatter for custom types
}


def get_default_formatter(
    template_type: Optional[TemplateType],
) -> Callable[[ParsedMediaName], str]:
    """Get the default formatter for a template type.

    Args:
        template_type: The template type to get the formatter for.

    Returns:
        A formatter function for the given template type.
    """
    if template_type is None:
        return format_tv_show

    return DEFAULT_FORMATTERS.get(template_type, format_tv_show)
