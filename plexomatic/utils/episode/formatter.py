"""Functions for formatting episode filenames according to Plex naming conventions."""

import re
import os
from pathlib import Path
from typing import List, Optional, Union

# Import parser functions for format_episode_filename
from plexomatic.utils.episode.parser import (
    extract_show_info,
    are_sequential,
)


def sanitize_filename(
    filename: str, replace_with: str = "", preserve_underscores: bool = False
) -> str:
    """
    Sanitize a filename by removing or replacing invalid characters.

    Args:
        filename: The filename to sanitize
        replace_with: Character to replace invalid characters with (default: remove them)
        preserve_underscores: Whether to preserve existing underscores from previous sanitization

    Returns:
        Sanitized filename
    """
    # Early return for None or empty values
    if not filename:
        return ""

    # Handle special case for tests expecting colons to be replaced with underscores
    if replace_with == "_" and ":" in filename:
        # Special case: replace colons first
        intermediate = filename.replace(":", "_")
        # Then replace other invalid characters
        cleaned = re.sub(r'[<>"/\\|?*]', replace_with, intermediate)
        # Remove leading/trailing periods and spaces
        return cleaned.strip(". ")
    else:
        # Default case: replace all invalid characters
        cleaned = re.sub(r'[<>:"/\\|?*]', replace_with, filename)
        # Remove leading/trailing periods and spaces
        return cleaned.strip(". ")


def format_show_name(show_name: str, style: str = "spaces") -> str:
    """
    Format a show name according to the specified style.

    Args:
        show_name: The show name to format
        style: The formatting style ('dots', 'spaces', or 'mixed')

    Returns:
        Formatted show name
    """
    # Remove any leading/trailing whitespace
    name = show_name.strip()

    # Replace colons with underscores first (special handling for Plex)
    if ":" in name and style != "mixed":
        name = name.replace(":", "_")

    # Preserve underscores from sanitization, as they replace invalid characters
    # This will ensure that "Show_The_Beginning" stays as "Show_The_Beginning"
    # or becomes "Show_The_Beginning" or "Show.The.Beginning" but not "Show The Beginning"
    has_underscores = "_" in name

    if style == "dots":
        if has_underscores:
            # If there are already underscores (from sanitization), replace spaces with dots but keep underscores
            name = re.sub(r"\s+", ".", name)
        else:
            # First remove any special characters
            name = "".join(c if c.isalnum() or c.isspace() else " " for c in name)
            # Normalize spaces
            name = re.sub(r"\s+", " ", name).strip()
            # For "dots" style, remove spaces entirely instead of replacing with dots
            name = name.replace(" ", "")
    elif style == "spaces":
        if has_underscores:
            # If there are already underscores (from sanitization), keep them
            name = re.sub(r"\s+", " ", name).strip()
        else:
            # Replace any special characters with spaces
            name = "".join(c if c.isalnum() or c.isspace() else " " for c in name)
            # Normalize spaces (replace multiple spaces with a single space)
            name = re.sub(r"\s+", " ", name).strip()
    elif style == "mixed":
        # For mixed style, replace special characters with spaces
        name = "".join(c if c.isalnum() or c.isspace() else " " for c in name)
        # Normalize spaces
        name = re.sub(r"\s+", " ", name).strip()

    return name


def format_episode_numbers(episode_numbers: List[int], season: int = 1) -> str:
    """
    Format episode numbers according to Plex conventions.

    Args:
        episode_numbers: List of episode numbers to format
        season: Season number for the episodes

    Returns:
        Formatted episode string (e.g., "S01E01" or "S01E01-E03")
    """
    if not episode_numbers:
        return f"S{season:02d}E00"  # Default to E00 if no episode numbers

    # Sort the episode numbers
    sorted_episodes = sorted(episode_numbers)

    # Check if they are sequential
    if len(sorted_episodes) == 1:
        # Single episode
        return f"S{season:02d}E{sorted_episodes[0]:02d}"
    elif are_sequential(sorted_episodes):
        # Sequential episodes use a range format S01E01-E03
        return f"S{season:02d}E{sorted_episodes[0]:02d}-E{sorted_episodes[-1]:02d}"
    else:
        # Non-sequential episodes use multiple E markers S01E01E03E05
        return f"S{season:02d}" + "".join([f"E{ep:02d}" for ep in sorted_episodes])


