"""Main CLI command implementations for plexomatic."""

import click
import logging
import sys
from pathlib import Path
from typing import List, Optional, Tuple

try:
    # Python 3.9+ has native support for these types
    from typing import Optional, List, Tuple, Any
except ImportError:
    # For Python 3.8 support
    from typing_extensions import Optional, List, Tuple, Any

from plexomatic import __version__
from plexomatic.core.file_scanner import FileScanner
from plexomatic.core.backup_system import BackupSystem
from plexomatic.config import ConfigManager
from plexomatic.utils.name_utils import preview_rename
from plexomatic.utils.file_ops import rename_file, rollback_operation
from plexomatic import cli_ui
from plexomatic.utils.templates.template_manager import TemplateManager
from plexomatic.core.constants import MediaType

# Remove imports that cause redefinition errors
# We'll define these functions directly in this file
# from plexomatic.cli.commands import (
#    preview_command,
#    apply_command,
#    scan_command,
#    rollback_command,
#    configure_command,
# )

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


@cli.command(name="scan", help="Scan media directories for files to organize")
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help="Path to directory containing media files",
)
@click.option("--recursive/--no-recursive", default=True, help="Scan directories recursively")
@click.option(
    "--extensions",
    "-e",
    default=",".join(config.get_allowed_extensions()),
    help="Comma-separated list of file extensions to scan (default from config)",
)
@click.option(
    "--anthology-mode",
    is_flag=True,
    help="Enable anthology mode for this scan (overrides config setting)",
)
@click.option(
    "--no-llm",
    is_flag=True,
    help="Disable LLM for parsing and segment detection",
)
@verbose_option
@click.pass_context
def scan_command(
    ctx: click.Context,
    path: Path,
    recursive: bool,
    extensions: str,
    anthology_mode: bool,
    no_llm: bool,
    verbose: bool,
) -> List[Any]:
    """Scan a directory for media files."""
    if verbose:
        cli_ui.print_status("Scanning directory", status="info")
        cli_ui.console.print(f"  Path: {path}")
        cli_ui.console.print(f"  Recursive: {recursive}")
        cli_ui.console.print(f"  Extensions: {extensions}")
        cli_ui.console.print(f"  Anthology mode: {anthology_mode}")
        cli_ui.console.print(f"  LLM assistance: {not no_llm}")

    # Convert comma-separated extensions to list
    extension_list = [ext.strip() for ext in extensions.split(",")]

    # Create file scanner
    scanner = FileScanner(path, extension_list)
    scanner.recursive = recursive

    # Store scanner options in context for later commands
    ctx.obj["scanner_options"] = {
        "path": path,
        "extensions": extension_list,
        "recursive": recursive,
        "anthology_mode": anthology_mode,
        "use_llm": not no_llm,
    }

    # Store path in context for later commands
    ctx.obj["scan_path"] = path

    # Handle anthology mode flag
    if anthology_mode:
        if "episode_handling" not in config.config:
            config.config["episode_handling"] = {}
        config.config["episode_handling"]["anthology_mode"] = True
        if verbose:
            cli_ui.print_status("Anthology mode enabled for this operation", status="info")

    cli_ui.print_heading(f"Scanning directory: {path}")

    # Perform scan with progress bar
    with cli_ui.progress_bar("Scanning for media files...") as progress_tuple:
        progress, task_id = progress_tuple
        media_files = []
        file_count = 0

        for media_file in scanner.scan():
            media_files.append(media_file)
            file_count += 1
            progress.update(task_id, advance=1)

            if verbose and file_count % 10 == 0:
                # Update occasionally for large scans
                logger.debug(f"Found {file_count} files so far...")

        # Mark as complete when done
        progress.update(task_id, completed=True)

    # Show results
    cli_ui.print_status(f"Found {len(media_files)} media files", status="success")

    # Store scan results in context
    ctx.obj["media_files"] = media_files

    if verbose:
        cli_ui.console.print("\n[bold]Files found:[/bold]")
        for media_file in media_files:
            cli_ui.console.print(f"  - {media_file.path}", style=cli_ui.STYLES["filename"])

    return media_files


