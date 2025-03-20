"""Advanced name parsing utilities for media files."""

import re
import enum
from pathlib import Path

try:
    # Python 3.9+ has native support for these types
    from typing import Dict, List, Optional, Any, Union
except ImportError:
    # For Python 3.8 support
    from typing_extensions import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
import unicodedata


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
    episodes: Optional[Union[int, List[int]]] = None
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

    # New fields for season packs
    is_season_pack: bool = False

    def __post_init__(self) -> None:
        """Validate and initialize any derived fields after initialization."""
        # Ensure episodes is always a list if provided
        if isinstance(self.episodes, int):
            self.episodes = [self.episodes]


def detect_media_type(filename: str) -> MediaType:
    """
    Detect the type of media file based on the filename.

    Args:
        filename: The filename to analyze

    Returns:
        MediaType: The detected media type
    """
    # Check for anime patterns first (must have [Group] prefix)
    if filename.startswith("["):
        # Check for anime special files first
        if re.search(r"\b(OVA|Special|Movie)\d*\b", filename, re.IGNORECASE):
            return MediaType.ANIME_SPECIAL
        # Then check for regular anime
        if re.search(r" - \d{1,2}(v\d)? \[", filename):
            return MediaType.ANIME

    # TV special patterns (check before regular TV show patterns)
    tv_special_patterns = [
        # S01.5xSpecial format
        r"[sS]\d{1,2}\.5x[Ss]pecial",
        # Special Episode format
        r"[Ss]pecial[. _-]+[Ee]pisode",
        # OVA format (when not in anime format)
        r"\bOVA\d*\b",
        # Special followed by separator or end of name
        r"[Ss]pecial(?:[. _-]|$)",
    ]

    for pattern in tv_special_patterns:
        if re.search(pattern, filename, re.IGNORECASE):
            return MediaType.TV_SPECIAL

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

    for pattern in tv_patterns:
        if re.search(pattern, filename):
            return MediaType.TV_SHOW

    # Movie patterns
    movie_patterns = [
        # Year in brackets or parentheses
        r"\(\d{4}\)",
        r"\[\d{4}\]",
        # Year with separator: Movie.Name.2020 or Movie Name 2020
        r"[. _-]+(19|20)\d{2}[. _-]",
        # Year followed by quality or other info
        r"\b(19|20)\d{2}\b.*\d+p",
        # Simple year at end of name
        r"(19|20)\d{2}(\.|$|\s)",
    ]

    for pattern in movie_patterns:
        if re.search(pattern, filename):
            return MediaType.MOVIE

    # Default to unknown if no pattern matches
    return MediaType.UNKNOWN