def format_episode_title(title: str, style: str = "spaces") -> str:
    """
    Format an episode title according to the specified style.

    Args:
        title: The episode title to format
        style: The formatting style ('dots', 'spaces', or 'mixed')

    Returns:
        Formatted episode title
    """
    if not title:
        return ""

    # Remove any leading/trailing whitespace
    clean_title = title.strip()

    # Handle colons based on style
    if ":" in clean_title:
        if style == "dots":
            # For dots style, replace colons with underscores
            clean_title = clean_title.replace(":", "_")
        elif style == "spaces":
            # For spaces style, replace colons with spaces
            clean_title = clean_title.replace(":", " ")
        # For mixed style, leave colons as-is

    if style == "dots":
        # Replace special characters with spaces first
        formatted = "".join(c if c.isalnum() or c.isspace() else " " for c in clean_title)
        # Normalize spaces
        formatted = re.sub(r"\s+", " ", formatted).strip()
        # Replace spaces with dots
        formatted = formatted.replace(" ", ".")
    elif style == "spaces":
        # Remove quotes
        clean_title = clean_title.replace('"', "").replace("'", "")

        # Replace special characters (except underscores) with spaces
        formatted = "".join(
            c if c.isalnum() or c.isspace() or c == "_" else " " for c in clean_title
        )
        # Normalize spaces (replace multiple spaces with a single space)
        formatted = re.sub(r"\s+", " ", formatted).strip()
    elif style == "mixed":
        if "_" in clean_title:
            # If there are already underscores (from sanitization), keep them
            formatted = re.sub(r"\s+", " ", clean_title).strip()
        else:
            # Allow some punctuation but normalize spaces
            formatted = "".join(c if c.isalnum() or c.isspace() else " " for c in clean_title)
            formatted = re.sub(r"\s+", " ", formatted).strip()
    else:
        formatted = clean_title

    return formatted


def format_multi_episode_title(segments: List[str], style: str = "spaces") -> str:
    """
    Format multiple episode segments into a single title.

    Args:
        segments: List of episode title segments
        style: The formatting style ('dots', 'spaces', or 'mixed')

    Returns:
        Formatted combined title
    """
    if not segments:
        return ""

    # Format each segment according to the style
    formatted_segments = [format_episode_title(segment, style) for segment in segments]

    # Join the segments based on style
    if style == "dots":
        separator = "."
    elif style == "spaces" or style == "mixed":
        separator = " - "
    else:
        separator = " - "

    return separator.join(formatted_segments)


def format_filename(
    show_name: str,
    season: int,
    episode_numbers: List[int],
    title: Optional[str] = None,
    extension: str = ".mp4",
    style: str = "spaces",
) -> str:
    """
    Format a complete filename according to Plex naming conventions.

    Args:
        show_name: The name of the show
        season: The season number
        episode_numbers: List of episode numbers
        title: The episode title (optional)
        extension: The file extension
        style: The formatting style ('dots', 'spaces', or 'mixed')

    Returns:
        Formatted filename
    """
    # Format show name
    formatted_show = format_show_name(show_name, style)

    # Format episode numbers
    formatted_episode = format_episode_numbers(episode_numbers, season)

    # If no title, just return show name and episode
    if not title:
        if style == "dots":
            return f"{formatted_show}.{formatted_episode}{extension}"
        else:
            return f"{formatted_show} {formatted_episode}{extension}"

    # Format title
    formatted_title = format_episode_title(title, style)

    # Combine components based on style
    if style == "dots":
        return f"{formatted_show}.{formatted_episode}.{formatted_title}{extension}"
    else:
        return f"{formatted_show} {formatted_episode} {formatted_title}{extension}"


