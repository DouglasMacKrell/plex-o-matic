"""Templates types and related constants for the name templates system.

This module provides the basic types, constants, and helper functions
for the name templates system. It's used by the template manager and
template formatters to handle different media types and their templates.
"""

import os
import enum
from pathlib import Path
from typing import Optional, Dict

from plexomatic.core.constants import MediaType


class TemplateType(enum.Enum):
    """Enum representing types of templates available in the system.

    Each template type corresponds to a specific media type category.
    """

    TV_SHOW = "tv_show"
    MOVIE = "movie"
    ANIME = "anime"
    CUSTOM = "custom"

    def __str__(self) -> str:
        """Return string representation of the template type.

        Returns:
            String value of the template type
        """
        return self.value

    @classmethod
    def from_media_type(cls, media_type: MediaType) -> "TemplateType":
        """Convert MediaType to TemplateType.

        Args:
            media_type: The MediaType to convert.

        Returns:
            The corresponding TemplateType.
        """
        return normalize_media_type(media_type)


# Default templates directory is in the user's home directory
HOME_DIR = Path(os.environ.get("HOME", os.path.expanduser("~")))
DEFAULT_TEMPLATES_DIR = HOME_DIR / ".plexomatic" / "templates"

# Default template strings for each media type
DEFAULT_TV_TEMPLATE = "{title}.S{season:02d}E{episode:02d}.{quality}.{extension}"
DEFAULT_MOVIE_TEMPLATE = "{title}.{year}.{quality}.{extension}"
DEFAULT_ANIME_TEMPLATE = "[{group}] {title} - {episode:02d} [{quality}].{extension}"

# Mapping of template types to their default template strings
DEFAULT_TEMPLATES: Dict[TemplateType, str] = {
    TemplateType.TV_SHOW: DEFAULT_TV_TEMPLATE,
    TemplateType.MOVIE: DEFAULT_MOVIE_TEMPLATE,
    TemplateType.ANIME: DEFAULT_ANIME_TEMPLATE,
    TemplateType.CUSTOM: DEFAULT_TV_TEMPLATE,  # Fallback to TV show template
}


def normalize_media_type(media_type: Optional[MediaType]) -> TemplateType:
    """Convert a MediaType to a TemplateType.

    Args:
        media_type: The MediaType to convert

    Returns:
        The corresponding TemplateType

    Raises:
        TypeError: If media_type is not None or a MediaType
    """
    if media_type is None:
        return TemplateType.TV_SHOW  # Default

    if not isinstance(media_type, MediaType):
        raise TypeError(f"Expected MediaType, got {type(media_type)}")

    if media_type in (MediaType.TV_SHOW, MediaType.TV_SPECIAL):
        return TemplateType.TV_SHOW
    elif media_type == MediaType.MOVIE:
        return TemplateType.MOVIE
    elif media_type in (MediaType.ANIME, MediaType.ANIME_SPECIAL):
        return TemplateType.ANIME
    else:
        return TemplateType.TV_SHOW  # Default for unknown types


def get_default_template_for_media_type(template_type: Optional[TemplateType]) -> str:
    """Get the default template string for a template type.

    Args:
        template_type: The template type to get the default template for

    Returns:
        The default template string for the template type
    """
    if template_type is None:
        return DEFAULT_TV_TEMPLATE

    return DEFAULT_TEMPLATES.get(template_type, DEFAULT_TV_TEMPLATE)


def get_default_template_dir() -> Path:
    """Get the default templates directory.

    Returns:
        Path to the default templates directory
    """
    return DEFAULT_TEMPLATES_DIR


def get_custom_template_dir() -> Path:
    """Get the custom templates directory.

    Returns:
        Path to the custom templates directory
    """
    return DEFAULT_TEMPLATES_DIR / "custom"
