import click
import logging
import sys

try:
    # Python 3.9+ has native support for these types
    from typing import Optional, List, Tuple, Any
except ImportError:
    # For Python 3.8 support
    from typing_extensions import Optional, List, Tuple, Any
from pathlib import Path

from plexomatic import __version__
from plexomatic.core.file_scanner import FileScanner
from plexomatic.core.backup_system import BackupSystem
from plexomatic.config import ConfigManager
from plexomatic.utils import rename_file, rollback_operation, get_preview_rename
from plexomatic import cli_ui
from plexomatic.utils.name_templates import TemplateManager

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
@verbose_option
@click.pass_context
def scan_command(
    ctx: click.Context, path: Path, recursive: bool, extensions: str, verbose: bool
) -> List[Any]:
    """Scan a directory for media files."""
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        # Also output to console for test capture
        cli_ui.print_status("Verbose mode enabled", status="info")

    cli_ui.print_heading(f"Scanning directory: {path}")

    # Parse extensions
    allowed_extensions = [ext.strip() for ext in extensions.split(",")]

    # Initialize file scanner
    scanner = FileScanner(
        base_path=str(path),  # Convert Path to str
        allowed_extensions=allowed_extensions,
        ignore_patterns=config.get_ignore_patterns(),
        recursive=recursive,
    )

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
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Path to directory containing media files",
)
@click.option("--recursive/--no-recursive", default=True, help="Scan directories recursively")
@click.option(
    "--extensions",
    "-e",
    default=",".join(config.get_allowed_extensions()),
    help="Comma-separated list of file extensions to scan (default from config)",
)
@verbose_option
@click.pass_context
def preview_command(
    ctx: click.Context, path: Optional[Path], recursive: bool, extensions: str, verbose: bool
) -> List[Tuple[Path, Path]]:
    """Preview changes that would be made to media files."""
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        # Also output to console for test capture
        cli_ui.print_status("Verbose mode enabled", status="info")

    cli_ui.print_heading("Previewing changes")

    # If no files in context, scan for files first
    media_files = ctx.obj.get("media_files")
    if not media_files and path:
        logger.debug("No media files in context, scanning first")
        ctx.invoke(
            scan_command, path=path, recursive=recursive, extensions=extensions, verbose=verbose
        )
        media_files = ctx.obj.get("media_files", [])

    if not media_files:
        cli_ui.print_status(
            "No media files found. Run 'scan' command first or specify a path.", status="warning"
        )
        return []

    # Generate previews for each file
    cli_ui.console.print("\n[bold]Rename Preview:[/bold]")

    previews: List[Tuple[Path, Path]] = []
    for media_file in media_files:
        original_path = media_file.path
        result = get_preview_rename(original_path)

        if result["new_name"] != result["original_name"]:
            original = original_path
            new = Path(result["new_path"])
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

    return previews


@cli.command(name="apply", help="Apply changes to media files")
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Path to directory containing media files",
)
@click.confirmation_option(prompt="Are you sure you want to apply changes to your media files?")
@verbose_option
@click.pass_context
def apply_command(ctx: click.Context, dry_run: bool, path: Optional[Path], verbose: bool) -> bool:
    """Apply changes to media files."""
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        # Also output to console for test capture
        cli_ui.print_status("Verbose mode enabled", status="info")

    cli_ui.print_heading("Applying changes")

    # Get or generate previews
    previews = ctx.obj.get("previews")
    if not previews:
        logger.debug("No previews in context, generating first")
        ctx.invoke(preview_command, path=path, verbose=verbose)
        previews = ctx.obj.get("previews", [])

    if not previews:
        cli_ui.print_status("No changes to apply.", status="info")
        return True

    # Get backup system
    backup_system = ctx.obj.get("backup_system")
    if not backup_system and not dry_run:
        cli_ui.format_error("Backup system not initialized. This is a bug.")
        return False

    # Apply changes with progress bar
    with cli_ui.progress_bar("Renaming files...", total=len(previews)) as progress_tuple:
        progress, task_id = progress_tuple
        success_count = 0
        error_count = 0

        for i, (original_path, new_path) in enumerate(previews):
            if dry_run:
                cli_ui.print_file_change(original_path, new_path)
                cli_ui.console.print("  [yellow](dry run - no changes made)[/yellow]")
                success_count += 1
            else:
                progress.update(task_id, description=f"Renaming file {i+1}/{len(previews)}")
                try:
                    success = rename_file(original_path, new_path, backup_system)

                    if success:
                        if verbose:
                            cli_ui.print_status(
                                f"Renamed: {original_path.name} → {new_path.name}", status="success"
                            )
                        success_count += 1
                    else:
                        cli_ui.print_status(f"Error renaming {original_path}", status="error")
                        error_count += 1
                except Exception as e:
                    cli_ui.print_status(f"Exception during rename: {str(e)}", status="error")
                    error_count += 1

            # Update progress bar
            progress.update(task_id, advance=1)

    # Show summary
    if dry_run:
        cli_ui.print_status(
            f"Dry run complete. {success_count} file(s) would be renamed.", status="info"
        )
    else:
        cli_ui.print_summary(
            "Rename Results",
            {
                "Total files": len(previews),
                "Successfully renamed": success_count,
                "Errors": error_count,
            },
        )

        if error_count == 0:
            cli_ui.print_status("All files renamed successfully!", status="success")
        elif success_count > 0:
            cli_ui.print_status(
                f"Partially successful: {success_count} renamed, {error_count} errors",
                status="warning",
            )
        else:
            cli_ui.print_status("All renames failed. See logs for details.", status="error")

    return success_count > 0 and error_count == 0


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
        api_config["tvdb"] = {"api_key": "", "auto_retry": True}

    current_tvdb_key = api_config["tvdb"].get("api_key", "")
    tvdb_key = click.prompt(
        f"Enter your TVDB API key [{current_tvdb_key}]",
        default=current_tvdb_key,
        show_default=False,
    )
    api_config["tvdb"]["api_key"] = tvdb_key

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


