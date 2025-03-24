"""Utilities for handling file names and path manipulation."""

import re
from pathlib import Path
import os
import logging
from typing import Dict, Optional, Union, List, Any

try:
    # Python 3.9+ has native support for these types
    from typing import Dict, Optional, Union, List
except ImportError:
    # For Python 3.8 support
    from typing_extensions import Dict, Optional, Union, List

from plexomatic.utils.episode_handler import (
    extract_show_info,
    format_multi_episode_filename,
    is_tv_show,
)

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters.

    Args:
        filename: The filename to sanitize

    Returns:
        str: Sanitized filename
    """
    # Replace characters that are invalid in filenames with underscore
    # The test expects 8 underscores for 8 invalid characters
    invalid_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
    sanitized = filename
    for char in invalid_chars:
        sanitized = sanitized.replace(char, "_")
    return sanitized


def generate_tv_filename(
    show_name: str,
    season: int,
    episode: Optional[Union[int, str, List[int]]],
    title: Optional[str] = None,
    extension: str = ".mp4",
    concatenated: bool = False,
) -> str:
    """Generate a standardized TV show filename.

    Args:
        show_name: Name of the show
        season: Season number
        episode: Episode number (int or str) or list of episode numbers
        title: Episode title, if available
        extension: File extension (including dot)
        concatenated: If True, format as concatenated episodes using +, otherwise as a range

    Returns:
        str: Standardized filename
    """

    if episode is None:
        # Default to episode 1 if None is provided
        episodes = [1]
    elif isinstance(episode, int):
        # Convert single episode to list format for consistency with multi-episode
        episodes = [episode]
    elif isinstance(episode, str) and episode.isdigit():
        # Convert string to int if it's a digit string
        episodes = [int(episode)]
    else:
        # Assume it's already a list of episodes
        episodes = episode  # type: ignore

    return format_multi_episode_filename(
        show_name, season, episodes, title, extension, concatenated
    )


def generate_movie_filename(movie_name: str, year: int, extension: str = ".mp4") -> str:
    """Generate a standardized movie filename.

    Args:
        movie_name: Name of the movie
        year: Release year
        extension: File extension (including dot)

    Returns:
        str: Standardized filename
    """
    movie_part = sanitize_filename(movie_name.replace(" ", "."))
    return f"{movie_part}.{year}{extension}"


def preview_rename(
    file_path: str,
    anthology_mode: bool = False,
    use_llm: bool = False,
    api_lookup: bool = False,
    use_dots: bool = False,
    season_type: str = "Aired Order",
) -> Optional[Dict[str, Any]]:
    """Preview how a file would be renamed.

    Args:
        file_path: Path to the file.
        anthology_mode: Whether to treat as an anthology.
        use_llm: Whether to use LLM for segmented detection.
        api_lookup: Whether to use API for episode lookup.
        use_dots: Whether to use dots instead of spaces.
        season_type: Season type to use when fetching episodes from TVDB.

    Returns:
        A dictionary containing original and new paths, or None if no change.
    """
    logger.debug(f"Previewing rename for: {file_path}")
    logger.debug(f"Anthology mode: {anthology_mode}")
    logger.debug(f"Use LLM: {use_llm}")
    logger.debug(f"API lookup: {api_lookup}")
    logger.debug(f"Use dots: {use_dots}")
    logger.debug(f"Season type: {season_type}")

    try:
        # Delegate to appropriate handler based on anthology mode
        from plexomatic.utils.episode_handler import (
            rename_tv_show_episodes,
            preprocess_anthology_episodes,
        )

        if anthology_mode:
            # Process as anthology (multiple segments in one file)
            episode_info = preprocess_anthology_episodes(
                file_path=file_path, use_llm=use_llm, api_lookup=api_lookup, season_type=season_type
            )
            if not episode_info:
                logger.debug(f"No episode info found for anthology: {file_path}")
                return None

            # Format the new filename
            new_name = format_anthology_name(
                episode_info=episode_info,
                use_dots=use_dots,
                preview_mode=True,  # Don't actually rename
            )

            # If no change, return None
            if os.path.basename(file_path) == new_name:
                logger.debug(f"No change needed for: {file_path}")
                return None

            # Construct new path
            dir_path = os.path.dirname(file_path)
            new_path = os.path.join(dir_path, new_name)

            return {
                "original_path": file_path,
                "new_path": new_path,
                "show_info": {
                    "show_name": episode_info[0].get("show_name", "Unknown"),
                    "season": episode_info[0].get("season", 0),
                    "episode_count": len(episode_info),
                    "is_anthology": True,
                },
            }
        else:
            # Process as regular episode file
            return rename_tv_show_episodes(
                file_path=file_path,
                use_dots=use_dots,
                api_lookup=api_lookup,
                preview_mode=True,  # Don't actually rename
                season_type=season_type,
            )
    except Exception as e:
        logger.error(f"Error previewing rename for {file_path}: {e}")
        return None


def is_movie(filename: str) -> bool:
    """Check if a filename appears to be a movie.

    Args:
        filename: The filename to check

    Returns:
        True if it's likely a movie, False otherwise
    """
    # Basic pattern for movies: Movie.Title.2023.Quality.ext or similar
    movie_pattern = re.compile(r".*?[. _-]+(19\d{2}|20\d{2})[. _-].*?(?:\.\w+)?$")

    # Check if the filename matches the movie pattern and does not match TV show pattern
    return bool(movie_pattern.search(filename)) and not is_tv_show(filename)


def format_movie_filename(filename: str, use_dots: bool = True) -> str:
    """Format a movie filename according to naming convention.

    Args:
        filename: The original filename
        use_dots: Whether to use dots instead of spaces

    Returns:
        A formatted filename
    """
    # Extract basic information
    show_info = extract_show_info(filename)
    if not show_info or not show_info.get("movie_name") or not show_info.get("year"):
        # If we can't extract info, return the original filename
        return filename

    # Get movie name and year
    movie_name = show_info.get("movie_name", "")
    year = show_info.get("year", "")

    # Get the file extension
    file_ext = Path(filename).suffix

    # Format the name
    if use_dots:
        # Example: Movie.Name.2020.mp4
        new_name = f"{movie_name.replace(' ', '.')}.{year}{file_ext}"
    else:
        # Example: Movie Name (2020).mp4
        new_name = f"{movie_name} ({year}){file_ext}"

    return new_name


def format_new_name(
    path: str, info: Dict[str, Any], is_preview: bool = False, use_dots: bool = False
) -> str:
    """
    Format a new filename based on the extracted info.

    Args:
        path: The original file path
        info: Dictionary with extracted show info
        is_preview: Whether this is for preview mode
        use_dots: Whether to use dots instead of spaces (default is spaces)

    Returns:
        The new formatted filename
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Formatting new name for: {path}")
    logger.debug(f"Info: {info}")
    logger.debug(f"Preview mode: {is_preview}")
    logger.debug(f"Use dots: {use_dots}")

    # If no info was extracted, return the original path
    if not info:
        logger.warning(f"No info extracted, keeping original name: {path}")
        return path

    # Check if this is an anthology episode
    is_anthology = info.get("is_anthology", False)
    logger.debug(f"Is anthology: {is_anthology}")

    # Format based on anthology vs. regular episode
    if is_anthology:
        # Handle anthology episode (multiple segments in one file)
        show_name = info.get("show_name", "")
        season = info.get("season", 0)
        episode_numbers = info.get("episode_numbers", [])
        segments = info.get("segments", [])

        logger.debug(f"Formatting anthology episode with segments: {segments}")

        if not episode_numbers or not segments:
            logger.warning("Missing episode numbers or segments, keeping original name")
            return path

        # Get the file extension from the original path
        _, extension = os.path.splitext(path)

        # Format the new name using format_multi_episode_filename
        from plexomatic.utils.episode_handler import format_multi_episode_filename

        # Choose style based on use_dots setting
        style = "dots" if use_dots else "spaces"

        # Format the filename
        new_name = format_multi_episode_filename(
            show_name=show_name,
            season=season,
            episode_numbers=episode_numbers,
            title=segments,  # Pass segments as title
            file_extension=extension,
            concatenated=True,  # Use concatenated format (S01E01-E03)
            style=style,
        )

        logger.debug(f"Formatted anthology name: {new_name}")

        # If preview mode, keep original directory
        if is_preview:
            return os.path.join(os.path.dirname(path), new_name)
        else:
            return new_name
    else:
        # Handle regular episode (single episode per file)
        # Extract relevant information
        show_name = info.get("show_name", "")
        season = info.get("season", 0)
        episode = info.get("episode", 0)
        title = info.get("title", "")

        logger.debug(f"Formatting regular episode: S{season}E{episode} - {title}")

        # Get the file extension from the original path
        _, extension = os.path.splitext(path)

        # Format the new name based on use_dots setting
        if use_dots:
            # Format with dots
            show_part = show_name.replace(" ", ".")
            episode_part = f"S{season:02d}E{episode:02d}"

            if title:
                title_part = title.replace(" ", ".")
                new_name = f"{show_part}.{episode_part}.{title_part}{extension}"
            else:
                new_name = f"{show_part}.{episode_part}{extension}"
        else:
            # Format with spaces
            episode_part = f"S{season:02d}E{episode:02d}"

            if title:
                new_name = f"{show_name} {episode_part} {title}{extension}"
            else:
                new_name = f"{show_name} {episode_part}{extension}"

        logger.debug(f"Formatted regular name: {new_name}")

        # If preview mode, keep original directory
        if is_preview:
            return os.path.join(os.path.dirname(path), new_name)
        else:
            return new_name


