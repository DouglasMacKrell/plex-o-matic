"""Template manager for handling name templates.

This module provides functionality for loading, storing, and retrieving
templates for different media types. It handles template files and
provides a global template manager instance.
"""

import os
import logging
import re
from pathlib import Path
from typing import Dict, Optional

from plexomatic.utils.template_types import (
    TemplateType,
    DEFAULT_TEMPLATES_DIR,
    get_default_template_for_media_type,
)

logger = logging.getLogger(__name__)


class TemplateError(Exception):
    """Base class for template-related exceptions."""

    pass


class TemplateNotFoundError(TemplateError):
    """Raised when a template cannot be found."""

    pass


class InvalidTemplateError(TemplateError):
    """Raised when a template is invalid."""

    pass


class TemplateManager:
    """Manages templates for media file renaming.

    This class handles loading, saving, and retrieving templates
    for different media types. It provides access to both built-in
    default templates and custom user-defined templates.
    """

    # Template filename pattern: {type}_{name}.template
    TEMPLATE_PATTERN = re.compile(r"^([a-z_]+)_([a-z0-9_]+)\.template$")

    def __init__(self, templates_dir: Optional[Path] = None):
        """Initialize the template manager.

        Args:
            templates_dir: Directory to load templates from. Defaults to DEFAULT_TEMPLATES_DIR.
        """
        self.templates_dir = templates_dir or DEFAULT_TEMPLATES_DIR
        os.makedirs(self.templates_dir, exist_ok=True)

        # Dictionary of templates, organized by template type and name
        # {TemplateType.TV_SHOW: {"default": "{title}.S{season:02d}E{episode:02d}.{extension}", ...}, ...}
        self.templates: Dict[TemplateType, Dict[str, str]] = {
            template_type: {} for template_type in TemplateType
        }

        # Dictionary of custom templates added at runtime
        self._custom_templates: Dict[TemplateType, Dict[str, str]] = {
            template_type: {} for template_type in TemplateType
        }

        # Load templates from disk
        self.load_templates_from_directory()

    def register_template(self, template_type: TemplateType, name: str, template: str) -> None:
        """Register a template for a specific type.

        Args:
            template_type: The type of template
            name: The name of the template
            template: The template string

        Raises:
            InvalidTemplateError: If the template or name is invalid
        """
        if not name:
            raise InvalidTemplateError("Template name cannot be empty")

        if not template:
            raise InvalidTemplateError("Template cannot be empty")

        self._custom_templates[template_type][name] = template

    def get_template(self, template_type: TemplateType, name: str, fallback: bool = False) -> str:
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
        # First check custom templates
        if name in self._custom_templates[template_type]:
            return self._custom_templates[template_type][name]

        # Then check loaded templates
        if name in self.templates[template_type]:
            return self.templates[template_type][name]

        # If not found, either use fallback or raise exception
        if fallback:
            return get_default_template_for_media_type(template_type)

        raise TemplateNotFoundError(f"Template {name} for {template_type} not found")

    def get_templates(self, template_type: TemplateType) -> Dict[str, str]:
        """Get all templates for a specific type.

        Args:
            template_type: The type of template

        Returns:
            Dictionary of {name: template} for the specified type
        """
        # Combine loaded and custom templates
        combined = {}
        combined.update(self.templates[template_type])
        combined.update(self._custom_templates[template_type])
        return combined

    def save_template_to_file(self, template_type: TemplateType, name: str) -> Path:
        """Save a template to a file.

        Args:
            template_type: The type of template
            name: The name of the template

        Returns:
            Path to the saved template file

        Raises:
            TemplateNotFoundError: If the template is not found
        """
        template = self.get_template(template_type, name)

        # Ensure the templates directory exists
        os.makedirs(self.templates_dir, exist_ok=True)

        # Create the template file
        filename = f"{template_type.value}_{name}.template"
        file_path = self.templates_dir / filename

        with open(file_path, "w") as f:
            f.write(template)

        logger.info(f"Saved template '{name}' to {file_path}")
        return file_path

    def load_templates_from_directory(self) -> None:
        """Load templates from the templates directory."""
        if not os.path.exists(self.templates_dir):
            logger.warning(f"Templates directory {self.templates_dir} does not exist")
            return

        # Clear existing loaded templates (but keep custom ones)
        for template_type in TemplateType:
            self.templates[template_type] = {}

        # Load templates from files
        for filename in os.listdir(self.templates_dir):
            file_path = self.templates_dir / filename

            # Skip directories
            if not os.path.isfile(file_path):
                continue

            # Parse filename to get template type and name
            match = self.TEMPLATE_PATTERN.match(filename)
            if not match:
                logger.warning(f"Invalid template filename: {filename}")
                continue

            type_str, name = match.groups()

            # Convert type string to TemplateType
            try:
                template_type = next(t for t in TemplateType if t.value == type_str)
            except StopIteration:
                logger.warning(f"Unknown template type: {type_str}")
                continue

            # Load template content
            try:
                with open(file_path, "r") as f:
                    template = f.read()

                # Add to templates dictionary
                self.templates[template_type][name] = template
                logger.debug(f"Loaded template '{name}' for {template_type}")
            except Exception as e:
                logger.warning(f"Error loading template {file_path}: {e}")


# Global template manager instance
_TEMPLATE_MANAGER: Optional[TemplateManager] = None


def get_template_manager() -> TemplateManager:
    """Get the global template manager instance.

    Returns:
        The global template manager instance
    """
    global _TEMPLATE_MANAGER
    if _TEMPLATE_MANAGER is None:
        _TEMPLATE_MANAGER = TemplateManager()
    return _TEMPLATE_MANAGER


def reset_template_manager() -> None:
    """Reset the global template manager instance."""
    global _TEMPLATE_MANAGER
    _TEMPLATE_MANAGER = None
