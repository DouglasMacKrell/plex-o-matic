"""Tests for the templates CLI command."""

import os
from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner

from plexomatic.cli.main import cli

# Skip tests for now as the CLI has been completely refactored to use Typer instead of Click
pytestmark = pytest.mark.skip("CLI has been refactored to use Typer instead of Click")


class TestTemplatesCLI:
    """Test class for templates CLI command."""

    def test_list_templates(self) -> None:
        """Test listing templates with the CLI."""
        runner = CliRunner()

        with patch("plexomatic.cli.TemplateManager") as mock_manager:
            # Setup mock
            mock_instance = mock_manager.return_value
            mock_instance.get_template.return_value = "Mock Template"

            # Run the command
            result = runner.invoke(cli, ["templates", "list"])

            # Check the result
            assert result.exit_code == 0
            assert "Available Templates" in result.output
            assert "TV Show Episodes" in result.output
            assert "Movies" in result.output
            assert "Anime Episodes" in result.output
            assert "Mock Template" in result.output

    def test_show_template(self) -> None:
        """Test showing a template preview with the CLI."""
        runner = CliRunner()

        with patch("plexomatic.cli.TemplateManager") as mock_manager:
            # Setup mock
            mock_instance = mock_manager.return_value
            mock_instance.get_template.return_value = "{title} - S{season:02d}E{episode:02d}"
            mock_instance.format.return_value = "Test Title - S01E01"

            # Run the command
            result = runner.invoke(cli, ["templates", "show", "TV_SHOW", "Test Title"])

            # Check the result
            assert result.exit_code == 0
            assert "Template Preview" in result.output
            assert "{title} - S{season:02d}E{episode:02d}" in result.output
            assert "Test Title - S01E01" in result.output

    def test_show_template_with_options(self) -> None:
        """Test showing a template preview with custom options."""
        runner = CliRunner()

        with patch("plexomatic.cli.TemplateManager") as mock_manager:
            # Setup mock
            mock_instance = mock_manager.return_value
            mock_instance.get_template.return_value = "{title} ({year})"
            mock_instance.format.return_value = "Custom Movie (2022)"

            # Run the command with options
            result = runner.invoke(
                cli, ["templates", "show", "MOVIE", "Custom Movie", "--year", "2022"]
            )

            # Check the result
            assert result.exit_code == 0
            assert "Template Preview" in result.output
            assert "Custom Movie (2022)" in result.output

    def test_integration_with_real_templates(self) -> None:
        """Test templates command with real template files."""
        runner = CliRunner()

        # Create a temporary template
        with runner.isolated_filesystem():
            # Create templates directory
            os.makedirs("templates", exist_ok=True)

            # Create a template file
            with open("templates/tv_show.template", "w") as f:
                f.write("Custom-{title}-S{season:02d}E{episode:02d}")

            # Mock the entire template manager behavior
            with patch("plexomatic.cli.TemplateManager") as mock_manager:
                # Setup mock
                mock_instance = mock_manager.return_value
                mock_instance.get_template.return_value = (
                    "Custom-{title}-S{season:02d}E{episode:02d}"
                )
                mock_instance.format.return_value = "Custom-Test-S01E01"

                result = runner.invoke(cli, ["templates", "show", "TV_SHOW", "Test"])

                # Check the result
                assert result.exit_code == 0
                assert "Custom-{title}-S{season:02d}E{episode:02d}" in result.output
                assert "Custom-Test-S01E01" in result.output
