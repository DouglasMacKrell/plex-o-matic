"""
Module for handling TV show episodes, including parsing, formatting, and processing.
"""

import logging
from typing import List, Dict, Tuple, Optional, Union, Any
try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict  # Python 3.8 support

# Parser module exports
from plexomatic.utils.episode.parser import (
    extract_show_info,
    detect_multi_episodes,
    parse_episode_range,
    are_sequential,
    detect_special_episodes,
    is_tv_show,
    split_title_by_separators,
)

# Formatter module exports
from plexomatic.utils.episode.formatter import (
    format_show_name,
    format_episode_title,
    sanitize_filename,
    format_new_name,
    format_episode_filename,
)

# Detector module exports
from plexomatic.utils.episode.episode_detector import (
    is_anthology_episode,
    get_segment_count,
    detect_season_finale,
    detect_season_premiere,
    is_multi_part_episode,
    get_episode_type,
)

# Processor module exports
from plexomatic.utils.episode.processor import (
    process_anthology_episode,
    detect_segments_with_llm,
    match_episode_titles,
    process_episode,
)

# Setup logger
logger = logging.getLogger(__name__)

# Define the public API
__all__ = [
    # Parser exports
    'extract_show_info',
    'detect_multi_episodes',
    'parse_episode_range',
    'are_sequential',
    'detect_special_episodes',
    'is_tv_show',
    'split_title_by_separators',
    
    # Formatter exports
    'format_show_name',
    'format_episode_title',
    'sanitize_filename',
    'format_new_name',
    'format_episode_filename',
    
    # Detector exports
    'is_anthology_episode',
    'get_segment_count',
    'detect_season_finale',
    'detect_season_premiere',
    'is_multi_part_episode',
    'get_episode_type',
    
    # Processor exports
    'process_anthology_episode',
    'detect_segments_with_llm',
    'match_episode_titles',
    'process_episode',
] 