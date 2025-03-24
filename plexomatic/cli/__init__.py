"""Command line interface package for plexomatic."""
# This file defines the CLI package but should not import from plexomatic.cli 

# Export the main CLI function
from plexomatic.cli.commands import cli  # This is the main Click CLI entry point

__all__ = ["cli"] 