import click
import logging
import sys
import os
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

from plexomatic import __version__
from plexomatic.core.file_scanner import FileScanner
from plexomatic.core.backup_system import BackupSystem, FileOperation
from plexomatic.config import ConfigManager
from plexomatic.utils import (
    rename_file, 
    rollback_operation, 
    get_preview_rename
)

# Initialize configuration
config = ConfigManager()

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.get("log_level", "INFO")),
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
    default=",".join(config.get_allowed_extensions()),
    help="Comma-separated list of file extensions to scan (default from config)"
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
        ignore_patterns=config.get_ignore_patterns(),
        recursive=recursive
    )
    
    # Perform scan
    media_files = list(scanner.scan())
    
    click.echo(f"Found {len(media_files)} media files")
    
    # Store scan results in context
    ctx.obj["media_files"] = media_files
    
    if verbose:
        for media_file in media_files:
            click.echo(f"  - {media_file.path}")
    
    return media_files

@cli.command(name="preview", help="Preview changes that would be made")
@click.option(
    "--path", "-p", 
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Path to directory containing media files"
)
@click.option(
    "--recursive/--no-recursive", 
    default=True, 
    help="Scan directories recursively"
)
@click.option(
    "--extensions", "-e", 
    default=",".join(config.get_allowed_extensions()),
    help="Comma-separated list of file extensions to scan (default from config)"
)
@verbose_option
@click.pass_context
def preview_command(
    ctx: click.Context, 
    path: Optional[Path], 
    recursive: bool,
    extensions: str,
    verbose: bool
):
    """Preview changes that would be made to media files."""
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        # Also output to console for test capture
        click.echo("Verbose mode enabled")
    
    click.echo("Previewing changes")
    
    # If no files in context, scan for files first
    media_files = ctx.obj.get("media_files")
    if not media_files and path:
        logger.debug("No media files in context, scanning first")
        ctx.invoke(
            scan_command, 
            path=path, 
            recursive=recursive,
            extensions=extensions,
            verbose=verbose
        )
        media_files = ctx.obj.get("media_files", [])
    
    if not media_files:
        click.echo("No media files found. Run 'scan' command first or specify a path.")
        return []
    
    # Generate previews for each file
    previews = []
    for media_file in media_files:
        original_path = media_file.path
        result = get_preview_rename(original_path)
        
        if result['new_name'] != result['original_name']:
            original = original_path
            new = Path(result['new_path'])
            previews.append((original, new))
            if verbose or len(previews) <= 10:  # Show at most 10 changes by default
                click.echo(f"{result['original_name']} → {result['new_name']}")
    
    if not previews:
        click.echo("No changes needed. All files are already properly named.")
    else:
        if len(previews) > 10 and not verbose:
            click.echo(f"... and {len(previews) - 10} more. Use --verbose to see all.")
        click.echo(f"\nTotal: {len(previews)} file(s) to rename")
    
    # Store previews in context
    ctx.obj["previews"] = previews
    
    return previews

@cli.command(name="apply", help="Apply changes to media files")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without making changes"
)
@click.option(
    "--path", "-p", 
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Path to directory containing media files"
)
@click.confirmation_option(
    prompt="Are you sure you want to apply changes to your media files?"
)
@verbose_option
@click.pass_context
def apply_command(
    ctx: click.Context, 
    dry_run: bool, 
    path: Optional[Path],
    verbose: bool
):
    """Apply changes to media files."""
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        # Also output to console for test capture
        click.echo("Verbose mode enabled")
    
    click.echo("Applying changes")
    
    # Get or generate previews
    previews = ctx.obj.get("previews")
    if not previews:
        logger.debug("No previews in context, generating first")
        ctx.invoke(preview_command, path=path, verbose=verbose)
        previews = ctx.obj.get("previews", [])
    
    if not previews:
        click.echo("No changes to apply.")
        return True
    
    # Get backup system
    backup_system = ctx.obj.get("backup_system")
    if not backup_system and not dry_run:
        click.echo("Error: Backup system not initialized. This is a bug.")
        return False
    
    # Apply changes
    success_count = 0
    error_count = 0
    
    for original_path, new_path in previews:
        if dry_run:
            click.echo(f"Would rename: {original_path} → {new_path}")
            success_count += 1
        else:
            click.echo(f"Renaming: {original_path} → {new_path}")
            success = rename_file(original_path, new_path, backup_system)
            
            if success:
                success_count += 1
            else:
                error_count += 1
                click.echo(f"Error renaming {original_path}")
    
    if dry_run:
        click.echo(f"\nDry run complete. {success_count} file(s) would be renamed.")
    else:
        click.echo(f"\nApplied changes to {success_count} file(s). {error_count} error(s).")
    
    return success_count > 0 and error_count == 0

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
    """Rollback the last operation."""
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        # Also output to console for test capture
        click.echo("Verbose mode enabled")
    
    click.echo("Rolling back changes")
    
    # Get backup system
    backup_system = ctx.obj.get("backup_system")
    if not backup_system:
        click.echo("Error: Backup system not initialized. This is a bug.")
        return False
    
    # If no operation ID provided, find the last completed operation
    if not operation_id:
        with backup_system.engine.connect() as conn:
            result = conn.execute(
                "SELECT id FROM file_renames WHERE status = 'completed' ORDER BY completed_at DESC LIMIT 1"
            )
            row = result.fetchone()
            if not row:
                click.echo("No completed operations found to roll back.")
                return False
            operation_id = row[0]
    
    if operation_id:
        click.echo(f"Rolling back operation {operation_id}")
        success = rollback_operation(operation_id, backup_system)
        
        if success:
            click.echo(f"Successfully rolled back operation {operation_id}")
        else:
            click.echo(f"Failed to roll back operation {operation_id}")
        
        return success
    else:
        click.echo("No operation to roll back.")
        return False