def format_multi_episode_filename(
    show_name: str,
    season: int,
    episode_numbers: List[int],
    titles: Optional[Union[str, List[str]]] = None,
    extension: str = ".mp4",
    style: str = "spaces",
    concatenated: bool = True,
) -> str:
    """
    Format a filename for a multi-episode file according to Plex naming convention.

    Args:
        show_name: Name of the TV show
        season: Season number
        episode_numbers: List of episode numbers (must be sequential)
        titles: Episode titles (can be a single string or list of strings)
        extension: File extension (with leading dot)
        style: Formatting style ('dots', 'spaces', or 'mixed')
        concatenated: Whether to use concatenated format for sequential episodes

    Returns:
        Formatted filename

    Raises:
        ValueError: If episode_numbers is empty or episodes are not sequential
    """
    # Check for empty episode list
    if not episode_numbers:
        raise ValueError("Episode numbers list cannot be empty")

    # Sort episode numbers
    sorted_episodes = sorted(episode_numbers)

    # Verify episodes are sequential (all anthology episodes should be sequential)
    if len(sorted_episodes) > 1 and not are_sequential(sorted_episodes):
        raise ValueError("Multi-episode files must contain sequential episodes")

    # Format the show name according to style
    formatted_show = format_show_name(show_name, style)

    # Format the episode part based on concatenated parameter
    if len(sorted_episodes) == 1 or not concatenated:
        # Single episode or non-concatenated format (just use the first episode)
        episode_str = f"S{season:02d}E{sorted_episodes[0]:02d}"
    else:
        # Sequential episodes with concatenated format - use hyphen: S01E01-E03
        episode_str = f"S{season:02d}E{sorted_episodes[0]:02d}-E{sorted_episodes[-1]:02d}"

    # Handle title formatting
    # Special case: for consistency with show_name, always replace colons in titles with underscores
    # This ensures both show names and titles follow the same sanitization rules
    if isinstance(titles, str) and ":" in titles and style != "mixed":
        titles = titles.replace(":", "_")

    # Format episode titles
    if isinstance(titles, list):
        # For list of titles, we need to sanitize each one before formatting
        if style != "mixed":
            titles = [t.replace(":", "_") if ":" in t else t for t in titles]
        title_str = format_multi_episode_title(titles, style)
    elif titles:
        # Single title
        title_str = format_episode_title(titles, style)
    else:
        # No title
        title_str = ""

    # Make sure the extension has a leading dot
    safe_ext = extension if extension.startswith(".") else f".{extension}"

    # Format the full filename according to style
    if style == "dots":
        # Format with dots (e.g., Show.Name.S01E01-E03.Episode.Title.mp4)
        if title_str:
            result = f"{formatted_show}.{episode_str}.{title_str}{safe_ext}"
        else:
            result = f"{formatted_show}.{episode_str}{safe_ext}"
    else:
        # Format with spaces (e.g., Show Name S01E01-E03 Episode Title.mp4)
        if title_str:
            result = f"{formatted_show} {episode_str} {title_str}{safe_ext}"
        else:
            result = f"{formatted_show} {episode_str}{safe_ext}"

    return result


def construct_episode_path(
    show_name: str,
    season: int,
    episode_numbers: List[int],
    title: Optional[str] = None,
    base_dir: str = "",
    extension: str = ".mp4",
    style: str = "spaces",
) -> str:
    """
    Construct a full episode path with proper Plex directory structure.

    Args:
        show_name: The name of the show
        season: The season number
        episode_numbers: List of episode numbers
        title: The episode title (optional)
        base_dir: Base directory for TV shows
        extension: The file extension
        style: The formatting style

    Returns:
        Full path for the episode file
    """
    # Format the show name for directory
    show_dir = format_show_name(show_name, "spaces")  # Use spaces for directory names

    # Create season directory name
    season_dir = f"Season {season:02d}"

    # Format the filename
    filename = format_filename(show_name, season, episode_numbers, title, extension, style)

    # Combine into full path
    if base_dir:
        return os.path.join(base_dir, show_dir, season_dir, filename)
    else:
        return os.path.join(show_dir, season_dir, filename)


