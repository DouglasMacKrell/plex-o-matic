#!/usr/bin/env python
"""
Plex-o-matic CLI: Command-line interface for plex-o-matic.
"""

from plexomatic.cli.commands import cli as plexomatic_cli


def main():
    """Run the CLI application."""
    plexomatic_cli()


if __name__ == "__main__":
    main()
