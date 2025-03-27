"""Default formatters for various media types."""

from typing import Dict, Optional, Callable
import logging

from plexomatic.utils.name_parser import ParsedMediaName
from plexomatic.utils.templates.template_types import TemplateType
from plexomatic.utils.multi_episode_formatter import ensure_episode_list

logger = logging.getLogger(__name__)


def format_tv_show(parsed: ParsedMediaName, concatenated: bool = False, style: str = "dots") -> str:
    """Format a TV show filename.

    Args:
        parsed: The parsed media name
        concatenated: Whether to format multi-episodes as concatenated (e.g. E01+E02+E03)
        style: The style to use for formatting ("dots", "spaces", or "standard")

    Returns:
        str: The formatted filename
    """
    logger.debug(f"Formatting TV show: {parsed}")

    # Handle missing or None values
    title = parsed.title or "Unknown"
    season = parsed.season or 1
    episodes = parsed.episodes or [1]
    episode_title = parsed.episode_title or ""
    extension = parsed.extension or "mp4"
    quality = parsed.quality or ""

    # Format episodes
    if len(episodes) > 1:
        # Sort episodes
        episodes = sorted(episodes)

        # Check if episodes are sequential
        is_sequential = all(episodes[i] == episodes[i - 1] + 1 for i in range(1, len(episodes)))

        # Always use range format for multi-episodes when more than one episode is present
        if is_sequential:
            # Format as E01-E03 for sequential episodes
            episode_str = f"E{episodes[0]:02d}-E{episodes[-1]:02d}"
        else:
            # Format as E01E02E03 for non-sequential episodes
            episode_str = "E" + "E".join(f"{ep:02d}" for ep in episodes)
    else:
        # Single episode
        episode_str = f"E{episodes[0]:02d}"

    # Apply style formatting to title and episode_title
    if style == "dots":
        title = title.replace(" ", ".")
        if episode_title:
            episode_title = episode_title.replace(" ", ".")
        separator = "."
    else:
        separator = " "

    # Build the final filename parts
    parts = [title, f"S{season:02d}{episode_str}"]

    # Add episode title if available
    if episode_title:
        parts.append(episode_title)

    # Add quality if available
    if quality:
        parts.append(quality)

    # Join with the appropriate separator
    filename = separator.join(parts)

    # Add extension
    if not extension.startswith("."):
        extension = f".{extension}"
    if not filename.endswith(extension):
        filename = f"{filename}{extension}"

    logger.debug(f"Formatted TV show filename: {filename}")
    return filename


def format_movie(parsed: ParsedMediaName, style: str = "dots") -> str:
    """Format a movie using the default format.

    Args:
        parsed: A ParsedMediaName object.
        style: The style to use for formatting ("dots", "spaces", or "standard")

    Returns:
        A formatted file name string.
    """
    # Get basic components
    title = parsed.title
    year = str(parsed.year) if parsed.year is not None else ""
    quality = parsed.quality or ""
    extension = parsed.extension

    if not extension.startswith("."):
        extension = f".{extension}"

    # Apply style formatting
    if style == "dots":
        title = title.replace(" ", ".")

        # Build the filename with dots
        parts = [title]
        if year:
            parts.append(year)
        if quality:
            parts.append(quality)

        # Join with dots and add extension
        return ".".join(filter(None, parts)) + extension
    else:
        # Spaces style
        if year:
            filename = f"{title} ({year})"
        else:
            filename = title

        if quality:
            filename += f" [{quality}]"

        return filename + extension


def format_anime(parsed: ParsedMediaName, style: str = "dots") -> str:
    """Format anime using the default format.

    Args:
        parsed: A ParsedMediaName object.
        style: The style to use for formatting ("dots", "spaces", or "standard")

    Returns:
        A formatted file name string.
    """
    # Determine if this is a special
    is_special = parsed.media_type and "SPECIAL" in str(parsed.media_type)

    # Format title based on style
    title = parsed.title
    if style == "dots":
        title = title.replace(" ", ".")

    # Handle anime special formatting
    if is_special and parsed.special_type:
        special_type = parsed.special_type.upper()
        special_number = parsed.special_number if parsed.special_number is not None else ""
        episode_text = f"E{special_type}{special_number}"
    else:
        # Format episodes with prefix for consistency
        episodes = ensure_episode_list(parsed.episodes)
        if not episodes:
            episode_text = ""
        elif len(episodes) == 1:
            episode_text = f"E{episodes[0]:02d}"
        else:
            # Format a range of episodes (e.g., E01-E03)
            episode_text = f"E{episodes[0]:02d}-E{episodes[-1]:02d}"

    # Format with or without group
    if parsed.group:
        # Group format is standard regardless of style
        result = f"[{parsed.group}] {title} - {episode_text.lstrip('E')}"
        if parsed.quality:
            result += f" [{parsed.quality}]"
    else:
        # Use style-specific formatting
        if style == "dots":
            parts = [title, episode_text]
            if parsed.quality:
                parts.append(parsed.quality)
            result = ".".join(parts)
        else:
            result = f"{title} {episode_text}"
            if parsed.quality:
                result += f" [{parsed.quality}]"

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
