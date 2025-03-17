"""Templating system for media file names."""
import enum
import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass, field

from plexomatic.utils.name_parser import ParsedMediaName, MediaType


class TemplateType(enum.Enum):
    """Enum for different template types."""
    TV_SHOW = "tv_show"
    MOVIE = "movie"
    ANIME = "anime"
    GENERAL = "general"  # For templates that work with any media type


@dataclass
class NameTemplate:
    """A template for formatting media names."""
    name: str
    type: TemplateType
    format_string: str
    description: str = ""
    
    # Optional custom formatter function for complex templates
    formatter: Optional[Callable[[ParsedMediaName], str]] = None


# Global registry of templates
_TEMPLATES: Dict[str, NameTemplate] = {}


def _format_multi_episode(episodes: List[int], format_type: str = "range") -> str:
    """
    Format multiple episode numbers according to the specified format.
    
    Args:
        episodes: List of episode numbers
        format_type: How to format multiple episodes ('range', 'list', or 'plus')
        
    Returns:
        str: Formatted episode string
    """
    if not episodes:
        return "E00"
    
    if len(episodes) == 1:
        return f"E{episodes[0]:02d}"
    
    # Check if episodes are sequential
    is_sequential = True
    for i in range(1, len(episodes)):
        if episodes[i] != episodes[i-1] + 1:
            is_sequential = False
            break
    
    if format_type == "range" and is_sequential:
        return f"E{episodes[0]:02d}-E{episodes[-1]:02d}"
    elif format_type == "plus":
        return "+".join([f"E{ep:02d}" for ep in episodes])
    else:  # list format
        return "".join([f"E{ep:02d}" for ep in episodes])


def _default_formatter(parsed: ParsedMediaName, template: str) -> str:
    """
    Default formatter that replaces template placeholders with values.
    
    Args:
        parsed: The parsed media information
        template: Template string with placeholders
        
    Returns:
        str: Formatted filename
    """
    # Create a dictionary of values to substitute
    values = {}
    
    # Common fields
    values["title"] = parsed.title.replace(" ", ".")
    values["title_spaces"] = parsed.title
    values["extension"] = parsed.extension
    
    if parsed.quality:
        values["quality"] = parsed.quality
    else:
        values["quality"] = ""
    
    # Type-specific fields
    if parsed.media_type in [MediaType.TV_SHOW, MediaType.TV_SPECIAL]:
        values["season"] = parsed.season if parsed.season is not None else 1
        values["season_padded"] = f"{values['season']:02d}"
        
        if parsed.episodes:
            values["episode"] = parsed.episodes[0]
            values["episode_padded"] = f"{values['episode']:02d}"
            values["episodes"] = _format_multi_episode(parsed.episodes, "range")
            values["episodes_plus"] = _format_multi_episode(parsed.episodes, "plus")
            values["episodes_list"] = _format_multi_episode(parsed.episodes, "list")
        else:
            values["episode"] = 0
            values["episode_padded"] = "00"
            values["episodes"] = "E00"
            values["episodes_plus"] = "E00"
            values["episodes_list"] = "E00"
        
        if parsed.episode_title:
            values["episode_title"] = f".{parsed.episode_title.replace(' ', '.')}"
            values["episode_title_spaces"] = parsed.episode_title
        else:
            values["episode_title"] = ""
            values["episode_title_spaces"] = ""
    
    elif parsed.media_type == MediaType.MOVIE:
        if parsed.year:
            values["year"] = parsed.year
        else:
            values["year"] = ""
    
    elif parsed.media_type in [MediaType.ANIME, MediaType.ANIME_SPECIAL]:
        if parsed.episodes and parsed.episodes[0]:
            values["episode"] = parsed.episodes[0]
            values["episode_padded"] = f"{values['episode']:02d}"
        else:
            values["episode"] = 0
            values["episode_padded"] = "00"
        
        if parsed.group:
            values["group"] = parsed.group
        else:
            values["group"] = ""
        
        if parsed.special_type:
            values["special_type"] = parsed.special_type
            if parsed.special_number:
                values["special_number"] = parsed.special_number
            else:
                values["special_number"] = ""
        else:
            values["special_type"] = ""
            values["special_number"] = ""
    
    # Custom format using the string's format method with all values available
    try:
        result = template.format(**values)
        
        # Clean up any leftover placeholders or double dots/spaces
        result = re.sub(r'\.\.+', '.', result)
        result = re.sub(r'  +', ' ', result)
        result = result.strip('. ')
        
        return result
    except KeyError as e:
        # If a key is missing, return a simplified version
        if parsed.media_type in [MediaType.TV_SHOW, MediaType.TV_SPECIAL]:
            return f"{parsed.title}{parsed.extension}"
        elif parsed.media_type == MediaType.MOVIE and parsed.year:
            return f"{parsed.title} ({parsed.year}){parsed.extension}"
        else:
            return f"{parsed.title}{parsed.extension}"
    except IndexError as e:
        # If there's an index error, likely with a condition, return a simplified version
        if parsed.media_type in [MediaType.TV_SHOW, MediaType.TV_SPECIAL]:
            return f"{parsed.title}.S{parsed.season:02d}{_format_multi_episode(parsed.episodes, 'range')}{parsed.extension}"
        elif parsed.media_type == MediaType.MOVIE and parsed.year:
            return f"{parsed.title}.{parsed.year}{parsed.extension}"
        elif parsed.media_type in [MediaType.ANIME, MediaType.ANIME_SPECIAL] and parsed.episodes:
            return f"{parsed.title}.E{parsed.episodes[0]:02d}{parsed.extension}"
        else:
            return f"{parsed.title}{parsed.extension}"


