"""Template registry for accessing and managing templates.

This module provides a public API for registering and accessing templates
from different parts of the application. It acts as a facade for the
template manager.
"""

from pathlib import Path
from typing import Dict

from plexomatic.utils.templates.template_types import TemplateType
from plexomatic.utils.templates.template_manager import (
    get_template_manager,
)


def register_template(template_type: TemplateType, name: str, template: str) -> None:
    """Register a template for a specific type.

    Args:
        template_type: The type of template
        name: The name of the template
        template: The template string

    Raises:
        InvalidTemplateError: If the template or name is invalid
    """
    manager = get_template_manager()
    manager.register_template(template_type, name, template)


def get_template(template_type: TemplateType, name: str, fallback: bool = False) -> str:
    """Get a template by type and name.

    Args:
        template_type: The type of template
        name: The name of the template
        fallback: Whether to fall back to the default template if not found

    Returns:
        The template string

    Raises:
        TemplateNotFoundError: If the template is not found and fallback is False
    """
    manager = get_template_manager()
    return manager.get_template(template_type, name, fallback)


def get_available_templates(template_type: TemplateType) -> Dict[str, str]:
    """Get all templates for a specific type.

    Args:
        template_type: The type of template

    Returns:
        Dictionary of {name: template} for the specified type
    """
    manager = get_template_manager()
    return manager.get_templates(template_type)


def save_template_to_file(template_type: TemplateType, name: str) -> Path:
    """Save a template to a file.

    Args:
        template_type: The type of template
        name: The name of the template

    Returns:
        Path to the saved template file

    Raises:
        TemplateNotFoundError: If the template is not found
    """
    manager = get_template_manager()
    return manager.save_template_to_file(template_type, name)


def load_templates() -> None:
    """Load templates from the templates directory."""
    manager = get_template_manager()
    manager.load_templates_from_directory()
