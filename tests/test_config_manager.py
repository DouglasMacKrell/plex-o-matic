"""Tests for the configuration manager."""

import os
import json
import pytest
from pathlib import Path
from plexomatic.config import ConfigManager


@pytest.fixture
def temp_config_path(tmp_path):
    """Fixture to create a temporary config file path."""
    config_file = tmp_path / "config.json"
    os.environ["PLEXOMATIC_CONFIG_PATH"] = str(config_file)
    yield config_file
    # Clean up
    if "PLEXOMATIC_CONFIG_PATH" in os.environ:
        del os.environ["PLEXOMATIC_CONFIG_PATH"]


def test_config_manager_init(temp_config_path) -> None:
    """Test configuration manager initialization."""
    config = ConfigManager()
    assert config is not None

    # Check that config file was created
    assert temp_config_path.exists()

    # Check that it contains default values
    with open(temp_config_path, "r") as f:
        data = json.load(f)

    assert "db_path" in data
    assert "allowed_extensions" in data
    assert "ignore_patterns" in data
    assert "recursive_scan" in data
    assert data["recursive_scan"] is True


def test_config_manager_get_set(temp_config_path) -> None:
    """Test getting and setting configuration values."""
    config = ConfigManager()

    # Test get with default
    assert config.get("nonexistent", "default") == "default"

    # Test set and get
    config.set("test_key", "test_value")
    assert config.get("test_key") == "test_value"

    # Verify it was saved to file
    with open(temp_config_path, "r") as f:
        data = json.load(f)
    assert data["test_key"] == "test_value"

    # Create a new instance and verify value persists
    new_config = ConfigManager()
    assert new_config.get("test_key") == "test_value"


def test_config_manager_helper_methods(temp_config_path) -> None:
    """Test helper methods for common configuration values."""
    config = ConfigManager()

    # Test db path
    db_path = config.get_db_path()
    assert isinstance(db_path, Path)

    # Test allowed extensions
    extensions = config.get_allowed_extensions()
    assert isinstance(extensions, list)
    assert ".mp4" in extensions

    # Test ignore patterns
    patterns = config.get_ignore_patterns()
    assert isinstance(patterns, list)
    assert "sample" in patterns


def test_config_manager_invalid_file(tmp_path) -> None:
    """Test handling of invalid configuration files."""
    config_file = tmp_path / "invalid_config.json"

    # Create an invalid JSON file
    with open(config_file, "w") as f:
        f.write("This is not valid JSON")

    # Initialize with the invalid file
    config = ConfigManager(str(config_file))

    # Should fall back to defaults
    assert config.get("db_path") == ConfigManager.DEFAULT_CONFIG["db_path"]

    # A new config file should have been created
    with open(config_file, "r") as f:
        content = f.read()

    # The file should now contain valid JSON
    assert "{" in content
    assert "}" in content