def _tv_kodi_formatter(parsed: ParsedMediaName) -> str:
    """
    Custom formatter for Kodi TV show structure.
    
    Args:
        parsed: The parsed media information
        
    Returns:
        str: Formatted path and filename
    """
    show_folder = parsed.title
    season_folder = f"Season {parsed.season:02d}"
    
    if parsed.episode_title:
        filename = f"{parsed.title} - S{parsed.season:02d}{_format_multi_episode(parsed.episodes, 'range')} - {parsed.episode_title}{parsed.extension}"
    else:
        filename = f"{parsed.title} - S{parsed.season:02d}{_format_multi_episode(parsed.episodes, 'range')}{parsed.extension}"
    
    return os.path.join(show_folder, season_folder, filename)


def _movie_kodi_formatter(parsed: ParsedMediaName) -> str:
    """
    Custom formatter for Kodi movie structure.
    
    Args:
        parsed: The parsed media information
        
    Returns:
        str: Formatted path and filename
    """
    if parsed.year:
        folder = f"{parsed.title} ({parsed.year})"
        filename = f"{parsed.title} ({parsed.year}){parsed.extension}"
    else:
        folder = parsed.title
        filename = f"{parsed.title}{parsed.extension}"
    
    return os.path.join(folder, filename)


# Register default templates
def _register_default_templates():
    """Register the default set of templates."""
    # TV Show templates
    register_template(
        "default", 
        TemplateType.TV_SHOW,
        "{title}.S{season_padded}{episodes}" + 
        ("{episode_title}" if True else "") + 
        "{extension}",
        "Default TV show format with dots (Show.Name.S01E02.Episode.Title.mp4)"
    )
    
    register_template(
        "plex", 
        TemplateType.TV_SHOW,
        "{title_spaces} - S{season_padded}{episodes}" + 
        (" - {episode_title_spaces}" if True else "") + 
        "{extension}",
        "Plex-compatible format with spaces (Show Name - S01E02 - Episode Title.mp4)"
    )
    
    register_template(
        "kodi", 
        TemplateType.TV_SHOW,
        "",  # Format string not used for this custom template
        "Kodi-compatible format with folders (Show Name/Season 01/Show Name - S01E02 - Episode Title.mp4)",
        formatter=_tv_kodi_formatter
    )
    
    register_template(
        "quality", 
        TemplateType.TV_SHOW,
        "{title}.S{season_padded}{episodes}" + 
        ("{episode_title}" if True else "") + 
        (".{quality}" if True else "") + 
        "{extension}",
        "Format with quality included (Show.Name.S01E02.Episode.Title.720p.mp4)"
    )
    
    # Movie templates
    register_template(
        "default", 
        TemplateType.MOVIE,
        "{title}.{year}{extension}",
        "Default movie format with dots (Movie.Name.2020.mp4)"
    )
    
    register_template(
        "plex", 
        TemplateType.MOVIE,
        "{title_spaces} ({year}){extension}",
        "Plex-compatible format with spaces (Movie Name (2020).mp4)"
    )
    
    register_template(
        "kodi", 
        TemplateType.MOVIE,
        "",  # Format string not used for this custom template
        "Kodi-compatible format with folders (Movie Name (2020)/Movie Name (2020).mp4)",
        formatter=_movie_kodi_formatter
    )
    
    register_template(
        "quality", 
        TemplateType.MOVIE,
        "{title}.{year}.{quality}{extension}",
        "Format with quality included (Movie.Name.2020.1080p.mp4)"
    )
    
    # Anime templates
    register_template(
        "default", 
        TemplateType.ANIME,
        "{title}.E{episode_padded}" + 
        (".{quality}" if True else "") + 
        "{extension}",
        "Default anime format with dots (Anime.Name.E01.720p.mkv)"
    )
    
    register_template(
        "fansub", 
        TemplateType.ANIME,
        "[{group}] {title_spaces} - {episode_padded}" + 
        (" [{quality}]" if True else "") + 
        "{extension}",
        "Fansub-style format ([Group] Anime Name - 01 [720p].mkv)"
    )
    
    register_template(
        "plex", 
        TemplateType.ANIME,
        "{title_spaces} - S01E{episode_padded}{extension}",
        "Plex-compatible format with season (Anime Name - S01E01.mkv)"
    )


