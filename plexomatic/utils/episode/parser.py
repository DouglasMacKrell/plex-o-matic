"""Functions for parsing episode information from filenames."""

import re
import os
import logging

try:
    # Python 3.9+ has native support for these types
    from typing import Dict, List, Optional, Union, Any
except ImportError:
    # For Python 3.8 support
    from typing_extensions import Dict, List, Optional, Union, Any

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
    (r"Special(?:s)?(?:\s*(\d+)|\.(\d+))?", "special"),
    # OVA keyword (Original Video Animation, common in anime)
    (r"OVA(?:\s*(\d+))?", "ova"),
    # OVA with number after dot
    (r"OVA\.(\d+)", "ova"),
    # Movie/Film specials with number
    (r"Movie\.(\d+)|Film\.(\d+)", "movie"),
    # Movie/Film specials general
    (r"Movie(?:\s*(\d+))?|Film(?:\s*(\d+))?", "movie"),
]


def extract_show_info(filename: str) -> Optional[Dict[str, Any]]:
    """
    Extract show information from a filename.

    Args:
        filename: The filename to extract information from

    Returns:
        Dictionary with show name, season, episode, and title information,
        or None if no information could be extracted
    """
    logger = logging.getLogger(__name__)

    # Get just the basename without the directory path
    basename = os.path.basename(filename)
    logger.debug(f"Extracting info from basename: {basename}")

    # Remove file extension
    name_without_ext, extension = os.path.splitext(basename)

    # Replace dots and hyphens with spaces to make parsing easier
    name_with_spaces = name_without_ext.replace(".", " ").replace("-", " ")

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
            # Extract basic info
            show_name = match.group(group_indices["show"]).strip()
            # Normalize show name (replace dots and hyphens with spaces)
            show_name = re.sub(r"[-._]+", " ", show_name).strip()

            season = int(match.group(group_indices["season"]))
            episode = int(match.group(group_indices["episode"]))

            # Get the raw title text
            raw_title = (
                match.group(group_indices["title"]).strip()
                if match.group(group_indices["title"])
                else ""
            )

            # Check for multi-episodes - using the direct pattern detection
            multi_episodes = detect_multi_episodes_direct(basename)

            # Clean title for multi-episode files by removing episode markers
            title = raw_title
            if len(multi_episodes) > 1:
                # Remove "E01", "E02", etc. from the title
                title = re.sub(r"\s*E\d+\s*", " ", raw_title, flags=re.IGNORECASE)
                # Remove "to E01", "& E02", etc.
                title = re.sub(r"\s*(?:to|&|\+|,)\s*E\d+\s*", " ", title, flags=re.IGNORECASE)
                # Clean up multiple spaces
                title = re.sub(r"\s+", " ", title).strip()

            logger.debug(
                f"Matched pattern, extracted: show={show_name}, season={season}, episode={episode}, title={title}"
            )

            result = {
                "show_name": show_name,
                "season": season,
                "episode": episode,
                "title": title,
                "extension": extension,
            }

            if len(multi_episodes) > 1:
                result["multi_episodes"] = multi_episodes

            return result

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

            # Normalize show name (replace dots and hyphens with spaces)
            show_name = re.sub(r"[-._]+", " ", parts[0].strip())

            # Get raw title
            raw_title = (
                parts[-1].strip().replace(".", " ").replace("-", " ") if len(parts) > 2 else ""
            )

            # Check for multi-episodes
            multi_episodes = detect_multi_episodes_direct(basename)

            # Clean title for multi-episode files
            title = raw_title
            if len(multi_episodes) > 1:
                # Remove "E01", "E02", etc. from the title
                title = re.sub(r"\s*E\d+\s*", " ", raw_title, flags=re.IGNORECASE)
                # Remove "to E01", "& E02", etc.
                title = re.sub(r"\s*(?:to|&|\+|,)\s*E\d+\s*", " ", title, flags=re.IGNORECASE)
                # Clean up multiple spaces
                title = re.sub(r"\s+", " ", title).strip()

            logger.debug(
                f"Matched fallback pattern, extracted: show={show_name}, season={season}, episode={episode}, title={title}"
            )

            result = {
                "show_name": show_name,
                "season": season,
                "episode": episode,
                "title": title,
                "extension": extension,
            }

            if len(multi_episodes) > 1:
                result["multi_episodes"] = multi_episodes

            return result

    logger.warning(f"Could not extract episode info from {basename}")
    return None


