"""CLI entry point for plexomatic."""

import click
import logging
import sys
from pathlib import Path

from plexomatic import __version__
from plexomatic.core.backup_system import BackupSystem
from plexomatic.config import ConfigManager
from plexomatic import cli_ui

# Import command modules from the commands directory
from plexomatic.cli.commands import (
    preview_command,
    apply_command,
    scan_command,
    rollback_command,
    configure_command,
)

# Initialize configuration
config = ConfigManager()

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.get("log_level", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("plexomatic")

# Common command options
verbose_option = click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")

@click.group(help="Plex-o-matic: Media file organization tool for Plex")
@click.version_option(version=__version__, message="plex-o-matic, version %(version)s")
@verbose_option
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """Main CLI entry point for Plex-o-matic."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    # Initialize backup system
    db_path = config.get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    backup_system = BackupSystem(db_path)
    backup_system.initialize_database()
    ctx.obj["backup_system"] = backup_system

    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        # Also output to console for test capture
        cli_ui.print_status("Verbose mode enabled", status="info")

# Register all commands
cli.add_command(preview_command)
cli.add_command(apply_command)
cli.add_command(scan_command)
cli.add_command(rollback_command)
cli.add_command(configure_command)

if __name__ == "__main__":
    cli()
