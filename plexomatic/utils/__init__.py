"""Utility functions and helpers."""

from .file_ops import calculate_file_checksum, rename_file, rollback_operation
from .name_utils import (
    sanitize_filename,
    extract_show_info,
    generate_tv_filename,
    generate_movie_filename,
    get_preview_rename,
)
from .name_parser import MediaType, ParsedMediaName, NameParser, parse_media_name, detect_media_type
from .name_templates import (
    TemplateType,
    NameTemplate,
    TemplateManager,
    apply_template,
    register_template,
    get_available_templates,
)

__all__ = [
    # File operations
    "calculate_file_checksum",
    "rename_file",
    "rollback_operation",
    # Basic name utilities
    "sanitize_filename",
    "extract_show_info",
    "generate_tv_filename",
    "generate_movie_filename",
    "get_preview_rename",
    # Advanced name parsing
    "MediaType",
    "ParsedMediaName",
    "NameParser",
    "parse_media_name",
    "detect_media_type",
    # Name templates
    "TemplateType",
    "NameTemplate",
    "TemplateManager",
    "apply_template",
    "register_template",
    "get_available_templates",
]
