import click
import logging
import sys
from typing import Optional, List
from pathlib import Path

from plexomatic import __version__
from plexomatic.core.file_scanner import FileScanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("plexomatic")

# Common command options
verbose_option = click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output."
)

@click.group(help="Plex-o-matic: Media file organization tool for Plex")
@click.version_option(version=__version__, message="plex-o-matic, version %(version)s")
@verbose_option
@click.pass_context
def cli(ctx: click.Context, verbose: bool):
    """Main CLI entry point for Plex-o-matic."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        # Also output to console for test capture
        click.echo("Verbose mode enabled")

@cli.command(name="scan", help="Scan media directories for files to organize")
@click.option(
    "--path", "-p", 
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help="Path to directory containing media files"
)
@click.option(
    "--recursive/--no-recursive", 
    default=True, 
    help="Scan directories recursively"
)
@click.option(
    "--extensions", "-e", 
    default=".mp4,.mkv,.avi,.mov,.m4v",
    help="Comma-separated list of file extensions to scan (default: .mp4,.mkv,.avi,.mov,.m4v)"
)
@verbose_option
@click.pass_context
def scan_command(
    ctx: click.Context, 
    path: Path, 
    recursive: bool, 
    extensions: str,
    verbose: bool
):
    """Scan a directory for media files."""
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        # Also output to console for test capture
        click.echo("Verbose mode enabled")
    
    click.echo(f"Scanning directory: {path}")
    
    # Parse extensions
    allowed_extensions = [ext.strip() for ext in extensions.split(",")]
    
    # Initialize file scanner
    scanner = FileScanner(
        base_path=path,
        allowed_extensions=allowed_extensions,
        recursive=recursive
    )
    
    # Perform scan
    media_files = list(scanner.scan())
    
    click.echo(f"Found {len(media_files)} media files")
    
    if verbose:
        for media_file in media_files:
            click.echo(f"  - {media_file.path}")
    
    return media_files

@cli.command(name="preview", help="Preview changes that would be made")
@verbose_option
@click.pass_context
def preview_command(ctx: click.Context, verbose: bool):
    """Preview changes that would be made to media files."""
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        # Also output to console for test capture
        click.echo("Verbose mode enabled")
    
    click.echo("Previewing changes")
    # Placeholder for preview functionality
    # Will be implemented in future sprints
    return True

@cli.command(name="apply", help="Apply changes to media files")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without making changes"
)
@click.confirmation_option(
    prompt="Are you sure you want to apply changes to your media files?"
)
@verbose_option
@click.pass_context
def apply_command(ctx: click.Context, dry_run: bool, verbose: bool):
    """Apply changes to media files."""
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        # Also output to console for test capture
        click.echo("Verbose mode enabled")
    
    click.echo("Applying changes")
    
    if dry_run:
        click.echo("Dry run mode - no changes will be made")
    
    # Placeholder for apply functionality
    # Will be implemented in future sprints
    return True

@cli.command(name="rollback", help="Rollback the last operation")
@click.option(
    "--operation-id", type=int, help="ID of the operation to roll back (defaults to last operation)"
)
@click.confirmation_option(
    prompt="Are you sure you want to rollback the last operation?"
)
@verbose_option
@click.pass_context
def rollback_command(ctx: click.Context, operation_id: Optional[int], verbose: bool):
    """Rollback the last operation or a specific operation by ID."""
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        # Also output to console for test capture
        click.echo("Verbose mode enabled")
    
    click.echo("Rolling back changes")
    
    if operation_id:
        click.echo(f"Rolling back operation {operation_id}")
    else:
        click.echo("Rolling back the last operation")
    
    # Placeholder for rollback functionality
    # Will be implemented in future sprints
    return True

if __name__ == "__main__":
    cli() 