@cli.command(name="preview", help="Preview changes that would be made")
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, path_type=Path),
    help="Path to directory or file to preview",
)
@click.option("--recursive/--no-recursive", default=True, help="Scan directories recursively")
@click.option(
    "--extensions",
    "-e",
    default=",".join(config.get_allowed_extensions()),
    help="Comma-separated list of file extensions to scan (default from config)",
)
@click.option(
    "--anthology-mode",
    is_flag=True,
    help="Enable anthology mode for this preview (overrides config setting)",
)
@click.option(
    "--no-llm",
    is_flag=True,
    help="Disable LLM for parsing and segment detection",
)
@click.option(
    "--no-api-lookup",
    is_flag=True,
    help="Disable API lookup for episode numbers (enabled by default)",
)
@click.option(
    "--season-type",
    "-s",
    default="Aired Order",
    help="Season type to use when fetching episodes from TVDB (e.g., 'Aired Order', 'DVD Order')",
)
@verbose_option
@click.pass_context
def preview_command(
    ctx: click.Context,
    path: Optional[Path],
    recursive: bool,
    extensions: str,
    anthology_mode: bool,
    no_llm: bool,
    no_api_lookup: bool,
    season_type: str,
    verbose: bool,
) -> List[Tuple[Path, Path]]:
    """Preview changes that would be made to media files."""
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        # Also output to console for test capture
        cli_ui.print_status("Verbose mode enabled", status="info")

    # Handle anthology mode flag
    if anthology_mode:
        if "episode_handling" not in config.config:
            config.config["episode_handling"] = {}
        config.config["episode_handling"]["anthology_mode"] = True
        if verbose:
            cli_ui.print_status("Anthology mode enabled for this operation", status="info")

    cli_ui.print_heading("Previewing changes")

    # If no media files in context and if path is provided
    media_files = ctx.obj.get("media_files")

    if not media_files and path:
        if path.is_file():
            # Process a single file directly without scanning
            logger.debug(f"Processing single file: {path}")
            from plexomatic.core.file_scanner import MediaFile

            media_files = [MediaFile(path=path)]
        else:
            # Scan a directory
            logger.debug("No media files in context, scanning directory")
            media_files = ctx.invoke(
                scan_command,
                path=path,
                recursive=recursive,
                extensions=extensions,
                anthology_mode=anthology_mode,
                no_llm=no_llm,
                verbose=verbose,
            )

    if not media_files:
        cli_ui.print_status("No media files found to preview", status="warning")
        return []

    # Generate previews for each file
    cli_ui.console.print("\n[bold]Rename Preview:[/bold]")

    previews: List[Tuple[Path, Path]] = []
    for media_file in media_files:
        original_path = media_file.path
        use_dots = config.get("formatting", {}).get("use_dots", False)
        result = preview_rename(
            file_path=str(original_path),
            anthology_mode=anthology_mode,
            use_llm=not no_llm,
            use_dots=use_dots,
            api_lookup=not no_api_lookup,
            season_type=season_type,
        )

        if result is None:
            # No changes needed
            if verbose:
                cli_ui.console.print(f"[dim]No changes needed for {original_path.name}[/dim]")
            continue

        original = Path(result["original_path"])
        new = Path(result["new_path"])

        # Debug output to see what's happening
        if "Chip" in str(original_path) and verbose:
            logger.debug(f"Preview result for {original_path.name}:")
            logger.debug(f"  Original path: {original}")
            logger.debug(f"  New path: {new}")
            # Direct output for debugging
            cli_ui.console.print(f"[dim]DEBUG: {new.name}[/dim]")

        if new != original:
            previews.append((original, new))
            if verbose or len(previews) <= 10:  # Show at most 10 changes by default
                cli_ui.print_file_change(original, new)

    if not previews:
        cli_ui.print_status(
            "No changes needed. All files are already properly named.", status="success"
        )
    else:
        if len(previews) > 10 and not verbose:
            cli_ui.console.print(
                f"... and {len(previews) - 10} more. Use --verbose to see all.", style="yellow"
            )

        cli_ui.print_summary(
            "Rename Summary",
            {
                "Total files": len(media_files),
                "Files to rename": len(previews),
                "Files already correct": len(media_files) - len(previews),
            },
        )

    # Store previews in context
    ctx.obj["previews"] = previews

    if verbose:
        cli_ui.print_status(f"Previewing changes for {len(media_files)} files", status="info")
        cli_ui.console.print(f"  Path: {path}")
        cli_ui.console.print(f"  Recursive: {recursive}")
        cli_ui.console.print(f"  Extensions: {','.join(extensions.split(','))}")
        cli_ui.console.print(f"  Anthology mode: {anthology_mode}")
        cli_ui.console.print(f"  LLM assistance: {not no_llm}")
        cli_ui.console.print(f"  API lookup: {not no_api_lookup}")
        cli_ui.console.print(f"  Season type: {season_type}")

    return previews


