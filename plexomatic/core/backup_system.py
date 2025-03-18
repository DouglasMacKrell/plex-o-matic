"""Backup system for tracking and managing file operations."""

from pathlib import Path
from dataclasses import dataclass

try:
    # Python 3.9+ has native support for these types
    from typing import List, cast
except ImportError:
    # For Python 3.8 support
    from typing_extensions import List, cast
from datetime import datetime, timezone
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from .models import Base, FileRename


@dataclass
class FileOperation:
    """Data class representing a file operation."""

    original_path: str
    new_path: str
    operation_type: str
    checksum: str


class BackupSystem:
    """System for tracking and managing file operations with rollback capability."""

    def __init__(self, db_path: Path):
        """Initialize the backup system.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)

    def initialize_database(self) -> None:
        """Create database tables if they don't exist."""
        Base.metadata.create_all(self.engine)

    def record_operation(self, operation: FileOperation) -> int:
        """Record a new file operation.

        Args:
            operation: FileOperation instance with operation details

        Returns:
            int: ID of the created operation record
        """
        with Session(self.engine) as session:
            rename = FileRename(
                original_path=operation.original_path,
                new_path=operation.new_path,
                operation_type=operation.operation_type,
                checksum=operation.checksum,
                status="pending",
            )
            session.add(rename)
            session.commit()
            return cast(int, rename.id)

    def mark_operation_complete(self, operation_id: int) -> None:
        """Mark an operation as completed.

        Args:
            operation_id: ID of the operation to mark as complete
        """
        with Session(self.engine) as session:
            operation = session.get(FileRename, operation_id)
            if operation:
                # Access the operation attributes through setattr to avoid typing issues
                setattr(operation, "status", "completed")
                setattr(operation, "completed_at", datetime.now(timezone.utc))
                session.commit()

    def rollback_operation(self, operation_id: int) -> None:
        """Roll back a completed operation.

        Args:
            operation_id: ID of the operation to roll back
        """
        with Session(self.engine) as session:
            operation = session.get(FileRename, operation_id)
            if operation:
                status = getattr(operation, "status", "")
                if status == "completed":
                    # Access the operation attributes through setattr to avoid typing issues
                    setattr(operation, "status", "rolled_back")
                    setattr(operation, "rolled_back_at", datetime.now(timezone.utc))
                    session.commit()

    def get_pending_operations(self) -> List[FileRename]:
        """Get all pending operations.

        Returns:
            List[FileRename]: List of pending operations
        """
        with Session(self.engine) as session:
            stmt = select(FileRename).where(FileRename.status == "pending")
            return list(session.scalars(stmt))

    def get_backup_items_by_operation(self, operation_id: int) -> List[FileRename]:
        """Get all backup items related to a specific operation.

        Args:
            operation_id: ID of the operation to get items for

        Returns:
            List[FileRename]: List of file rename operations
        """
        with Session(self.engine) as session:
            stmt = select(FileRename).where(FileRename.id == operation_id)
            return list(session.scalars(stmt))

    def verify_operation_checksum(self, operation_id: int, checksum: str) -> bool:
        """Verify the checksum of an operation.

        Args:
            operation_id: ID of the operation to verify
            checksum: Checksum to verify against

        Returns:
            bool: True if checksum matches, False otherwise
        """
        with Session(self.engine) as session:
            operation = session.get(FileRename, operation_id)
            if operation is None:
                return False
            return cast(str, operation.checksum) == checksum
