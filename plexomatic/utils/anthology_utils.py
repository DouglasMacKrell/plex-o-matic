"""Utilities for handling anthology episodes and segments."""

import logging
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)


def detect_segments(title: str, use_llm: bool = False, max_segments: int = 10) -> List[str]:
    """
    Detect segments in a title string.

    Args:
        title: The title string to analyze
        use_llm: Whether to use LLM for segment detection
        max_segments: Maximum number of segments to detect

    Returns:
        List of detected segments
    """
    # If use_llm is True, delegate to the LLM-based detection
    if use_llm:
        from plexomatic.utils.episode.parser import extract_show_info
        from plexomatic.utils.episode.processor import detect_segments_with_llm

        # If the input is a filename, extract the title from it
        if "." in title and ("/" in title or "\\" in title):
            info = extract_show_info(title)
            if info and "title" in info:
                title = info["title"]

        # Use LLM to detect segments
        return detect_segments_with_llm(title, max_segments)

    # Original logic for basic segment detection
    if not title:
        return []

    # Common segment separators
    separators = ["&", "and", "+", ",", "|", "/"]

    # Try each separator
    for sep in separators:
        if sep in title:
            # Split on the separator and clean up each segment
            segments = [s.strip() for s in title.split(sep)]
            # Filter out empty segments
            segments = [s for s in segments if s]
            if len(segments) > 1:
                return segments

    # If no segments found, return the whole title as one segment
    return [title.strip()]


def preprocess_anthology_episodes(
    files: List[str],
    use_llm: bool = True,
    api_lookup: bool = True,
) -> Dict[str, Dict[str, Any]]:
    """
    Preprocess files for anthology mode to ensure proper episode numbering.

    Args:
        files: List of file paths to process
        use_llm: Whether to use LLM for parsing and segment detection
        api_lookup: Whether to use API lookup for episode numbers

    Returns:
        Dictionary mapping file paths to their preprocessed data
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Preprocessing {len(files)} files for anthology mode")

    preprocessed_data = {}

    # Sort files to ensure consistent ordering
    sorted_files = sorted(files)

    for i, file_path in enumerate(sorted_files, 1):
        path = Path(file_path)
        preprocessed_data[str(path)] = {
            "original_path": str(path),
            "new_episode": i,
            "segments": [],  # Will be populated if needed
        }

    return preprocessed_data