@cli.command(name="apply", help="Apply changes to media files")
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Path to directory containing media files",
)
@click.option(
    "--batch-size",
    "-b",
    type=int,
    default=0,
    help="Process files in batches of specified size (0 for all at once)",
)
@click.option(
    "--anthology-mode",
    is_flag=True,
    help="Enable anthology mode for this operation (overrides config setting)",
)
@click.option(
    "--no-llm",
    is_flag=True,
    help="Disable LLM for parsing and segment detection",
)
@click.option(
    "--no-api-lookup",
    is_flag=True,
    help="Disable API lookup for episode numbers (enabled by default)",
)
@click.confirmation_option(prompt="Are you sure you want to apply changes to your media files?")
@verbose_option
@click.pass_context
def apply_command(
    ctx: click.Context,
    dry_run: bool,
    path: Optional[Path],
    batch_size: int,
    anthology_mode: bool,
    no_llm: bool,
    no_api_lookup: bool,
    verbose: bool,
) -> bool:
    """Apply changes to media files."""
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        # Also output to console for test capture
        cli_ui.print_status("Verbose mode enabled", status="info")

    # Handle anthology mode flag
    if anthology_mode:
        if "episode_handling" not in config.config:
            config.config["episode_handling"] = {}
        config.config["episode_handling"]["anthology_mode"] = True
        if verbose:
            cli_ui.print_status("Anthology mode enabled for this operation", status="info")

    cli_ui.print_heading("Applying changes")

    # If no previews in context, generate first
    previews = ctx.obj.get("previews")
    if not previews and path:
        logger.debug("No previews in context, generating first")
        previews = ctx.invoke(
            preview_command,
            path=path,
            recursive=True,
            extensions=",".join(config.get_allowed_extensions()),
            anthology_mode=anthology_mode,
            no_llm=no_llm,
            no_api_lookup=no_api_lookup,
            verbose=verbose,
        )

    if not previews:
        cli_ui.print_status("No changes to apply", status="warning")
        return True

    # Get backup system
    backup_system = ctx.obj.get("backup_system")
    if not backup_system and not dry_run:
        cli_ui.format_error("Backup system not initialized. This is a bug.")
        return False

    # Determine if we're using batch processing
    total_files = len(previews)
    if batch_size > 0 and total_files > batch_size:
        total_batches = (total_files + batch_size - 1) // batch_size
        cli_ui.print_status(
            f"Processing in batches of {batch_size} files ({total_batches} batches total)",
            status="info",
        )
        batched_processing = True
    else:
        batched_processing = False
        batch_size = total_files  # Process all files in one "batch"
        total_batches = 1

    # Tracking success and failures
    success_count = 0
    error_count = 0
    error_files = []

    # Process files in batches if needed
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, total_files)
        current_batch = previews[start_idx:end_idx]

        if batched_processing:
            cli_ui.print_status(
                f"Batch {batch_num + 1}/{total_batches} ({len(current_batch)} files)", status="info"
            )

        # Apply changes with progress bar
        with cli_ui.progress_bar("Renaming files...", total=len(current_batch)) as progress_tuple:
            progress, task_id = progress_tuple

            for i, (original_path, new_path) in enumerate(current_batch):
                if dry_run:
                    cli_ui.print_file_change(original_path, new_path)
                    cli_ui.console.print("  [yellow](dry run - no changes made)[/yellow]")
                    success_count += 1
                else:
                    progress.update(
                        task_id, description=f"Renaming file {i+1}/{len(current_batch)}"
                    )
                    try:
                        success = rename_file(original_path, new_path, backup_system)

                        if success:
                            if verbose:
                                cli_ui.print_status(
                                    f"Renamed: {original_path.name} → {new_path.name}",
                                    status="success",
                                )
                            success_count += 1
                        else:
                            cli_ui.print_status(
                                f"Failed to rename: {original_path.name}", status="error"
                            )
                            error_count += 1
                            error_files.append(original_path)
                    except Exception as e:
                        logger.error(f"Error renaming {original_path}: {e}")
                        cli_ui.print_status(
                            f"Error renaming {original_path.name}: {e}", status="error"
                        )
                        error_count += 1
                        error_files.append(original_path)

                # Update progress
                progress.update(task_id, advance=1)

        # Add a newline between batches for better readability
        if batched_processing and batch_num < total_batches - 1:
            cli_ui.print_newline()

    # Summary
    if dry_run:
        cli_ui.print_status("Dry run complete. No changes were made.", status="success")
    else:
        # Format summary based on results
        if error_count == 0:
            cli_ui.print_status(
                f"All operations completed successfully. {success_count} files processed.",
                status="success",
            )
        else:
            cli_ui.print_status(
                f"{success_count} files processed successfully. {error_count} errors occurred.",
                status="warning" if success_count > 0 else "error",
            )
            if verbose and error_files:
                cli_ui.print_status("Files with errors:", status="error")
                for error_file in error_files:
                    cli_ui.console.print(f"  - {error_file}")

    # Store results in context
    ctx.obj["rename_results"] = {
        "success_count": success_count,
        "error_count": error_count,
        "error_files": error_files,
    }

    return error_count == 0


