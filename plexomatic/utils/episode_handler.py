"""Utilities for handling TV show episodes, including multi-episode detection and special episode handling."""
import re
from pathlib import Path
from typing import List, Dict, Union, Optional
from plexomatic.utils.name_utils import sanitize_filename, extract_show_info

# Regular expressions for detecting various episode formats
MULTI_EPISODE_PATTERNS = [
    # Standard multi-episode format: S01E01E02
    r'S(\d+)E(\d+)(?:E(\d+))+',
    # Hyphen format: S01E01-E02
    r'S(\d+)E(\d+)-E(\d+)',
    # X format with hyphen: 01x01-02
    r'(\d+)x(\d+)-(\d+)',
    # E format with hyphen but no second E: S01E01-02
    r'S(\d+)E(\d+)-(\d+)',
    # Space separator: S01E01 E02
    r'S(\d+)E(\d+)(?:\s+E(\d+))+',
    # Text separators like "to", "&", "+"
    r'S(\d+)E(\d+)(?:\s*(?:to|&|\+|,)\s*E(\d+))+',
]

# Regular expressions for detecting special episodes
SPECIAL_PATTERNS = [
    # Season 0 specials: S00E01
    (r'S00E(\d+)', 'special'),
    # Special keyword
    (r'Special(?:s)?(?:\s*(\d+))?', 'special'),
    # OVA keyword (Original Video Animation, common in anime)
    (r'OVA(?:\s*(\d+))?', 'ova'),
    # OVA with number after dot
    (r'OVA\.(\d+)', 'ova'),
    # Movie/Film specials with number
    (r'Movie\.(\d+)|Film\.(\d+)', 'movie'),
    # Movie/Film specials general
    (r'Movie(?:\s*(\d+))?|Film(?:\s*(\d+))?', 'movie'),
]

def detect_multi_episodes(filename: str) -> List[int]:
    """
    Detect if a filename contains multiple episodes and return a list of episode numbers.
    
    Args:
        filename: The filename to analyze
        
    Returns:
        A list of episode numbers found in the filename.
        For a single episode, returns a list with one element.
        For no episodes found, returns an empty list.
    """
    # Extract show info to see if it's already identified as a TV show
    show_info = extract_show_info(filename)
    
    # Check if we have episode information
    if show_info.get('episode'):
        # Convert episode to int if it's a string
        episode = int(show_info['episode']) if isinstance(show_info['episode'], str) else show_info['episode']
        # Initialize the result with the first detected episode
        result = [episode]
        
        # Check for multi-episode patterns
        for pattern in MULTI_EPISODE_PATTERNS:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                # Extract the season and episode numbers
                groups = match.groups()
                # If it's a range (e.g., E01-E03), parse the range
                if len(groups) >= 3:
                    # Try to get the season, start and end episodes
                    start_ep = int(groups[1]) if groups[1] else None
                    end_ep = int(groups[2]) if groups[2] else None
                    
                    if start_ep and end_ep:
                        return parse_episode_range(start_ep, end_ep)
                
                # If there are multiple episode markers (E01E02E03...)
                episode_markers = re.findall(r'E(\d+)', filename)
                if len(episode_markers) > 1:
                    return [int(ep) for ep in episode_markers]
        
        return result
    
    # Direct episode detection if extract_show_info didn't find anything
    # Standard format: S01E01E02
    multi_ep_pattern = r'S(\d+)E(\d+)(?:E(\d+))+'
    match = re.search(multi_ep_pattern, filename, re.IGNORECASE)
    if match:
        episode_markers = re.findall(r'E(\d+)', filename)
        if episode_markers:
            return [int(ep) for ep in episode_markers]
            
    # Hyphen format: S01E01-E02 or S01E01-02
    hyphen_pattern = r'S\d+E(\d+)[-](?:E)?(\d+)'
    match = re.search(hyphen_pattern, filename, re.IGNORECASE)
    if match:
        start_ep = int(match.group(1))
        end_ep = int(match.group(2))
        return parse_episode_range(start_ep, end_ep)
    
    # For patterns like "01x02-03" without S01E01 format
    x_pattern = r'(\d+)x(\d+)(?:-(\d+))?'
    match = re.search(x_pattern, filename, re.IGNORECASE)
    if match:
        groups = match.groups()
        if len(groups) >= 3 and groups[2]:
            return parse_episode_range(int(groups[1]), int(groups[2]))
        else:
            return [int(groups[1])]
            
    # Space separator: S01E01 E02
    space_pattern = r'S\d+E(\d+)(?:\s+E(\d+))+'
    match = re.search(space_pattern, filename, re.IGNORECASE)
    if match:
        episode_markers = re.findall(r'E(\d+)', filename)
        if episode_markers:
            return [int(ep) for ep in episode_markers]
            
    # Special pattern for "S01 E01 E02" format
    spaced_season_pattern = r'S(\d+)\s+E(\d+)(?:\s+E(\d+))+'
    match = re.search(spaced_season_pattern, filename, re.IGNORECASE)
    if match:
        episode_markers = re.findall(r'E(\d+)', filename)
        if episode_markers:
            return [int(ep) for ep in episode_markers]
            
    # Text separators
    text_sep_pattern = r'S\d+E(\d+)(?:\s*(?:to|&|\+|,)\s*E(\d+))'
    match = re.search(text_sep_pattern, filename, re.IGNORECASE)
    if match:
        start_ep = int(match.group(1))
        end_ep = int(match.group(2))
        if 'to' in filename:
            return parse_episode_range(start_ep, end_ep)
        else:
            return [start_ep, end_ep]
    
    # If we couldn't find any multi-episode pattern
    return []

