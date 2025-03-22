"""Tests for the template_registry module."""

from unittest.mock import patch, MagicMock

from plexomatic.utils.template_types import TemplateType
from plexomatic.utils.template_registry import (
    register_template,
    get_template,
    get_available_templates,
    save_template_to_file,
    load_templates,
)


@patch("plexomatic.utils.template_registry.get_template_manager")
class TestTemplateRegistry:
    """Tests for the template registry module."""

    def test_register_template(self, mock_get_manager):
        """Test registering a template."""
        # Setup
        mock_manager = MagicMock()
        mock_get_manager.return_value = mock_manager

        # Call the function
        register_template(TemplateType.TV_SHOW, "test", "Test template")

        # Assert
        mock_manager.register_template.assert_called_once_with(
            TemplateType.TV_SHOW, "test", "Test template"
        )

    def test_get_template(self, mock_get_manager):
        """Test getting a template."""
        # Setup
        mock_manager = MagicMock()
        mock_manager.get_template.return_value = "Test template"
        mock_get_manager.return_value = mock_manager

        # Call the function
        template = get_template(TemplateType.TV_SHOW, "test")

        # Assert
        assert template == "Test template"
        mock_manager.get_template.assert_called_once_with(TemplateType.TV_SHOW, "test", False)

    def test_get_template_with_fallback(self, mock_get_manager):
        """Test getting a template with fallback."""
        # Setup
        mock_manager = MagicMock()
        mock_manager.get_template.return_value = "Default template"
        mock_get_manager.return_value = mock_manager

        # Call the function
        template = get_template(TemplateType.TV_SHOW, "test", fallback=True)

        # Assert
        assert template == "Default template"
        mock_manager.get_template.assert_called_once_with(TemplateType.TV_SHOW, "test", True)

    def test_get_available_templates(self, mock_get_manager):
        """Test getting available templates."""
        # Setup
        mock_manager = MagicMock()
        mock_manager.get_templates.return_value = {"test": "Test template"}
        mock_get_manager.return_value = mock_manager

        # Call the function
        templates = get_available_templates(TemplateType.TV_SHOW)

        # Assert
        assert templates == {"test": "Test template"}
        mock_manager.get_templates.assert_called_once_with(TemplateType.TV_SHOW)

    def test_save_template_to_file(self, mock_get_manager):
        """Test saving a template to a file."""
        # Setup
        mock_manager = MagicMock()
        mock_get_manager.return_value = mock_manager

        # Call the function
        save_template_to_file(TemplateType.TV_SHOW, "test")

        # Assert
        mock_manager.save_template_to_file.assert_called_once_with(TemplateType.TV_SHOW, "test")

    def test_load_templates(self, mock_get_manager):
        """Test loading templates."""
        # Setup
        mock_manager = MagicMock()
        mock_get_manager.return_value = mock_manager

        # Call the function
        load_templates()

        # Assert
        mock_manager.load_templates_from_directory.assert_called_once()
