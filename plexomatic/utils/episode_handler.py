"""Utilities for handling TV show episodes, including multi-episode detection and special episode handling."""

import re
from pathlib import Path
import logging
import os
import difflib
import json
import hashlib

try:
    # Python 3.9+ has native support for these types
    from typing import (
        Dict,
        List,
        Optional,
        Union,
        Any,
    )
except ImportError:
    # For Python 3.8 support
    from typing_extensions import (
        Dict,
        List,
        Optional,
        Union,
        Any,
    )

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
    # Special keyword
    (r"Special(?:s)?(?:\s*(\d+))?", "special"),
    # OVA keyword (Original Video Animation, common in anime)
    (r"OVA(?:\s*(\d+))?", "ova"),
    # OVA with number after dot
    (r"OVA\.(\d+)", "ova"),
    # Movie/Film specials with number
    (r"Movie\.(\d+)|Film\.(\d+)", "movie"),
    # Movie/Film specials general
    (r"Movie(?:\s*(\d+))?|Film(?:\s*(\d+))?", "movie"),
]


def extract_show_info(filename: str) -> Dict[str, Any]:
    """
    Extract show information from a filename.

    Args:
        filename: The filename to extract information from

    Returns:
        Dictionary with show name, season, episode, and title information
    """
    logger = logging.getLogger(__name__)

    # Get just the basename without the directory path
    basename = os.path.basename(filename)
    logger.debug(f"Extracting info from basename: {basename}")

    # Remove file extension
    name_without_ext, extension = os.path.splitext(basename)

    # Replace dots with spaces to make parsing easier
    name_with_spaces = name_without_ext.replace(".", " ")

    # Try to find season and episode information using regex patterns

    # Pattern 1: Standard format "Show Name S01E02 Title"
    pattern1 = r"(.+?)(?:[-_\s.]*)(s|season\s+)(\d+)(e|episode\s+)(\d+)(?:[-_\s.]*)(.+)?"

    # Pattern 2: Format with no explicit markers, "Show Name 1x02 Title"
    pattern2 = r"(.+?)(?:[-_\s.]*)(\d+)x(\d+)(?:[-_\s.]*)(.+)?"

    # Pattern 3: Format with dash, "Show Name - S01E02 - Title"
    pattern3 = r"(.+?)(?:-\s*)(s|season\s+)(\d+)(e|episode\s+)(\d+)(?:\s*-)(?:[-_\s.]*)(.+)?"

    # Try each pattern
    for pattern, group_indices in [
        (pattern1, {"show": 1, "season": 3, "episode": 5, "title": 6}),
        (pattern2, {"show": 1, "season": 2, "episode": 3, "title": 4}),
        (pattern3, {"show": 1, "season": 3, "episode": 5, "title": 6}),
    ]:
        match = re.search(pattern, name_with_spaces, re.IGNORECASE)
        if match:
            show_name = match.group(group_indices["show"]).strip()
            season = int(match.group(group_indices["season"]))
            episode = int(match.group(group_indices["episode"]))
            title = (
                match.group(group_indices["title"]).strip()
                if match.group(group_indices["title"])
                else ""
            )

            logger.debug(
                f"Matched pattern, extracted: show={show_name}, season={season}, episode={episode}, title={title}"
            )

            return {
                "show_name": show_name,
                "season": season,
                "episode": episode,
                "title": title,
                "extension": extension,
            }

    # If no pattern matched, try a more lenient approach
    # Look for just the season and episode numbers
    season_ep_pattern = r"[Ss](\d+)[Ee](\d+)"
    alt_pattern = r"(\d+)x(\d+)"

    for pattern in [season_ep_pattern, alt_pattern]:
        match = re.search(pattern, name_without_ext)
        if match:
            season = int(match.group(1))
            episode = int(match.group(2))

            # Try to extract show name and title
            parts = re.split(pattern, name_without_ext, maxsplit=1)
            show_name = parts[0].strip().replace(".", " ")
            title = parts[-1].strip().replace(".", " ") if len(parts) > 2 else ""

            logger.debug(
                f"Matched fallback pattern, extracted: show={show_name}, season={season}, episode={episode}, title={title}"
            )

            return {
                "show_name": show_name,
                "season": season,
                "episode": episode,
                "title": title,
                "extension": extension,
            }

    logger.warning(f"Could not extract episode info from {basename}")
    return {}


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
    if show_info.get("episode"):
        # Convert episode to int if it's a string
        episode = (
            int(show_info["episode"])
            if isinstance(show_info["episode"], str)
            else show_info["episode"]
        )
        # Ensure episode is an int, not None or another type
        if not isinstance(episode, int):
            return []

        # Initialize the result with the first detected episode
        result: List[int] = [episode]

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

                    if start_ep is not None and end_ep is not None:
                        return parse_episode_range(start_ep, end_ep)

                # If there are multiple episode markers (E01E02E03...)
                episode_markers = re.findall(r"E(\d+)", filename)
                if len(episode_markers) > 1:
                    return [int(ep) for ep in episode_markers]

        return result

    # Direct episode detection if extract_show_info didn't find anything
    # Standard format: S01E01E02
    multi_ep_pattern = r"S(\d+)E(\d+)(?:E(\d+))+"
    match = re.search(multi_ep_pattern, filename, re.IGNORECASE)
    if match:
        episode_markers = re.findall(r"E(\d+)", filename)
        if episode_markers:
            return [int(ep) for ep in episode_markers]

    # Hyphen format: S01E01-E02 or S01E01-02
    hyphen_pattern = r"S\d+E(\d+)[-](?:E)?(\d+)"
    match = re.search(hyphen_pattern, filename, re.IGNORECASE)
    if match:
        start_ep = int(match.group(1))
        end_ep = int(match.group(2))
        return parse_episode_range(start_ep, end_ep)

    # For patterns like "01x02-03" without S01E01 format
    x_pattern = r"(\d+)x(\d+)(?:-(\d+))?"
    match = re.search(x_pattern, filename, re.IGNORECASE)
    if match:
        groups = match.groups()
        if len(groups) >= 3 and groups[2]:
            start_ep = int(groups[1])
            end_ep = int(groups[2])
            return parse_episode_range(start_ep, end_ep)
        else:
            return [int(groups[1])]

    # Space separator: S01E01 E02
    space_pattern = r"S\d+E(\d+)(?:\s+E(\d+))+"
    match = re.search(space_pattern, filename, re.IGNORECASE)
    if match:
        episode_markers = re.findall(r"E(\d+)", filename)
        if episode_markers:
            return [int(ep) for ep in episode_markers]

    # Special pattern for "S01 E01 E02" format
    spaced_season_pattern = r"S(\d+)\s+E(\d+)(?:\s+E(\d+))+"
    match = re.search(spaced_season_pattern, filename, re.IGNORECASE)
    if match:
        episode_markers = re.findall(r"E(\d+)", filename)
        if episode_markers:
            return [int(ep) for ep in episode_markers]

    # Text separators
    text_sep_pattern = r"S\d+E(\d+)(?:\s*(?:to|&|\+|,)\s*E(\d+))"
    match = re.search(text_sep_pattern, filename, re.IGNORECASE)
    if match:
        start_ep = int(match.group(1))
        end_ep = int(match.group(2))
        if "to" in filename:
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


