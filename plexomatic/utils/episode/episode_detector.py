"""Functions for detecting anthology and other episode types."""

import re
import os
import logging
from typing import Dict, List, Optional, Union, Any, Tuple

from plexomatic.utils.episode.parser import (
    extract_show_info,
    detect_multi_episodes,
    split_title_by_separators
)


def is_anthology_episode(filename: str) -> bool:
    """
    Detect if an episode is likely an anthology episode (containing multiple segments).
    
    Args:
        filename: The filename to analyze
        
    Returns:
        True if the episode appears to be an anthology, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    # Extract show info
    show_info = extract_show_info(filename)
    if not show_info:
        return False
    
    # Check if there are multiple episodes in one file
    multi_episodes = detect_multi_episodes(filename)
    
    # Check if the title contains separators that might indicate multiple segments
    title = show_info.get("title", "")
    segments = split_title_by_separators(title)
    
    # If we have multiple segments in the title, it's likely an anthology
    if len(segments) > 1:
        logger.debug(f"Detected anthology episode by title segments: {segments}")
        return True
    
    # If we have multiple episodes (E01E02) in the filename, it might be an anthology
    if len(multi_episodes) > 1:
        logger.debug(f"Detected anthology episode by multi-episodes: {multi_episodes}")
        return True
    
    # Otherwise, not an anthology
    return False


def get_segment_count(filename: str) -> int:
    """
    Determine the number of segments in an episode.
    
    Args:
        filename: The filename to analyze
        
    Returns:
        The number of segments (defaults to 1 if not an anthology)
    """
    logger = logging.getLogger(__name__)
    
    if not is_anthology_episode(filename):
        return 1
    
    # Extract show info
    show_info = extract_show_info(filename)
    if not show_info:
        return 1
    
    # Check if there are multiple episodes in one file
    multi_episodes = detect_multi_episodes(filename)
    if len(multi_episodes) > 1:
        return len(multi_episodes)
    
    # Check title segments
    title = show_info.get("title", "")
    segments = split_title_by_separators(title)
    if len(segments) > 1:
        return len(segments)
    
    # Default to 1 segment
    return 1


def detect_season_finale(filename: str) -> bool:
    """
    Detect if an episode is a season finale.
    
    Args:
        filename: The filename to analyze
        
    Returns:
        True if the episode appears to be a season finale, False otherwise
    """
    # Check if the title contains "finale" keywords
    title_patterns = [
        r'(?:season|series)[\s.-]*finale',
        r'final[\s.-]*episode',
        r'finale'
    ]
    
    # Get the lowercase filename for easier matching
    lower_filename = filename.lower()
    
    for pattern in title_patterns:
        if re.search(pattern, lower_filename):
            return True
    
    return False


def detect_season_premiere(filename: str) -> bool:
    """
    Detect if an episode is a season premiere.
    
    Args:
        filename: The filename to analyze
        
    Returns:
        True if the episode appears to be a season premiere, False otherwise
    """
    # Check if the title contains "premiere" keywords
    title_patterns = [
        r'(?:season|series)[\s-]*premiere',
        r'first[\s.-]*episode',
        r'premiere',
        r'pilot'
    ]
    
    # Get the lowercase filename for easier matching
    lower_filename = filename.lower()
    
    for pattern in title_patterns:
        if re.search(pattern, lower_filename):
            return True
    
    # We no longer automatically consider S01E01 as a premiere
    # without specific keywords in the title
    return False


def is_multi_part_episode(filename: str) -> bool:
    """
    Detect if an episode is part of a multi-part story.
    
    Args:
        filename: The filename to analyze
        
    Returns:
        True if the episode appears to be part of a multi-part story, False otherwise
    """
    # Check for common multi-part indicators
    part_patterns = [
        r'part[\s.-]*(\d+|one|two|three|four|five|i|ii|iii|iv|v)',
        r'pt[\s.-]*(\d+|one|two|three|four|five|i|ii|iii|iv|v)',
        r'\((\d+|one|two|three|four|five|i|ii|iii|iv|v)[\s.-]*of[\s.-]*(\d+|one|two|three|four|five|i|ii|iii|iv|v)\)'
    ]
    
    # Get the lowercase filename for easier matching
    lower_filename = filename.lower()
    
    for pattern in part_patterns:
        if re.search(pattern, lower_filename):
            return True
    
    return False


def get_episode_type(filename: str) -> Dict[str, Any]:
    """
    Determine the type of episode based on various detection methods.
    
    Args:
        filename: The filename to analyze
        
    Returns:
        Dictionary with episode type information
    """
    logger = logging.getLogger(__name__)
    
    result = {
        "is_anthology": False,
        "segment_count": 1,
        "is_finale": False,
        "is_premiere": False,
        "is_multi_part": False
    }
    
    # Detect anthology episodes
    result["is_anthology"] = is_anthology_episode(filename)
    if result["is_anthology"]:
        result["segment_count"] = get_segment_count(filename)
    
    # Detect finale
    result["is_finale"] = detect_season_finale(filename)
    
    # Detect premiere
    result["is_premiere"] = detect_season_premiere(filename)
    
    # Detect multi-part episodes
    result["is_multi_part"] = is_multi_part_episode(filename)
    
    logger.debug(f"Episode type for {filename}: {result}")
    return result 