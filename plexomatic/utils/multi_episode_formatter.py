"""Formatter for handling multiple episodes in templates.

This module provides functions to handle formatting multiple episodes in templates.
It can detect ranges of sequential episodes and format them appropriately.
"""

from typing import List, Optional, Union
import logging

from plexomatic.utils.name_parser import ParsedMediaName

logger = logging.getLogger(__name__)


def ensure_episode_list(episodes: Optional[Union[int, str, List[int]]]) -> List[int]:
    """Ensure that episodes is a list.

    Args:
        episodes: An episode number, list of episode numbers, string representation of an episode, or None.

    Returns:
        A list of episode numbers, or an empty list if episodes is None.

    Raises:
        TypeError: If episodes is not an int, str, list, or None.
    """
    if episodes is None:
        return []
    elif isinstance(episodes, int):
        return [episodes]
    elif isinstance(episodes, str):
        try:
            return [int(episodes)]
        except ValueError:
            # If the string is not a number, raise TypeError
            raise TypeError(f"String episode must be a number, got '{episodes}'")
    elif isinstance(episodes, list):
        return episodes
    else:
        raise TypeError(f"Expected int, str, list, or None, got {type(episodes)}")


def format_multi_episode(episodes: List[int], episode_format: str, skip_range: bool = False) -> str:
    """Format multiple episodes using the provided episode format.

    Args:
        episodes: A list of episode numbers.
        episode_format: A format string for episode numbers, e.g. "E{:02d}".
        skip_range: If True, don't use ranges even for sequential episodes.

    Returns:
        A formatted string representing the episodes.
    """
    if not episodes:
        return ""

    # Format each episode individually
    formatted_episodes = [episode_format.format(ep) for ep in episodes]

    if len(episodes) == 1 or skip_range:
        # Single episode or skip_range is True
        return ",".join(formatted_episodes)

    # Find ranges of sequential episodes
    ranges = []
    current_range = [episodes[0]]

    for ep in episodes[1:]:
        if ep == current_range[-1] + 1:
            # Episode is sequential
            current_range.append(ep)
        else:
            # Episode is not sequential, end the current range
            ranges.append(current_range)
            current_range = [ep]

    # Add the last range
    ranges.append(current_range)

    # Format ranges
    formatted_ranges = []
    for r in ranges:
        if len(r) == 1:
            # Single episode
            formatted_ranges.append(episode_format.format(r[0]))
        else:
            # Range of episodes
            formatted_ranges.append(f"{episode_format.format(r[0])}-{episode_format.format(r[-1])}")

    return ",".join(formatted_ranges)


def get_formatted_episodes(parsed: ParsedMediaName, episode_format: str = "E{:02d}") -> str:
    """Get a formatted string of episodes from a ParsedMediaName.

    Args:
        parsed: A ParsedMediaName object.
        episode_format: A format string for episode numbers.

    Returns:
        A formatted string representing the episodes.
    """
    episodes = ensure_episode_list(parsed.episodes)
    return format_multi_episode(episodes, episode_format)
