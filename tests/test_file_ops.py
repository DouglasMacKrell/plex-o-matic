"""Tests for file operations utilities."""

import hashlib
import pytest
from unittest.mock import patch, MagicMock
import shutil

from plexomatic.utils.file_ops import (
    calculate_file_checksum,
    rename_file,
    rollback_operation,
)
from plexomatic.core.backup_system import BackupSystem


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file with known content."""
    file_path = tmp_path / "test.txt"
    content = b"test content"
    file_path.write_bytes(content)
    return file_path, content


@pytest.fixture
def mock_backup_system():
    """Create a mock backup system."""
    mock = MagicMock(spec=BackupSystem)
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    mock.engine = mock_engine
    return mock


class TestCalculateChecksum:
    """Test the calculate_file_checksum function."""

    def test_calculate_checksum(self, temp_file) -> None:
        """Test calculating checksum of a file with known content."""
        file_path, content = temp_file
        expected = hashlib.sha256(content).hexdigest()
        assert calculate_file_checksum(file_path) == expected

    def test_empty_file(self, tmp_path) -> None:
        """Test calculating checksum of an empty file."""
        file_path = tmp_path / "empty.txt"
        file_path.write_bytes(b"")
        expected = hashlib.sha256(b"").hexdigest()
        assert calculate_file_checksum(file_path) == expected

    def test_large_file(self, tmp_path) -> None:
        """Test calculating checksum of a large file."""
        file_path = tmp_path / "large.txt"
        # Create a 10MB file with repeating pattern
        content = b"0123456789" * 1024 * 1024
        file_path.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert calculate_file_checksum(file_path) == expected

    def test_nonexistent_file(self, tmp_path) -> None:
        """Test calculating checksum of a nonexistent file."""
        file_path = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            calculate_file_checksum(file_path)


class TestRenameFile:
    """Test the rename_file function."""

    def test_basic_rename(self, temp_file) -> None:
        """Test basic file renaming without backup."""
        file_path, _ = temp_file
        new_path = file_path.parent / "renamed.txt"
        assert rename_file(file_path, new_path)
        assert not file_path.exists()
        assert new_path.exists()

    def test_rename_with_backup(self, temp_file, mock_backup_system) -> None:
        """Test file renaming with backup system."""
        file_path, _ = temp_file
        new_path = file_path.parent / "renamed.txt"
        mock_backup_system.record_operation.return_value = 1

        assert rename_file(file_path, new_path, mock_backup_system)
        assert not file_path.exists()
        assert new_path.exists()

        # Verify backup system calls
        mock_backup_system.record_operation.assert_called_once()
        mock_backup_system.mark_operation_complete.assert_called_once_with(1)

    def test_rename_nonexistent_file(self, tmp_path) -> None:
        """Test renaming a nonexistent file."""
        file_path = tmp_path / "nonexistent.txt"
        new_path = tmp_path / "renamed.txt"
        assert not rename_file(file_path, new_path)

    def test_rename_to_existing_directory(self, temp_file) -> None:
        """Test renaming when target directory doesn't exist."""
        file_path, _ = temp_file
        new_path = file_path.parent / "subdir" / "renamed.txt"
        assert rename_file(file_path, new_path)
        assert not file_path.exists()
        assert new_path.exists()

    @patch("shutil.move")
    def test_rename_error_handling(self, mock_move, temp_file) -> None:
        """Test error handling during rename."""
        file_path, _ = temp_file
        new_path = file_path.parent / "renamed.txt"
        mock_move.side_effect = OSError("Permission denied")
        assert not rename_file(file_path, new_path)
        assert file_path.exists()  # Original file should still exist