def rename_file(
    file_path: str,
    new_path: Optional[str] = None,
    use_dots: bool = False,
    anthology_mode: bool = False,
    use_llm: bool = True,
    api_lookup: bool = True,
    preprocessed_data: Optional[Dict[str, Dict[str, Any]]] = None,
) -> bool:
    """
    Rename a file using consistent naming conventions.

    Args:
        file_path: Path to the file to rename
        new_path: Optional target path (if not provided, will be generated)
        use_dots: Whether to use dots instead of spaces in filenames
        anthology_mode: Whether to enable anthology mode
        use_llm: Whether to use LLM for segment detection
        api_lookup: Whether to use API lookup for episodes
        preprocessed_data: Optional preprocessed data for anthology episodes

    Returns:
        True if rename was successful, False otherwise
    """
    logger = logging.getLogger(__name__)

    if not os.path.exists(file_path):
        logger.warning(f"File doesn't exist: {file_path}")
        return False

    # If new path is not provided, generate it
    if not new_path:
        preview_result = preview_rename(
            file_path=file_path,
            use_dots=use_dots,
            anthology_mode=anthology_mode,
            use_llm=use_llm,
            api_lookup=api_lookup,
            preview=True,
            preprocessed_data=preprocessed_data,
        )

        if not preview_result:
            logger.warning(f"Could not generate new path for {file_path}")
            return False

        new_path = preview_result["new_path"]

    # Skip if the path doesn't need to change
    if file_path == new_path:
        logger.debug(f"No rename needed for {file_path}")
        return True

    # Create target directory if it doesn't exist
    target_dir = os.path.dirname(new_path)
    if not os.path.exists(target_dir):
        logger.debug(f"Creating directory: {target_dir}")
        os.makedirs(target_dir, exist_ok=True)

    # Rename the file
    try:
        # If the target file already exists, don't overwrite it
        if os.path.exists(new_path) and file_path != new_path:
            logger.warning(f"Target file already exists: {new_path}")
            return False

        # Move the file
        logger.debug(f"Renaming {file_path} to {new_path}")
        os.rename(file_path, new_path)
        return True

    except Exception as e:
        logger.error(f"Error renaming {file_path}: {e}")
        return False


