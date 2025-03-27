"""Command to scan media directories for files to organize."""

import logging
from pathlib import Path
from typing import List, Any, Optional

import click
from rich.console import Console

from plexomatic.core.file_scanner import FileScanner
from plexomatic.config.config_manager import ConfigManager


@click.command()
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
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output.")
@click.pass_context
def scan_command(
    ctx: click.Context,
    path: Path,
    recursive: bool,
    extensions: Optional[str],
    anthology_mode: bool,
    no_llm: bool,
    verbose: bool,
) -> List[Any]:
    """Scan a directory for media files."""
    logger = logging.getLogger("plexomatic")
    console = Console()

    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        console.print("[info]Verbose mode enabled[/info]")

    if anthology_mode:
        console.print("[info]Anthology mode enabled for this operation[/info]")

    # Load config
    config = ConfigManager()

    # Resolve extensions
    if not extensions:
        extension_list = config.get_allowed_extensions()
    else:
        extension_list = [ext.strip() for ext in extensions.split(",")]

    # Ensure extensions have dots
    extension_list = [ext if ext.startswith(".") else f".{ext}" for ext in extension_list]

    # Create file scanner
    scanner = FileScanner(path, extension_list)
    scanner.recursive = recursive

    # Store scanner options in context for later commands
    ctx.obj = ctx.obj or {}
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
            console.print("[info]Anthology mode enabled for this operation[/info]")

    console.print(f"Scanning directory: {path}")

    # Perform scan
    media_files = []
    for media_file in scanner.scan():
        media_files.append(media_file)

    console.print(f"Found {len(media_files)} media files")

    # Store scan results in context
    ctx.obj["media_files"] = media_files

    if verbose:
        console.print("\nFiles found:")
        for media_file in media_files:
            console.print(f"  - {media_file.path}")

    # Print scan summary
    console.print(
        f"[info]Scanned {path} for media files[/info]\n"
        f"  Recursive: {recursive}\n"
        f"  Extensions: {','.join(extension_list)}\n"
        f"  Anthology mode: {anthology_mode}\n"
        f"  LLM assistance: {not no_llm}"
    )

    return media_files
