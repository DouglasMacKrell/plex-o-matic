"""Functions for detecting segments in episode files."""

import re
import os
import json
import hashlib
import logging
from typing import List, Dict, Any, Optional, Union, Set
from pathlib import Path

# For Python 3.8 support
try:
    from typing import TypedDict, Literal
except ImportError:
    from typing_extensions import TypedDict, Literal

from plexomatic.utils.episode.parser import (
    extract_show_info,
    detect_multi_episodes,
    split_title_by_separators
)


def is_thinking_section(text: str) -> bool:
    """
    Check if a text string contains thinking tags.

    Args:
        text: Text to check for thinking tags

    Returns:
        True if text contains thinking tags, False otherwise
    """
    return "<thinking>" in text or "</thinking>" in text


def process_thinking_tags(text: str) -> str:
    """
    Process and remove thinking tags from text.

    Args:
        text: Text with potential thinking tags

    Returns:
        Text with thinking sections removed
    """
    if not text:
        return ""
    
    logger = logging.getLogger(__name__)
    cleaned_text = text
    
    # Process multiple thinking sections
    while "<thinking>" in cleaned_text.lower() and "</thinking>" in cleaned_text.lower():
        try:
            start_index = cleaned_text.lower().find("<thinking>")
            end_index = cleaned_text.lower().find("</thinking>") + len("</thinking>")
            
            # Extract content before thinking and after thinking
            before_thinking = cleaned_text[:start_index].strip()
            after_thinking = cleaned_text[end_index:].strip()
            
            # Combine parts, skipping the thinking section
            cleaned_text = (before_thinking + "\n" + after_thinking).strip()
            logger.debug(f"Removed thinking section from text")
        except Exception as e:
            logger.warning(f"Error removing thinking tags: {e}")
            break
    
    return cleaned_text


def filter_segments(segments: List[str]) -> List[str]:
    """
    Filter segments to remove thinking tags and other artifacts.

    Args:
        segments: List of segment strings to filter

    Returns:
        Filtered list of valid segments, or ["Unknown"] if no valid segments
    """
    if not segments:
        return ["Unknown"]
    
    logger = logging.getLogger(__name__)
    
    # Filter out thinking sections and other artifacts
    filtered_segments = []
    
    for segment in segments:
        # Skip segments with thinking tags
        if is_thinking_section(segment):
            continue
            
        # Skip segments with common artifacts
        if (segment.lower().startswith("thinking:") or
            "thinking" in segment.lower() or
            "summary:" in segment.lower() or  # Only filter if it's a summary label
            "approach:" in segment.lower() or  # Only filter if it's an approach label
            "confirm:" in segment.lower() or   # Only filter if it's a confirmation label
            segment.lower() == "in progress" or
            "format:" in segment.lower() or    # Only filter if it's a format label
            segment.lower() == "episode"):
            continue
        
        # Accept segments that start with "Segment" but don't have a colon
        # This handles test cases like "Segment 1", "Segment 2", etc.
        if segment.lower().startswith("segment") and ":" not in segment:
            filtered_segments.append(segment)
            continue
            
        # Add valid segment
        if not segment.lower().startswith("segment"):
            filtered_segments.append(segment)
    
    # Return filtered segments or fallback to "Unknown"
    if filtered_segments:
        logger.debug(f"Filtered segments: {filtered_segments}")
        return filtered_segments
    else:
        logger.debug("No valid segments after filtering, using 'Unknown'")
        return ["Unknown"]


def detect_segments(transcript: str) -> List[str]:
    """
    Detect segments from a transcript.

    Args:
        transcript: Text transcript to analyze for segments

    Returns:
        List of segment titles, or ["Unknown"] if no segments found
    """
    if not transcript or not transcript.strip():
        return ["Unknown"]
    
    logger = logging.getLogger(__name__)
    
    # Process transcript to remove thinking tags
    cleaned_transcript = process_thinking_tags(transcript)
    
    # Extract segment information using regex patterns
    segment_patterns = [
        r'Segment \d+:\s*(.*?)(?=\n|$)',  # "Segment 1: Title"
        r'\d+\.\s*(.*?)(?=\n|$)',          # "1. Title"
        r'•\s*(.*?)(?=\n|$)',              # "• Title"
        r'\*\s*(.*?)(?=\n|$)',             # "* Title"
        r'-\s*(.*?)(?=\n|$)',              # "- Title"
    ]
    
    all_segments = []
    
    for pattern in segment_patterns:
        matches = re.findall(pattern, cleaned_transcript)
        if matches:
            logger.debug(f"Found {len(matches)} segments with pattern: {pattern}")
            all_segments.extend([match.strip() for match in matches if match.strip()])
    
    # If no segments found with patterns, try splitting by lines and filtering
    if not all_segments:
        logger.debug("No segments found with patterns, trying line-by-line analysis")
        lines = [line.strip() for line in cleaned_transcript.split('\n') if line.strip()]
        
        # Look for potential segment titles (typically shorter lines)
        potential_segments = [
            line for line in lines 
            if len(line) < 100  # Not too long
            and ":" not in line  # Not likely to be a detailed description
            and not line.startswith("Summary")  # Not a summary line
        ]
        
        all_segments.extend(potential_segments)
    
    # Filter segments to remove artifacts
    filtered_segments = filter_segments(all_segments)
    
    logger.debug(f"Detected {len(filtered_segments)} segments: {filtered_segments}")
    return filtered_segments


