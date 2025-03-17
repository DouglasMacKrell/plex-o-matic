"""Backup system for tracking and managing file operations."""

from datetime import datetime, UTC
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
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
            return rename.id

    def mark_operation_complete(self, operation_id: int) -> None:
        """Mark an operation as completed.

        Args:
            operation_id: ID of the operation to mark as complete
        """
        with Session(self.engine) as session:
            operation = session.get(FileRename, operation_id)
            if operation:
                operation.status = "completed"
                operation.completed_at = datetime.now(UTC)
                session.commit()

    def rollback_operation(self, operation_id: int) -> None:
        """Roll back a completed operation.

        Args:
            operation_id: ID of the operation to roll back
        """
        with Session(self.engine) as session:
            operation = session.get(FileRename, operation_id)
            if operation and operation.status == "completed":
                operation.status = "rolled_back"
                operation.rolled_back_at = datetime.now(UTC)
                session.commit()

    def get_pending_operations(self) -> List[FileRename]:
        """Get all pending operations.

        Returns:
            List[FileRename]: List of pending operations
        """
        with Session(self.engine) as session:
            stmt = select(FileRename).where(FileRename.status == "pending")
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
            return operation is not None and operation.checksum == checksum