def detect_multi_episodes_direct(filename: str) -> List[int]:
    """
    Helper function to detect multi-episodes directly from patterns without dependencies.

    Args:
        filename: The filename to analyze

    Returns:
        List of episode numbers
    """
    # Mixed format with multiple ranges: S01E01-E03E05E07-E09
    # Try this complex pattern first
    complex_mixed_pattern = r"S\d+E(\d+)-E(\d+)E(\d+)E(\d+)-E(\d+)"
    match = re.search(complex_mixed_pattern, filename, re.IGNORECASE)
    if match:
        first_start = int(match.group(1))
        first_end = int(match.group(2))
        second_start = int(match.group(3))
        second_mid = int(match.group(4))
        second_end = int(match.group(5))

        result = []
        # Add first range (e.g., E01-E03)
        result.extend(parse_episode_range(first_start, first_end))
        # Add second_start (e.g., E05)
        result.append(second_start)
        # Add second_mid (e.g., E07)
        result.append(second_mid)
        # Add remaining range (e.g., E08-E09)
        result.extend(parse_episode_range(second_mid + 1, second_end))
        return result

    # Standard format: S01E01E02
    multi_ep_pattern = r"S(\d+)E(\d+)(?:E(\d+))+"
    match = re.search(multi_ep_pattern, filename, re.IGNORECASE)
    if match:
        episode_markers = re.findall(r"E(\d+)", filename, re.IGNORECASE)
        if episode_markers:
            return [int(ep) for ep in episode_markers]

    # Hyphen format: S01E01-E02 or S01E01-02
    hyphen_pattern = r"S\d+E(\d+)[-](?:E)?(\d+)"
    match = re.search(hyphen_pattern, filename, re.IGNORECASE)
    if match:
        start_ep = int(match.group(1))
        end_ep = int(match.group(2))
        return parse_episode_range(start_ep, end_ep)

    # Space separator: S01E01 E02 E03
    space_pattern = r"S\d+E(\d+)(?:\s+E(\d+))+"
    match = re.search(space_pattern, filename, re.IGNORECASE)
    if match:
        episode_markers = re.findall(r"E(\d+)", filename, re.IGNORECASE)
        if episode_markers:
            return [int(ep) for ep in episode_markers]

    # Text separators like "to", "&", "+"
    text_sep_pattern = r"S\d+E(\d+)(?:\s*(?:to|&|\+|,)\s*E(\d+))"
    match = re.search(text_sep_pattern, filename, re.IGNORECASE)
    if match:
        start_ep = int(match.group(1))
        end_ep = int(match.group(2))
        if "to" in filename.lower():
            return parse_episode_range(start_ep, end_ep)
        else:
            return [start_ep, end_ep]

    # X format with hyphen: 01x01-03
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

    # Single episode
    single_ep_pattern = r"S\d+E(\d+)"
    match = re.search(single_ep_pattern, filename, re.IGNORECASE)
    if match:
        return [int(match.group(1))]

    return []


