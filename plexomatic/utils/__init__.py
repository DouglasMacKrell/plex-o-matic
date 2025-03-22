"""Utilities for the plexomatic application."""

# Importing from template_types.py
from plexomatic.utils.template_types import TemplateType, normalize_media_type

# Importing from template_registry.py
from plexomatic.utils.template_registry import (
    register_template,
    get_template,
    get_available_templates,
    save_template_to_file,
    load_templates,
)

# Importing from template_formatter.py
from plexomatic.utils.template_formatter import (
    apply_template,
    replace_variables,
    format_field,
    get_field_value,
)

# Importing from default_formatters.py
from plexomatic.utils.default_formatters import (
    format_tv_show,
    format_movie,
    format_anime,
    get_default_formatter,
)

# Importing from multi_episode_formatter.py
from plexomatic.utils.multi_episode_formatter import (
    ensure_episode_list,
    format_multi_episode,
    get_formatted_episodes,
)

# Importing from template_manager.py
from plexomatic.utils.template_manager import (
    TemplateManager,
    TemplateError,
    TemplateNotFoundError,
    InvalidTemplateError,
    get_template_manager,
    reset_template_manager,
)

# Importing from file_utils.py
from plexomatic.utils.file_utils import (
    sanitize_filename,
    extract_show_info,
    generate_tv_filename,
    generate_movie_filename,
    get_preview_rename,
)

# Keep importing any other existing utils that are still used
from plexomatic.utils.preview_system import (
    PreviewResult,
    DiffStyle,
)

__all__ = [
    # Template types
    "TemplateType", 
    "normalize_media_type",
    
    # Template registry
    "register_template",
    "get_template",
    "get_available_templates",
    "save_template_to_file",
    "load_templates",
    
    # Template formatter
    "apply_template",
    "replace_variables",
    "format_field",
    "get_field_value",
    
    # Default formatters
    "format_tv_show",
    "format_movie",
    "format_anime",
    "get_default_formatter",
    
    # Multi episode formatter
    "ensure_episode_list",
    "format_multi_episode",
    "get_formatted_episodes",
    
    # Template manager
    "TemplateManager",
    "TemplateError",
    "TemplateNotFoundError",
    "InvalidTemplateError",
    "get_template_manager",
    "reset_template_manager",
    
    # File utilities
    "sanitize_filename",
    "extract_show_info",
    "generate_tv_filename",
    "generate_movie_filename",
    "get_preview_rename",
    
    # Preview system
    "PreviewResult",
    "DiffStyle",
]
