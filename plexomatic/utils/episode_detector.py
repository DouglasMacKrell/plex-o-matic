"""Utilities for detecting episode patterns in filenames (DEPRECATED).

This module is deprecated and maintained for backward compatibility.
Please use plexomatic.utils.episode.detector instead.
"""

import logging
import warnings
from typing import Dict, List, Optional, Union, Any

# Import the canonical versions from the new module
from plexomatic.utils.episode.detector import (
    detect_multi_episodes as _detect_multi_episodes,
    detect_special_episodes as _detect_special_episodes,
    is_anthology_episode as _is_anthology_episode,
    get_segment_count as _get_segment_count,
    detect_season_finale as _detect_season_finale,
    detect_season_premiere as _detect_season_premiere,
    is_multi_part_episode as _is_multi_part_episode,
    get_episode_type as _get_episode_type,
)

logger = logging.getLogger(__name__)

# Display a deprecation warning when this module is imported
warnings.warn(
    "The plexomatic.utils.episode_detector module is deprecated. "
    "Please use plexomatic.utils.episode.detector instead.",
    DeprecationWarning,
    stacklevel=2,
)


def detect_multi_episodes(filename: str) -> List[int]:
    """
    Detect if a filename contains multiple episodes (DEPRECATED).

    This function is deprecated. Please use plexomatic.utils.episode.detector.detect_multi_episodes instead.

    Args:
        filename: The filename to check

    Returns:
        List of episode numbers if found, empty list otherwise
    """
    warnings.warn(
        "detect_multi_episodes is deprecated. "
        "Use plexomatic.utils.episode.detector.detect_multi_episodes instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _detect_multi_episodes(filename)


def detect_special_episodes(filename: str) -> Optional[Dict[str, Union[str, int, None]]]:
    """
    Detect if a filename represents a special episode (DEPRECATED).

    This function is deprecated. Please use plexomatic.utils.episode.detector.detect_special_episodes instead.

    Args:
        filename: The filename to check

    Returns:
        Dictionary with special episode info if found, None otherwise
    """
    warnings.warn(
        "detect_special_episodes is deprecated. "
        "Use plexomatic.utils.episode.detector.detect_special_episodes instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _detect_special_episodes(filename)


def is_anthology_episode(filename: str) -> bool:
    """
    Detect if an episode is likely an anthology episode (DEPRECATED).

    This function is deprecated. Please use plexomatic.utils.episode.detector.is_anthology_episode instead.

    Args:
        filename: The filename to analyze

    Returns:
        True if the episode appears to be an anthology, False otherwise
    """
    warnings.warn(
        "is_anthology_episode is deprecated. "
        "Use plexomatic.utils.episode.detector.is_anthology_episode instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _is_anthology_episode(filename)


def get_segment_count(filename: str) -> int:
    """
    Determine the number of segments in an episode (DEPRECATED).

    This function is deprecated. Please use plexomatic.utils.episode.detector.get_segment_count instead.

    Args:
        filename: The filename to analyze

    Returns:
        The number of segments (defaults to 1 if not an anthology)
    """
    warnings.warn(
        "get_segment_count is deprecated. "
        "Use plexomatic.utils.episode.detector.get_segment_count instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _get_segment_count(filename)


def detect_season_finale(filename: str) -> bool:
    """
    Detect if an episode is a season finale (DEPRECATED).

    This function is deprecated. Please use plexomatic.utils.episode.detector.detect_season_finale instead.

    Args:
        filename: The filename to analyze

    Returns:
        True if the episode appears to be a season finale, False otherwise
    """
    warnings.warn(
        "detect_season_finale is deprecated. "
        "Use plexomatic.utils.episode.detector.detect_season_finale instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _detect_season_finale(filename)


def detect_season_premiere(filename: str) -> bool:
    """
    Detect if an episode is a season premiere (DEPRECATED).

    This function is deprecated. Please use plexomatic.utils.episode.detector.detect_season_premiere instead.

    Args:
        filename: The filename to analyze

    Returns:
        True if the episode appears to be a season premiere, False otherwise
    """
    warnings.warn(
        "detect_season_premiere is deprecated. "
        "Use plexomatic.utils.episode.detector.detect_season_premiere instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _detect_season_premiere(filename)


def is_multi_part_episode(filename: str) -> bool:
    """
    Detect if an episode is part of a multi-part story (DEPRECATED).

    This function is deprecated. Please use plexomatic.utils.episode.detector.is_multi_part_episode instead.

    Args:
        filename: The filename to analyze

    Returns:
        True if the episode appears to be part of a multi-part story, False otherwise
    """
    warnings.warn(
        "is_multi_part_episode is deprecated. "
        "Use plexomatic.utils.episode.detector.is_multi_part_episode instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _is_multi_part_episode(filename)


def get_episode_type(filename: str) -> Dict[str, Any]:
    """
    Determine the type of episode based on various detection methods (DEPRECATED).

    This function is deprecated. Please use plexomatic.utils.episode.detector.get_episode_type instead.

    Args:
        filename: The filename to analyze

    Returns:
        Dictionary with episode type information
    """
    warnings.warn(
        "get_episode_type is deprecated. "
        "Use plexomatic.utils.episode.detector.get_episode_type instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _get_episode_type(filename)