def are_sequential(numbers: List[int]) -> bool:
    """Check if a list of integers is sequential.

    Args:
        numbers: List of integers to check

    Returns:
        True if numbers are sequential, False otherwise
    """
    if not numbers:
        return False
    if len(numbers) == 1:
        return True

    for i in range(1, len(numbers)):
        if numbers[i] != numbers[i - 1] + 1:
            return False
    return True


def format_multi_episode_filename(
    show_name: str,
    season: int,
    episode_numbers: List[int],
    title: str,
    file_extension: str,
    concatenated: bool = True,
    style: str = "spaces",
) -> str:
    """
    Format a multi-episode filename according to parameters.

    Args:
        show_name: The show name
        season: The season number
        episode_numbers: List of episode numbers
        title: The title/segments
        file_extension: The file extension (with leading dot)
        concatenated: Whether to use concatenated episode range (S01E01-E03) or separate (S01E01E02E03)
        style: Format style - "dots" for dots between words, "spaces" for spaces (default)

    Returns:
        Formatted filename
    """
    if not episode_numbers:
        raise ValueError("Episode numbers list cannot be empty")

    logger = logging.getLogger(__name__)
    logger.debug(f"Formatting multi-episode filename with style: {style}")
    logger.debug(f"Show: {show_name}, Season: {season}, Episodes: {episode_numbers}")
    logger.debug(f"Title: {title}, Extension: {file_extension}")

    # Sort episode numbers to ensure consistent formatting
    sorted_episodes = sorted(episode_numbers)

    # Format the show name based on style
    if style == "dots":
        # For dots style, replace spaces with dots, remove special chars
        sanitized_show = re.sub(r"[^\w\s]", "", show_name)  # Remove special chars except spaces
        sanitized_show = re.sub(r"\s+", ".", sanitized_show)  # Replace spaces with dots
    else:
        # For spaces style, keep spaces but remove/replace special chars
        sanitized_show = re.sub(r"[^\w\s]", " ", show_name)  # Replace special chars with spaces
        sanitized_show = re.sub(r"\s+", " ", sanitized_show)  # Normalize multiple spaces

    # Format episode numbers
    if concatenated and len(sorted_episodes) > 1:
        episode_part = f"S{season:02d}E{sorted_episodes[0]:02d}-E{sorted_episodes[-1]:02d}"
    else:
        episode_part = f"S{season:02d}E" + "E".join([f"{ep:02d}" for ep in sorted_episodes])

    # Format the title based on style
    title_segments = []
    if title:
        if isinstance(title, list):
            # If title is already a list of segments
            title_segments = title
        elif "&" in title:
            # If title contains & separators
            title_segments = [segment.strip() for segment in title.split("&")]
        else:
            # Single segment
            title_segments = [title]

    # Sanitize segment titles based on style
    sanitized_segments = []
    for segment in title_segments:
        if style == "dots":
            # For dots style, replace spaces with dots, remove special chars
            sanitized = re.sub(r"[^\w\s]", "", segment)  # Remove special chars except spaces
            sanitized = re.sub(r"\s+", ".", sanitized)  # Replace spaces with dots
            sanitized_segments.append(sanitized)
        else:
            # For spaces style, keep spaces but remove/replace special chars
            sanitized = re.sub(r"[^\w\s]", " ", segment)  # Replace special chars with spaces
            sanitized = re.sub(r"\s+", " ", sanitized)  # Normalize multiple spaces
            sanitized_segments.append(sanitized)

    # Join segments with appropriate separator
    if sanitized_segments:
        if style == "dots":
            segments_part = ".&.".join(sanitized_segments)
        else:
            segments_part = " & ".join(sanitized_segments)

        # Assemble the full filename
        if style == "dots":
            result = f"{sanitized_show}.{episode_part}.{segments_part}{file_extension}"
        else:
            result = f"{sanitized_show} {episode_part} {segments_part}{file_extension}"
    else:
        # No segments, just use show name and episode part
        if style == "dots":
            result = f"{sanitized_show}.{episode_part}{file_extension}"
        else:
            result = f"{sanitized_show} {episode_part}{file_extension}"

    logger.debug(f"Formatted filename: {result}")
    return result


def detect_special_episodes(filename: str) -> Optional[Dict[str, Union[str, int, None]]]:
    """
    Detect if a filename represents a special episode.

    Args:
        filename: The filename to analyze

    Returns:
        A dictionary with 'type' (special, ova, movie) and 'number' if found, None otherwise.
    """
    # Check for S00E pattern first (most reliable)
    season_pattern = r"S00E(\d+)"
    match = re.search(season_pattern, filename, re.IGNORECASE)
    if match:
        return {"type": "special", "number": int(match.group(1))}

    # Check for OVA.number pattern specifically
    ova_dot_pattern = r"OVA\.(\d+)"
    match = re.search(ova_dot_pattern, filename, re.IGNORECASE)
    if match:
        return {"type": "ova", "number": int(match.group(1))}

    # Check for Movie.number pattern specifically
    movie_dot_pattern = r"Movie\.(\d+)|Film\.(\d+)"
    match = re.search(movie_dot_pattern, filename, re.IGNORECASE)
    if match:
        number = None
        # Check which group matched (movie or film)
        if match.group(1):
            number = int(match.group(1))
        elif match.group(2):
            number = int(match.group(2))

        return {"type": "movie", "number": number}

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

            result: Dict[str, Union[str, int, None]] = {"type": special_type, "number": number}
            return result

    return None


