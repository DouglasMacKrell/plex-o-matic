"""Template modules for the plexomatic application."""

# Import key types and functions for convenience
from plexomatic.utils.templates.template_types import TemplateType, normalize_media_type
from plexomatic.utils.templates.template_registry import register_template, get_template, get_available_templates
from plexomatic.utils.templates.template_formatter import apply_template, replace_variables
from plexomatic.utils.templates.template_manager import TemplateManager