def parse_tv_show(filename: str, media_type: Optional[MediaType] = None) -> ParsedMediaName:
    """
    Parse a TV show filename into a structured format.

    Args:
        filename: The filename to parse
        media_type: The media type to set in the result (defaults to TV_SHOW)

    Returns:
        ParsedMediaName: Object containing parsed information
    """
    # Base information
    media_type = media_type or MediaType.TV_SHOW
    extension = ""
    title = ""
    season = 1  # Default to season 1 if not specified
    episodes: List[int] = []  # Initialize as empty list of ints
    episode_title = None
    quality = None
    confidence = 0.8  # Default confidence

    # Handle empty filename
    if not filename:
        return ParsedMediaName(
            media_type=media_type,
            title=title,
            extension=extension,
            quality=quality,
            confidence=confidence,
            season=season,
            episodes=episodes,
            episode_title=episode_title,
        )

    # Special case for filenames that only contain an extension (e.g., ".mp4")
    if filename.startswith(".") and "/" not in filename and "\\" not in filename:
        return ParsedMediaName(
            media_type=media_type,
            title=title,
            extension=Path(filename).suffix,  # Use Path to extract the proper suffix
            quality=quality,
            confidence=confidence,
            season=season,
            episodes=episodes,
            episode_title=episode_title,
        )

    # Get extension and name part
    path = Path(filename)
    extension = path.suffix
    name_part = path.stem

    # Handle Unicode normalization for international titles
    # This ensures consistent handling of accented characters
    name_part = unicodedata.normalize("NFKC", name_part)

    # If filename is just an extension, return minimal info
    if not name_part:
        return ParsedMediaName(
            media_type=media_type,
            title=title,
            extension=extension,  # This already contains the extension
            quality=quality,
            confidence=confidence,
            season=season,
            episodes=episodes,
            episode_title=episode_title,
        )

    # Extract quality if present
    quality_parts = []
    quality_patterns = [
        r"(\d{3,4}p)",  # 720p, 1080p, etc.
        r"(HDTV|WEB-DL|BluRay|BRRip)",  # Source
        r"(x264|x265|HEVC)",  # Codec
    ]

    # Extract all quality components
    for pattern in quality_patterns:
        match = re.search(pattern, name_part, re.IGNORECASE)
        if match:
            quality_parts.append(match.group(1))
            name_part = re.sub(pattern, "", name_part, flags=re.IGNORECASE)

    quality = " ".join(quality_parts) if quality_parts else None

    # Special case for standard dash format with quality
    dash_quality_match = re.search(
        r"(?P<show_name>.*?)\s+-\s+[sS](?P<season>\d{1,2})[eE](?P<episode>\d{1,2})\s+-\s+(?P<title>.*?)(?:\s+-\s+(?P<quality>.*?))?$",
        name_part,
    )

    if dash_quality_match:
        match_dict = dash_quality_match.groupdict()
        title = match_dict["show_name"].strip()
        season = int(match_dict["season"])
        episodes = [int(match_dict["episode"])]
        episode_title = match_dict["title"].strip()
        if match_dict.get("quality"):
            quality = match_dict["quality"].strip()
        confidence = 0.95  # High confidence for well-formatted names

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
        confidence = 0.95  # High confidence for well-formatted names

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

    # Check for season pack format (ShowName.S01.Complete or ShowName.Season.01)
    season_pack_match = re.search(
        r"(?P<show_name>.*?)(?:[. _-]+[sS](?P<season>\d{1,2})(?:[. _-]+(?:Complete|COMPLETE|complete))|[. _-]+[sS]eason[. _-]+(?P<season2>\d{1,2}))",
        name_part,
    )

    if season_pack_match:
        match_dict = season_pack_match.groupdict()
        title_part = match_dict["show_name"]
        title = title_part.replace(".", " ").replace("_", " ").replace("-", " ").strip()
        # Remove multiple spaces
        title = " ".join(title.split())

        # Get season number
        season = int(match_dict["season"] or match_dict["season2"] or 1)

        # Season packs don't have specific episodes
        episodes = []

        confidence = 0.85  # Higher confidence for season packs

        return ParsedMediaName(
            media_type=media_type,
            title=title,
            season=season,
            episodes=episodes,
            episode_title=None,
            extension=extension,
            quality=quality,
            confidence=confidence,
            is_season_pack=True,  # Mark as season pack
        )

    # Check for multi-episode range format
    range_match = re.search(
        r"(?P<show_name>.*?)[. _-]+[sS](?P<season>\d{1,2})[eE](?P<first_ep>\d{1,2})-[eE](?P<last_ep>\d{1,2})(?:[. _-]+(?P<title>.*))?",
        name_part,
    )

    if range_match:
        match_dict = range_match.groupdict()
        title_part = match_dict["show_name"]
        title = title_part.replace(".", " ").replace("_", " ").replace("-", " ").strip()
        # Remove multiple spaces
        title = " ".join(title.split())

        season = int(match_dict["season"])
        first_ep = int(match_dict["first_ep"])
        last_ep = int(match_dict["last_ep"])
        episodes = list(range(first_ep, last_ep + 1))

        if match_dict.get("title"):
            episode_title = (
                match_dict["title"].replace(".", " ").replace("_", " ").replace("-", " ").strip()
            )
            # Remove multiple spaces
            episode_title = " ".join(episode_title.split())

        confidence = 0.8  # Standard format confidence

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

    # Check for multi-episode separate format (S01E01E02)
    multi_ep_match = re.search(
        r"(?P<show_name>.*?)[. _-]+[sS](?P<season>\d{1,2})(?P<episodes>(?:[eE]\d{1,2})+)(?:[. _-]+(?P<title>.*))?",
        name_part,
    )

    if multi_ep_match:
        match_dict = multi_ep_match.groupdict()
        title_part = match_dict["show_name"]
        title = title_part.replace(".", " ").replace("_", " ").replace("-", " ").strip()
        # Remove multiple spaces
        title = " ".join(title.split())

        season = int(match_dict["season"])
        episode_numbers = re.findall(r"[eE](\d{1,2})", match_dict["episodes"])
        episodes = [int(ep) for ep in episode_numbers]

        if match_dict.get("title"):
            episode_title = (
                match_dict["title"].replace(".", " ").replace("_", " ").replace("-", " ").strip()
            )
            # Remove multiple spaces
            episode_title = " ".join(episode_title.split())

        confidence = 0.8  # Standard format confidence

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

    # Extract season and episode information
    season_ep_match = re.search(
        r"(?P<show_name>.*?)(?:[. _-]+(?:(?:[sS](?P<season>\d{1,2})[eE](?P<episode>\d{1,2}))|(?:(?P<alt_season>\d{1,2})x(?P<alt_episode>\d{1,2})))(?:[. _-]+(?P<title>.*))?|[. _-]+[sS](?P<season2>\d{1,2})[. _-]+[eE](?P<episode2>\d{1,2}))",
        name_part,
    )

    if season_ep_match:
        match_dict = season_ep_match.groupdict()
        title_part = match_dict["show_name"]
        title = title_part.replace(".", " ").replace("_", " ").replace("-", " ").strip()
        # Remove multiple spaces
        title = " ".join(title.split())

        # Get season and episode numbers
        season = int(match_dict["season"] or match_dict["alt_season"] or match_dict["season2"] or 0)
        episode = int(
            match_dict["episode"] or match_dict["alt_episode"] or match_dict["episode2"] or 0
        )
        episodes = [episode]

        if match_dict.get("title"):
            episode_title = (
                match_dict["title"].replace(".", " ").replace("_", " ").replace("-", " ").strip()
            )
            # Remove multiple spaces
            episode_title = " ".join(episode_title.split())

        # Set confidence based on available information
        confidence = 0.8  # Default confidence
        if match_dict.get("alt_season") or match_dict.get("alt_episode"):
            confidence = 0.85  # Higher confidence for alternative format (1x01)
        elif episode_title or quality:
            confidence = 0.85  # Higher confidence when episode title or quality is present

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

    # Special case for TV specials
    elif media_type == MediaType.TV_SPECIAL:
        # Extract title by taking everything before "Special" or "OVA"
        special_match = re.search(r"(Special|OVA)", name_part, re.IGNORECASE)
        if special_match:
            title_part = name_part[: special_match.start()]
            title = title_part.replace(".", " ").replace("_", " ").replace("-", " ").strip()
            # Remove multiple spaces
            title = " ".join(title.split())
        confidence = 0.85  # Moderate confidence for specials

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

    name_part = Path(filename).stem

    # Extract quality components
    quality_parts = []
    quality_patterns = [
        r"(4K)",  # 4K resolution
        r"(\d{3,4}p)",  # 720p, 1080p, etc.
        r"(HDTV|WEB-DL|BluRay|BRRip)",  # Source
        r"(x264|x265|HEVC)",  # Codec
    ]

    # Extract all quality components
    for pattern in quality_patterns:
        match = re.search(pattern, name_part, re.IGNORECASE)
        if match:
            quality_parts.append(match.group(1))
            name_part = re.sub(pattern, "", name_part, flags=re.IGNORECASE)

    quality = " ".join(quality_parts) if quality_parts else None

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