@cli.group()
def templates() -> None:
    """Manage file name templates."""
    pass


@templates.command("list")
def list_templates() -> None:
    """List all available templates."""
    cli_ui.print_heading("Available Templates")

    # Initialize template manager
    template_manager = TemplateManager()

    # Media type names and descriptions
    media_types = [
        ("TV_SHOW", "TV Show Episodes"),
        ("MOVIE", "Movies"),
        ("ANIME", "Anime Episodes"),
        ("TV_SPECIAL", "TV Show Specials"),
        ("ANIME_SPECIAL", "Anime Specials"),
        ("UNKNOWN", "Unknown Media Types"),
    ]

    # Print templates for each media type
    for media_type_name, description in media_types:
        from plexomatic.core.models import MediaType

        media_type = getattr(MediaType, media_type_name)
        template = template_manager.get_template(media_type)

        cli_ui.print_info(f"{description} ({media_type_name}):")
        cli_ui.print_result(template)
        cli_ui.print_newline()


@templates.command("show")
@click.argument(
    "media_type",
    type=click.Choice(["TV_SHOW", "MOVIE", "ANIME", "TV_SPECIAL", "ANIME_SPECIAL", "UNKNOWN"]),
)
@click.argument("title", default="Example Title")
@click.option("--season", type=int, default=1, help="Season number")
@click.option("--episode", type=int, default=1, help="Episode number")
@click.option("--episode-title", type=str, default="Example Episode", help="Episode title")
@click.option("--year", type=int, default=2023, help="Release year (for movies)")
@click.option("--quality", type=str, default="1080p", help="Video quality")
@click.option("--group", type=str, default="GROUP", help="Release group (for anime)")
def show_template(
    media_type: str,
    title: str,
    season: int,
    episode: int,
    episode_title: str,
    year: int,
    quality: str,
    group: str,
) -> None:
    """Show how a template would be applied to sample data."""
    from plexomatic.core.models import MediaType
    from plexomatic.utils.name_parser import ParsedMediaName

    # Map string to MediaType enum
    media_type_enum = getattr(MediaType, media_type)

    # Create a parsed media name
    parsed = ParsedMediaName(
        title=title,
        season=season,
        episodes=[episode],
        episode_title=episode_title,
        year=year,
        quality=quality,
        group=group,
        media_type=media_type_enum,
        extension=".mp4",
    )

    # Initialize template manager
    template_manager = TemplateManager()

    # Get template and formatted result
    template = template_manager.get_template(media_type_enum)
    result = template_manager.format(parsed)

    # Print results
    cli_ui.print_heading(f"Template Preview for {media_type}")
    cli_ui.print_info("Template:")
    cli_ui.print_result(template)
    cli_ui.print_newline()
    cli_ui.print_info("Formatted Result:")
    cli_ui.print_result(result)


if __name__ == "__main__":
    cli()
