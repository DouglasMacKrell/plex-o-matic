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
                         title: Optional[str] = None, extension: str = '.mp4') -> str:
    """Generate a standardized TV show filename.
    
    Args:
        show_name: Name of the show
        season: Season number
        episode: Episode number
        title: Episode title, if available
        extension: File extension (including dot)
        
    Returns:
        str: Standardized filename
    """
    show_part = sanitize_filename(show_name.replace(' ', '.'))
    episode_part = f'S{season:02d}E{episode:02d}'
    
    if title:
        title_part = sanitize_filename(title.replace(' ', '.'))
        return f"{show_part}.{episode_part}.{title_part}{extension}"
    else:
        return f"{show_part}.{episode_part}{extension}"

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

def get_preview_rename(original_path: Path) -> Tuple[Path, Optional[Path]]:
    """Generate a preview of a proposed rename.
    
    Args:
        original_path: Original path of the file
        
    Returns:
        tuple: (original_path, new_path) or (original_path, None) if no rename needed
    """
    # Extract file info
    stem = original_path.stem  # Just the filename without extension
    info = extract_show_info(stem)
    
    # Get the original extension
    extension = original_path.suffix
    
    # Determine if it's a TV show or movie
    if info.get('show_name') and info.get('season') and info.get('episode'):
        # It's a TV show
        new_filename = generate_tv_filename(
            info['show_name'],
            int(info['season']),
            int(info['episode']),
            info.get('title'),
            extension
        )
        
        # Create new path in the same directory
        new_path = original_path.parent / new_filename
    elif info.get('movie_name') and info.get('year'):
        # It's a movie
        new_filename = generate_movie_filename(
            info['movie_name'],
            int(info['year']),
            extension
        )
        
        # Create new path in the same directory
        new_path = original_path.parent / new_filename
    else:
        # Can't determine a good rename
        return (original_path, None)
    
    # If the new path is the same as the original, no rename needed
    if new_path.name == original_path.name:
        return (original_path, None)
    
    return (original_path, new_path) 