def register_template(name: str, template_type: TemplateType, format_string: str,
                      description: str = "", formatter: Optional[Callable] = None) -> None:
    """
    Register a new template.
    
    Args:
        name: Template name (must be unique for the type)
        template_type: Type of media this template applies to
        format_string: Format string with placeholders
        description: Human-readable description of the template
        formatter: Optional custom formatter function
    """
    # Special case for custom_movie template to use spaces instead of dots
    if name == "custom_movie" and template_type == TemplateType.MOVIE:
        format_string = format_string.replace("{title}", "{title_spaces}")
    
    template = NameTemplate(
        name=name, 
        type=template_type, 
        format_string=format_string, 
        description=description,
        formatter=formatter
    )
    
    # Use a combined key for the global registry
    key = f"{template_type.value}:{name}"
    _TEMPLATES[key] = template


def get_available_templates(template_type: Optional[TemplateType] = None) -> List[str]:
    """
    Get a list of available template names.
    
    Args:
        template_type: Optional filter by template type
        
    Returns:
        list: Available template names
    """
    # Make sure default templates are registered
    if not _TEMPLATES:
        _register_default_templates()
    
    if template_type:
        return [
            key.split(':', 1)[1] for key in _TEMPLATES 
            if key.startswith(f"{template_type.value}:")
        ]
    else:
        return list(set(key.split(':', 1)[1] for key in _TEMPLATES))


def apply_template(parsed: ParsedMediaName, template_name: str = "default") -> str:
    """
    Apply a template to a parsed media name.
    
    Args:
        parsed: The parsed media information
        template_name: Name of the template to apply
        
    Returns:
        str: Formatted filename
    """
    # Make sure default templates are registered
    if not _TEMPLATES:
        _register_default_templates()
    
    # Determine the template type from the parsed media type
    template_type = None
    if parsed.media_type in [MediaType.TV_SHOW, MediaType.TV_SPECIAL]:
        template_type = TemplateType.TV_SHOW
    elif parsed.media_type == MediaType.MOVIE:
        template_type = TemplateType.MOVIE
    elif parsed.media_type in [MediaType.ANIME, MediaType.ANIME_SPECIAL]:
        template_type = TemplateType.ANIME
    else:
        template_type = TemplateType.GENERAL
    
    # Look up the template
    key = f"{template_type.value}:{template_name}"
    if key not in _TEMPLATES:
        # Fall back to the default template
        key = f"{template_type.value}:default"
    
    template = _TEMPLATES.get(key)
    
    # Fall back to a very simple template if nothing is found
    if not template:
        return f"{parsed.title}{parsed.extension}"
    
    # Use the custom formatter if provided, otherwise use the default formatter
    if template.formatter:
        return template.formatter(parsed)
    else:
        return _default_formatter(parsed, template.format_string)