class TestRollback:
    """Test the rollback_operation function."""

    def test_successful_rollback(self, temp_file, mock_backup_system) -> None:
        """Test successful rollback of a rename operation."""
        file_path, content = temp_file
        new_path = file_path.parent / "renamed.txt"

        # Set up mock operation record
        mock_operation = MagicMock()
        mock_operation.original_path = str(file_path)
        mock_operation.new_path = str(new_path)
        mock_operation.status = "completed"

        # Set up mock database query
        mock_backup_system.engine.connect.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = (
            mock_operation
        )
        mock_backup_system.verify_operation_checksum.return_value = True

        # Move file to simulate completed rename
        shutil.move(str(file_path), str(new_path))

        # Perform rollback
        assert rollback_operation(1, mock_backup_system)
        assert file_path.exists()
        assert not new_path.exists()

        # Verify backup system calls
        mock_backup_system.rollback_operation.assert_called_once_with(1)

    def test_rollback_missing_file(self, mock_backup_system) -> None:
        """Test rollback when renamed file is missing."""
        # Set up mock operation record
        mock_operation = MagicMock()
        mock_operation.original_path = "/path/to/original"
        mock_operation.new_path = "/path/to/renamed"
        mock_operation.status = "completed"

        # Set up mock database query
        mock_backup_system.engine.connect.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = (
            mock_operation
        )

        assert not rollback_operation(1, mock_backup_system)
        mock_backup_system.rollback_operation.assert_not_called()

    def test_rollback_invalid_operation(self, mock_backup_system) -> None:
        """Test rollback with invalid operation ID."""
        # Set up mock database query to return None
        mock_backup_system.engine.connect.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = (
            None
        )

        assert not rollback_operation(1, mock_backup_system)
        mock_backup_system.rollback_operation.assert_not_called()

    def test_rollback_incomplete_operation(self, mock_backup_system) -> None:
        """Test rollback of incomplete operation."""
        # Set up mock operation record with incomplete status
        mock_operation = MagicMock()
        mock_operation.status = "pending"

        # Set up mock database query
        mock_backup_system.engine.connect.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = (
            mock_operation
        )

        assert not rollback_operation(1, mock_backup_system)
        mock_backup_system.rollback_operation.assert_not_called()

    def test_rollback_checksum_mismatch(self, temp_file, mock_backup_system) -> None:
        """Test rollback with checksum mismatch."""
        file_path, content = temp_file
        new_path = file_path.parent / "renamed.txt"

        # Set up mock operation record
        mock_operation = MagicMock()
        mock_operation.original_path = str(file_path)
        mock_operation.new_path = str(new_path)
        mock_operation.status = "completed"

        # Set up mock database query
        mock_backup_system.engine.connect.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = (
            mock_operation
        )
        mock_backup_system.verify_operation_checksum.return_value = False

        # Move file to simulate completed rename
        shutil.move(str(file_path), str(new_path))

        # Perform rollback - should continue with warning
        assert rollback_operation(1, mock_backup_system)
        assert file_path.exists()
        assert not new_path.exists()

        # Verify backup system calls
        mock_backup_system.rollback_operation.assert_called_once_with(1)

    def test_rollback_checksum_error(self, temp_file, mock_backup_system) -> None:
        """Test rollback when checksum calculation fails."""
        file_path, content = temp_file
        new_path = file_path.parent / "renamed.txt"

        # Set up mock operation record
        mock_operation = MagicMock()
        mock_operation.original_path = str(file_path)
        mock_operation.new_path = str(new_path)
        mock_operation.status = "completed"

        # Set up mock database query
        mock_backup_system.engine.connect.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = (
            mock_operation
        )

        # Make verify_operation_checksum raise an exception
        mock_backup_system.verify_operation_checksum.side_effect = Exception(
            "Failed to verify checksum"
        )

        # Move file to simulate completed rename
        shutil.move(str(file_path), str(new_path))

        # Should proceed with warning
        assert rollback_operation(1, mock_backup_system)
        assert file_path.exists()
        assert not new_path.exists()
        mock_backup_system.rollback_operation.assert_called_once_with(1)

    @patch("shutil.move")
    def test_rollback_move_error(self, mock_move, temp_file, mock_backup_system) -> None:
        """Test rollback when move operation fails."""
        file_path, content = temp_file
        new_path = file_path.parent / "renamed.txt"

        # Create the "renamed" file directly
        new_path.write_bytes(content)

        # Set up mock operation record
        mock_operation = MagicMock()
        mock_operation.original_path = str(file_path)
        mock_operation.new_path = str(new_path)
        mock_operation.status = "completed"

        # Set up mock database query
        mock_backup_system.engine.connect.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = (
            mock_operation
        )
        mock_backup_system.verify_operation_checksum.return_value = True

        # Make move operation fail
        mock_move.side_effect = OSError("Permission denied")

        # Should fail and not mark operation as rolled back
        assert not rollback_operation(1, mock_backup_system)
        mock_backup_system.rollback_operation.assert_not_called()
        assert new_path.exists()  # File should still exist at new location
