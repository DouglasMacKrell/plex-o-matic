"""Functions for formatting episode filenames according to Plex naming conventions."""

import re
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple

# For Python 3.8 support
try:
    from typing import TypedDict, Literal
except ImportError:
    from typing_extensions import TypedDict, Literal

# Import parser functions for format_episode_filename
from plexomatic.utils.episode.parser import extract_show_info, split_title_by_separators, are_sequential


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Replace characters that are invalid in filenames
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '', filename)
    
    # Remove leading/trailing periods and spaces
    sanitized = sanitized.strip('. ')
    
    return sanitized


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
    
    if style == "dots":
        # First normalize the name (replace special chars with spaces)
        name = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in name)
        # Normalize spaces
        name = re.sub(r'\s+', ' ', name).strip()
        # Now replace spaces with dots for final format
        name = re.sub(r'\s+', '', name)  # Remove spaces completely for dots style
    elif style == "spaces":
        # Normalize spaces (replace multiple spaces with a single space)
        name = re.sub(r'\s+', ' ', name)
        # Remove other special characters except spaces
        name = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in name)
        name = re.sub(r'\s+', ' ', name).strip()
    elif style == "mixed":
        # Keep spaces but remove special characters
        name = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in name)
        name = re.sub(r'\s+', ' ', name).strip()
    
    return sanitize_filename(name)


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
        return f"S{season:02d}" + ''.join([f"E{ep:02d}" for ep in sorted_episodes])


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
    
    if style == "dots":
        # Replace spaces with dots
        formatted = re.sub(r'\s+', '.', clean_title)
        # Remove other special characters
        formatted = re.sub(r'[^\w.]', '.', formatted)
        # Remove consecutive dots
        formatted = re.sub(r'\.+', '.', formatted)
        # Remove leading/trailing dots
        formatted = formatted.strip('.')
    elif style == "spaces":
        # Normalize spaces (replace multiple spaces with a single space)
        formatted = re.sub(r'\s+', ' ', clean_title)
        # Replace special characters with spaces
        formatted = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in formatted)
        # Remove consecutive spaces
        formatted = re.sub(r'\s+', ' ', formatted).strip()
    elif style == "mixed":
        # Allow some punctuation but normalize spaces
        formatted = re.sub(r'\s+', ' ', clean_title)
        # Remove problematic characters
        formatted = re.sub(r'[<>:"/\\|?*]', '', formatted)
    else:
        formatted = clean_title
    
    return sanitize_filename(formatted)


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
    style: str = "spaces"
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
    titles: Optional[Union[List[str], str]] = None,
    extension: str = ".mp4",
    style: str = "spaces",
    concatenated: bool = True
) -> str:
    """
    Format a filename for multiple episodes.
    
    Args:
        show_name: The name of the show
        season: The season number
        episode_numbers: List of episode numbers
        titles: Episode titles as a list or a single string
        extension: The file extension
        style: The formatting style ('dots', 'spaces', or 'mixed')
        concatenated: Whether episodes are concatenated (True) or separate (False)
        
    Returns:
        Formatted filename for multi-episode
    """
    # Format show name
    formatted_show = format_show_name(show_name, style)
    
    # Format episode numbers
    if concatenated:
        # For concatenated files, use range or multiple-episode format
        formatted_episode = format_episode_numbers(episode_numbers, season)
    else:
        # For non-concatenated files, just use the first episode
        formatted_episode = format_episode_numbers([episode_numbers[0]], season)
    
    # Format titles
    if not titles:
        # If no title, just return show name and episode
        if style == "dots":
            return f"{formatted_show}.{formatted_episode}{extension}"
        else:
            return f"{formatted_show} {formatted_episode}{extension}"
    
    # Process titles based on whether it's a list or single string
    if isinstance(titles, list):
        # For list of titles, combine them
        title_segments = []
        for i, title in enumerate(titles):
            if i < len(episode_numbers):
                # Add each title to the segments
                title_segments.append(title)
        
        # Format the combined title
        formatted_title = format_multi_episode_title(title_segments, style)
    else:
        # Single title for all episodes
        formatted_title = format_episode_title(titles, style)
    
    # Combine components based on style
    if style == "dots":
        return f"{formatted_show}.{formatted_episode}.{formatted_title}{extension}"
    else:
        return f"{formatted_show} {formatted_episode} {formatted_title}{extension}"


def construct_episode_path(
    show_name: str,
    season: int,
    episode_numbers: List[int],
    title: Optional[str] = None,
    base_dir: str = "",
    extension: str = ".mp4",
    style: str = "spaces"
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
        title=safe_title,
        file_extension=file_extension,
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
        title=title,
        file_extension=file_ext,
        style=style,
    ) 