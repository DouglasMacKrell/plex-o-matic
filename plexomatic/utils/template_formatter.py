"""Template formatter for applying templates to parsed media names.

This module provides functions to apply templates to parsed media names,
handling field replacements and format expressions.
"""

import re
import logging
from typing import Any, Optional, Match

from plexomatic.utils.name_parser import ParsedMediaName
from plexomatic.utils.template_types import TemplateType, normalize_media_type
from plexomatic.utils.default_formatters import get_default_formatter
from plexomatic.utils.template_registry import get_template
from plexomatic.core.constants import MediaType as CoreMediaType

logger = logging.getLogger(__name__)

# Regular expression for template variables
VARIABLE_PATTERN = re.compile(r"\{([^{}:]+)(?::([^{}]+))?\}")


def get_field_value(parsed: ParsedMediaName, field_name: str) -> Any:
    """Get a field value from a ParsedMediaName object.

    Args:
        parsed: A ParsedMediaName object.
        field_name: The name of the field to get.

    Returns:
        The value of the field or None if not found.
    """
    # Handle special cases
    if field_name == "extension" and parsed.extension and not parsed.extension.startswith("."):
        return f".{parsed.extension}"

    # Handle array indexing (e.g., episodes[0])
    if "[" in field_name and field_name.endswith("]"):
        base_name, index_str = field_name.split("[", 1)
        index = int(index_str.rstrip("]"))
        base_value = getattr(parsed, base_name, None)
        if base_value is not None and isinstance(base_value, list) and 0 <= index < len(base_value):
            return base_value[index]
        return None

    return getattr(parsed, field_name, None)


def format_field(value: Any, format_spec: Optional[str] = None) -> str:
    """Format a field value using the provided format specification.

    Args:
        value: The value to format.
        format_spec: The format specification to use.

    Returns:
        The formatted value as a string.
    """
    if value is None:
        return ""

    if format_spec is None:
        return str(value)

    # Handle special format specifications
    if format_spec.startswith("pad"):
        try:
            # Extract the pad width
            pad_width = int(format_spec[3:])
            return str(value).zfill(pad_width)
        except (ValueError, IndexError):
            logger.warning(f"Invalid pad format: {format_spec}")
            return str(value)

    # Handle Python's standard format specifications
    try:
        return f"{value:{format_spec}}"
    except (ValueError, TypeError) as e:
        logger.warning(f"Format error for {value} with spec {format_spec}: {e}")
        return str(value)


def replace_variables(template: str, parsed: ParsedMediaName) -> str:
    """Replace variables in a template with values from a ParsedMediaName object.

    Args:
        template: The template string.
        parsed: A ParsedMediaName object.

    Returns:
        The template with variables replaced.
    """

    def replace_match(match: Match) -> str:
        field_name = match.group(1)
        format_spec = match.group(2)

        value = get_field_value(parsed, field_name)
        return format_field(value, format_spec)

    return VARIABLE_PATTERN.sub(replace_match, template)


def apply_template(
    parsed: ParsedMediaName,
    template_name: str = "default",
    template_type: Optional[TemplateType] = None,
) -> str:
    """Apply a template to a parsed media name.

    Args:
        parsed: A ParsedMediaName object.
        template_name: The name of the template to use.
        template_type: The type of template to use.

    Returns:
        The formatted file name.

    Raises:
        ValueError: If the template is not found.
    """
    # Determine the template type from the parsed media object if not provided
    if template_type is None and parsed.media_type is not None:
        # Convert from name_parser.MediaType to core.constants.MediaType
        media_type_value = parsed.media_type.value
        core_media_type = getattr(CoreMediaType, media_type_value.upper())
        template_type = normalize_media_type(core_media_type)

    try:
        # Try to get the named template
        template = get_template(template_type=template_type, name=template_name)
        return replace_variables(template, parsed)
    except ValueError:
        # If template not found, use the default formatter
        logger.info(
            f"Template '{template_name}' not found for type {template_type}, using default formatter"
        )
        formatter = get_default_formatter(template_type)
        return formatter(parsed)