def format_new_name(
    show_name: str,
    season: Optional[int],
    episode: Optional[int],
    title: Optional[str] = None,
    use_dots: bool = False,
) -> str:
    """Format a new filename for a TV show episode.

    Args:
        show_name: The show name
        season: The season number
        episode: The episode number
        title: Optional episode title
        use_dots: Whether to use dots instead of spaces

    Returns:
        Formatted filename
    """
    # Ensure title is not None for the function call
    safe_title = title or ""

    # Make sure season is not None
    safe_season = season if season is not None else 1

    # Make sure episode is not None
    safe_episode = episode if episode is not None else 1

    # Get file extension
    file_extension = ".mp4"  # Default extension

    # Format the episode filename with the given parameters
    return format_multi_episode_filename(
        show_name=show_name,
        season=safe_season,
        episode_numbers=[safe_episode],
        titles=safe_title,
        extension=file_extension,
        style="dots" if use_dots else "spaces",
    )


def format_episode_filename(filename: str, use_dots: bool = False) -> str:
    """Format a single episode filename according to naming convention.

    Args:
        filename: The original filename
        use_dots: Whether to use dots instead of spaces

    Returns:
        A formatted filename
    """
    # Extract basic information
    show_info = extract_show_info(filename)
    if not show_info:
        # If we can't extract info, return the original filename
        return filename

    # Get show name and episode details
    show_name = show_info.get("show_name")
    season = show_info.get("season")
    episode = show_info.get("episode")
    title = show_info.get("title")

    if not show_name or not season or not episode:
        # If we're missing essential info, return the original filename
        return filename

    # Convert to proper types
    try:
        season_num = int(season)
        episode_num = int(episode)
    except (ValueError, TypeError):
        # If conversion fails, return original filename
        return filename

    # Get the file extension
    file_ext = Path(filename).suffix

    # Format using the multi-episode formatter with a single episode
    style = "dots" if use_dots else "spaces"
    return format_multi_episode_filename(
        show_name=show_name,
        season=season_num,
        episode_numbers=[episode_num],
        titles=title,
        extension=file_ext,
        style=style,
    )


def generate_filename_from_metadata(original_filename: str, metadata: dict) -> str:
    """
    Generate a properly formatted filename from metadata.

    Args:
        original_filename: The original filename (for extension)
        metadata: Dictionary containing metadata like title, season, episode, etc.

    Returns:
        A formatted filename according to Plex naming conventions
    """
    # Get file extension from original file
    extension = os.path.splitext(original_filename)[1]
    if not extension:
        extension = ".mp4"  # Default extension

    # Determine filename style
    use_dots = metadata.get("use_dots", False)
    style = "dots" if use_dots else "spaces"

    # Check if it's a special episode
    if "special_type" in metadata:
        special_type = metadata["special_type"]
        special_number = metadata.get("special_number")

        # Get title from special episode metadata if available
        title = None
        if "special_episode" in metadata and isinstance(metadata["special_episode"], dict):
            title = metadata["special_episode"].get("title")

        # If no title is available, use the special type as the title
        if not title:
            if special_number is not None:
                title = f"{special_type.title()} {special_number}"
            else:
                title = special_type.title()

        # Format the filename for special episode
        return format_filename(
            show_name=metadata["title"],
            season=0,  # Specials are in season 0
            episode_numbers=[special_number if special_number is not None else 0],
            title=title,
            extension=extension,
            style=style,
        )

    # Check if it's a multi-episode
    elif "episode_numbers" in metadata and len(metadata.get("episode_numbers", [])) > 1:
        episode_numbers = metadata["episode_numbers"]
        season = metadata.get("season", 1)

        # Get titles if available
        titles = None
        if "multi_episodes" in metadata and isinstance(metadata["multi_episodes"], list):
            titles = [
                ep.get("title", "") for ep in metadata["multi_episodes"] if isinstance(ep, dict)
            ]
            if all(not title for title in titles):
                titles = None

        # Format the filename for multi-episode
        return format_multi_episode_filename(
            show_name=metadata["title"],
            season=season,
            episode_numbers=episode_numbers,
            titles=titles,
            extension=extension,
            style=style,
        )

    # Regular episode
    else:
        season = metadata.get("season", 1)
        episode = metadata.get("episode", 1)
        title = metadata.get("episode_title")

        # Format the filename for regular episode
        return format_filename(
            show_name=metadata["title"],
            season=season,
            episode_numbers=[episode],
            title=title,
            extension=extension,
            style=style,
        )
