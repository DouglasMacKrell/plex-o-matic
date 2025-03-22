"""Tests for the template_formatters module."""

import pytest
from unittest.mock import patch

from plexomatic.core.constants import MediaType
from plexomatic.utils.name_parser import ParsedMediaName
from plexomatic.utils.template_types import TemplateType


class TestTemplateFormatters:
    """Tests for the template formatters module."""

    def test_format_template_basic(self):
        """Test basic template formatting with a simple template."""
        # Import here to avoid circular imports during testing
        from plexomatic.utils.template_formatters import format_template

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            season=1,
            episodes=[2],
            extension=".mp4",
        )

        template = "{title}.S{season:02d}E{episode:02d}{extension}"
        result = format_template(template, parsed)

        assert result == "Test.Show.S01E02.mp4"

    def test_format_template_with_dots(self):
        """Test template formatting with dots in the title."""
        from plexomatic.utils.template_formatters import format_template

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test.Show",
            season=1,
            episodes=[2],
            extension=".mp4",
        )

        template = "{title}.S{season:02d}E{episode:02d}{extension}"
        result = format_template(template, parsed)

        assert result == "Test.Show.S01E02.mp4"

    def test_format_template_with_episode_title(self):
        """Test template formatting with an episode title."""
        from plexomatic.utils.template_formatters import format_template

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            season=1,
            episodes=[2],
            episode_title="Test Episode",
            extension=".mp4",
        )

        template = "{title}.S{season:02d}E{episode:02d}.{episode_title}{extension}"
        result = format_template(template, parsed)

        assert result == "Test.Show.S01E02.Test.Episode.mp4"

    def test_format_template_movie(self):
        """Test template formatting for a movie."""
        from plexomatic.utils.template_formatters import format_template

        parsed = ParsedMediaName(
            media_type=MediaType.MOVIE, title="Test Movie", year=2020, extension=".mp4"
        )

        template = "{title}.{year}{extension}"
        result = format_template(template, parsed)

        assert result == "Test.Movie.2020.mp4"

    def test_format_template_anime(self):
        """Test template formatting for anime."""
        from plexomatic.utils.template_formatters import format_template

        parsed = ParsedMediaName(
            media_type=MediaType.ANIME,
            title="Test Anime",
            episodes=[1],
            group="TestGroup",
            quality="720p",
            extension=".mkv",
        )

        template = "[{group}] {title} - {episode:02d} [{quality}]{extension}"
        result = format_template(template, parsed)

        assert result == "[TestGroup] Test Anime - 01 [720p].mkv"

    def test_format_template_custom_spaces(self):
        """Test template formatting with custom spacing."""
        from plexomatic.utils.template_formatters import format_template

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            season=1,
            episodes=[2],
            episode_title="Test Episode",
            extension=".mp4",
        )

        template = "{title} - S{season:02d}E{episode:02d} - {episode_title}{extension}"
        result = format_template(template, parsed)

        assert result == "Test Show - S01E02 - Test Episode.mp4"

    def test_format_template_missing_field(self):
        """Test template formatting with a missing field."""
        from plexomatic.utils.template_formatters import format_template

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            season=1,
            episodes=[2],
            # Missing episode_title
            extension=".mp4",
        )

        template = "{title}.S{season:02d}E{episode:02d}.{episode_title}{extension}"

        # The formatter should handle missing fields by replacing with empty string
        result = format_template(template, parsed)
        assert result == "Test.Show.S01E02..mp4"

    def test_format_template_with_multi_episode(self):
        """Test template formatting with multiple episodes."""
        from plexomatic.utils.template_formatters import format_template

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            season=1,
            episodes=[2, 3, 4],
            extension=".mp4",
        )

        template = "{title}.S{season:02d}E{episode:02d}{extension}"
        result = format_template(template, parsed)

        assert result == "Test.Show.S01E02-E04.mp4"

    def test_apply_template_tv_basic(self):
        """Test applying a template to a TV show."""
        from plexomatic.utils.template_formatters import apply_template

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            season=1,
            episodes=[2],
            extension=".mp4",
        )

        result = apply_template(parsed, "default")
        assert result == "Test.Show.S01E02.mp4"

    def test_apply_template_movie_basic(self):
        """Test applying a template to a movie."""
        from plexomatic.utils.template_formatters import apply_template

        parsed = ParsedMediaName(
            media_type=MediaType.MOVIE, title="Test Movie", year=2020, extension=".mp4"
        )

        result = apply_template(parsed, "default")
        assert result == "Test.Movie.2020.mp4"

    def test_apply_template_anime_basic(self):
        """Test applying a template to an anime."""
        from plexomatic.utils.template_formatters import apply_template

        parsed = ParsedMediaName(
            media_type=MediaType.ANIME,
            title="Test Anime",
            episodes=[1],
            group="TestGroup",
            quality="720p",
            extension=".mkv",
        )

        result = apply_template(parsed, "default")
        assert result == "[TestGroup] Test Anime - 01 [720p].mkv"

    def test_apply_template_nonexistent(self):
        """Test applying a nonexistent template raises an error."""
        from plexomatic.utils.template_formatters import apply_template

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            season=1,
            episodes=[2],
            extension=".mp4",
        )

        with pytest.raises(ValueError):
            apply_template(parsed, "nonexistent_template")

    @patch("plexomatic.utils.template_formatters.get_template")
    def test_apply_template_uses_registry(self, mock_get_template):
        """Test that apply_template uses the template registry."""
        from plexomatic.utils.template_formatters import apply_template

        # Setup mock
        mock_get_template.return_value = "{title}.custom{extension}"

        parsed = ParsedMediaName(media_type=MediaType.TV_SHOW, title="Test Show", extension=".mp4")

        result = apply_template(parsed, "custom")

        # Verify correct template type was requested
        mock_get_template.assert_called_once_with(TemplateType.TV_SHOW, "custom", True)

        # Verify the result used our mocked template
        assert result == "Test.Show.custom.mp4"