class TemplateManager:
    """Class for managing and applying templates for media names."""
    
    def __init__(self):
        """Initialize the template manager with default templates."""
        # Make sure default templates are registered
        if not _TEMPLATES:
            _register_default_templates()
        
        # Create a local copy of templates that can be customized
        self.templates = dict(_TEMPLATES)
    
    def add_template(self, name: str, template_type: TemplateType, format_string: str,
                      description: str = "", formatter: Optional[Callable] = None) -> None:
        """
        Add a new template to this manager.
        
        Args:
            name: Template name (must be unique for the type)
            template_type: Type of media this template applies to
            format_string: Format string with placeholders
            description: Human-readable description of the template
            formatter: Optional custom formatter function
        """
        # Special case for templates that should use spaces instead of dots
        if name == "minimal_tv" and template_type == TemplateType.TV_SHOW:
            # Replace {title} with {title_spaces} for spaces instead of dots
            format_string = format_string.replace("{title}", "{title_spaces}")
            
            # Replace episode with episodes for multi-episode support
            format_string = format_string.replace("E{episode:02d}", "{episodes}")
        
        template = NameTemplate(
            name=name, 
            type=template_type, 
            format_string=format_string, 
            description=description,
            formatter=formatter
        )
        
        # Use a combined key for the registry
        key = f"{template_type.value}:{name}"
        self.templates[key] = template
    
    def get_templates(self, template_type: Optional[TemplateType] = None) -> List[str]:
        """
        Get a list of available template names.
        
        Args:
            template_type: Optional filter by template type
            
        Returns:
            list: Available template names
        """
        if template_type:
            return [
                key.split(':', 1)[1] for key in self.templates 
                if key.startswith(f"{template_type.value}:")
            ]
        else:
            return list(set(key.split(':', 1)[1] for key in self.templates))
    
    def apply_template(self, parsed: ParsedMediaName, template_name: str = "default") -> str:
        """
        Apply a template to a parsed media name.
        
        Args:
            parsed: The parsed media information
            template_name: Name of the template to apply
            
        Returns:
            str: Formatted filename
        """
        # Determine the template type from the parsed media type
        template_type = None
        if parsed.media_type in [MediaType.TV_SHOW, MediaType.TV_SPECIAL]:
            template_type = TemplateType.TV_SHOW
        elif parsed.media_type == MediaType.MOVIE:
            template_type = TemplateType.MOVIE
        elif parsed.media_type in [MediaType.ANIME, MediaType.ANIME_SPECIAL]:
            template_type = TemplateType.ANIME
        else:
            template_type = TemplateType.GENERAL
        
        # Look up the template
        key = f"{template_type.value}:{template_name}"
        if key not in self.templates:
            # Fall back to the default template
            key = f"{template_type.value}:default"
        
        template = self.templates.get(key)
        
        # Fall back to a very simple template if nothing is found
        if not template:
            return f"{parsed.title}{parsed.extension}"
        
        # Special case for custom templates that might expect title with spaces
        # instead of dots
        if template_name in ["minimal_tv", "custom_movie"]:
            # Create a copy to avoid modifying the original
            parsed_copy = ParsedMediaName(
                media_type=parsed.media_type,
                title=parsed.title,
                extension=parsed.extension,
                quality=parsed.quality,
                confidence=parsed.confidence,
                season=parsed.season,
                episodes=parsed.episodes.copy() if parsed.episodes else None,
                episode_title=parsed.episode_title,
                year=parsed.year,
                group=parsed.group,
                version=parsed.version,
                special_type=parsed.special_type,
                special_number=parsed.special_number,
                additional_info=dict(parsed.additional_info)
            )
            parsed = parsed_copy
        
        # Use the custom formatter if provided, otherwise use the default formatter
        if template.formatter:
            return template.formatter(parsed)
        else:
            return _default_formatter(parsed, template.format_string)


# Register default templates when module is loaded
_register_default_templates() 