def match_episode_titles(
    show_name: str, season_number: int, segment_titles: List[str]
) -> Dict[str, int]:
    """
    Match segment titles to episode numbers using TVDb API.

    Args:
        show_name: The name of the show
        season_number: The season number
        segment_titles: List of segment titles to match

    Returns:
        Dictionary mapping segment titles to episode numbers
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Matching segment titles with TVDb API: {segment_titles}")

    # Initialize the returned mapping
    title_to_episode_map = {}

    try:
        # Import here to avoid circular imports
        from plexomatic.api.tvdb_client import TVDBClient
        from plexomatic.config.config_manager import ConfigManager

        # Get API key from environment or config
        config = ConfigManager()
        api_key = os.environ.get("TVDB_API_KEY") or config.get("tvdb_api_key")

        if not api_key:
            logger.warning("No TVDB API key found in environment or config")
            return {}

        # Initialize TVDb client
        client = TVDBClient(api_key=api_key)

        # Search for the series
        search_results = client.get_series_by_name(show_name)
        if not search_results:
            logger.warning(f"No series found for '{show_name}'")
            return {}

        # Use the first result (most relevant)
        series_id = search_results[0].get("id")
        if not series_id:
            logger.warning("Series ID not found in search results")
            return {}

        # Get episodes for the season
        all_episodes = client.get_episodes_by_series_id(series_id)
        if not all_episodes:
            logger.warning(f"No episodes found for series {series_id}")
            return {}

        # Filter episodes for the specified season
        episodes = [ep for ep in all_episodes if ep.get("airedSeason") == season_number]
        if not episodes:
            logger.warning(f"No episodes found for series {series_id}, season {season_number}")
            return {}

        logger.debug(f"Found {len(episodes)} episodes for {show_name} Season {season_number}")

        # Create a mapping of normalized titles to episode numbers for fuzzy matching
        normalized_title_map = {}
        for episode in episodes:
            episode_title = episode.get("name", "")
            episode_number = episode.get("number")

            if episode_title and episode_number is not None:
                # Normalize the title for better matching
                normalized_title = episode_title.lower().strip()
                normalized_title_map[normalized_title] = episode_number

        # Match each segment title to the closest episode title
        for segment_title in segment_titles:
            normalized_segment = segment_title.lower().strip()

            # Try exact match first
            if normalized_segment in normalized_title_map:
                title_to_episode_map[segment_title] = normalized_title_map[normalized_segment]
                continue

            # Try fuzzy matching
            best_score = 0
            best_match = None

            for api_title, episode_number in normalized_title_map.items():
                # Skip titles that were already matched
                if episode_number in title_to_episode_map.values():
                    continue

                # Calculate similarity score
                score = difflib.SequenceMatcher(None, normalized_segment, api_title).ratio()

                # If it's a good enough match and better than previous matches
                if score > 0.8 and score > best_score:
                    best_score = score
                    best_match = (api_title, episode_number)

            # If we found a good match, use it
            if best_match:
                title_to_episode_map[segment_title] = best_match[1]
                logger.debug(
                    f"Matched '{segment_title}' to '{best_match[0]}' (E{best_match[1]}) with score {best_score:.2f}"
                )

    except Exception as e:
        logger.error(f"Error matching episode titles: {e}")
        if logger.level == logging.DEBUG:
            logger.exception(e)

    # Return the mapping, which may be empty if no matches were found
    return title_to_episode_map


def preprocess_anthology_episodes(
    file_path: str,
    use_llm: bool = False,
    api_lookup: bool = False,
    season_type: str = "Aired Order",
) -> List[Dict[str, Any]]:
    """Preprocess anthology episodes to detect segments and match with API info.

    Args:
        file_path: Path to the anthology episode file.
        use_llm: Whether to use LLM to detect segments.
        api_lookup: Whether to use API to look up episodes.
        season_type: Season type to use when fetching episodes from TVDB.

    Returns:
        A list of episode information dictionaries.
    """
    logger = logging.getLogger(__name__)

    # Check if file exists
    if not os.path.exists(file_path):
        logger.error(f"File doesn't exist: {file_path}")
        return []

    # Get basename
    basename = os.path.basename(file_path)

    # Extract show information
    logger.debug(f"Processing file: {file_path}")
    logger.debug("Anthology mode: True")
    logger.debug(f"LLM assistance: {use_llm}")
    logger.debug(f"API lookup: {api_lookup}")

    # Extract basic info from filename
    logger.debug(f"Extracting info from basename: {basename}")
    extracted_info = extract_show_info(basename)

    if not extracted_info:
        logger.debug(f"Could not extract info from {basename}")
        return []

    # Get show name and season
    show_name = extracted_info.get("show_name")
    season = extracted_info.get("season")

    if not show_name or season is None:
        logger.debug(f"Missing required show info in {basename}")
        return []

    # Detect segments in the file
    logger.debug(f"Detecting segments in: {basename}")
    logger.debug(f"Using LLM: {use_llm}")

    # Extract segments using various methods
    segments = detect_segments(basename, use_llm=use_llm)

    if not segments:
        logger.warning(f"No segments detected in {basename}")
        return []

    logger.info(f"Detected {len(segments)} segments in {basename}")

    # Get episode data from API if requested
    api_episodes = []
    if api_lookup:
        try:
            # Get episodes from the API
            api_episode_data = fetch_episodes_from_tvdb(show_name, season, season_type)
            logger.debug(
                f"Fetched {len(api_episode_data) if api_episode_data else 0} episodes from API"
            )

            # If segments count matches episode count, we can assign titles
            if api_episode_data and len(segments) <= len(api_episode_data):
                # Assign API info to segments
                api_episodes = api_episode_data[: len(segments)]
            else:
                logger.debug(
                    f"Segment count mismatch: {len(segments)} segments vs {len(api_episode_data)} API episodes"
                )
        except Exception as e:
            logger.error(f"Error looking up episodes: {e}")

    # Prepare result
    result = []

    for i, segment in enumerate(segments):
        episode_info = {
            "show_name": show_name,
            "season": season,
            "episode": i + 1,  # Assume sequential episodes
            "title": segment,
            "is_anthology_segment": True,
        }

        # Add API info if available
        if i < len(api_episodes):
            api_episode = api_episodes[i]
            episode_info["episode"] = api_episode.get("episodeNumber", i + 1)
            episode_info["title"] = api_episode.get("name", segment)
            episode_info["api_matched"] = True

        result.append(episode_info)

    return result


def process_anthology_episode(
    filename: str,
    anthology_mode: bool = False,
    use_llm: bool = False,
    api_lookup: bool = False,
    preprocessed_data: Optional[Dict[str, Dict[str, Any]]] = None,
    season_type: str = "Aired Order",
) -> Dict[str, Any]:
    """
    Process a file as a potential anthology episode with multiple segments.

    Args:
        filename: The filename to process
        anthology_mode: Whether to enable anthology mode
        use_llm: Whether to use LLM assistance for detection
        api_lookup: Whether to use API lookup for episode numbers
        preprocessed_data: Optional preprocessed data from preprocess_anthology_episodes
        season_type: Season type to use when fetching episodes from TVDB

    Returns:
        Dictionary with episode numbers and segment information
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Processing file: {filename}")
    logger.debug(f"Anthology mode: {anthology_mode}")
    logger.debug(f"LLM assistance: {use_llm}")
    logger.debug(f"API lookup: {api_lookup}")

    # If we have preprocessed data for this file, use it
    if preprocessed_data and filename in preprocessed_data:
        logger.debug(f"Using preprocessed data for {filename}")
        return preprocessed_data[filename]

    # Extract show information
    info = extract_show_info(filename)

    # Get show name, season and episode numbers
    show_name = info.get("show_name", "")
    season = info.get("season")
    episode = info.get("episode")

    if not all([show_name, season is not None, episode is not None]):
        logger.warning(f"Missing required information from {filename}")
        return None

    logger.debug(f"Extracted info: show={show_name}, season={season}, episode={episode}")

    # If not in anthology mode, just return basic info
    if not anthology_mode:
        return {
            "episode_numbers": [episode],
            "show_name": show_name,
            "season": season,
            "is_anthology": False,
        }

    # API data to provide context to the LLM
    api_episode_data = None

    # If API lookup is enabled, fetch episode data first
    if api_lookup and show_name and season is not None:
        try:
            # Get episodes from the API
            api_episode_data = fetch_episodes_from_tvdb(show_name, season, season_type)
            logger.debug(
                f"Fetched {len(api_episode_data) if api_episode_data else 0} episodes from API"
            )
        except Exception as e:
            logger.warning(f"Error fetching API data: {e}")

    # For anthology episodes, detect segments with API context if available
    segments = detect_segments(filename, use_llm, api_episode_data)

    # If no segments were detected, create a single segment from the title
    if not segments:
        title = info.get("title", "")
        if title:
            segments = [title]
        else:
            # If we can't get segments or a title, just use the base episode number
            return {
                "episode_numbers": [episode],
                "show_name": show_name,
                "season": season,
                "is_anthology": False,
            }

    logger.debug(f"Detected {len(segments)} segments: {segments}")

    # Episode numbers mapping - dictionary mapping segment index to episode number
    episodes_map = {}

    # If API lookup is enabled and we have data, try to match segment titles to episode numbers
    if api_lookup and api_episode_data:
        title_to_episode_map = match_episode_titles_with_data(segments, api_episode_data)

        # If we got some matches from the API, use them
        if title_to_episode_map:
            logger.debug(f"API matched {len(title_to_episode_map)} segments to episode numbers")

            # Create episode map using API data
            for i, segment in enumerate(segments):
                if segment in title_to_episode_map:
                    episodes_map[i + 1] = title_to_episode_map[segment]

            # If we mapped all segments, we're done
            if len(episodes_map) == len(segments):
                episode_numbers = [episodes_map[i + 1] for i in range(len(segments))]

                logger.debug(f"Using API episode numbers for anthology segments: {episode_numbers}")

                return {
                    "episode_numbers": episode_numbers,
                    "segments": segments,
                    "segment_map": {episodes_map[i + 1]: segments[i] for i in range(len(segments))},
                    "show_name": show_name,
                    "season": season,
                    "is_anthology": True,
                }

    # If API lookup failed or is disabled, we use the episode number from the file
    # as a fallback, but in a production scenario, you should prioritize preprocessing
    logger.debug("Using sequential numbering for anthology segments")

    # Start from the episode number in the filename and assign
    # sequential numbers to each segment
    episode_numbers = []
    for i in range(len(segments)):
        episode_numbers.append(episode + i)

    # Create segment mapping (episode number -> segment title)
    segment_map = {episode_numbers[i]: segments[i] for i in range(len(segments))}

    logger.debug(f"Processed anthology episode with numbers: {episode_numbers}")

    return {
        "episode_numbers": episode_numbers,
        "segments": segments,
        "segment_map": segment_map,
        "show_name": show_name,
        "season": season,
        "is_anthology": True,
    }


