"""Tests for the CLI commands module."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

# Import the commands we want to test directly
from plexomatic.cli.commands import preview_command, apply_command, scan_command, rollback_command, configure_command

@pytest.fixture
def runner() -> CliRunner:
    """Fixture that creates a CLI runner for testing commands."""
    return CliRunner()

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

def test_scan_command(runner: CliRunner, media_dir: Path) -> None:
    """Test that the scan command runs without error."""
    with patch("plexomatic.cli.commands.scan.FileScanner") as mock_scanner_class:
        # Mock the scanner to return some media files
        mock_scanner = MagicMock()
        mock_scanner_class.return_value = mock_scanner
        
        mock_media_files = [MagicMock(path=media_dir / f) for f in ["file1.mp4", "file2.mkv"]]
        mock_scanner.scan.return_value = mock_media_files
        
        # Set up ConfigManager mock
        with patch("plexomatic.cli.commands.scan.ConfigManager") as mock_config_class:
            mock_config = MagicMock()
            mock_config_class.return_value = mock_config
            mock_config.get_allowed_extensions.return_value = [".mp4", ".mkv"]
            
            result = runner.invoke(scan_command, ["--path", str(media_dir)])
            
            assert result.exit_code == 0
            assert "Scanning directory" in result.output
            assert "Found" in result.output
            
            # Verify scanner was called with correct parameters
            mock_scanner_class.assert_called_once()
            mock_scanner.scan.assert_called_once()

@patch("plexomatic.cli.commands.rollback.BackupSystem")
def test_rollback_command_with_id(mock_backup_system_class: MagicMock, runner: CliRunner) -> None:
    """Test the rollback command with a specific operation ID."""
    # Create a mock instance of BackupSystem
    mock_backup_system = MagicMock()
    mock_backup_system_class.return_value = mock_backup_system
    
    # Mock the get_backup_items_by_operation method to return a non-empty list
    mock_backup_system.get_backup_items_by_operation.return_value = [MagicMock()]
    
    # Mock rollback_operation to return success
    with patch("plexomatic.cli.commands.rollback.rollback_operation") as mock_rollback:
        mock_rollback.return_value = True
        
        result = runner.invoke(rollback_command, ["--operation-id", "1"], input="y\n")
        
        assert result.exit_code == 0
        assert "Rolling back operation 1" in result.output
        assert mock_rollback.called
        mock_rollback.assert_called_with(1, mock_backup_system)

@patch("plexomatic.cli.commands.configure.ConfigManager")
def test_configure_command(mock_config_class: MagicMock, runner: CliRunner) -> None:
    """Test that the configure command works correctly."""
    # Set up mock config
    mock_config = MagicMock()
    mock_config_class.return_value = mock_config
    mock_config.config = {
        "api": {
            "tvdb": {"api_key": ""},
            "tmdb": {"api_key": ""},
            "anidb": {"username": "", "password": ""},
            "tvmaze": {"cache_size": 100},
            "llm": {"model_name": "deepseek-r1:8b", "base_url": "http://localhost:11434"},
        }
    }
    
    # Simulate user input for API keys
    user_input = "\n".join(
        [
            "test-tvdb-key",        # TVDB API key
            "test-pin",             # TVDB PIN
            "test-tmdb-key",        # TMDB API key
            "n",                    # Skip AniDB
            "n",                    # Skip LLM
        ]
    )
    
    result = runner.invoke(configure_command, input=user_input)
    
    assert result.exit_code == 0
    assert "Configuration saved successfully" in result.output
    
    # Verify the config was updated
    assert mock_config.config["api"]["tvdb"]["api_key"] == "test-tvdb-key"
    assert mock_config.config["api"]["tvdb"]["pin"] == "test-pin"
    assert mock_config.config["api"]["tmdb"]["api_key"] == "test-tmdb-key"
    
    # Verify save was called
    mock_config.save.assert_called_once()

def test_configure_command_help(runner: CliRunner) -> None:
    """Test that the configure command exists and has help text."""
    result = runner.invoke(configure_command, ["--help"])
    assert result.exit_code == 0
    assert "Configure API keys and application settings" in result.output 