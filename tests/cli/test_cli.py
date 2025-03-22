import pytest
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

try:
    # Python 3.9+ has native support for these types
    from typing import Generator
except ImportError:
    # For Python 3.8 support
    from typing_extensions import Generator

from plexomatic.cli import cli
from plexomatic.core.backup_system import BackupSystem


@pytest.fixture
def runner() -> CliRunner:
    """Fixture that creates a CLI runner for testing commands."""
    return CliRunner()


@pytest.fixture(autouse=True)
def mock_config_db_path() -> Generator[None, None, None]:
    """Fixture that mocks the config.get_db_path method to return a test path."""
    with patch("plexomatic.cli.config.get_db_path", return_value=Path("/tmp/test-plexomatic.db")):
        yield


@pytest.fixture
def media_dir(tmp_path: Path) -> Path:
    """Fixture that creates a temporary directory with media files."""
    media_dir = tmp_path / "media"
    media_dir.mkdir()

    # Create test media files
    test_files = [
        "The.Show.S01E01.mp4",
        "The.Show.S01E02.mp4",
        "Another Show S02E05 Episode.mkv",
        "Movie.2020.1080p.mp4",
    ]

    for filename in test_files:
        (media_dir / filename).write_text("dummy content")

    return media_dir


@pytest.fixture
def mock_backup_system() -> MagicMock:
    """Mock backup system for testing."""
    backup_system = MagicMock(spec=BackupSystem)
    backup_system.record_operation.return_value = 1
    return backup_system


def test_cli_entrypoint(runner: CliRunner) -> None:
    """Test that the CLI entrypoint runs without error."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Plex-o-matic: Media file organization tool for Plex" in result.output


def test_scan_command(runner: CliRunner, media_dir: Path) -> None:
    """Test that the scan command runs without error."""
    result = runner.invoke(cli, ["scan", "--path", str(media_dir)])
    assert result.exit_code == 0
    assert "Scanning directory" in result.output
    assert media_dir.name in result.output
    assert "Found 4 media files" in result.output


def test_preview_command_with_path(runner: CliRunner, media_dir: Path) -> None:
    """Test that the preview command runs with a path parameter."""
    result = runner.invoke(cli, ["preview", "--path", str(media_dir)])
    assert result.exit_code == 0
    assert "Previewing changes" in result.output
    # At least one file should need renaming
    assert "Another Show S02E05 Episode.mkv → Another.Show.S02E05.Episode.mkv" in result.output


@patch("plexomatic.cli.get_preview_rename")
def test_preview_command_no_changes(
    mock_preview: MagicMock, runner: CliRunner, media_dir: Path
) -> None:
    """Test preview command when no changes are needed."""
    # Mock get_preview_rename to return no changes needed
    mock_preview.return_value = {
        "original_name": "file.mp4",
        "new_name": "file.mp4",  # Same name means no change needed
        "original_path": "/path/to/file.mp4",
        "new_path": "/path/to/file.mp4",
    }

    result = runner.invoke(cli, ["preview", "--path", str(media_dir)])
    assert result.exit_code == 0
    assert "No changes needed" in result.output


@patch("plexomatic.cli.rename_file")
def test_apply_command_with_path(
    mock_rename: MagicMock, runner: CliRunner, media_dir: Path
) -> None:
    """Test that the apply command runs with a path parameter."""
    # Mock rename_file to return success
    mock_rename.return_value = True

    result = runner.invoke(cli, ["apply", "--path", str(media_dir)], input="y\n")
    assert result.exit_code == 0
    assert "Applying changes" in result.output
    assert mock_rename.called


@patch("plexomatic.cli.rename_file")
def test_apply_command_dry_run(mock_rename: MagicMock, runner: CliRunner, media_dir: Path) -> None:
    """Test the apply command in dry run mode."""
    result = runner.invoke(cli, ["apply", "--dry-run", "--path", str(media_dir)], input="y\n")
    assert result.exit_code == 0
    assert "Applying changes" in result.output
    assert "dry run - no changes made" in result.output
    assert "Dry run complete" in result.output
    # Should not attempt to rename files in dry run mode
    assert not mock_rename.called


@patch("plexomatic.cli.rollback_operation")
def test_rollback_command_with_id(mock_rollback: MagicMock, runner: CliRunner) -> None:
    """Test the rollback command with a specific operation ID."""
    # Mock rollback_operation to return success
    mock_rollback.return_value = True

    # Mock the BackupSystem class
    with patch("plexomatic.cli.BackupSystem") as mock_backup_system_class:
        # Create a mock instance of BackupSystem
        mock_backup_system = MagicMock()
        mock_backup_system_class.return_value = mock_backup_system

        # Mock the get_backup_items_by_operation method to return a non-empty list
        mock_backup_system.get_backup_items_by_operation.return_value = [MagicMock()]

        result = runner.invoke(cli, ["rollback", "--operation-id", "1"], input="y\n")
        assert result.exit_code == 0
        assert "Rolling back changes" in result.output
        assert "Rolling back operation 1" in result.output
        assert mock_rollback.called


@patch("plexomatic.cli.BackupSystem")
def test_rollback_command_no_operations(mock_backup_system: MagicMock, runner: CliRunner) -> None:
    """Test the rollback command when no operations are available."""
    # Mock the connection and cursor to return no results
    conn_mock = MagicMock()
    conn_mock.execute.return_value.fetchone.return_value = None
    mock_backup_system.return_value.engine.connect.return_value.__enter__.return_value = conn_mock

    with patch("plexomatic.cli.config.get_db_path", return_value=Path("/tmp/test.db")):
        result = runner.invoke(cli, ["rollback"], input="y\n")
        assert result.exit_code == 0
        assert "No completed operations found to roll back" in result.output


def test_version_flag(runner: CliRunner) -> None:
    """Test that the version flag shows version info."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "plex-o-matic, version" in result.output


def test_scan_with_verbose_flag(runner: CliRunner, media_dir: Path) -> None:
    """Test that the verbose flag increases output detail."""
    result = runner.invoke(cli, ["scan", "--path", str(media_dir), "--verbose"])
    assert result.exit_code == 0
    assert "Verbose mode enabled" in result.output
    # With verbose, it should show each found file
    assert "The.Show.S01E01.mp4" in result.output