@cli.command(name="rollback", help="Rollback the last operation")
@click.option(
    "--operation-id", type=int, help="ID of the operation to roll back (defaults to last operation)"
)
@click.confirmation_option(prompt="Are you sure you want to rollback the last operation?")
@verbose_option
@click.pass_context
def rollback_command(ctx: click.Context, operation_id: Optional[int], verbose: bool) -> bool:
    """Rollback the last operation."""
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        # Also output to console for test capture
        cli_ui.print_status("Verbose mode enabled", status="info")

    cli_ui.print_heading("Rolling back changes")

    # Get backup system
    backup_system = ctx.obj.get("backup_system")
    if not backup_system:
        cli_ui.format_error("Backup system not initialized. This is a bug.")
        return False

    # If no operation ID provided, find the last completed operation
    if not operation_id:
        from sqlalchemy import text

        with backup_system.engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT id FROM file_renames WHERE status = 'completed' ORDER BY completed_at DESC LIMIT 1"
                )
            )
            row = result.fetchone()
            if not row:
                cli_ui.print_status("No completed operations found to roll back.", status="warning")
                return False
            operation_id = row[0]

    if operation_id:
        cli_ui.print_status(f"Rolling back operation {operation_id}", status="info")

        # Perform rollback with progress indicator
        rollback_items = backup_system.get_backup_items_by_operation(operation_id)
        if not rollback_items:
            cli_ui.print_status(f"No items found for operation {operation_id}", status="warning")
            return False

        with cli_ui.progress_bar(f"Rolling back operation {operation_id}...") as progress_tuple:
            progress, task_id = progress_tuple
            success = rollback_operation(operation_id, backup_system)
            progress.update(task_id, completed=True)

        if success:
            cli_ui.print_status(
                f"Successfully rolled back operation {operation_id}", status="success"
            )
        else:
            cli_ui.print_status(f"Failed to roll back operation {operation_id}", status="error")

        return success
    else:
        cli_ui.print_status("No operation to roll back.", status="warning")
        return False


