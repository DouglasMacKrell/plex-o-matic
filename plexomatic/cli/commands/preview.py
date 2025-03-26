"""Command to preview naming convention changes without applying them."""

import logging
import os
from pathlib import Path
from typing import Optional, List

import click
from rich.console import Console
from rich.table import Table

from plexomatic.core.file_scanner import FileScanner
from plexomatic.utils.name_utils import preview_rename
from plexomatic.utils.episode import is_anthology_episode, get_segment_count
from plexomatic.utils.anthology_utils import preprocess_anthology_episodes
from plexomatic.config.config_manager import ConfigManager


@click.command()
@click.option(
    "-p",
    "--path",
    type=click.Path(exists=True),
    help="Path to directory or file to preview",
)
@click.option(
    "--recursive/--no-recursive",
    default=True,
    help="Scan directories recursively",
)
@click.option(
    "-e",
    "--extensions",
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
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output.")
def preview_command(
    path: Optional[str],
    recursive: bool,
    extensions: Optional[str],
    anthology_mode: bool,
    no_llm: bool,
    no_api_lookup: bool,
    verbose: bool,
):
    """Preview changes that would be made."""
    logger = logging.getLogger("plexomatic")
    console = Console()

    if verbose:
        logger.debug("Verbose mode enabled")
        console.print("[info]Verbose mode enabled[/info]")

    if anthology_mode:
        console.print("[info]Anthology mode enabled for this operation[/info]")

    # Load config
    config = ConfigManager()

    # Default to current directory if no path provided
    if not path:
        path = os.getcwd()
    
    path_obj = Path(path)

    # Resolve extensions
    if not extensions:
        extensions = config.get("video_extensions", ".mp4,.mkv,.avi,.mov,.m4v")

    extension_list = extensions.split(",")
    
    # Ensure extensions have dots
    extension_list = [ext if ext.startswith('.') else f'.{ext}' for ext in extension_list]

    # Scan files
    console.print("Previewing changes")
    
    # Check if we have a single file or a directory
    if path_obj.is_file():
        logger.debug(f"Processing single file: {path}")
        files = [str(path_obj)]
    else:
        logger.debug(f"Processing directory: {path}")
        # Use the FileScanner class
        scanner = FileScanner(path, allowed_extensions=extension_list, recursive=recursive)
        files = [str(media_file.path) for media_file in scanner.scan()]

    # For anthology mode with multiple files, preprocess episode numbering
    preprocessed_data = None
    if anthology_mode and len(files) > 1:
        use_llm = not no_llm
        api_lookup = not no_api_lookup
        preprocessed_data = preprocess_anthology_episodes(files, use_llm, api_lookup)
        logger.debug(f"Preprocessed {len(preprocessed_data)} files for anthology sequential numbering")

    # Process each file for preview
    rename_count = 0
    unchanged_count = 0
    preview_results = []

    for file_path in files:
        use_dots = config.get("use_dots", False)
        use_llm = not no_llm
        api_lookup = not no_api_lookup

        result = preview_rename(
            file_path=file_path,
            use_dots=use_dots,
            anthology_mode=anthology_mode,
            use_llm=use_llm,
            api_lookup=api_lookup,
            preprocessed_data=preprocessed_data
        )

        if result:
            preview_results.append(result)
            if result["needs_rename"]:
                rename_count += 1
                if verbose:
                    logger.debug(f"{result['original_basename']} → {result['new_basename']}")
                    console.print(
                        f"{result['original_basename']} → {result['new_basename']}"
                    )
            else:
                unchanged_count += 1

    # Print summary
    table = Table(title="Rename Summary")
    table.add_column("Item", style="dim")
    table.add_column("Value")

    table.add_row("Total files", str(len(files)))
    table.add_row("Files to rename", str(rename_count))
    table.add_row("Files already correct", str(unchanged_count))

    console.print(table)

    # Print preview summary
    console.print(
        f"[info]Previewing changes for {len(files)} files[/info]\n"
        f"  Path: {path}\n"
        f"  Recursive: {recursive}\n"
        f"  Extensions: {extensions}\n"
        f"  Anthology mode: {anthology_mode}\n"
        f"  LLM assistance: {not no_llm}\n"
        f"  API lookup: {not no_api_lookup}"
    ) 