def parse_anime(filename: str, media_type: Optional[MediaType] = None) -> ParsedMediaName:
    """
    Parse an anime filename into its components.

    Args:
        filename: The filename to parse
        media_type: Optional media type to use (defaults to ANIME)

    Returns:
        ParsedMediaName: Object containing parsed information
    """
    # Base information
    media_type = media_type or MediaType.ANIME
    extension = Path(filename).suffix
    title = ""
    episodes = []
    quality = None
    group = None
    version = None
    special_type = None
    special_number = None
    confidence = 0.8  # Default confidence

    name_part = Path(filename).stem

    # Extract quality components
    quality_parts = []
    quality_patterns = [
        r"(\d{3,4}p)",  # 720p, 1080p, etc.
        r"(HDTV|WEB-DL|BluRay|BRRip)",  # Source
        r"(x264|x265|HEVC)",  # Codec
    ]

    # Extract all quality components
    for pattern in quality_patterns:
        match = re.search(pattern, name_part, re.IGNORECASE)
        if match:
            quality_parts.append(match.group(1))
            name_part = re.sub(pattern, "", name_part, flags=re.IGNORECASE)

    quality = " ".join(quality_parts) if quality_parts else None

    # Extract group name(s) from brackets at start
    group_parts = []
    while name_part.startswith("["):
        group_match = re.match(r"^\[([^\]]+)\]", name_part)
        if group_match:
            group_parts.append(group_match.group(1))
            name_part = name_part[len(group_match.group(0)) :].strip()
        else:
            break

    if group_parts:
        group = group_parts[0]  # Only use the first group
        confidence = 0.9  # Higher confidence when group is present

    # Check for special episode types
    special_match = re.search(r"\b(OVA|Special|Movie)\d*\b", name_part, re.IGNORECASE)
    if special_match:
        media_type = MediaType.ANIME_SPECIAL
        special_type = special_match.group(1)
        special_number = 1  # Default to 1 if not specified
        # Look for a number after the special type
        number_match = re.search(rf"{special_type}(\d+)", name_part, re.IGNORECASE)
        if number_match:
            special_number = int(number_match.group(1))
        # Remove the special part from the name_part
        name_part = re.sub(rf"{special_type}\d*", "", name_part, flags=re.IGNORECASE)
        confidence = 0.95  # Higher confidence for special episodes

    # Extract title and episode number
    title_ep_match = re.search(r"(.*?)(?:\s*-\s*(\d+(?:v\d)?|\w+\d*))?(?:\s*\[.*)?$", name_part)
    if title_ep_match:
        title = title_ep_match.group(1).strip()
        # Clean up trailing hyphens
        title = re.sub(r"\s*-\s*$", "", title)
        if title_ep_match.group(2):
            episode_str = title_ep_match.group(2)
            # Check for version number
            version_match = re.search(r"v(\d+)$", episode_str)
            if version_match:
                version = int(version_match.group(1))
                episode_str = re.sub(r"v\d+$", "", episode_str)
                confidence = 0.95  # Higher confidence when version is present

            try:
                episode_num = int(episode_str)
                episodes = [episode_num]
                if not version:  # Only increase confidence if not already increased
                    confidence = 0.9  # Higher confidence when episode number is present
            except ValueError:
                # Handle non-numeric episode strings (e.g., OVA1)
                pass
    else:
        title = name_part.strip()

    # Clean up title
    title = title.replace(".", " ").replace("_", " ").strip()

    # If we have a title with a year in parentheses, keep it that way
    year_match = re.search(r"(.*?) \((\d{4})\)", title)
    if year_match:
        title = f"{year_match.group(1)} ({year_match.group(2)})"

    return ParsedMediaName(
        media_type=media_type,
        title=title,
        extension=extension,
        quality=quality,
        group=group,
        version=version,
        episodes=episodes,
        special_type=special_type,
        special_number=special_number,
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
        return parse_tv_show(filename, media_type)
    elif media_type == MediaType.MOVIE:
        return parse_movie(filename)
    elif media_type == MediaType.ANIME or media_type == MediaType.ANIME_SPECIAL:
        return parse_anime(filename, media_type)
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
