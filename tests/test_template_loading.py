"""Tests for template loading functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


from plexomatic.utils.name_templates import TemplateManager, DEFAULT_TV_TEMPLATE
from plexomatic.utils.name_parser import MediaType, ParsedMediaName


class TestTemplateLoading:
    """Test class for template loading functionality."""

    def test_template_directory_creation(self) -> None:
        """Test that the template directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a non-existent path
            templates_dir = Path(temp_dir) / "templates"

            # Initialize template manager with this path
            _ = TemplateManager(templates_dir)

            # Check that the directory was created
            assert templates_dir.exists()
            assert templates_dir.is_dir()

    def test_template_loading(self) -> None:
        """Test loading templates from files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a templates directory
            templates_dir = Path(temp_dir) / "templates"
            os.makedirs(templates_dir, exist_ok=True)

            # Create a custom template file
            tv_template = "{title}/Custom/{title} - S{season:02d}E{episode:02d}"
            with open(templates_dir / "tv_show.template", "w") as f:
                f.write(tv_template)

            # Initialize template manager with this path
            manager = TemplateManager(templates_dir)

            # Verify that the custom template was loaded
            assert manager.get_template(MediaType.TV_SHOW) == tv_template

            # Verify that other templates use defaults
            assert manager.get_template(MediaType.MOVIE) != tv_template

    def test_template_fallbacks(self) -> None:
        """Test fallback behavior when templates are missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a templates directory
            templates_dir = Path(temp_dir) / "templates"
            os.makedirs(templates_dir, exist_ok=True)

            # Initialize template manager with this path (no template files)
            manager = TemplateManager(templates_dir)

            # Verify that default templates are used
            assert manager.get_template(MediaType.TV_SHOW) == DEFAULT_TV_TEMPLATE

    def test_template_format_application(self) -> None:
        """Test applying a loaded template to format a media name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a templates directory
            templates_dir = Path(temp_dir) / "templates"
            os.makedirs(templates_dir, exist_ok=True)

            # Create a custom template file
            tv_template = "Custom-{title}-S{season:02d}E{episode:02d}"
            with open(templates_dir / "tv_show.template", "w") as f:
                f.write(tv_template)

            # Initialize template manager with this path
            manager = TemplateManager(templates_dir)

            # Create a parsed media name
            parsed = ParsedMediaName(
                title="Test Show",
                season=1,
                episodes=[5],
                media_type=MediaType.TV_SHOW,
                extension=".mp4",
            )

            # Apply the template
            result = manager.format(parsed)

            # Verify the result
            assert result == "Custom-Test Show-S01E05"

    @patch("logging.Logger.warning")
    def test_missing_templates_directory_warning(self, mock_warning: MagicMock) -> None:
        """Test that a warning is logged when templates directory is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a non-existent path (but don't create it)
            templates_dir = Path(temp_dir) / "nonexistent"

            # Initialize template manager but prevent directory creation
            with patch("os.makedirs") as mock_makedirs:
                mock_makedirs.side_effect = OSError("Permission denied")
                _ = TemplateManager(templates_dir)

            # Verify that a warning was logged
            mock_warning.assert_called_once()
            assert "does not exist" in mock_warning.call_args[0][0]

    def test_template_error_handling(self) -> None:
        """Test error handling when template files are invalid."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a templates directory
            templates_dir = Path(temp_dir) / "templates"
            os.makedirs(templates_dir, exist_ok=True)

            # Create a template file with invalid format placeholders
            with open(templates_dir / "tv_show.template", "w") as f:
                f.write("{invalid_placeholder}")

            # Initialize template manager
            manager = TemplateManager(templates_dir)

            # Create a parsed media name
            parsed = ParsedMediaName(
                title="Test Show",
                season=1,
                episodes=[5],
                media_type=MediaType.TV_SHOW,
                extension=".mp4",
            )

            # Apply the template (should handle the error gracefully)
            result = manager.format(parsed)

            # Verify the result contains an error message
            assert "Error" in result