def parse_episode_range(start: int, end: int) -> List[int]:
    """
    Parse a range of episodes and return a list of all episode numbers in the range.
    
    Args:
        start: The starting episode number
        end: The ending episode number
        
    Returns:
        A list of all episode numbers in the range [start, end]
        
    Raises:
        ValueError: If the range is invalid (end < start) or if start <= 0
    """
    # Validate input
    if start <= 0 or end <= 0:
        raise ValueError("Episode numbers must be positive integers")
    
    if end < start:
        raise ValueError(f"Invalid episode range: {start} to {end}")
    
    # Limit very large ranges to prevent performance issues
    if end - start > 19:  # Fixed to ensure max 20 episodes in range
        end = start + 19
    
    # Generate the range
    return list(range(start, end + 1))

def format_multi_episode_filename(
    show_name: str, 
    season: int, 
    episodes: List[int], 
    title: Optional[str], 
    extension: str,
    concatenated: bool = False
) -> str:
    """
    Format a filename for a multi-episode file.
    
    Args:
        show_name: The name of the show
        season: The season number
        episodes: List of episode numbers
        title: Episode title (optional)
        extension: File extension (including the dot)
        concatenated: If True, format as concatenated episodes (E01+E02+E03), 
                     otherwise as a range (E01-E03) if episodes are sequential
        
    Returns:
        A formatted filename
        
    Raises:
        ValueError: If episodes list is empty
    """
    if not episodes:
        raise ValueError("Episodes list cannot be empty")
    
    # Sanitize inputs
    show_name = sanitize_filename(show_name).replace(" ", ".")
    if title:
        title = sanitize_filename(title).replace(" ", ".")
    
    # Format season and episode part
    season_part = f"S{season:02d}"
    
    # Single episode
    if len(episodes) == 1:
        episode_part = f"E{episodes[0]:02d}"
    # Multiple episodes
    else:
        # Check if episodes are sequential
        is_sequential = True
        for i in range(1, len(episodes)):
            if episodes[i] != episodes[i-1] + 1:
                is_sequential = False
                break
        
        # Format as range or concatenated
        if is_sequential and not concatenated:
            episode_part = f"E{episodes[0]:02d}-E{episodes[-1]:02d}"
        else:
            episode_parts = [f"E{ep:02d}" for ep in episodes]
            episode_part = "+".join(episode_parts)
    
    # Combine parts
    parts = [show_name, season_part + episode_part]
    if title:
        parts.append(title)
    
    # Join with dots and add extension
    return ".".join(parts) + extension

def detect_special_episodes(filename: str) -> Optional[Dict[str, Union[str, int, None]]]:
    """
    Detect if a filename represents a special episode.
    
    Args:
        filename: The filename to analyze
        
    Returns:
        A dictionary with 'type' (special, ova, movie) and 'number' if found, None otherwise.
    """
    # Check for S00E pattern first (most reliable)
    season_pattern = r'S00E(\d+)'
    match = re.search(season_pattern, filename, re.IGNORECASE)
    if match:
        return {
            'type': 'special',
            'number': int(match.group(1))
        }
    
    # Check for OVA.number pattern specifically
    ova_dot_pattern = r'OVA\.(\d+)'
    match = re.search(ova_dot_pattern, filename, re.IGNORECASE)
    if match:
        return {
            'type': 'ova',
            'number': int(match.group(1))
        }
        
    # Check for Movie.number pattern specifically
    movie_dot_pattern = r'Movie\.(\d+)|Film\.(\d+)'
    match = re.search(movie_dot_pattern, filename, re.IGNORECASE)
    if match:
        number = None
        # Check which group matched (movie or film)
        if match.group(1):
            number = int(match.group(1))
        elif match.group(2):
            number = int(match.group(2))
            
        return {
            'type': 'movie',
            'number': number
        }
    
    # Check other special patterns
    for pattern, special_type in SPECIAL_PATTERNS:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            # Extract the special episode number if available
            number = None
            groups = match.groups()
            
            # Try to find a number in any of the matched groups
            for group in groups:
                if group and str(group).isdigit():
                    number = int(group)
                    break
            
            return {
                'type': special_type,
                'number': number
            }
    
    return None

def organize_season_pack(files: List[Path]) -> Dict[str, List[Path]]:
    """
    Organize files from a season pack into appropriate season folders.
    
    Args:
        files: List of file paths to organize
        
    Returns:
        Dictionary with season folder names as keys and lists of files as values
    """
    result = {
        "Specials": [],
        "Unknown": []
    }
    
    for file in files:
        filename = file.name
        
        # Check if it's a special episode
        special_info = detect_special_episodes(filename)
        if special_info:
            result["Specials"].append(file)
            continue
        
        # Direct pattern matching for TV shows
        tv_pattern = re.compile(r'[sS](?P<season>\d{1,2})[eE](?P<episode>\d{1,2})')
        tv_match = tv_pattern.search(filename)
        
        if tv_match:
            season = int(tv_match.group('season'))
            season_folder = f"Season {season}"
            
            # Create the season entry if it doesn't exist
            if season_folder not in result:
                result[season_folder] = []
                
            result[season_folder].append(file)
        else:
            # Files we couldn't categorize
            result["Unknown"].append(file)
    
    return result 