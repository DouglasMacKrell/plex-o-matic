"""Module for managing media file name templates and format strings.

This module provides classes and functions for managing templates for media file names
and applying format strings to generate consistent filenames.
"""

import logging
from pathlib import Path
from typing import Any, Callable, Optional

# Python 3.9+ has native support for these types
try:
    from typing import Dict, List
except ImportError:
    # Python 3.8 compatibility
    try:
        from typing_extensions import Dict, List
    except ImportError:
        from typing import Dict, List

from plexomatic.core.models import MediaType
from plexomatic.utils.name_parser import ParsedMediaName

logger = logging.getLogger(__name__)

# Default templates directory
DEFAULT_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Default templates for different media types
DEFAULT_TV_TEMPLATE = "{title}/Season {season:02d}/{title} - S{season:02d}E{episode:02d}{episode_title_suffix}{quality_suffix}"
DEFAULT_MOVIE_TEMPLATE = "{title} ({year}){quality_suffix}"
DEFAULT_ANIME_TEMPLATE = "Anime/{title}/Season {season:02d}/{title} - {episode:02d}{episode_title_suffix}{quality_suffix}"


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
            templates_dir: Directory where templates are stored, or None to use default
        """
        self.templates_dir = templates_dir or DEFAULT_TEMPLATES_DIR
        self.formatters: Dict[str, Callable[[Any], str]] = {
            "episode_title_suffix": format_episode_title_suffix,
            "quality_suffix": format_quality_suffix,
        }
        self.templates: Dict[MediaType, str] = {
            MediaType.TV_SHOW: DEFAULT_TV_TEMPLATE,
            MediaType.MOVIE: DEFAULT_MOVIE_TEMPLATE,
            MediaType.ANIME: DEFAULT_ANIME_TEMPLATE,
            MediaType.TV_SPECIAL: DEFAULT_TV_TEMPLATE,  # Use TV template for specials
            MediaType.ANIME_SPECIAL: DEFAULT_ANIME_TEMPLATE,  # Use anime template for anime specials
        }
        self._load_templates()

    def _load_templates(self) -> None:
        """Load templates from the templates directory."""
        if not self.templates_dir.exists():
            logger.info(f"Templates directory {self.templates_dir} does not exist, using defaults")
            return

        for template_file in self.templates_dir.glob("*.template"):
            try:
                media_type_str = template_file.stem.upper()
                try:
                    media_type = MediaType[media_type_str]
                except KeyError:
                    logger.warning(
                        f"Unknown media type {media_type_str} in template file {template_file}"
                    )
                    continue

                with open(template_file, "r") as f:
                    template = f.read().strip()
                    if template:
                        self.templates[media_type] = template
                        logger.debug(f"Loaded template for {media_type}: {template}")
            except Exception as e:
                logger.error(f"Error loading template {template_file}: {e}")

    def register_formatter(self, name: str, formatter: Callable[[Any], str]) -> None:
        """Register a custom formatter function.

        Args:
            name: Name of the formatter to use in templates
            formatter: Function that takes a value and returns a formatted string
        """
        self.formatters[name] = formatter
        logger.debug(f"Registered formatter {name}")

    def register_template(self, media_type: MediaType, template: str) -> None:
        """Register a custom template for a media type.

        Args:
            media_type: Type of media (TV show, movie, anime, etc.)
            template: Template string
        """
        self.templates[media_type] = template
        logger.debug(f"Registered template for {media_type}: {template}")

    def get_template(self, media_type: MediaType) -> str:
        """Get the template for a media type.

        Args:
            media_type: Type of media (TV show, movie, anime, etc.)

        Returns:
            Template string for the media type
        """
        return self.templates.get(media_type, DEFAULT_TV_TEMPLATE)

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
        if parsed.media_type in (MediaType.TV_SPECIAL, MediaType.ANIME_SPECIAL):
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
        """Format a media name using the appropriate template.

        Args:
            parsed: Parsed media name

        Returns:
            Formatted media name
        """
        template = self.get_template(parsed.media_type)
        return self._format_with_template(parsed, template)

    def _format_with_template(self, parsed: ParsedMediaName, template: str) -> str:
        """Format a parsed media name with a specific template.

        Args:
            parsed: Parsed media name
            template: Template string to use

        Returns:
            Formatted name
        """
        # Create a dictionary of values to format
        format_values = {
            "title": parsed.title or "Unknown",
            "season": parsed.season or 1,
            "episode": parsed.episode or 1,
            "year": parsed.year or "",
            "quality": parsed.quality or "",
            "episode_title": parsed.episode_title or "",
            "group": parsed.group or "",
        }

        # Add any extra info
        if parsed.extra_info:
            format_values.update(parsed.extra_info)

        # Apply custom formatters
        for name, formatter in self.formatters.items():
            format_values[name] = formatter(format_values.get(name.replace("_suffix", ""), ""))

        try:
            # Format the template with the values
            result = template.format(**format_values)
            logger.debug(f"Formatted {parsed.media_type} name: {result}")
            return result
        except KeyError as e:
            logger.warning(f"Missing key in template {template}: {e}")
            # Fall back to a simpler template
            if parsed.media_type in (MediaType.TV_SHOW, MediaType.TV_SPECIAL):
                return f"{parsed.title or 'Unknown'} - S{parsed.season or 1:02d}E{parsed.episode or 1:02d}"
            elif parsed.media_type in (MediaType.ANIME, MediaType.ANIME_SPECIAL):
                return f"{parsed.title or 'Unknown'} - {parsed.episode or 1:02d}"
            else:  # Movie or unknown
                return f"{parsed.title or 'Unknown'} ({parsed.year or 'Unknown Year'})"
        except Exception as e:
            logger.error(f"Error formatting template {template}: {e}")
            return f"{parsed.title or 'Unknown'}"


# Singleton template manager
template_manager = TemplateManager()
