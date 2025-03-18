"""File operations utilities with backup support."""

import hashlib
import shutil
from pathlib import Path
from typing import Optional

from plexomatic.core.backup_system import BackupSystem, FileOperation


def calculate_file_checksum(file_path: Path) -> str:
    """Calculate the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file

    Returns:
        str: Hex-encoded SHA-256 checksum
    """
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()


def rename_file(
    original_path: Path, new_path: Path, backup_system: Optional[BackupSystem] = None
) -> bool:
    """Rename a file with backup.

    Args:
        original_path: Original path of the file
        new_path: New path for the file
        backup_system: BackupSystem instance, or None to skip backup

    Returns:
        bool: True if successful, False otherwise
    """
    if not original_path.exists():
        return False

    # Create directory if it doesn't exist
    new_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Record operation in backup system if provided
        operation_id = None
        if backup_system:
            checksum = calculate_file_checksum(original_path)
            operation = FileOperation(
                original_path=str(original_path),
                new_path=str(new_path),
                operation_type="rename",
                checksum=checksum,
            )
            operation_id = backup_system.record_operation(operation)

        # Perform the rename
        shutil.move(str(original_path), str(new_path))

        # Mark operation as complete
        if backup_system and operation_id:
            backup_system.mark_operation_complete(operation_id)

        return True
    except Exception as e:
        print(f"Error renaming file: {e}")
        return False


def rollback_operation(operation_id: int, backup_system: BackupSystem) -> bool:
    """Roll back a file operation.

    Args:
        operation_id: ID of the operation to roll back
        backup_system: BackupSystem instance

    Returns:
        bool: True if successful, False otherwise
    """
    with backup_system.engine.connect() as conn:
        # Use parameterized query instead of string interpolation for security and compatibility
        from sqlalchemy import text

        result = conn.execute(
            text("SELECT * FROM file_renames WHERE id = :operation_id"),
            {"operation_id": operation_id},
        )
        operation = result.fetchone()

        if not operation or operation.status != "completed":
            return False

        original_path = Path(operation.original_path)
        new_path = Path(operation.new_path)

        if not new_path.exists():
            return False

        # Verify checksum if possible
        try:
            current_checksum = calculate_file_checksum(new_path)
            if not backup_system.verify_operation_checksum(operation_id, current_checksum):
                print(f"Warning: Checksum verification failed for operation {operation_id}")
                # Continue anyway, but with a warning
        except Exception as e:
            print(f"Error verifying checksum: {e}")

        try:
            # Ensure the directory exists
            original_path.parent.mkdir(parents=True, exist_ok=True)

            # Move the file back
            shutil.move(str(new_path), str(original_path))

            # Mark as rolled back
            backup_system.rollback_operation(operation_id)

            return True
        except Exception as e:
            print(f"Error rolling back operation: {e}")
            return False