def detect_segments_from_file(
    file_path: str, 
    use_llm: bool = False,
    max_segments: int = 10,
    use_cache: bool = True
) -> List[str]:
    """
    Detect segments in a file using LLM or cached results.
    
    Args:
        file_path: Path to the file
        use_llm: Whether to use LLM for detection
        max_segments: Maximum number of segments to detect
        use_cache: Whether to use cached results if available
        
    Returns:
        List of segment titles or ["Unknown"] if no segments detected
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Detecting segments in: {file_path}")
    
    if not use_llm:
        logger.debug("LLM assistance disabled, returning default segment")
        return ["Unknown"]
    
    # Check cache if enabled
    if use_cache:
        segments = _load_segments_from_cache(file_path)
        if segments:
            return segments
    
    # Use LLM to detect segments
    try:
        from plexomatic.api.llm_client import LLMClient
        from plexomatic.utils.episode.parser import extract_show_info
        
        # Extract info from file name to use in LLM context
        parsed_info = extract_show_info(os.path.basename(file_path))
        show_name = parsed_info.get("show_name", os.path.basename(file_path))
        
        logger.info(f"Using LLM to detect segments in: {os.path.basename(file_path)}")
        
        # Create a client for the LLM
        llm_client = LLMClient()
        
        # Build context for the LLM request
        prompt = f"""
        You are a content analyzer working with TV shows. You need to identify the segments in this file:

        File: {os.path.basename(file_path)}
        Show: {show_name}

        If this is an anthology episode, it might contain multiple segments/stories.
        For example, "Mickey Mouse Clubhouse S01E01" might contain segments like:
        - "Daisy's Dance"
        - "Goofy's Bird"
        - "Minnie's Birthday"
        
        Other anthology shows like "Daniel Tigers Neighborhood" or "Chip 'n Dale: Park Life" typically contain 3-4 segments per episode.

        Please identify segment titles if this is an anthology episode. Return ONLY the segment titles, one per line.
        If you can't identify specific segment titles, return the word "Unknown" for each estimated segment.
        If this is not an anthology episode or you can't determine segments, return nothing.
        
        Segments:
        """
        
        logger.debug(f"Sending prompt to LLM")
        
        # Get response from LLM
        response = llm_client.generate_text(prompt).strip()
        
        # Process the response
        if not response or ("." in response and len(response) < 10):
            logger.warning(f"No valid segments returned from LLM for {file_path}")
            return ["Unknown"]
        
        # Process thinking tags
        cleaned_response = process_thinking_tags(response)
        
        # Process the segments from the response
        # Split by lines and clean up
        segments = [
            s.strip()
            for s in cleaned_response.strip().split("\n")
            if s.strip()  # Only filter empty lines, keep bullet points
        ]
        
        # Remove bullet points and numbering
        segments = [re.sub(r"^[\d\.\-\•\*]+\s*", "", s) for s in segments]
        
        # Remove quotes
        segments = [s.strip('"\'') for s in segments]
        
        # Filter and limit segments
        filtered_segments = filter_segments(segments)
        filtered_segments = filtered_segments[:max_segments]
        
        if filtered_segments:
            # Cache the results
            _cache_segments(file_path, filtered_segments)
        
        return filtered_segments
        
    except Exception as e:
        logger.error(f"Error detecting segments with LLM: {e}")
        return ["Unknown"]


def _load_segments_from_cache(file_path: str) -> Optional[List[str]]:
    """Load segments from cache if available."""
    logger = logging.getLogger(__name__)
    
    cache_dir = os.path.join(os.path.expanduser("~"), ".plexomatic", "cache")
    cache_file = os.path.join(
        cache_dir, f"segments_{hashlib.md5(file_path.encode()).hexdigest()}.json"
    )
    
    # Check for cached segments
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                segments = json.load(f)
                # Filter segments
                filtered_segments = filter_segments(segments)
                if filtered_segments and filtered_segments != ["Unknown"]:
                    logger.debug(f"Loaded {len(filtered_segments)} valid segments from cache: {filtered_segments}")
                    return filtered_segments
                else:
                    logger.debug("No valid segments found in cache, will regenerate")
        except Exception as e:
            logger.warning(f"Error loading segment cache: {e}")
    
    return None


def _cache_segments(file_path: str, segments: List[str]) -> None:
    """Cache segments for future use."""
    logger = logging.getLogger(__name__)
    
    try:
        cache_dir = os.path.join(os.path.expanduser("~"), ".plexomatic", "cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        cache_file = os.path.join(
            cache_dir, f"segments_{hashlib.md5(file_path.encode()).hexdigest()}.json"
        )
        
        with open(cache_file, "w") as f:
            json.dump(segments, f)
            
        logger.debug(f"Cached {len(segments)} segments for {os.path.basename(file_path)}")
    except Exception as e:
        logger.warning(f"Error caching segments: {e}")


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
        r'(?:season|series)[\s-]*finale',
        r'final[\s-]*episode',
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
        r'first[\s-]*episode',
        r'premiere',
        r'pilot'
    ]
    
    # Get the lowercase filename for easier matching
    lower_filename = filename.lower()
    
    for pattern in title_patterns:
        if re.search(pattern, lower_filename):
            return True
    
    # Also check if it's episode 1
    show_info = extract_show_info(filename)
    if show_info and show_info.get("episode") == 1:
        return True
    
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
        r'part[\s-]*(\d+|one|two|three|four|five|i|ii|iii|iv|v)',
        r'pt[\s.-]*(\d+|one|two|three|four|five|i|ii|iii|iv|v)',
        r'\((\d+|one|two|three|four|five|i|ii|iii|iv|v) of (\d+|one|two|three|four|five|i|ii|iii|iv|v)\)'
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