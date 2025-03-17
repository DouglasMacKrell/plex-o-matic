"""Tests for the configure command in the CLI."""

from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner

from plexomatic.cli import cli


def test_configure_command_help():
    """Test that the configure command exists and has help text."""
    runner = CliRunner()
    result = runner.invoke(cli, ["configure", "--help"])
    assert result.exit_code == 0
    assert "Configure API keys and application settings" in result.output


@patch("plexomatic.cli.config")
def test_configure_command_initial_setup(mock_config):
    """Test that the configure command works for initial setup."""
    # Set up mock config
    mock_config.config = {
        "api": {
            "tvdb": {"api_key": ""},
            "tmdb": {"api_key": ""},
            "anidb": {"username": "", "password": ""},
            "tvmaze": {"cache_size": 100},
            "llm": {"model_name": "deepseek-r1:8b", "base_url": "http://localhost:11434"},
        }
    }
    # Properly mock get_db_path to return a Path object
    mock_config.get_db_path.return_value = Path("/tmp/test-plexomatic.db")

    runner = CliRunner()

    # Simulate user input for API keys
    user_input = "\n".join(
        [
            "test-tvdb-key",  # TVDB API key
            "test-tmdb-key",  # TMDB API key
            "y",  # Configure AniDB
            "test-anidb-user",  # AniDB username
            "test-anidb-pass",  # AniDB password
            "y",  # Configure LLM
            "",  # Default LLM URL
            "",  # Default LLM model
        ]
    )

    result = runner.invoke(cli, ["configure"], input=user_input)
    assert result.exit_code == 0
    assert "Configuration saved successfully" in result.output

    # Verify the config was updated
    assert mock_config.config["api"]["tvdb"]["api_key"] == "test-tvdb-key"
    assert mock_config.config["api"]["tmdb"]["api_key"] == "test-tmdb-key"
    assert mock_config.config["api"]["anidb"]["username"] == "test-anidb-user"
    assert mock_config.config["api"]["anidb"]["password"] == "test-anidb-pass"

    # Verify save was called
    mock_config.save.assert_called_once()


@patch("plexomatic.cli.config")
def test_configure_command_skip_optional(mock_config):
    """Test that the configure command allows skipping optional sections."""
    # Set up mock config
    mock_config.config = {
        "api": {
            "tvdb": {"api_key": ""},
            "tmdb": {"api_key": ""},
            "anidb": {"username": "", "password": ""},
            "tvmaze": {"cache_size": 100},
            "llm": {"model_name": "deepseek-r1:8b", "base_url": "http://localhost:11434"},
        }
    }
    # Properly mock get_db_path to return a Path object
    mock_config.get_db_path.return_value = Path("/tmp/test-plexomatic.db")

    runner = CliRunner()

    # Simulate user input skipping AniDB and LLM
    user_input = "\n".join(
        [
            "test-tvdb-key",  # TVDB API key
            "test-tmdb-key",  # TMDB API key
            "n",  # Skip AniDB
            "n",  # Skip LLM
        ]
    )

    result = runner.invoke(cli, ["configure"], input=user_input)
    assert result.exit_code == 0
    assert "Configuration saved successfully" in result.output

    # Verify the config was updated
    assert mock_config.config["api"]["tvdb"]["api_key"] == "test-tvdb-key"
    assert mock_config.config["api"]["tmdb"]["api_key"] == "test-tmdb-key"
    assert mock_config.config["api"]["anidb"]["username"] == ""  # Should remain empty
    assert mock_config.config["api"]["anidb"]["password"] == ""  # Should remain empty

    # Verify save was called
    mock_config.save.assert_called_once()


@patch("plexomatic.cli.config")
def test_configure_command_create_api_section(mock_config):
    """Test that the configure command creates API section if it doesn't exist."""
    # Set up mock config without API section
    mock_config.config = {
        "db_path": "test/path",
        "log_level": "INFO",
        "allowed_extensions": [".mp4", ".mkv"],
    }
    # Properly mock get_db_path to return a Path object
    mock_config.get_db_path.return_value = Path("/tmp/test-plexomatic.db")

    runner = CliRunner()

    # Simulate minimal user input
    user_input = "\n".join(["", "", "n", "n"])  # Skip TVDB  # Skip TMDB  # Skip AniDB  # Skip LLM

    result = runner.invoke(cli, ["configure"], input=user_input)
    assert result.exit_code == 0

    # Verify the config was updated with API section
    assert "api" in mock_config.config
    assert "tvdb" in mock_config.config["api"]
    assert "tmdb" in mock_config.config["api"]
    assert "anidb" in mock_config.config["api"]
    assert "llm" in mock_config.config["api"]

    # Verify save was called
    mock_config.save.assert_called_once()
