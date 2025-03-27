"""Tests for the template manager module."""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from plexomatic.utils.templates.template_types import TemplateType, DEFAULT_TEMPLATES_DIR
from plexomatic.utils.templates.template_manager import (
    TemplateManager,
    TemplateNotFoundError,
    InvalidTemplateError,
    get_template_manager,
    reset_template_manager,
)


@pytest.fixture
def temp_template_dir():
    """Create a temporary directory for templates."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def template_manager(temp_template_dir):
    """Create a template manager with the temporary template directory."""
    manager = TemplateManager(templates_dir=temp_template_dir)
    yield manager


class TestTemplateManager:
    """Tests for the template manager class."""

    def test_initialization(self, temp_template_dir):
        """Test initialization of template manager."""
        manager = TemplateManager(templates_dir=temp_template_dir)
        assert manager.templates_dir == temp_template_dir
        assert os.path.exists(temp_template_dir)
        assert isinstance(manager.templates, dict)
        assert isinstance(manager._custom_templates, dict)

    def test_initialization_without_directory(self):
        """Test initialization without a directory."""
        with patch("os.makedirs") as mock_makedirs:
            manager = TemplateManager()
            assert manager.templates_dir == DEFAULT_TEMPLATES_DIR
            mock_makedirs.assert_called_once_with(DEFAULT_TEMPLATES_DIR, exist_ok=True)

    def test_register_template(self, template_manager):
        """Test registering a template."""
        template_manager.register_template(TemplateType.TV_SHOW, "test", "Test template {title}")
        assert (
            template_manager.get_template(TemplateType.TV_SHOW, "test") == "Test template {title}"
        )

    def test_register_template_invalid_name(self, template_manager):
        """Test registering a template with an invalid name."""
        with pytest.raises(InvalidTemplateError):
            template_manager.register_template(TemplateType.TV_SHOW, "", "Test template")

    def test_register_template_invalid_template(self, template_manager):
        """Test registering an invalid template."""
        with pytest.raises(InvalidTemplateError):
            template_manager.register_template(TemplateType.TV_SHOW, "test", "")

    def test_get_template(self, template_manager):
        """Test getting a template."""
        template_manager.register_template(TemplateType.TV_SHOW, "test", "Test template")
        assert template_manager.get_template(TemplateType.TV_SHOW, "test") == "Test template"

    def test_get_template_missing(self, template_manager):
        """Test getting a missing template."""
        with pytest.raises(TemplateNotFoundError):
            template_manager.get_template(TemplateType.TV_SHOW, "missing")

    def test_get_template_default_fallback(self, template_manager):
        """Test getting a template with default fallback."""
        # Don't register the template, but ask for it with fallback=True
        template = template_manager.get_template(TemplateType.TV_SHOW, "default", fallback=True)
        assert template is not None  # Should get default template

    def test_get_templates(self, template_manager):
        """Test getting all templates of a type."""
        template_manager.register_template(TemplateType.TV_SHOW, "test1", "Test template 1")
        template_manager.register_template(TemplateType.TV_SHOW, "test2", "Test template 2")
        templates = template_manager.get_templates(TemplateType.TV_SHOW)
        assert len(templates) == 2
        assert "test1" in templates
        assert "test2" in templates

    def test_get_templates_empty(self, template_manager):
        """Test getting templates for a type with no templates."""
        templates = template_manager.get_templates(TemplateType.MOVIE)
        assert templates == {}

    def test_save_template_to_file(self, template_manager, temp_template_dir):
        """Test saving a template to a file."""
        template_manager.register_template(TemplateType.TV_SHOW, "test", "Test template")
        template_manager.save_template_to_file(TemplateType.TV_SHOW, "test")
        template_file = temp_template_dir / "tv_show_test.template"
        assert os.path.exists(template_file)
        with open(template_file, "r") as f:
            assert f.read() == "Test template"

    def test_save_template_to_file_directory_creation(self, template_manager):
        """Test saving a template creates the directory if needed."""
        # Make the directory non-existent
        shutil.rmtree(template_manager.templates_dir)

        template_manager.register_template(TemplateType.TV_SHOW, "test", "Test template")
        template_manager.save_template_to_file(TemplateType.TV_SHOW, "test")

        assert os.path.exists(template_manager.templates_dir)
        template_file = template_manager.templates_dir / "tv_show_test.template"
        assert os.path.exists(template_file)

    def test_load_templates_from_directory(self, template_manager, temp_template_dir):
        """Test loading templates from a directory."""
        # Create template files
        tv_file = temp_template_dir / "tv_show_test.template"
        movie_file = temp_template_dir / "movie_test.template"
        with open(tv_file, "w") as f:
            f.write("TV template")
        with open(movie_file, "w") as f:
            f.write("Movie template")

        # Load templates
        template_manager.load_templates_from_directory()

        # Check if templates were loaded correctly
        assert template_manager.get_template(TemplateType.TV_SHOW, "test") == "TV template"
        assert template_manager.get_template(TemplateType.MOVIE, "test") == "Movie template"

    def test_load_templates_invalid_filename(self, template_manager, temp_template_dir):
        """Test loading templates with invalid filenames."""
        # Create template file with invalid name
        invalid_file = temp_template_dir / "invalid.template"
        with open(invalid_file, "w") as f:
            f.write("Invalid template")

        # Load templates (should log a warning but not fail)
        with patch("logging.Logger.warning") as mock_warning:
            template_manager.load_templates_from_directory()
            mock_warning.assert_called_once()

    def test_global_template_manager(self):
        """Test the global template manager functions."""
        # Reset to ensure we start fresh
        reset_template_manager()

        # Get the global manager
        manager1 = get_template_manager()
        assert isinstance(manager1, TemplateManager)

        # Get it again, should be the same instance
        manager2 = get_template_manager()
        assert manager1 is manager2

        # Reset and get a new one, should be a different instance
        reset_template_manager()
        manager3 = get_template_manager()
        assert manager1 is not manager3
