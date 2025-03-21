"""Module for managing media file name templates and format strings.

This module provides classes and functions for managing templates for media file names
and applying format strings to generate consistent filenames.
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional, Union, Dict, List

# Used to verify Python 3.8 compatibility at runtime
try:
    from typing import Literal  # noqa: F401
except ImportError:
    from typing_extensions import Literal  # noqa: F401

from plexomatic.core.models import MediaType as CoreMediaType
from plexomatic.utils.name_parser import ParsedMediaName, MediaType as ParserMediaType

# Create a unified MediaType for internal use
MediaType = Union[CoreMediaType, ParserMediaType]

logger = logging.getLogger(__name__)


class TemplateType(Enum):
    """Enum for template types."""

    TV_SHOW = "tv_show"
    MOVIE = "movie"
    ANIME = "anime"
    GENERAL = "general"


# Helper function to normalize MediaType between different implementations
def normalize_media_type(media_type: MediaType) -> str:
    """Normalize MediaType to a standard string representation.

    This handles both CoreMediaType and ParserMediaType implementations.
    """
    return media_type.name


# Default templates directory
DEFAULT_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Default templates for different media types
DEFAULT_TV_TEMPLATE = "{title}/Season {season:02d}/{title} - S{season:02d}E{episode:02d}{episode_title_suffix}{quality_suffix}"
DEFAULT_MOVIE_TEMPLATE = "{title} ({year}){quality_suffix}"
DEFAULT_ANIME_TEMPLATE = "{title}/Season {season:02d}/{title} - S{season:02d}E{episode:02d}{episode_title_suffix} [{group}]"


# Formatter functions
def format_episode_title_suffix(episode_title: Optional[str]) -> str:
    """Format the episode title suffix.

    Args:
        episode_title: The episode title

    Returns:
        Formatted episode title suffix (e.g., " - Title" or empty string)
    """
    return f" - {episode_title}" if episode_title else ""


def format_quality_suffix(quality: Optional[str]) -> str:
    """Format the quality suffix.

    Args:
        quality: The quality string (e.g., "1080p", "720p")

    Returns:
        Formatted quality suffix (e.g., " [1080p]" or empty string)
    """
    return f" [{quality}]" if quality else ""


def ensure_episode_list(episodes: Any) -> List[int]:
    """Ensure that episodes is a list of integers.

    Args:
        episodes: Episode number(s) as int, str, or list

    Returns:
        List of episode numbers as integers
    """
    if episodes is None:
        return []
    if isinstance(episodes, int):
        return [episodes]
    if isinstance(episodes, str):
        try:
            return [int(episodes)]
        except ValueError:
            # Try to parse a range like "1-3"
            if "-" in episodes:
                try:
                    start, end = episodes.split("-", 1)
                    return list(range(int(start), int(end) + 1))
                except (ValueError, TypeError):
                    pass
            # Try to parse a list like "1,2,3"
            if "," in episodes:
                try:
                    return [int(ep.strip()) for ep in episodes.split(",")]
                except (ValueError, TypeError):
                    pass
            return []
    if isinstance(episodes, list):
        return [int(ep) if not isinstance(ep, int) else ep for ep in episodes if ep]
    return []


class TemplateManager:
    """Manager for file name templates."""

    def __init__(self, templates_dir: Optional[Path] = None):
        """Initialize the template manager.

        Args:
            templates_dir: Path to the templates directory. If None, uses the default.
        """
        self.templates_dir = templates_dir or DEFAULT_TEMPLATES_DIR
        self._formatters = {
            "episode_title_suffix": format_episode_title_suffix,
            "quality_suffix": format_quality_suffix,
        }
        self._templates: Dict[str, str] = {
            "TV_SHOW": DEFAULT_TV_TEMPLATE,
            "MOVIE": DEFAULT_MOVIE_TEMPLATE,
            "ANIME": DEFAULT_ANIME_TEMPLATE,
            "TV_SPECIAL": DEFAULT_TV_TEMPLATE,  # Use TV template for specials
            "ANIME_SPECIAL": DEFAULT_ANIME_TEMPLATE,  # Use anime template for anime specials
            "UNKNOWN": DEFAULT_TV_TEMPLATE,  # Fallback
        }
        self._load_templates()

    def _load_templates(self) -> None:
        """Load templates from the templates directory."""
        if not self.templates_dir.exists():
            logger.warning(f"Templates directory {self.templates_dir} does not exist")
            return

        # Map of file names to media types
        file_map = {
            "tv_show.template": "TV_SHOW",
            "movie.template": "MOVIE",
            "anime.template": "ANIME",
            "tv_special.template": "TV_SPECIAL",
            "anime_special.template": "ANIME_SPECIAL",
            "general.template": "UNKNOWN",
        }

        for file_name, media_type_str in file_map.items():
            template_file = self.templates_dir / file_name
            if template_file.exists():
                try:
                    with open(template_file, "r") as f:
                        template = f.read().strip()
                        if template:
                            self._templates[media_type_str] = template
                            logger.debug(f"Loaded template for {media_type_str}: {template}")
                except Exception as e:
                    logger.error(f"Error loading template {template_file}: {e}")

    def register_formatter(self, name: str, formatter: Callable[[Any], str]) -> None:
        """Register a custom formatter function.

        Args:
            name: Name of the formatter to use in templates
            formatter: Function that takes a value and returns a formatted string
        """
        self._formatters[name] = formatter
        logger.debug(f"Registered formatter {name}")

    def register_template(self, media_type: MediaType, template: str) -> None:
        """Register a template for a specific media type.

        Args:
            media_type: The MediaType enum value.
            template: The template string.
        """
        media_type_name = normalize_media_type(media_type)
        self._templates[media_type_name] = template
        logger.debug(f"Registered template for {media_type_name}: {template}")

    def get_template(self, media_type: MediaType) -> str:
        """Get the template string for a specific media type.

        Args:
            media_type: The MediaType enum value.

        Returns:
            The template string.
        """
        media_type_name = normalize_media_type(media_type)
        return self._templates.get(
            media_type_name, self._templates.get("UNKNOWN", DEFAULT_TV_TEMPLATE)
        )

    def format_multi_episode(
        self, parsed: ParsedMediaName, episodes: List[int], separator: str = "-"
    ) -> str:
        """Format a multi-episode filename.

        Args:
            parsed: Parsed media name
            episodes: List of episode numbers
            separator: Separator to use between episode numbers

        Returns:
            Formatted filename
        """
        if not episodes:
            return ""

        # Handle special episodes
        media_type_name = normalize_media_type(parsed.media_type)
        if media_type_name in ("TV_SPECIAL", "ANIME_SPECIAL"):
            return self.format(parsed)

        # Sort episodes
        episodes = sorted(episodes)

        # If consecutive episodes, use a range
        if len(episodes) > 1 and episodes[-1] - episodes[0] + 1 == len(episodes):
            # Use range for consecutive episodes (e.g., E01-E03)
            parsed_with_range = ParsedMediaName(
                title=parsed.title,
                season=parsed.season,
                episode=episodes[0],
                media_type=parsed.media_type,
                quality=parsed.quality,
                episode_title=parsed.episode_title,
                year=parsed.year,
                group=parsed.group,
                extra_info=parsed.extra_info,
            )
            template = self.get_template(parsed.media_type)

            # Replace episode placeholder with range
            episode_range = f"{episodes[0]:02d}{separator}{episodes[-1]:02d}"
            if "{episode:02d}" in template:
                template = template.replace("{episode:02d}", episode_range)
            elif "{episode}" in template:
                template = template.replace("{episode}", episode_range)
            else:
                # If no episode placeholder in template, append episode range
                template += f"E{episode_range}"

            return self._format_with_template(parsed_with_range, template)
        else:
            # Use concatenated episodes for non-consecutive ones (e.g., E01E03)
            episode_string = "".join(f"E{ep:02d}" for ep in episodes)
            # Replace episode in template with episode string
            template = self.get_template(parsed.media_type)
            if "{episode:02d}" in template:
                template = template.replace("E{episode:02d}", episode_string)
            elif "{episode}" in template:
                template = template.replace("E{episode}", episode_string)
            else:
                template += episode_string

            return self._format_with_template(parsed, template)

    def format(self, parsed: ParsedMediaName) -> str:
        """Format a parsed media name using the appropriate template.

        Args:
            parsed: The parsed media name.

        Returns:
            Formatted string.
        """
        media_type_name = normalize_media_type(parsed.media_type)
        template = self._templates.get(
            media_type_name, self._templates.get("UNKNOWN", DEFAULT_TV_TEMPLATE)
        )
        return self._format_with_template(parsed, template)

    def _format_with_template(self, parsed: ParsedMediaName, template: str) -> str:
        """Format a parsed media name with a specific template.

        Args:
            parsed: The parsed media name.
            template: The template string to use.

        Returns:
            Formatted string.
        """
        # Prepare format values
        format_values = {
            "title": parsed.title.replace(" ", "."),
            "extension": parsed.extension,
            "quality": parsed.quality or "",
        }

        # Add TV show specific fields
        if parsed.season is not None:
            format_values["season"] = parsed.season
        if parsed.episodes:
            if len(parsed.episodes) == 1:
                format_values["episode"] = parsed.episodes[0]
            else:
                # Handle multi-episode case
                return self.format_multi_episode(parsed, parsed.episodes, template=template)
        if parsed.episode_title:
            format_values["episode_title"] = parsed.episode_title.replace(" ", ".")

        # Add movie specific fields
        if parsed.year:
            format_values["year"] = parsed.year

        # Add anime specific fields
        if parsed.group:
            format_values["group"] = parsed.group
        if parsed.version is not None:
            format_values["version"] = parsed.version

        # Apply custom formatters
        for name, formatter in self._formatters.items():
            format_values[name] = formatter(format_values.get(name.replace("_suffix", ""), ""))

        try:
            # Replace dots with spaces for display templates
            if "{title}" in template and "{title.lower()}" not in template:
                format_values["title"] = parsed.title

            if "{episode_title}" in template and parsed.episode_title:
                format_values["episode_title"] = parsed.episode_title

            result = template.format(**format_values)
            return result
        except KeyError as e:
            logger.error(f"Missing key in template: {e}")
            return f"{parsed.title} - Error formatting filename"
        except Exception as e:
            logger.error(f"Error formatting filename: {e}")
            return f"{parsed.title} - Error formatting filename"


# Singleton template manager
template_manager = TemplateManager()


class NameTemplate:
    """Class representing a name template."""

    def __init__(self, name: str, template_type: TemplateType, format_string: str):
        """Initialize a name template.

        Args:
            name: Name of the template
            template_type: Type of the template
            format_string: Format string for the template
        """
        self.name = name
        self.type = template_type
        self.format_string = format_string

    def apply(self, parsed: ParsedMediaName) -> str:
        """Apply the template to a parsed media name.

        Args:
            parsed: Parsed media name

        Returns:
            Formatted string
        """
        return _apply_template(parsed, self.format_string)


# Template registry
_templates: Dict[TemplateType, Dict[str, NameTemplate]] = {
    TemplateType.TV_SHOW: {},
    TemplateType.MOVIE: {},
    TemplateType.ANIME: {},
    TemplateType.GENERAL: {},
}


def _default_formatter(value: Any) -> str:
    """Default formatter for template values.

    Args:
        value: Value to format

    Returns:
        Formatted string
    """
    if value is None:
        return ""
    return str(value)


def _ensure_episode_list(episodes: Any) -> List[int]:
    """Ensure episodes is a list of integers.

    Args:
        episodes: Episode number(s)

    Returns:
        List of episode numbers
    """
    # Reuse existing function
    return ensure_episode_list(episodes)


def _format_multi_episode(
    parsed: ParsedMediaName, episodes: List[int], separator: str = "-"
) -> str:
    """Format a multi-episode filename.

    Args:
        parsed: Parsed media name
        episodes: List of episode numbers
        separator: Separator for episode numbers

    Returns:
        Formatted string
    """
    # Use existing template manager function
    return template_manager.format_multi_episode(parsed, episodes, separator)


def _apply_template(parsed: ParsedMediaName, template: str) -> str:
    """Apply a template to a parsed media name.

    Args:
        parsed: Parsed media name
        template: Template string

    Returns:
        Formatted string
    """
    # Use existing template manager
    return template_manager._format_with_template(parsed, template)


def apply_template(parsed: ParsedMediaName, template_name: str) -> str:
    """Apply a named template to a parsed media name.

    Args:
        parsed: Parsed media name
        template_name: Name of the template

    Returns:
        Formatted string
    """
    media_type_name = normalize_media_type(parsed.media_type)

    # Map MediaType name to TemplateType
    template_type = None
    if media_type_name in ("TV_SHOW", "TV_SPECIAL"):
        template_type = TemplateType.TV_SHOW
    elif media_type_name == "MOVIE":
        template_type = TemplateType.MOVIE
    elif media_type_name in ("ANIME", "ANIME_SPECIAL"):
        template_type = TemplateType.ANIME
    else:
        template_type = TemplateType.GENERAL

    # Find the template
    templates = _templates.get(template_type, {})
    template_obj = templates.get(template_name)

    if template_obj:
        # Use the template directly without going through the template manager
        format_values = {
            "title": parsed.title or "Unknown",
            "season": parsed.season or 1,
            "episode": (
                parsed.episodes[0]
                if parsed.episodes and isinstance(parsed.episodes, list) and parsed.episodes
                else 1
            ),
            "year": parsed.year or "",
            "quality": parsed.quality or "",
            "episode_title": parsed.episode_title or "",
            "group": parsed.group or "",
            "extension": parsed.extension or "",
        }

        try:
            # Format the template with the values
            result = template_obj.format_string.format(**format_values)
            logger.debug(f"Applied template {template_name} to {parsed.media_type}: {result}")
            return result
        except Exception as e:
            logger.error(f"Error applying template {template_name}: {e}")

    # Fallback to using the template manager
    return template_manager.format(parsed)


def register_template(name: str, template_type: TemplateType, format_string: str) -> None:
    """Register a template.

    Args:
        name: Name of the template
        template_type: Type of the template
        format_string: Format string for the template
    """
    template = NameTemplate(name, template_type, format_string)
    _templates[template_type][name] = template
    logger.debug(f"Registered template {name} for {template_type}: {format_string}")


def get_available_templates(template_type: TemplateType) -> Dict[str, NameTemplate]:
    """Get available templates for a template type.

    Args:
        template_type: Type of templates to get

    Returns:
        Dictionary of template name to template object
    """
    return _templates.get(template_type, {})


# Register default templates
register_template(
    "default",
    TemplateType.TV_SHOW,
    "{title}.S{season:02d}E{episode:02d}.{episode_title}.{extension}",
)
register_template(
    "plex",
    TemplateType.TV_SHOW,
    "{title} - S{season:02d}E{episode:02d} - {episode_title}{extension}",
)
register_template("default", TemplateType.MOVIE, "{title}.({year}){extension}")
register_template("plex", TemplateType.MOVIE, "{title} ({year}){extension}")
register_template("default", TemplateType.ANIME, "Anime.{title}.{episode:02d}{extension}")
register_template("plex", TemplateType.ANIME, "Anime/{title} - {episode:02d}{extension}")
