"""Tests for the backup system module."""

import os
import pytest
from pathlib import Path
from sqlalchemy.orm import Session
from plexomatic.core.backup_system import BackupSystem, FileOperation
from plexomatic.core.models import FileRename


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Create a temporary database file."""
    return tmp_path / "test.db"


@pytest.fixture
def backup_system(db_path: Path) -> BackupSystem:
    """Create a backup system instance for testing."""
    system = BackupSystem(db_path)
    system.initialize_database()
    return system


@pytest.fixture
def sample_operation(backup_system: BackupSystem) -> FileOperation:
    """Create a sample file operation."""
    operation = FileOperation(
        original_path="/test/path/old_name.mp4",
        new_path="/test/path/new_name.mp4",
        operation_type="rename",
        checksum="abc123",
    )
    return operation


def test_backup_system_initialization(db_path: Path) -> None:
    """Test that BackupSystem initializes correctly."""
    system = BackupSystem(db_path)
    system.initialize_database()

    assert system.db_path == db_path
    assert os.path.exists(db_path)


def test_file_operation_creation(
    backup_system: BackupSystem, sample_operation: FileOperation
) -> None:
    """Test creating a new file operation."""
    operation_id = backup_system.record_operation(sample_operation)

    with Session(backup_system.engine) as session:
        stored_op = session.query(FileRename).filter_by(id=operation_id).first()

        assert stored_op is not None
        assert stored_op.original_path == sample_operation.original_path
        assert stored_op.new_path == sample_operation.new_path
        assert stored_op.operation_type == sample_operation.operation_type
        assert stored_op.checksum == sample_operation.checksum
        assert stored_op.status == "pending"


def test_operation_completion(backup_system: BackupSystem, sample_operation: FileOperation) -> None:
    """Test marking an operation as complete."""
    operation_id = backup_system.record_operation(sample_operation)
    backup_system.mark_operation_complete(operation_id)

    with Session(backup_system.engine) as session:
        stored_op = session.query(FileRename).filter_by(id=operation_id).first()
        assert stored_op is not None  # Add a check to ensure it's not None
        assert stored_op.status == "completed"
        assert stored_op.completed_at is not None


def test_operation_rollback(backup_system: BackupSystem, sample_operation: FileOperation) -> None:
    """Test rolling back an operation."""
    operation_id = backup_system.record_operation(sample_operation)
    backup_system.mark_operation_complete(operation_id)

    # Simulate rollback
    backup_system.rollback_operation(operation_id)

    with Session(backup_system.engine) as session:
        stored_op = session.query(FileRename).filter_by(id=operation_id).first()
        assert stored_op is not None  # Add a check to ensure it's not None
        assert stored_op.status == "rolled_back"
        assert stored_op.rolled_back_at is not None


def test_get_pending_operations(backup_system: BackupSystem) -> None:
    """Test retrieving pending operations."""
    # Create multiple operations
    ops = [
        FileOperation("/test/1.mp4", "/test/1_new.mp4", "rename", "sum1"),
        FileOperation("/test/2.mp4", "/test/2_new.mp4", "rename", "sum2"),
        FileOperation("/test/3.mp4", "/test/3_new.mp4", "rename", "sum3"),
    ]

    for op in ops:
        backup_system.record_operation(op)

    pending = backup_system.get_pending_operations()
    assert len(pending) == 3

    # Complete one operation
    operation_id = int(pending[0].id)  # Explicitly cast to int
    backup_system.mark_operation_complete(operation_id)

    pending = backup_system.get_pending_operations()
    assert len(pending) == 2


def test_verify_checksum(backup_system: BackupSystem, sample_operation: FileOperation) -> None:
    """Test checksum verification for operations."""
    operation_id = backup_system.record_operation(sample_operation)

    # Simulate successful verification
    assert backup_system.verify_operation_checksum(operation_id, "abc123") is True

    # Simulate failed verification
    assert backup_system.verify_operation_checksum(operation_id, "wrong123") is False
