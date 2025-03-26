"""Utilities for detecting episode patterns in filenames."""

import re
import logging
from typing import Dict, List, Optional, Union, Any

logger = logging.getLogger(__name__)

# Regular expressions for detecting various episode formats
MULTI_EPISODE_PATTERNS = [
    # Standard multi-episode format: S01E01E02
    r"S(\d+)E(\d+)(?:E(\d+))+",
    # Hyphen format: S01E01-E02
    r"S(\d+)E(\d+)-E(\d+)",
    # X format with hyphen: 01x01-02
    r"(\d+)x(\d+)-(\d+)",
    # E format with hyphen but no second E: S01E01-02
    r"S(\d+)E(\d+)-(\d+)",
    # Space separator: S01E01 E02
    r"S(\d+)E(\d+)(?:\s+E(\d+))+",
    # Text separators like "to", "&", "+"
    r"S(\d+)E(\d+)(?:\s*(?:to|&|\+|,)\s*E(\d+))+",
]

# Regular expressions for detecting special episodes
SPECIAL_PATTERNS = [
    # Season 0 specials: S00E01
    (r"S00E(\d+)", "special"),
    # Special keyword with number
    (r"Special\.(\d+)", "special"),
    # Special keyword with number after word
    (r"Special\s*(\d+)", "special"),
    # Special keyword general
    (r"Special(?:s)?", "special"),
    # OVA keyword with number after dot
    (r"OVA\.(\d+)", "ova"),
    # OVA keyword with number after word
    (r"OVA\s*(\d+)", "ova"),
    # OVA keyword general
    (r"OVA(?:s)?", "ova"),
    # Movie/Film specials with number
    (r"Movie\.(\d+)|Film\.(\d+)", "movie"),
    # Movie/Film specials with number after word
    (r"Movie\s*(\d+)|Film\s*(\d+)", "movie"),
    # Movie/Film specials general
    (r"Movie|Film", "movie"),
]


def detect_multi_episodes(filename: str) -> List[int]:
    """
    Detect if a filename contains multiple episodes.

    Args:
        filename: The filename to check

    Returns:
        List of episode numbers if found, empty list otherwise
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Checking for multi-episodes in: {filename}")

    # First, try multi-episode patterns
    for pattern in MULTI_EPISODE_PATTERNS:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            # Extract all episode numbers from the match
            episode_numbers = []
            # For the first pattern, we need special handling to avoid duplicates
            if pattern == r"S(\d+)E(\d+)(?:E(\d+))+":
                # This is the "S01E01E02" pattern
                season_num = int(match.group(1)) if match.group(1) else None
                groups = match.groups()
                # Skip the season group and start from first episode
                episode_numbers = [int(g) for g in groups[1:] if g is not None]
            else:
                # For other patterns, just collect all episode numbers
                for group in match.groups():
                    if group is not None:
                        episode_numbers.append(int(group))
            
            if episode_numbers:
                logger.debug(f"Found multi-episodes: {episode_numbers}")
                return episode_numbers

    # If no multi-episodes found, check for a single episode
    single_episode_pattern = r"S\d+E(\d+)|(\d+)x\d+|Episode\s*(\d+)"
    match = re.search(single_episode_pattern, filename, re.IGNORECASE)
    if match:
        for group in match.groups():
            if group is not None:
                episode_number = int(group)
                logger.debug(f"Found single episode: {episode_number}")
                return [episode_number]

    logger.debug("No episodes found")
    return []


def detect_special_episodes(filename: str) -> Optional[Dict[str, Union[str, int, None]]]:
    """
    Detect if a filename represents a special episode.

    Args:
        filename: The filename to check

    Returns:
        Dictionary with special episode info if found, None otherwise
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Checking for special episodes in: {filename}")

    # Extract digits that might be referring to a special episode number
    standalone_number_match = re.search(r'\.(\d+)\.', filename)
    standalone_number = None
    if standalone_number_match:
        standalone_number = int(standalone_number_match.group(1))

    # Try each pattern
    for pattern, special_type in SPECIAL_PATTERNS:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            # Extract the number if present in the match groups
            number = None
            for group in match.groups():
                if group is not None:
                    number = int(group)
                    break
            
            # If no number found in the direct match but we have a standalone number
            # from the filename (like in "Show.Special.1.mp4"), use that
            if number is None and standalone_number is not None:
                number = standalone_number

            logger.debug(f"Found special episode: type={special_type}, number={number}")
            return {
                "type": special_type,
                "number": number,
            }

    logger.debug("No special episode found")
    return None 