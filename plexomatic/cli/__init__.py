"""Command line interface package for plexomatic."""

# This file defines the CLI package but should not import from plexomatic.cli

# Import the commands from submodules to make them available
from plexomatic.cli.commands import (
    preview_command,
    apply_command,
    scan_command,
    rollback_command,
    configure_command,
)

__all__ = [
    "preview_command",
    "apply_command",
    "scan_command",
    "rollback_command",
    "configure_command",
]