def format_anthology_name(
    episode_info: List[Dict[str, Any]],
    use_dots: bool = False,
    preview_mode: bool = False,
) -> str:
    """Format a filename for an anthology episode.

    Args:
        episode_info: List of dictionaries with episode information
        use_dots: Whether to use dots instead of spaces
        preview_mode: Whether this is for preview mode

    Returns:
        The formatted filename
    """
    logger = logging.getLogger(__name__)
    
    if not episode_info or not isinstance(episode_info, list) or len(episode_info) == 0:
        logger.warning("No episode info provided for anthology formatting")
        return ""
    
    # Extract common information from the first episode
    first_episode = episode_info[0]
    show_name = first_episode.get("show_name", "Unknown Show")
    season = first_episode.get("season", 0)
    
    # Collect all episode numbers
    episode_numbers = [ep.get("episode", 0) for ep in episode_info if ep.get("episode")]
    
    # Get the file extension from the first episode
    extension = first_episode.get("extension", ".mp4")
    
    # Sort episode numbers
    episode_numbers.sort()
    
    # Format the episode part (e.g., S01E01-E03)
    if len(episode_numbers) > 1:
        # Multiple episodes
        episode_part = f"S{season:02d}E{episode_numbers[0]:02d}-E{episode_numbers[-1]:02d}"
    else:
        # Single episode
        episode_part = f"S{season:02d}E{episode_numbers[0]:02d}"
    
    # Format the filename
    if use_dots:
        # Example: Show.Name.S01E01-E03.mp4
        formatted_name = f"{show_name.replace(' ', '.')}.{episode_part}{extension}"
    else:
        # Example: Show Name S01E01-E03.mp4
        formatted_name = f"{show_name} {episode_part}{extension}"
    
    logger.debug(f"Formatted anthology name: {formatted_name}")
    return formatted_name