def detect_multi_episodes(filename: str) -> List[int]:
    """
    Detect if a filename contains multiple episodes.

    Args:
        filename: The filename to check

    Returns:
        A list of episode numbers if found, or an empty list if not a multi-episode
    """
    # Get the basename
    basename = os.path.basename(filename)

    # Check for complex mixed pattern: S01E01-E03E05E07-E09
    complex_mixed_pattern = re.search(
        r"S\d+E(\d+)-E(\d+)E(\d+)E(\d+)-E(\d+)", basename, re.IGNORECASE
    )
    if complex_mixed_pattern:
        first_start = int(complex_mixed_pattern.group(1))
        first_end = int(complex_mixed_pattern.group(2))
        second_start = int(complex_mixed_pattern.group(3))
        second_mid = int(complex_mixed_pattern.group(4))
        second_end = int(complex_mixed_pattern.group(5))

        result = []
        # Add first range (e.g., E01-E03)
        result.extend(parse_episode_range(first_start, first_end))
        # Add second_start (e.g., E05)
        result.append(second_start)
        # Add second_mid (e.g., E07)
        result.append(second_mid)
        # Add remaining range (e.g., E07-E09)
        result.extend(parse_episode_range(second_mid + 1, second_end))
        return result

    # Check for multiple episodes with spaces: "S01E01 E02 E03"
    multiple_ep_pattern = re.search(r"S\d+E(\d+)(?:\s+E\d+)+", basename, re.IGNORECASE)
    if multiple_ep_pattern:
        # Find all episode numbers
        episode_numbers = re.findall(r"E(\d+)", basename, re.IGNORECASE)
        if episode_numbers:
            return [int(ep) for ep in episode_numbers]

    # Check for special pattern "S01 E01 E02" (with space between season and episodes)
    space_pattern = re.search(r"S(\d+)\s+E(\d+)\s+E(\d+)", basename, re.IGNORECASE)
    if space_pattern:
        first_episode = int(space_pattern.group(2))
        second_episode = int(space_pattern.group(3))
        return [first_episode, second_episode]

    # Check for "S01E01 E02" format (space between episode markers)
    space_ep_pattern = re.search(r"S\d+E(\d+)\s+E(\d+)", basename, re.IGNORECASE)
    if space_ep_pattern:
        first_episode = int(space_ep_pattern.group(1))
        second_episode = int(space_ep_pattern.group(2))
        return [first_episode, second_episode]

    # Check for "S01E01-E02" format (hyphen with E prefix)
    hyphen_e_pattern = re.search(r"S\d+E(\d+)-E(\d+)", basename, re.IGNORECASE)
    if hyphen_e_pattern:
        first_episode = int(hyphen_e_pattern.group(1))
        second_episode = int(hyphen_e_pattern.group(2))
        return parse_episode_range(first_episode, second_episode)

    # Check for "S01E01-02" format (hyphen with no E prefix for second episode)
    hyphen_no_e_pattern = re.search(r"S\d+E(\d+)-(\d+)", basename, re.IGNORECASE)
    if hyphen_no_e_pattern:
        first_episode = int(hyphen_no_e_pattern.group(1))
        second_episode = int(hyphen_no_e_pattern.group(2))
        return parse_episode_range(first_episode, second_episode)

    # Check for "Show 01x02-03" format (x format common in anime)
    x_pattern = re.search(r"(\d+)x(\d+)-(\d+)", basename, re.IGNORECASE)
    if x_pattern:
        first_episode = int(x_pattern.group(2))
        second_episode = int(x_pattern.group(3))
        return parse_episode_range(first_episode, second_episode)

    # Check for "S01E05 to E07" format
    to_pattern = re.search(r"S\d+E(\d+)\s+to\s+E(\d+)", basename, re.IGNORECASE)
    if to_pattern:
        first_episode = int(to_pattern.group(1))
        second_episode = int(to_pattern.group(2))
        return parse_episode_range(first_episode, second_episode)

    # Check for "&" and "+" separators
    other_sep_pattern = re.search(r"S\d+E(\d+)\s*[&+,]\s*E(\d+)", basename, re.IGNORECASE)
    if other_sep_pattern:
        first_episode = int(other_sep_pattern.group(1))
        second_episode = int(other_sep_pattern.group(2))
        return [first_episode, second_episode]

    # Check for single episode pattern
    single_pattern = re.search(r"S(\d+)E(\d+)(?!\d|E\d+)", basename, re.IGNORECASE)
    if single_pattern:
        episode = int(single_pattern.group(2))
        return [episode]

    # Check for all multi-episode patterns
    for pattern in MULTI_EPISODE_PATTERNS:
        match = re.search(pattern, basename, re.IGNORECASE)
        if match:
            if len(match.groups()) == 2:
                # Simple range: S01E01-02
                start_episode = int(match.group(2))
                end_episode = int(match.group(2))  # Default to same as start if no end
                return [start_episode]
            elif len(match.groups()) == 3:
                # Start and end specified: S01E01-E02 or S01E01E02
                start_episode = int(match.group(2))
                end_episode = int(match.group(3))
                if pattern == r"S(\d+)E(\d+)-E(\d+)" or pattern == r"S(\d+)E(\d+)(?:E(\d+))+":
                    # For patterns specifying multiple episodes
                    if start_episode == end_episode:
                        return [start_episode]
                    elif start_episode > end_episode:
                        return []  # Invalid range
                    else:
                        return parse_episode_range(start_episode, end_episode)
                else:
                    # For other patterns like xNN-NN
                    return parse_episode_range(start_episode, end_episode)

    # No multi-episode pattern found
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
        return True  # Empty list is considered sequential by convention

    if len(numbers) == 1:
        return True

    for i in range(1, len(numbers)):
        if numbers[i] != numbers[i - 1] + 1:
            return False
    return True


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

    # Check for Special.number pattern specifically
    special_dot_pattern = r"Special\.(\d+)"
    match = re.search(special_dot_pattern, filename, re.IGNORECASE)
    if match:
        return {"type": "special", "number": int(match.group(1))}

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

    # First, normalize the title by ensuring consistent spacing around separators
    normalized_title = title

    # Handle mixed separators by converting them all to a common separator temporarily
    normalized_title = re.sub(r"\s*[&,+]\s*", "|SEPARATOR|", normalized_title)
    normalized_title = re.sub(r"\s+-\s+", "|SEPARATOR|", normalized_title)
    normalized_title = re.sub(r"\s+and\s+", "|SEPARATOR|", normalized_title)

    # Split by the common separator and clean up each segment
    if "|SEPARATOR|" in normalized_title:
        return [segment.strip() for segment in normalized_title.split("|SEPARATOR|")]

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