@cli.command(name="configure", help="Configure API keys and application settings")
@verbose_option
@click.pass_context
def configure_command(ctx: click.Context, verbose: bool):
    """Configure API keys and application settings.
    
    This command provides an interactive interface to set up API keys
    for TVDB, TMDB, AniDB, and configure the local LLM.
    """
    # Use existing config as a base
    if verbose:
        click.echo("Loading existing configuration...")
    
    # Make sure we're working with the most current config
    config_data = config.config
    
    # Initialize API section if it doesn't exist
    if "api" not in config_data:
        config_data["api"] = {}
    
    api_config = config_data["api"]
    
    # TVDB API configuration
    if "tvdb" not in api_config:
        api_config["tvdb"] = {"api_key": "", "auto_retry": True}
    
    current_tvdb_key = api_config["tvdb"].get("api_key", "")
    tvdb_key = click.prompt(
        f"Enter your TVDB API key [{current_tvdb_key}]", 
        default=current_tvdb_key,
        show_default=False
    )
    api_config["tvdb"]["api_key"] = tvdb_key
    
    # TMDB API configuration
    if "tmdb" not in api_config:
        api_config["tmdb"] = {"api_key": ""}
    
    current_tmdb_key = api_config["tmdb"].get("api_key", "")
    tmdb_key = click.prompt(
        f"Enter your TMDB API key [{current_tmdb_key}]", 
        default=current_tmdb_key,
        show_default=False
    )
    api_config["tmdb"]["api_key"] = tmdb_key
    
    # AniDB configuration
    if "anidb" not in api_config:
        api_config["anidb"] = {
            "username": "", 
            "password": "", 
            "client_name": "plexomatic",
            "client_version": 1,
            "rate_limit_wait": 2.5
        }
    
    configure_anidb = click.confirm("Do you want to configure AniDB credentials?", default=False)
    if configure_anidb:
        current_anidb_user = api_config["anidb"].get("username", "")
        anidb_user = click.prompt(
            f"Enter your AniDB username [{current_anidb_user}]", 
            default=current_anidb_user,
            show_default=False
        )
        api_config["anidb"]["username"] = anidb_user
        
        anidb_pass = click.prompt(
            "Enter your AniDB password", 
            hide_input=True,
            default="",
            show_default=False
        )
        if anidb_pass:
            api_config["anidb"]["password"] = anidb_pass
    
    # TVMaze configuration (doesn't require API key)
    if "tvmaze" not in api_config:
        api_config["tvmaze"] = {"cache_size": 100}
    
    # LLM configuration
    if "llm" not in api_config:
        api_config["llm"] = {
            "model_name": "deepseek-r1:8b",
            "base_url": "http://localhost:11434"
        }
    
    configure_llm = click.confirm(
        "Do you want to configure local LLM settings (Ollama with Deepseek R1)?", 
        default=True
    )
    if configure_llm:
        current_llm_url = api_config["llm"].get("base_url", "http://localhost:11434")
        llm_url = click.prompt(
            f"Enter Ollama base URL [{current_llm_url}]", 
            default=current_llm_url,
            show_default=False
        )
        api_config["llm"]["base_url"] = llm_url
        
        current_llm_model = api_config["llm"].get("model_name", "deepseek-r1:8b")
        llm_model = click.prompt(
            f"Enter LLM model name [{current_llm_model}]", 
            default=current_llm_model,
            show_default=False
        )
        api_config["llm"]["model_name"] = llm_model
    
    # Update the config with our changes
    config.config = config_data
    
    # Save the updated configuration
    if verbose:
        click.echo("Saving configuration...")
    config.save()
    click.echo("Configuration saved successfully.")
    
    # Display API connection status if verbose
    if verbose:
        click.echo("\nAPI connection status:")
        if api_config["tvdb"]["api_key"]:
            click.echo("✓ TVDB API key is set")
        else:
            click.echo("✗ TVDB API key is not set")
            
        if api_config["tmdb"]["api_key"]:
            click.echo("✓ TMDB API key is set")
        else:
            click.echo("✗ TMDB API key is not set")
            
        if api_config["anidb"]["username"] and api_config["anidb"]["password"]:
            click.echo("✓ AniDB credentials are set")
        else:
            click.echo("✗ AniDB credentials are not fully set")
            
        click.echo("✓ TVMaze API does not require authentication")
        
        click.echo(f"✓ LLM configured to use {api_config['llm']['model_name']} at {api_config['llm']['base_url']}")

if __name__ == "__main__":
    cli() 