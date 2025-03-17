"""Advanced name parsing utilities for media files."""

import re
import enum
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field


class MediaType(enum.Enum):
    """Enum representing different types of media files."""

    TV_SHOW = "tv_show"
    TV_SPECIAL = "tv_special"
    MOVIE = "movie"
    ANIME = "anime"
    ANIME_SPECIAL = "anime_special"
    UNKNOWN = "unknown"


@dataclass
class ParsedMediaName:
    """Class for storing parsed media name information."""

    media_type: MediaType

    # Common fields
    title: str
    extension: str
    quality: Optional[str] = None
    confidence: float = 1.0  # Confidence score for the parsing

    # TV Show specific fields
    season: Optional[int] = None
    episodes: Optional[List[int]] = None
    episode_title: Optional[str] = None

    # Movie specific fields
    year: Optional[int] = None

    # Anime specific fields
    group: Optional[str] = None
    version: Optional[int] = None
    special_type: Optional[str] = None
    special_number: Optional[int] = None

    # Additional metadata that doesn't fit elsewhere
    additional_info: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and initialize any derived fields after initialization."""
        # Ensure episodes is always a list if provided
        if self.episodes is not None and not isinstance(self.episodes, list):
            self.episodes = [self.episodes]


def detect_media_type(filename: str) -> MediaType:
    """
    Detect the type of media file based on the filename.

    Args:
        filename: The filename to analyze

    Returns:
        MediaType: The detected media type
    """
    # Check for anime special files first
    if re.search(r"^\[.*?\].*?OVA\d*\s*\[", filename):
        return MediaType.ANIME_SPECIAL

    # TV show patterns
    tv_patterns = [
        # Standard S01E01 format
        r"[sS]\d{1,2}[eE]\d{1,2}",
        # Multi-episode format S01E01E02
        r"[sS]\d{1,2}[eE]\d{1,2}(?:[eE]\d{1,2})+",
        # 1x01 format
        r"\d{1,2}x\d{1,2}",
        # "Season 1 Episode 2" format
        r"[Ss]eason\s+\d{1,2}\s+[Ee]pisode\s+\d{1,2}",
        # S01.E01 format (period separated)
        r"[sS]\d{1,2}\.[eE]\d{1,2}",
    ]

    # TV special patterns
    tv_special_patterns = [
        # S01.5xSpecial format
        r"[sS]\d{1,2}\.5x[Ss]pecial",
        # Special Episode format
        r"[Ss]pecial\s+[Ee]pisode",
        # OVA format (often anime)
        r"OVA\d*",
    ]

    # Movie patterns
    movie_patterns = [
        # Year in brackets or parentheses
        r"\(\d{4}\)",
        r"\[\d{4}\]",
        # Year with separator: Movie.Name.2020 or Movie Name 2020
        r"[. _-]+(19|20)\d{2}[. _-]",
        # Year followed by quality or other info
        r"\b(19|20)\d{2}\b.*\d+p",
    ]

    # Anime patterns
    anime_patterns = [
        # Group format
        r"^\[([^\]]+)\]",
        # Episode number without season
        r" - \d{1,2}(v\d)? \[",
        # OVA, special, etc.
        r" - (OVA|Special)\d* \[",
    ]

    # Check anime patterns first
    for pattern in anime_patterns:
        if re.search(pattern, filename):
            # Differentiate between regular anime and specials
            if "OVA" in filename or "Special" in filename:
                return MediaType.ANIME_SPECIAL
            return MediaType.ANIME

    # Check TV special patterns
    for pattern in tv_special_patterns:
        if re.search(pattern, filename):
            return MediaType.TV_SPECIAL

    # Check TV show patterns
    for pattern in tv_patterns:
        if re.search(pattern, filename):
            return MediaType.TV_SHOW

    # Check movie patterns
    for pattern in movie_patterns:
        if re.search(pattern, filename):
            return MediaType.MOVIE

    # Simple movie pattern - name followed by four-digit year at the end of the name part
    if re.search(r"(19|20)\d{2}(\.|$|\s)", filename):
        return MediaType.MOVIE

    # Default to unknown if no pattern matches
    return MediaType.UNKNOWN


def parse_tv_show(filename: str) -> ParsedMediaName:
    """
    Parse a TV show filename into its components.

    Args:
        filename: The filename to parse

    Returns:
        ParsedMediaName: Object containing parsed information
    """
    # Base information
    media_type = MediaType.TV_SHOW
    extension = Path(filename).suffix
    title = ""
    season = 1  # Default to season 1 if not specified
    episodes = []
    episode_title = None
    quality = None
    confidence = 0.8  # Default confidence

    # Extract quality if present
    quality_patterns = [
        r"(\d{3,4}p\s+(?:HDTV|WEB-DL|BluRay|BRRip))",  # Combined formats: 720p HDTV
        r"(\d{3,4}p)",  # 720p, 1080p, etc.
        r"(HDTV|WEB-DL|BluRay|BRRip)",  # Source
        r"(x264|x265|HEVC)",  # Codec
    ]

    name_part = Path(filename).stem

    # Special case for standard dash format with quality
    dash_quality_match = re.search(
        r"(?P<show_name>.*?)\s+-\s+[sS](?P<season>\d{1,2})[eE](?P<episode>\d{1,2})\s+-\s+(?P<title>.*?)\s+-\s+(?P<quality>.*?)$",
        name_part,
    )

    if dash_quality_match:
        match_dict = dash_quality_match.groupdict()
        title = match_dict["show_name"].strip()
        season = int(match_dict["season"])
        episodes = [int(match_dict["episode"])]
        episode_title = match_dict["title"].strip()
        quality = match_dict["quality"].strip()
        confidence = 0.95

        return ParsedMediaName(
            media_type=media_type,
            title=title,
            season=season,
            episodes=episodes,
            episode_title=episode_title,
            extension=extension,
            quality=quality,
            confidence=confidence,
        )

    # Remove quality information to avoid it being included in episode title
    for pattern in quality_patterns:
        match = re.search(pattern, name_part, re.IGNORECASE)
        if match:
            quality = match.group(1)
            name_part = re.sub(pattern, "", name_part, flags=re.IGNORECASE)

    # Alternative format with dash separator (without quality)
    dash_match = re.search(
        r"(?P<show_name>.*?)\s+-\s+[sS](?P<season>\d{1,2})[eE](?P<episode>\d{1,2})\s+-\s+(?P<title>.*?)(?:\s+-\s+.*)?$",
        name_part,
    )

    if dash_match:
        match_dict = dash_match.groupdict()
        title = match_dict["show_name"].strip()
        season = int(match_dict["season"])
        episodes = [int(match_dict["episode"])]
        episode_title = match_dict["title"].strip()
        confidence = 0.95

        return ParsedMediaName(
            media_type=media_type,
            title=title,
            season=season,
            episodes=episodes,
            episode_title=episode_title,
            extension=extension,
            quality=quality,
            confidence=confidence,
        )

    # Check for range format with hyphen "S01E02-E03"
    range_match = re.search(
        r"(?P<show_name>.*?)[. _-]+[sS](?P<season>\d{1,2})[eE](?P<first_ep>\d{1,2})-[eE](?P<last_ep>\d{1,2})(?:[. _-]+(?P<title>.*))?",
        name_part,
    )

    if range_match:
        match_dict = range_match.groupdict()
        title = match_dict["show_name"].replace(".", " ").replace("_", " ").strip()
        season = int(match_dict["season"])
        first_ep = int(match_dict["first_ep"])
        last_ep = int(match_dict["last_ep"])
        episodes = list(range(first_ep, last_ep + 1))

        if match_dict["title"]:
            episode_title = match_dict["title"].replace(".", " ").replace("_", " ").strip()

        confidence = 0.9

        return ParsedMediaName(
            media_type=media_type,
            title=title,
            season=season,
            episodes=episodes,
            episode_title=episode_title,
            extension=extension,
            quality=quality,
            confidence=confidence,
        )

    # Standard patterns
    # S01E02 format
    se_match = re.search(
        r"(?P<show_name>.*?)[. _-]+[sS](?P<season>\d{1,2})[eE](?P<episode>\d{1,2})(?P<multi_ep>(?:[eE]\d{1,2})*)(?:[. _-]+(?P<title>.*))?",
        name_part,
    )

    # 1x02 format
    alt_match = re.search(
        r"(?P<show_name>.*?)[. _-]+(?P<season>\d{1,2})x(?P<episode>\d{1,2})(?:[. _-]+(?P<title>.*))?",
        name_part,
    )

    # Season 1 Episode 2 format
    verbose_match = re.search(
        r"(?P<show_name>.*?)[. _-]+[Ss]eason[. _-]+(?P<season>\d{1,2})[. _-]+[Ee]pisode[. _-]+(?P<episode>\d{1,2})(?:[. _-]+(?P<title>.*))?",
        name_part,
    )

    # S01.E02 format
    period_match = re.search(
        r"(?P<show_name>.*?)[. _-]+[sS](?P<season>\d{1,2})\.[eE](?P<episode>\d{1,2})(?:[. _-]+(?P<title>.*))?",
        name_part,
    )

    # Process the matches
    if se_match:
        match_dict = se_match.groupdict()
        title = match_dict["show_name"].replace(".", " ").replace("_", " ").strip()
        season = int(match_dict["season"])
        episodes = [int(match_dict["episode"])]

        # Handle multi-episode format (S01E01E02E03)
        if match_dict["multi_ep"]:
            additional_eps = re.findall(r"[eE](\d{1,2})", match_dict["multi_ep"])
            episodes.extend([int(ep) for ep in additional_eps])

        if match_dict["title"]:
            episode_title = match_dict["title"].replace(".", " ").replace("_", " ").strip()

        confidence = 0.95

    # Process other formats
    elif alt_match:
        match_dict = alt_match.groupdict()
        title = match_dict["show_name"].replace(".", " ").replace("_", " ").strip()
        season = int(match_dict["season"])
        episodes = [int(match_dict["episode"])]

        if match_dict["title"]:
            episode_title = match_dict["title"].replace(".", " ").replace("_", " ").strip()

        confidence = 0.85

    elif verbose_match:
        match_dict = verbose_match.groupdict()
        title = match_dict["show_name"].replace(".", " ").replace("_", " ").strip()
        season = int(match_dict["season"])
        episodes = [int(match_dict["episode"])]

        if match_dict["title"]:
            episode_title = match_dict["title"].replace(".", " ").replace("_", " ").strip()

        confidence = 0.8

    elif period_match:
        match_dict = period_match.groupdict()
        title = match_dict["show_name"].replace(".", " ").replace("_", " ").strip()
        season = int(match_dict["season"])
        episodes = [int(match_dict["episode"])]

        if match_dict["title"]:
            episode_title = match_dict["title"].replace(".", " ").replace("_", " ").strip()

        confidence = 0.8

    # If we have a title with a year in parentheses, keep it that way
    year_match = re.search(r"(.*?) \((\d{4})\)", title)
    if year_match:
        title = f"{year_match.group(1)} ({year_match.group(2)})"

    return ParsedMediaName(
        media_type=media_type,
        title=title,
        season=season,
        episodes=episodes,
        episode_title=episode_title,
        extension=extension,
        quality=quality,
        confidence=confidence,
    )


def parse_movie(filename: str) -> ParsedMediaName:
    """
    Parse a movie filename into its components.

    Args:
        filename: The filename to parse

    Returns:
        ParsedMediaName: Object containing parsed information
    """
    # Base information
    media_type = MediaType.MOVIE
    extension = Path(filename).suffix
    title = ""
    year = None
    quality = None
    confidence = 0.8  # Default confidence

    # Extract quality if present
    quality_patterns = [
        r"(\d{3,4}p)",  # 720p, 1080p, etc.
        r"(HDTV|WEB-DL|BluRay|BRRip)",  # Source
        r"(x264|x265|HEVC)",  # Codec
        r"(\d{3,4}p\s+(?:HDTV|WEB-DL|BluRay|BRRip))",  # Combined
    ]

    for pattern in quality_patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            quality = match.group(1)

    # Year formats
    # Year in parentheses: Movie Name (2020)
    paren_match = re.search(r"(?P<movie_name>.*?)\s*\((?P<year>\d{4})\)(?:.*)?$", filename)

    # Year in brackets: Movie Name [2020]
    bracket_match = re.search(r"(?P<movie_name>.*?)\s*\[(?P<year>\d{4})\](?:.*)?$", filename)

    # Year with separator: Movie.Name.2020 or Movie Name 2020
    sep_match = re.search(
        r"(?P<movie_name>.*?)[. _-]+(?P<year>19\d{2}|20\d{2})(?:[. _-]+(?P<info>.*))?$", filename
    )

    # Process the matches
    if paren_match:
        match_dict = paren_match.groupdict()
        title = match_dict["movie_name"].strip()
        year = int(match_dict["year"])
        confidence = 0.95

    elif bracket_match:
        match_dict = bracket_match.groupdict()
        title = match_dict["movie_name"].strip()
        year = int(match_dict["year"])
        confidence = 0.9

    elif sep_match:
        match_dict = sep_match.groupdict()
        title = match_dict["movie_name"].replace(".", " ").replace("_", " ").strip()
        year = int(match_dict["year"])
        confidence = 0.85

    return ParsedMediaName(
        media_type=media_type,
        title=title,
        year=year,
        extension=extension,
        quality=quality,
        confidence=confidence,
    )


def parse_anime(filename: str) -> ParsedMediaName:
    """
    Parse an anime filename into its components.

    Args:
        filename: The filename to parse

    Returns:
        ParsedMediaName: Object containing parsed information
    """
    # Base information
    extension = Path(filename).suffix
    title = ""
    episodes = []
    group = None
    version = None
    special_type = None
    special_number = None
    quality = None
    confidence = 0.8  # Default confidence

    # Determine if it's a special or regular episode
    if "OVA" in filename or "Special" in filename:
        media_type = MediaType.ANIME_SPECIAL
    else:
        media_type = MediaType.ANIME

    # Extract group name from [Group] format
    group_match = re.search(r"^\[([^\]]+)\]", filename)
    if group_match:
        group = group_match.group(1)

    # Extract quality (usually in brackets at the end)
    quality_match = re.search(r"\[(\d{3,4}p)\]", filename)
    if quality_match:
        quality = quality_match.group(1)

    # Standard fansub format: [Group] Anime Name - 01 [720p].mkv
    standard_match = re.search(
        r"^\[(?P<group>[^\]]+)\]\s*(?P<title>.*?)\s*-\s*(?P<episode>\d{1,2})(?P<version>v\d)?\s*(?:\[.*?)\]",
        filename,
    )

    # Special episode format: [Group] Anime Name - OVA1 [1080p].mkv
    special_match = re.search(
        r"^\[(?P<group>[^\]]+)\]\s*(?P<title>.*?)\s*-\s*(?P<special_type>OVA|Special)(?P<special_number>\d*)\s*(?:\[.*?)\]",
        filename,
    )

    # Process matches
    if standard_match:
        match_dict = standard_match.groupdict()
        title = match_dict["title"].strip()
        episodes = [int(match_dict["episode"])]
        group = match_dict["group"]

        if match_dict["version"]:
            version = int(match_dict["version"][1:])  # Extract number from "v2"

        confidence = 0.9

    elif special_match:
        match_dict = special_match.groupdict()
        title = match_dict["title"].strip()
        special_type = match_dict["special_type"]

        if match_dict["special_number"]:
            special_number = int(match_dict["special_number"])
        else:
            special_number = 1  # Default to 1 if not specified

        group = match_dict["group"]
        confidence = 0.85
        media_type = MediaType.ANIME_SPECIAL  # Ensure special type is set

    # For cases without clear match, try to extract basic information
    else:
        # Try to extract title and episode number
        basic_match = re.search(r"^\[.*?\]\s*(.*?)\s*-\s*(\d{1,2})", filename)
        if basic_match:
            title = basic_match.group(1).strip()
            episodes = [int(basic_match.group(2))]
            confidence = 0.6

    return ParsedMediaName(
        media_type=media_type,
        title=title,
        episodes=episodes,
        group=group,
        version=version,
        special_type=special_type,
        special_number=special_number,
        extension=extension,
        quality=quality,
        confidence=confidence,
    )


def parse_media_name(filename: str) -> ParsedMediaName:
    """
    Parse a media filename into its components.

    Args:
        filename: The filename to parse

    Returns:
        ParsedMediaName: Object containing parsed information
    """
    # First detect the media type
    media_type = detect_media_type(filename)

    # Parse according to media type
    if media_type == MediaType.TV_SHOW or media_type == MediaType.TV_SPECIAL:
        return parse_tv_show(filename)
    elif media_type == MediaType.MOVIE:
        return parse_movie(filename)
    elif media_type == MediaType.ANIME or media_type == MediaType.ANIME_SPECIAL:
        result = parse_anime(filename)
        # Make sure we respect the detected media type
        result.media_type = media_type
        return result
    else:
        # Unknown type - return minimal information
        return ParsedMediaName(
            media_type=MediaType.UNKNOWN,
            title=Path(filename).stem,
            extension=Path(filename).suffix,
            confidence=0.2,
        )


class NameParser:
    """Class for parsing media filenames with configuration options."""

    def __init__(self, strict_mode: bool = False, use_llm: bool = False):
        """
        Initialize the NameParser.

        Args:
            strict_mode: If True, require higher confidence threshold
            use_llm: If True, use LLM for verification
        """
        self.strict_mode = strict_mode
        self.use_llm = use_llm
        self.confidence_threshold = 0.8 if strict_mode else 0.5

    def parse(self, filename: str) -> ParsedMediaName:
        """
        Parse a media filename.

        Args:
            filename: The filename to parse

        Returns:
            ParsedMediaName: The parsed media information
        """
        # Parse the filename
        result = parse_media_name(filename)

        # Apply verification if configured to use LLM
        if self.use_llm and result.confidence < 0.95:
            result = self.verify_with_llm(result, filename)

        # If strict mode is enabled and confidence is too low, mark as unknown
        if self.strict_mode and result.confidence < self.confidence_threshold:
            result.media_type = MediaType.UNKNOWN

        return result

    def verify_with_llm(self, result: ParsedMediaName, original_filename: str) -> ParsedMediaName:
        """
        Verify and enhance parsed results using LLM.

        Args:
            result: The initial parsed result
            original_filename: The original filename

        Returns:
            ParsedMediaName: Enhanced parsed result
        """
        # Implementation would depend on the actual LLM client
        # This is a placeholder - the actual implementation would be added later

        # For now, just return the original result
        return result