def detect_segments(
    file_path: str, use_llm: bool = False, max_segments: int = 10
) -> Optional[List[str]]:
    """Attempt to detect segments in a file.

    Args:
        file_path: Path to the file
        use_llm: Whether to use LLM for detection
        max_segments: Maximum number of segments to detect

    Returns:
        List of segment titles or None if no segments detected
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Detecting segments in: {file_path}")
    logger.debug(f"Using LLM: {use_llm}")

    # Extract info from file name to use in LLM context
    parsed_info = extract_show_info(file_path)
    show_name = parsed_info.get("show_name", os.path.basename(file_path))
    
    logger.debug(f"Extracted info from basename: {os.path.basename(file_path)}")
    if parsed_info:
        info_str = ', '.join([f"{k}={v}" for k, v in parsed_info.items() if v])
        logger.debug(f"Matched pattern, extracted: {info_str}")

    if not use_llm:
        logger.debug("LLM assistance disabled, skipping segment detection")
        return None

    # First try to load segments from cache
    cache_dir = os.path.join(os.path.expanduser("~"), ".plexomatic", "cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    cache_file = os.path.join(
        cache_dir, f"segments_{hashlib.md5(file_path.encode()).hexdigest()}.json"
    )
    
    # Check for cached segments
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                segments = json.load(f)
                # Filter out thinking tags and other artifacts
                segments = [s for s in segments 
                          if len(s) > 1 
                          and "<think>" not in s.lower() 
                          and "</think>" not in s.lower()
                          and "summary" not in s.lower() 
                          and "approach" not in s.lower()
                          and "confirm" not in s.lower() 
                          and not s.startswith("In ")
                          and "format" not in s.lower()
                          and "episode" not in s.lower()]
                if segments:
                    logger.debug(f"Loaded {len(segments)} valid segments from cache: {segments}")
                    return segments
                else:
                    logger.debug("No valid segments found in cache, will regenerate")
        except Exception as e:
            logger.warning(f"Error loading segment cache: {e}")

    try:
        # If we get here, we need to use LLM
        logger.info(f"Using LLM to detect segments in: {os.path.basename(file_path)}")
        
        # Create a client for the LLM
        from plexomatic.api.llm_client import LLMClient

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
        
        logger.debug(f"Sending prompt to LLM: {prompt}")
        
        # Get response from LLM
        response = llm_client.generate_text(prompt).strip()
        
        logger.debug(f"LLM response: {response}")
        
        # Process the response
        if not response or "." in response and len(response) < 10:
            logger.warning(f"No valid segments returned from LLM for {file_path}")
            return None
        
        # Remove thinking process if present
        cleaned_response = response
        if "<think>" in response.lower() and "</think>" in response.lower():
            logger.debug("Found <think> tags in LLM response, removing thinking process")
            try:
                start_index = response.lower().find("<think>")
                end_index = response.lower().find("</think>") + 8
                
                # Extract content before thinking and after thinking
                before_thinking = response[:start_index].strip()
                after_thinking = response[end_index:].strip()
                
                # Combine parts, skipping the thinking section
                cleaned_response = (before_thinking + " " + after_thinking).strip()
                logger.debug(f"Response after removing thinking tags: {cleaned_response}")
            except Exception as e:
                logger.warning(f"Error removing thinking tags: {e}")
            
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
        
        # Filter out non-segment lines and thinking process artifacts
        segments = [s for s in segments if len(s) > 1 
                    and "<think>" not in s.lower() 
                    and "</think>" not in s.lower()
                    and "segment" not in s.lower() 
                    and "summary" not in s.lower() 
                    and "approach" not in s.lower()
                    and "confirm" not in s.lower() 
                    and not s.startswith("In ")
                    and "format" not in s.lower()
                    and "episode" not in s.lower()]
        
        if "unknown" in cleaned_response.lower() and len(segments) == 0:
            # If the model responded with unknown but our filtering removed it,
            # add it back based on common anthology format (3 segments)
            segments = ["Unknown 1", "Unknown 2", "Unknown 3"]
            logger.debug("Added generic unknown segments based on LLM response")
            
        if not segments:
            logger.warning(f"No segments detected in {os.path.basename(file_path)} after processing LLM response")
            return None
            
        # Limit number of segments
        segments = segments[:max_segments]
        
        logger.info(f"Detected {len(segments)} segments: {segments}")
        
        # Cache the results
        try:
            with open(cache_file, "w") as f:
                json.dump(segments, f)
        except Exception as e:
            logger.warning(f"Error caching segments: {e}")
            
        return segments
        
    except Exception as e:
        logger.error(f"Error detecting segments with LLM: {e}")
        return None


def get_show_id(show_name: str) -> Optional[str]:
    """Get the show ID from the show name using Plex or TVDB API.

    Args:
        show_name: The name of the show

    Returns:
        The show ID or None if not found
    """
    # This is a stub function that should be implemented to call your media API
    # For now, mock with a fixed ID for testing
    logger = logging.getLogger(__name__)
    logger.debug(f"Looking up show ID for: {show_name}")

    # In a real implementation, this would make an API call
    # For now, return a mock ID for testing
    known_shows = {
        "chip n dale park life": "12345",
        "ducktales": "67890",
        # Add more known shows as needed
    }

    # Normalize the show name for lookup
    normalized_name = show_name.lower().strip()

    # Check if we have a fixed ID for this show
    if normalized_name in known_shows:
        logger.debug(f"Found ID {known_shows[normalized_name]} for show {show_name}")
        return known_shows[normalized_name]

    logger.debug(f"No show ID found for {show_name}")
    return None


def organize_season_pack(files: List[Path]) -> Dict[str, List[Path]]:
    """
    Organize files from a season pack into appropriate season folders.

    Args:
        files: List of file paths to organize

    Returns:
        Dictionary with season folder names as keys and lists of files as values
    """
    result: Dict[str, List[Path]] = {"Specials": [], "Unknown": []}

    for file in files:
        filename = file.name

        # Check if it's a special episode
        special_info = detect_special_episodes(filename)
        if special_info:
            result["Specials"].append(file)
            continue

        # Direct pattern matching for TV shows
        tv_pattern = re.compile(r"[sS](?P<season>\d{1,2})[eE](?P<episode>\d{1,2})")
        tv_match = tv_pattern.search(filename)

        if tv_match:
            season = int(tv_match.group("season"))
            season_folder = f"Season {season}"

            # Create the season entry if it doesn't exist
            if season_folder not in result:
                result[season_folder] = []

            result[season_folder].append(file)
        else:
            # Files we couldn't categorize
            result["Unknown"].append(file)

    return result


def generate_filename_from_metadata(original_filename: str, metadata: Dict[str, Any]) -> str:
    """
    Generate a standardized filename based on metadata and episode information.

    This function handles different types of episodes:
    - Regular episodes
    - Special episodes (season 0)
    - Multi-episodes
    - Anthology episodes

    Args:
        original_filename: The original filename
        metadata: The metadata dictionary containing show information

    Returns:
        A standardized filename
    """
    # Get the file extension
    extension = Path(original_filename).suffix

    # Extract basic show information
    show_name = metadata.get("title", "Unknown")

    # Handle special episodes
    if "special_type" in metadata:
        # Get the special number or default to 1
        special_number = metadata.get("special_number", 1)

        # Get the special title if available
        special_title = None
        if "special_episode" in metadata and "title" in metadata["special_episode"]:
            special_title = metadata["special_episode"]["title"]
        else:
            # Generate a title based on the special type
            special_type = metadata["special_type"].capitalize()
            special_title = f"{special_type} {special_number}" if special_number else special_type

        # Generate a special episode filename (use season 0 for specials)
        return format_multi_episode_filename(
            show_name=show_name,
            season=0,
            episode_numbers=[special_number],
            title=special_title,
            file_extension=extension,
        )

    # Check for anthology mode
    anthology_mode = metadata.get("anthology_mode", False)

    # Process anthology episodes
    if anthology_mode and "original_title" in metadata:
        # Use process_anthology_episode to extract the segments and episode numbers
        anthology_result = process_anthology_episode(
            metadata["original_title"], anthology_mode=True
        )

        episodes = anthology_result["episode_numbers"]
        segments = anthology_result["segments"]

        # Generate the title based on segments
        title = None
        if segments:
            # Join segments with ampersands
            title = " & ".join(segments)

        # Generate a multi-episode filename
        return format_multi_episode_filename(
            show_name=show_name,
            season=metadata.get("season", 1),
            episode_numbers=episodes,
            title=title,
            file_extension=extension,
        )

    # Handle multi-episodes
    elif "episode_numbers" in metadata:
        episodes = metadata["episode_numbers"]
        season = metadata.get("season", 1)

        # Get the episode title
        title = None
        if "multi_episodes" in metadata and metadata["multi_episodes"]:
            # Use the first episode's title or join multiple titles
            if len(metadata["multi_episodes"]) == 1:
                title = metadata["multi_episodes"][0].get("title")
            else:
                # Join the episode titles if available
                titles = [ep.get("title") for ep in metadata["multi_episodes"] if ep.get("title")]
                if titles:
                    title = " & ".join(titles)

        # Generate a multi-episode filename
        return format_multi_episode_filename(
            show_name=show_name,
            season=season,
            episode_numbers=episodes,
            title=title,
            file_extension=extension,
        )

    # Handle regular episodes
    else:
        season = metadata.get("season", 1)
        episode = metadata.get("episode", 1)
        title = metadata.get("episode_title")

        return format_multi_episode_filename(
            show_name=show_name,
            season=season,
            episode_numbers=[episode],
            title=title,
            file_extension=extension,
        )


def format_episode_filename(filename: str, use_dots: bool = True) -> str:
    """Format a single episode filename according to naming convention.

    Args:
        filename: The original filename
        use_dots: Whether to use dots instead of spaces

    Returns:
        A formatted filename
    """
    # Extract basic information
    show_info = extract_show_info(filename)
    if not show_info:
        # If we can't extract info, return the original filename
        return filename

    # Get show name and episode details
    show_name = show_info.get("show_name")
    season = show_info.get("season")
    episode = show_info.get("episode")
    title = show_info.get("title")

    if not show_name or not season or not episode:
        # If we're missing essential info, return the original filename
        return filename

    # Convert to proper types
    try:
        season_num = int(season)
        episode_num = int(episode)
    except (ValueError, TypeError):
        # If conversion fails, return original filename
        return filename

    # Get the file extension
    file_ext = Path(filename).suffix

    # Format using the multi-episode formatter with a single episode
    style = "dot" if use_dots else "space"
    return format_multi_episode_filename(
        show_name=show_name,
        season=season_num,
        episode_numbers=[episode_num],
        title=title,
        file_extension=file_ext,
        style=style,
    )


def is_tv_show(filename: str) -> bool:
    """Check if a filename appears to be a TV show.

    Args:
        filename: The filename to check

    Returns:
        True if it's likely a TV show, False otherwise
    """
    # Basic pattern for TV shows: Show.S01E01.Title.ext or similar
    tv_pattern = re.compile(r".*?[. _-]*[sS](\d{1,2})[eE](\d{1,2})(?:[eE]\d{1,2})*.*?(?:\.\w+)?$")

    # Check if the filename matches the TV show pattern
    return bool(tv_pattern.search(filename))


def split_title_by_separators(title: str) -> List[str]:
    """
    Split a title into segments using common separators.

    Args:
        title: The title to split

    Returns:
        List of segments
    """
    if not title:
        return []

    # Check for explicit segment separators
    if " & " in title:
        return [s.strip() for s in title.split(" & ")]
    elif ", " in title:
        return [s.strip() for s in title.split(", ")]
    elif " + " in title:
        return [s.strip() for s in title.split(" + ")]
    elif " - " in title:
        return [s.strip() for s in title.split(" - ")]
    elif " and " in title:
        return [s.strip() for s in title.split(" and ")]

    # Check for capitalization patterns
    words = title.split()
    if len(words) > 6:  # Only try this for longer titles
        segments = []
        current_segment = []

        for i, word in enumerate(words):
            current_segment.append(word)

            # Check if this might be the end of a segment
            if i > 0 and i < len(words) - 1:
                next_word = words[i + 1]
                # If next word starts with capital and current segment is at least 2 words
                if next_word[0].isupper() and len(current_segment) >= 2:
                    segments.append(" ".join(current_segment))
                    current_segment = []

        # Add the last segment if not empty
        if current_segment:
            segments.append(" ".join(current_segment))

        # If we found multiple segments, return them
        if len(segments) > 1:
            return segments

    # No segments found, return the whole title
    return [title]


def fetch_episodes_from_tvdb(
    show_name: str, season: int = 1, season_type: str = "Aired Order"
) -> List[Dict[str, Any]]:
    """Fetch episode data from TVDB API.

    Args:
        show_name: The name of the TV show.
        season: The season number to fetch.
        season_type: The season type to use when fetching episodes.

    Returns:
        A list of episode dictionaries, or an empty list if none found.
    """
    logger = logging.getLogger(__name__)
    logger.info(
        f"Fetching episodes from TVDB for '{show_name}', season {season}, type '{season_type}'"
    )

    try:
        from plexomatic.api.tvdb_client import TVDBClient, TVDBAuthenticationError

        # Create and authenticate client
        client = TVDBClient()
        logger.debug(f"Authenticating with TVDB API for show: {show_name}")
        try:
            client.authenticate()
            logger.debug("Successfully authenticated with TVDB API")
        except TVDBAuthenticationError as e:
            logger.error(f"TVDB authentication failed: {e}")
            logger.warning(
                "For TVDb v4 API, you may need to provide both API key and subscriber PIN."
            )
            return []
        except Exception as e:
            logger.error(f"Unexpected error during TVDB authentication: {e}")
            return []

        # Try different search strategies if necessary
        series_list = []
        search_attempts = [
            (show_name, "original name"),
            (show_name.replace("'", ""), "removed apostrophes"),
            (
                show_name.replace("n", "'n"),
                "added apostrophe",
            ),  # For cases like "Chip n Dale" -> "Chip 'n Dale"
        ]

        # If name has "and", try with "&" instead
        if " and " in show_name.lower():
            search_attempts.append(
                (show_name.lower().replace(" and ", " & "), "replaced 'and' with '&'")
            )

        # If name has colon, try without the subtitle
        if ":" in show_name:
            main_title = show_name.split(":", 1)[0].strip()
            search_attempts.append((main_title, "main title only"))

        # Try each search strategy in order
        for search_term, strategy in search_attempts:
            if series_list:
                break  # Stop if we already found results

            logger.debug(f"Searching for '{search_term}' ({strategy})")
            series_list = client.get_series_by_name(search_term)

            if series_list:
                logger.info(f"Found {len(series_list)} results using '{strategy}' strategy")
            else:
                logger.debug(f"No results found using '{strategy}' strategy")

        if not series_list:
            logger.warning(
                f"No series found for '{show_name}' after trying multiple search strategies"
            )
            return []

        # Get the series ID from the first result
        series = series_list[0]
        series_id = series.get("id")
        series_name = series.get("name", "Unknown")

        if not series_id:
            logger.warning(f"No series ID found in the first result for '{show_name}'")
            return []

        logger.info(f"Selected series: '{series_name}' (ID: {series_id})")

        # Get episodes for the series
        logger.debug(
            f"Fetching episodes for series ID {series_id}, season {season}, type '{season_type}'"
        )

        # Try to fetch episodes for the specific season directly first
        try:
            season_episodes = client.get_season_episodes(series_id, season, season_type)
            if season_episodes:
                logger.info(
                    f"Successfully retrieved {len(season_episodes)} episodes using season_episodes method"
                )
                return season_episodes
            else:
                logger.warning(
                    f"No episodes found for '{series_name}' season {season} using direct season lookup"
                )
        except Exception as e:
            logger.warning(f"Error using get_season_episodes: {e}")

        # If we get here, try the extended series method for more info about available seasons
        try:
            series_extended = client.get_series_extended(series_id)
            seasons = series_extended.get("seasons", [])
            season_numbers = [s.get("number") for s in seasons if "number" in s]

            if seasons:
                logger.info(f"Available seasons for '{series_name}': {sorted(season_numbers)}")

                # If season 1 was requested but not found, check if season 0 exists (specials)
                if season == 1 and season not in season_numbers and 0 in season_numbers:
                    logger.info(
                        "Season 1 not found, but found season 0 (Specials). Trying that instead."
                    )
                    special_episodes = client.get_season_episodes(series_id, 0, season_type)
                    if special_episodes:
                        logger.info(
                            f"Found {len(special_episodes)} episodes in season 0 (Specials)"
                        )
                        return special_episodes
            else:
                logger.warning(f"No seasons found in extended series data for '{series_name}'")
        except Exception as e:
            logger.warning(f"Error fetching extended series data: {e}")

        # Fall back to fetching all episodes and filtering
        logger.debug("Falling back to get_episodes_by_series_id and filtering")
        try:
            all_episodes = client.get_episodes_by_series_id(series_id)

            if not all_episodes:
                logger.warning(
                    f"No episodes found for '{series_name}' using get_episodes_by_series_id"
                )
                return []

            logger.info(f"Retrieved {len(all_episodes)} total episodes for '{series_name}'")

            # Count episodes by season for debugging
            season_counts = {}
            for ep in all_episodes:
                ep_season = ep.get("seasonNumber") or ep.get("airedSeason")
                if ep_season is not None:
                    season_counts[ep_season] = season_counts.get(ep_season, 0) + 1

            logger.debug(f"Episode count by season: {season_counts}")

            # Filter episodes for the given season
            season_episodes = [
                episode
                for episode in all_episodes
                if (episode.get("seasonNumber") == season or episode.get("airedSeason") == season)
            ]

            if season_episodes:
                logger.info(
                    f"Found {len(season_episodes)} episodes for '{series_name}' season {season} after filtering"
                )
                return season_episodes
            else:
                logger.warning(
                    f"No episodes found for '{series_name}' season {season} after filtering"
                )
                return []

        except Exception as e:
            logger.error(f"Error fetching all episodes: {e}")
            return []

    except TVDBAuthenticationError as e:
        logger.error(f"TVDB authentication failed: {e}")
        logger.warning("For TVDb v4 API, you may need to provide both API key and subscriber PIN.")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching episodes from TVDB: {e}")
        return []


def match_episode_titles_with_data(
    segments: List[str], episode_data: List[Dict[str, Any]]
) -> Dict[str, int]:
    """
    Match segment titles with episode data from the API.

    Args:
        segments: List of segment titles
        episode_data: List of episode data dictionaries from the API

    Returns:
        Dictionary mapping segment titles to episode numbers
    """
    logger = logging.getLogger(__name__)

    if not segments or not episode_data:
        return {}

    # Create a dictionary of episode names to numbers
    episode_names_to_numbers = {}
    for episode in episode_data:
        name = episode.get("name", "")
        number = episode.get("episode_number")

        if name and number is not None:
            episode_names_to_numbers[name.lower()] = number

    logger.debug(f"API episode data: {episode_names_to_numbers}")

    # Try to match segment titles to episode names
    segment_to_episode = {}

    for segment in segments:
        if not segment:
            continue

        # First try exact match
        segment_lower = segment.lower()
        if segment_lower in episode_names_to_numbers:
            segment_to_episode[segment] = episode_names_to_numbers[segment_lower]
            continue

        # Try substring match (episode title contains segment or vice versa)
        best_match = None
        best_similarity = 0

        for episode_name, episode_number in episode_names_to_numbers.items():
            # Check if episode name contains segment or vice versa
            if segment_lower in episode_name or episode_name in segment_lower:
                # Calculate similarity (longer common substring = better match)
                similarity = len(set(segment_lower.split()) & set(episode_name.split()))

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = (episode_name, episode_number)

        # If we found a good match, use it
        if best_match and best_similarity > 0:
            logger.debug(
                f"Matched '{segment}' to episode '{best_match[0]}' with similarity {best_similarity}"
            )
            segment_to_episode[segment] = best_match[1]

    logger.debug(f"Matched {len(segment_to_episode)} segments to episodes: {segment_to_episode}")
    return segment_to_episode


def rename_tv_show_episodes(
    file_path: str,
    use_dots: bool = False,
    api_lookup: bool = False,
    preview_mode: bool = False,
    season_type: str = "Aired Order",
) -> Optional[Dict[str, Any]]:
    """Rename TV show episodes with proper formatting.

    Args:
        file_path: Path to the file to rename
        use_dots: Whether to use dots instead of spaces in filenames
        api_lookup: Whether to look up episode information via API
        preview_mode: Whether to just preview the change
        season_type: Season type to use when fetching episodes from TVDB

    Returns:
        A dictionary containing original and new paths, or None
    """
    logger = logging.getLogger(__name__)

    # Verify this is a media file
    if not os.path.exists(file_path):
        logger.warning(f"File does not exist: {file_path}")
        return None

    # Check if this is a media file by extension
    _, ext = os.path.splitext(file_path)
    media_extensions = [".mp4", ".mkv", ".avi", ".mov", ".m4v"]
    if ext.lower() not in media_extensions:
        logger.debug(f"File is not a media file: {file_path}")
        return None

    # Define a function to check if a file is a media file
    def is_media_file(path: str) -> bool:
        _, extension = os.path.splitext(path)
        return extension.lower() in media_extensions

    # Extract show information from filename
    logger.debug(f"Extracting info from basename: {os.path.basename(file_path)}")
    extracted_info = extract_show_info(os.path.basename(file_path))

    if not extracted_info:
        logger.debug(f"Could not extract show info from {os.path.basename(file_path)}")
        return None

    show_name = extracted_info.get("show_name")
    season = extracted_info.get("season")
    episode = extracted_info.get("episode")

    if not show_name or season is None or episode is None:
        logger.debug(f"Missing required show info in {os.path.basename(file_path)}")
        return None

    # Look up episode title from API if enabled
    title = extracted_info.get("title", "")

    if api_lookup and is_tv_show(os.path.basename(file_path)):
        logger.debug(f"Looking up episode info from API for {show_name} S{season}E{episode}")
        try:
            # Fetch episodes from TVDB
            episodes = fetch_episodes_from_tvdb(show_name, season, season_type)

            # Find the matching episode
            matching_episode = next(
                (
                    ep
                    for ep in episodes
                    if ep.get("episodeNumber") == episode or ep.get("airedEpisodeNumber") == episode
                ),
                None,
            )

            if matching_episode:
                # Get episode title
                api_title = matching_episode.get("name")
                if api_title:
                    title = api_title
                    logger.debug(f"Using API title: {title}")
                else:
                    logger.debug("No title found in API data")
            else:
                logger.debug(f"No matching episode found for S{season}E{episode}")
        except Exception as e:
            logger.error(f"Error looking up episode info: {e}")

    # Update the extracted info with title from API
    extracted_info["title"] = title

    # Format the new filename
    logger.debug(f"Formatting new name for: {os.path.basename(file_path)}")
    logger.debug(f"Info: {extracted_info}")
    logger.debug(f"Preview mode: {preview_mode}")
    logger.debug(f"Use dots: {use_dots}")
    logger.debug("Is anthology: False")  # This function only handles regular episodes

    # Call format_new_name with the extracted info
    from plexomatic.utils.name_utils import format_new_name as name_utils_format_new_name

    new_name = name_utils_format_new_name(
        path=os.path.basename(file_path),
        info=extracted_info,
        is_preview=preview_mode,
        use_dots=use_dots,
    )
    dir_path = os.path.dirname(file_path)
    new_path = os.path.join(dir_path, new_name)

    # Check if the file already has the correct name
    if os.path.basename(file_path) == new_name:
        logger.debug(f"File already has correct name: {os.path.basename(file_path)}")
        return None

    # If preview mode, just return the info
    if preview_mode:
        return {
            "original_path": file_path,
            "new_path": new_path,
            "show_info": {
                "show_name": show_name,
                "season": season,
                "episode": episode,
                "title": title,
                "is_anthology": False,
            },
        }

    # Perform the rename
    try:
        os.rename(file_path, new_path)
        logger.info(f"Renamed {os.path.basename(file_path)} to {new_name}")
        return {
            "original_path": file_path,
            "new_path": new_path,
            "show_info": {
                "show_name": show_name,
                "season": season,
                "episode": episode,
                "title": title,
                "is_anthology": False,
            },
        }
    except Exception as e:
        logger.error(f"Failed to rename {file_path}: {e}")
        return None


def process_anthology_episodes(
    files: List[str],
    use_llm: bool = False,
    api_lookup: bool = False,
    season_type: str = "Aired Order",
) -> Dict[str, Dict[str, Any]]:
    """Process anthology episode files to extract segment info.

    Args:
        files: List of file paths to process.
        use_llm: Whether to use LLM for segment detection.
        api_lookup: Whether to use API lookup for episode data.
        season_type: Season type to use when fetching episodes from TVDB.

    Returns:
        Dictionary mapping file paths to their processed information.
    """
    logger = logging.getLogger(__name__)

    result = {}
    for file_path in files:
        logger.debug(f"Processing anthology file: {file_path}")

        if not os.path.exists(file_path):
            logger.error(f"File doesn't exist: {file_path}")
            continue

        basename = os.path.basename(file_path)

        # Extract show info from filename
        logger.debug(f"Extracting info from basename: {basename}")
        info = extract_show_info(basename)

        if not info:
            logger.debug(f"Could not extract info from {basename}")
            continue

        show_name = info.get("show_name")
        season = info.get("season")

        if not show_name or season is None:
            logger.debug(f"Missing required show info in {basename}")
            continue

        # Detect segments in the file
        logger.debug(f"Detecting segments in: {basename}")
        segments = detect_segments(basename, use_llm=use_llm)

        if not segments:
            logger.warning(f"No segments detected in {basename}")
            continue

        logger.info(f"Detected {len(segments)} segments in {basename}")

        # Initialize episode info
        episode_info = {
            "show_name": show_name,
            "season": season,
            "is_anthology": True,
            "episode_numbers": [],
            "segments": segments,
        }

        # Try to get episode data from API
        segment_to_episode = {}
        if api_lookup:
            try:
                # Get episodes from the API
                api_episode_data = fetch_episodes_from_tvdb(show_name, season, season_type)
                logger.debug(
                    f"Fetched {len(api_episode_data) if api_episode_data else 0} episodes from API"
                )

                # If we have the same number of segments as episodes, map them directly
                if len(segments) <= len(api_episode_data):
                    for i, segment in enumerate(segments):
                        if i < len(api_episode_data):
                            api_episode = api_episode_data[i]
                            episode_num = api_episode.get("episodeNumber", i + 1)
                            episode_info["episode_numbers"].append(episode_num)
                            segment_to_episode[segment] = api_episode

                            # Log the mapping
                            logger.debug(f"Mapped segment '{segment}' to episode {episode_num}")
                else:
                    # Just use sequential numbering
                    episode_info["episode_numbers"] = list(range(1, len(segments) + 1))
                    logger.debug(
                        f"Using sequential episode numbers: {episode_info['episode_numbers']}"
                    )
            except Exception as e:
                logger.error(f"Error getting episode data: {e}")
                # Use sequential numbering as fallback
                episode_info["episode_numbers"] = list(range(1, len(segments) + 1))
        else:
            # Use sequential numbering if not using API
            episode_info["episode_numbers"] = list(range(1, len(segments) + 1))

        # Store the result
        result[file_path] = episode_info

    logger.debug(f"Processed {len(result)} anthology episode files")
    logger.debug(f"Matched {len(segment_to_episode)} segments to episodes: {segment_to_episode}")
    return result


def format_new_name(
    show_name: str,
    season: Optional[int],
    episode: Optional[int],
    title: Optional[str] = None,
    use_dots: bool = False,
) -> str:
    """Format a new filename for a TV show episode.

    Args:
        show_name: The show name
        season: The season number
        episode: The episode number
        title: Optional episode title
        use_dots: Whether to use dots instead of spaces

    Returns:
        Formatted filename
    """
    # Use the format_multi_episode_filename function from name_utils
    from plexomatic.utils.name_utils import format_multi_episode_filename

    # Ensure title is not None for the function call
    safe_title = title or ""

    # Make sure season is not None
    safe_season = season if season is not None else 1

    # Make sure episode is not None
    safe_episode = episode if episode is not None else 1

    # Get file extension
    file_extension = ".mp4"  # Default extension

    # Format the episode filename with the given parameters
    return format_multi_episode_filename(
        show_name=show_name,
        season=safe_season,
        episode_numbers=[safe_episode],
        title=safe_title,
        file_extension=file_extension,
        style="dots" if use_dots else "spaces",
    )
