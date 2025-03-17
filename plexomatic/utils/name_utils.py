"""Utilities for handling file names and path manipulation."""
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing invalid characters.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        str: Sanitized filename
    """
    # Replace characters that are invalid in filenames with underscore
    # The test expects 8 underscores for 8 invalid characters
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def extract_show_info(filename: str) -> Dict[str, Optional[str]]:
    """Extract show information from a filename.
    
    Args:
        filename: The filename to parse
        
    Returns:
        dict: Extracted information (show_name, season, episode, etc.)
    """
    # Basic pattern for TV shows: ShowName.S01E02.OptionalInfo.ext
    tv_pattern = re.compile(
        r'(?P<show_name>.*?)[. _-]+'
        r'[sS](?P<season>\d{1,2})[eE](?P<episode>\d{1,2})(?:[eE]\d{1,2})*'
        r'(?:[. _-](?P<title>.*))?$'
    )
    
    # Try to match the TV show pattern
    tv_match = tv_pattern.search(filename)
    if tv_match:
        info = tv_match.groupdict()
        # Clean up show name
        if info['show_name']:
            info['show_name'] = info['show_name'].replace('.', ' ').replace('_', ' ').strip()
        return info
    
    # If not a TV show, try movie pattern: MovieName.Year.OptionalInfo.ext
    movie_pattern = re.compile(
        r'(?P<movie_name>.*?)[. _-]+'
        r'(?P<year>19\d{2}|20\d{2})'
        r'(?:[. _-](?P<info>.*))?$'
    )
    
    movie_match = movie_pattern.search(filename)
    if movie_match:
        info = movie_match.groupdict()
        # Clean up movie name
        if info['movie_name']:
            info['movie_name'] = info['movie_name'].replace('.', ' ').replace('_', ' ').strip()
        return info
    
    # If no patterns match, return just the name
    return {
        'name': Path(filename).stem,
        'show_name': None,
        'movie_name': None,
        'season': None,
        'episode': None,
        'year': None,
        'title': None
    }

def generate_tv_filename(show_name: str, season: int, episode: int, 
                         title: Optional[str] = None, extension: str = '.mp4', 
                         concatenated: bool = False) -> str:
    """Generate a standardized TV show filename.
    
    Args:
        show_name: Name of the show
        season: Season number
        episode: Episode number or list of episode numbers
        title: Episode title, if available
        extension: File extension (including dot)
        concatenated: If True, format as concatenated episodes using +, otherwise as a range
        
    Returns:
        str: Standardized filename
    """
    from plexomatic.utils.episode_handler import format_multi_episode_filename
    
    # Convert single episode to list format for consistency with multi-episode
    episodes = [episode] if isinstance(episode, int) else episode
    
    return format_multi_episode_filename(show_name, season, episodes, title, extension, concatenated)

def generate_movie_filename(movie_name: str, year: int, 
                           extension: str = '.mp4') -> str:
    """Generate a standardized movie filename.
    
    Args:
        movie_name: Name of the movie
        year: Release year
        extension: File extension (including dot)
        
    Returns:
        str: Standardized filename
    """
    movie_part = sanitize_filename(movie_name.replace(' ', '.'))
    return f"{movie_part}.{year}{extension}"

def get_preview_rename(path: Path, name: Optional[str] = None, 
                       season: Optional[int] = None, episode: Optional[int] = None,
                       title: Optional[str] = None, concatenated: bool = False) -> Dict[str, str]:
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
    from plexomatic.utils.episode_handler import detect_multi_episodes
    
    original_name = path.name
    info = extract_show_info(original_name)
    extension = path.suffix
    
    # TV Show
    if 'show_name' in info and info['show_name']:
        show_name = name if name else info['show_name']
        show_season = season if season is not None else int(info['season']) if info['season'] else 1
        
        # Handle multi-episode files
        if episode is not None:
            # If episode is provided, use it directly
            episodes = [episode] if isinstance(episode, int) else episode
        else:
            # Otherwise, try to detect multi-episodes from the filename
            episodes = detect_multi_episodes(original_name)
            # If no multi-episodes detected, use the single episode from info
            if not episodes and info['episode']:
                episodes = [int(info['episode'])]
            # If still no episodes found, default to episode 1
            if not episodes:
                episodes = [1]
                
        show_title = title if title else info.get('title')
        
        new_name = generate_tv_filename(show_name, show_season, episodes, show_title, extension, concatenated)
    
    # Movie
    elif 'movie_name' in info and info['movie_name']:
        movie_name = name if name else info['movie_name']
        movie_year = season if season else int(info['year']) if info['year'] else 2020
        
        new_name = generate_movie_filename(movie_name, movie_year, extension)
    
    # Unrecognized format - no rename
    else:
        new_name = original_name
    
    return {
        'original_name': original_name,
        'new_name': new_name,
        'original_path': str(path),
        'new_path': str(path.parent / new_name)
    } 