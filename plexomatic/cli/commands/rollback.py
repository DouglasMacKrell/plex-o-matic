"""Command to rollback previous file operations."""

import logging
from typing import Optional

import click
from rich.console import Console

from plexomatic.core.backup_system import BackupSystem
from plexomatic.config.config_manager import ConfigManager
from plexomatic.utils.file_ops import rollback_operation


@click.command()
@click.option(
    "--operation-id", type=int, help="ID of the operation to roll back (defaults to last operation)"
)
@click.confirmation_option(prompt="Are you sure you want to rollback the last operation?")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output.")
@click.pass_context
def rollback_command(ctx: click.Context, operation_id: Optional[int], verbose: bool) -> bool:
    """Rollback the last operation."""
    logger = logging.getLogger("plexomatic")
    console = Console()

    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        console.print("[info]Verbose mode enabled[/info]")

    console.print("Rolling back changes")

    # Load config
    config = ConfigManager()

    # Initialize the backup system
    db_path = config.get_db_path()
    backup_system = BackupSystem(db_path)
    backup_system.initialize_database()

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
                console.print("[warning]No completed operations found to roll back.[/warning]")
                return False
            operation_id = row[0]

    if operation_id:
        console.print(f"[info]Rolling back operation {operation_id}[/info]")

        # Get the rollback items
        rollback_items = backup_system.get_backup_items_by_operation(operation_id)
        if not rollback_items:
            console.print(f"[warning]No items found for operation {operation_id}[/warning]")
            return False

        # Perform the rollback
        success = rollback_operation(operation_id, backup_system)

        if success:
            console.print(f"[success]Successfully rolled back operation {operation_id}[/success]")
        else:
            console.print(f"[error]Failed to roll back operation {operation_id}[/error]")

        return success
    else:
        console.print("[warning]No operation to roll back.[/warning]")
        return False