@cli.command(name="configure", help="Configure API keys and application settings")
@verbose_option
@click.pass_context
def configure_command(ctx: click.Context, verbose: bool) -> None:
    """Configure API keys and application settings.

    This command provides an interactive interface to set up API keys
    for TVDB, TMDB, AniDB, and configure the local LLM.
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        # Also output to console for test capture
        cli_ui.print_status("Verbose mode enabled", status="info")

    cli_ui.print_heading("Configuration", "Set up API keys and application settings")

    # Use existing config as a base
    config_data = config.config

    # Initialize API section if it doesn't exist
    if "api" not in config_data:
        config_data["api"] = {}

    api_config = config_data["api"]

    # TVDB API configuration
    if "tvdb" not in api_config:
        api_config["tvdb"] = {"api_key": "", "auto_retry": True, "pin": ""}

    current_tvdb_key = api_config["tvdb"].get("api_key", "")
    tvdb_key = click.prompt(
        f"Enter your TVDB API key [{current_tvdb_key}]",
        default=current_tvdb_key,
        show_default=False,
    )
    api_config["tvdb"]["api_key"] = tvdb_key

    # Add TVDB PIN configuration for v4 API
    current_tvdb_pin = api_config["tvdb"].get("pin", "")
    tvdb_pin = click.prompt(
        f"Enter your TVDB subscriber PIN (for v4 API) [{current_tvdb_pin}]",
        default=current_tvdb_pin,
        show_default=False,
    )
    api_config["tvdb"]["pin"] = tvdb_pin

    # TMDB API configuration
    if "tmdb" not in api_config:
        api_config["tmdb"] = {"api_key": ""}

    current_tmdb_key = api_config["tmdb"].get("api_key", "")
    tmdb_key = click.prompt(
        f"Enter your TMDB API key [{current_tmdb_key}]",
        default=current_tmdb_key,
        show_default=False,
    )
    api_config["tmdb"]["api_key"] = tmdb_key

    # AniDB configuration
    if "anidb" not in api_config:
        api_config["anidb"] = {
            "username": "",
            "password": "",
            "client_name": "plexomatic",
            "client_version": 1,
            "rate_limit_wait": 2.5,
        }

    configure_anidb = click.confirm("Do you want to configure AniDB credentials?", default=False)
    if configure_anidb:
        current_anidb_user = api_config["anidb"].get("username", "")
        anidb_user = click.prompt(
            f"Enter your AniDB username [{current_anidb_user}]",
            default=current_anidb_user,
            show_default=False,
        )
        api_config["anidb"]["username"] = anidb_user

        anidb_pass = click.prompt(
            "Enter your AniDB password", hide_input=True, default="", show_default=False
        )
        if anidb_pass:
            api_config["anidb"]["password"] = anidb_pass

    # TVMaze configuration (doesn't require API key)
    if "tvmaze" not in api_config:
        api_config["tvmaze"] = {"cache_size": 100}

    # LLM configuration
    if "llm" not in api_config:
        api_config["llm"] = {"model_name": "deepseek-r1:8b", "base_url": "http://localhost:11434"}

    configure_llm = click.confirm(
        "Do you want to configure local LLM settings (Ollama with Deepseek R1)?", default=True
    )
    if configure_llm:
        current_llm_url = api_config["llm"].get("base_url", "http://localhost:11434")
        llm_url = click.prompt(
            f"Enter Ollama base URL [{current_llm_url}]",
            default=current_llm_url,
            show_default=False,
        )
        api_config["llm"]["base_url"] = llm_url

        current_llm_model = api_config["llm"].get("model_name", "deepseek-r1:8b")
        llm_model = click.prompt(
            f"Enter LLM model name [{current_llm_model}]",
            default=current_llm_model,
            show_default=False,
        )
        api_config["llm"]["model_name"] = llm_model

    # Update the config with our changes
    config.config = config_data

    # Save the updated configuration
    if verbose:
        cli_ui.print_status("Saving configuration...", status="info")
    config.save()
    cli_ui.print_status("Configuration saved successfully.", status="success")

    # Display API connection status if verbose
    if verbose:
        cli_ui.console.print("\n[bold]API connection status:[/bold]")

        if api_config["tvdb"]["api_key"]:
            cli_ui.print_status("TVDB API key is set", status="success")
            if api_config["tvdb"]["pin"]:
                cli_ui.print_status("TVDB subscriber PIN is set", status="success")
            else:
                cli_ui.print_status(
                    "TVDB subscriber PIN is not set (may be required for v4 API)", status="warning"
                )
        else:
            cli_ui.print_status("TVDB API key is not set", status="error")

        if api_config["tmdb"]["api_key"]:
            cli_ui.print_status("TMDB API key is set", status="success")
        else:
            cli_ui.print_status("TMDB API key is not set", status="error")

        if api_config["anidb"]["username"] and api_config["anidb"]["password"]:
            cli_ui.print_status("AniDB credentials are set", status="success")
        else:
            cli_ui.print_status("AniDB credentials are not fully set", status="warning")

        cli_ui.print_status("TVMaze API does not require authentication", status="success")

        cli_ui.print_status(
            f"LLM configured to use {api_config['llm']['model_name']} at {api_config['llm']['base_url']}",
            status="success",
        )


@cli.group(name="templates", help="Manage file name templates.")
@verbose_option
@click.pass_context
def templates(ctx: click.Context, verbose: bool) -> None:
    """Manage and preview file name templates.

    This command provides subcommands for listing available templates
    and previewing how they'll format a file name.
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        # Also output to console for test capture
        cli_ui.print_status("Verbose mode enabled", status="info")

    # Initialize template manager and store in context
    manager = TemplateManager()
    ctx.obj = ctx.obj or {}
    ctx.obj["template_manager"] = manager


@templates.command(name="list", help="List all available templates")
@click.pass_context
def list_templates(ctx: click.Context) -> None:
    """List all available templates."""
    manager = ctx.obj.get("template_manager")
    if not manager:
        cli_ui.format_error("Template manager not initialized. This is a bug.")
        return

    cli_ui.print_heading("Available Templates")

    # Create sections for different template types
    sections = {
        "TV Show Episodes": MediaType.TV_SHOW,
        "Movies": MediaType.MOVIE,
        "Anime Episodes": MediaType.ANIME,
    }

    # Print each section with its templates
    for section_name, media_type in sections.items():
        cli_ui.print_heading(section_name, "")

        try:
            template = manager.get_template(media_type)
            cli_ui.console.print(f"  Default: [cyan]{template}[/cyan]")
        except Exception as e:
            logger.error(f"Error getting template for {media_type}: {e}")
            cli_ui.print_status(f"Error loading template: {e}", status="error")


@templates.command(name="show", help="Show a template preview")
@click.argument("media_type", type=click.Choice(["TV_SHOW", "MOVIE", "ANIME"]))
@click.argument("title")
@click.option("--season", type=int, default=1, help="Season number (for TV shows)")
@click.option("--episode", type=int, default=1, help="Episode number (for TV shows)")
@click.option("--year", type=str, help="Year (for movies)")
@click.option("--quality", type=str, help="Quality (e.g., 1080p)")
@click.option("--episode-title", type=str, help="Episode title")
@click.pass_context
def show_template(
    ctx: click.Context,
    media_type: str,
    title: str,
    season: int = 1,
    episode: int = 1,
    year: Optional[str] = None,
    quality: Optional[str] = None,
    episode_title: Optional[str] = None,
) -> None:
    """Show a preview of how a template will format a file name."""
    manager = ctx.obj.get("template_manager")
    if not manager:
        cli_ui.format_error("Template manager not initialized. This is a bug.")
        return

    # Map string media type to enum
    media_type_map = {
        "TV_SHOW": MediaType.TV_SHOW,
        "MOVIE": MediaType.MOVIE,
        "ANIME": MediaType.ANIME,
    }

    template_media_type = media_type_map.get(media_type)
    if template_media_type is None:
        cli_ui.format_error(f"Invalid media type: {media_type}")
        return

    # Get template
    try:
        template = manager.get_template(template_media_type)
    except Exception as e:
        cli_ui.format_error(f"Error loading template: {e}")
        return

    # Create format params
    params = {
        "title": title,
        "season": season,
        "episode": episode,
    }

    if year:
        params["year"] = year

    if quality:
        params["quality"] = quality

    if episode_title:
        params["episode_title"] = episode_title

    # Format the template
    try:
        formatted = manager.format(template_media_type, **params)

        # Display the result
        cli_ui.print_heading("Template Preview")
        cli_ui.console.print(f"Template: [cyan]{template}[/cyan]")
        cli_ui.console.print(f"Result:   [green]{formatted}[/green]")

    except Exception as e:
        cli_ui.format_error(f"Error formatting template: {e}")


# Register the imported commands
cli.add_command(preview_command)
cli.add_command(apply_command)
cli.add_command(scan_command)
cli.add_command(rollback_command)
cli.add_command(configure_command)

# Export the cli object for main.py
__all__ = ["cli"]

if __name__ == "__main__":
    cli()
