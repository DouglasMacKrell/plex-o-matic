"""Tests for the template_formatter module."""

from unittest.mock import patch
import pytest

from plexomatic.core.constants import MediaType
from plexomatic.utils.name_parser import ParsedMediaName


class TestTemplateFormatters:
    """Test cases for the template formatters."""

    def test_format_template_basic(self):
        """Test formatting a template with basic substitution."""
        from plexomatic.utils.template_formatter import format_template

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            season=1,
            episodes=[1],
            extension=".mp4",
        )

        result = format_template("{title}.S{season:02d}E{episode:02d}{extension}", parsed)

        assert result == "Test.Show.S01E01.mp4"

    def test_format_template_with_dots(self):
        """Test formatting a template with dots in the template."""
        from plexomatic.utils.template_formatter import format_template

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            season=1,
            episodes=[1],
            extension=".mp4",
        )

        result = format_template("{title}.S{season:02d}.E{episode:02d}{extension}", parsed)

        assert result == "Test.Show.S01.E01.mp4"

    def test_format_template_with_episode_title(self):
        """Test formatting a template with an episode title."""
        from plexomatic.utils.template_formatter import format_template

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            season=1,
            episodes=[1],
            episode_title="Test Episode",
            extension=".mp4",
        )

        result = format_template(
            "{title}.S{season:02d}E{episode:02d}.{episode_title}{extension}", parsed
        )

        assert result == "Test.Show.S01E01.Test.Episode.mp4"

    def test_format_template_movie(self):
        """Test formatting a template for a movie."""
        from plexomatic.utils.template_formatter import format_template

        parsed = ParsedMediaName(
            media_type=MediaType.MOVIE, title="Test Movie", year=2020, extension=".mp4"
        )

        result = format_template("{title}.{year}{extension}", parsed)

        assert result == "Test.Movie.2020.mp4"

    def test_format_template_anime(self):
        """Test formatting a template for an anime."""
        from plexomatic.utils.template_formatter import format_template

        parsed = ParsedMediaName(
            media_type=MediaType.ANIME,
            title="Test Anime",
            episodes=[1],
            group="TestGroup",
            quality="720p",
            extension=".mkv",
        )

        result = format_template("[{group}] {title} - {episode:02d} [{quality}]{extension}", parsed)

        assert result == "[TestGroup] Test Anime - 01 [720p].mkv"

    def test_format_template_custom_spaces(self):
        """Test formatting a template with custom spacing."""
        from plexomatic.utils.template_formatter import format_template

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            season=1,
            episodes=[2],
            episode_title="Test Episode",
            extension=".mp4",
        )

        result = format_template(
            "{title} - S{season:02d}E{episode:02d} - {episode_title}{extension}", parsed
        )

        assert result == "Test Show - S01E02 - Test Episode.mp4"

    def test_format_template_missing_field(self):
        """Test formatting a template with a missing field."""
        from plexomatic.utils.template_formatter import format_template

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            season=1,
            episodes=[1],
            extension=".mp4",
        )

        # Missing 'episode_title'
        result = format_template(
            "{title}.S{season:02d}E{episode:02d}.{episode_title}{extension}", parsed
        )

        assert result == "Test.Show.S01E01..mp4"

    def test_format_template_with_multi_episode(self):
        """Test formatting a template with multiple episodes."""
        from plexomatic.utils.template_formatter import format_template

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            season=1,
            episodes=[2, 3, 4],
            extension=".mp4",
        )

        result = format_template("{title}.S{season:02d}E{episode:02d}{extension}", parsed)

        assert result == "Test.Show.S01E02-E04.mp4"

    @patch("plexomatic.utils.template_formatter.get_template")
    def test_apply_template_tv_basic(self, mock_get_template):
        """Test applying a template to a TV show."""
        mock_get_template.return_value = "{title}.S{season:02d}E{episode:02d}{extension}"

        from plexomatic.utils.template_formatter import apply_template

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            season=1,
            episodes=[2],
            extension=".mp4",
        )

        result = apply_template(parsed, "default")

        assert result == "Test.Show.S01E02.mp4"
        # Verify the mock was called
        mock_get_template.assert_called_once()

    @patch("plexomatic.utils.template_formatter.get_template")
    def test_apply_template_movie_basic(self, mock_get_template):
        """Test applying a template to a movie."""
        mock_get_template.return_value = "{title}.{year}{extension}"

        from plexomatic.utils.template_formatter import apply_template

        parsed = ParsedMediaName(
            media_type=MediaType.MOVIE, title="Test Movie", year=2020, extension=".mp4"
        )

        result = apply_template(parsed, "default")

        assert result == "Test.Movie.2020.mp4"
        # Verify the mock was called
        mock_get_template.assert_called_once()

    @patch("plexomatic.utils.template_formatter.get_template")
    def test_apply_template_anime_basic(self, mock_get_template):
        """Test applying a template to an anime."""
        mock_get_template.return_value = "[{group}] {title} - {episode:02d} [{quality}]{extension}"

        from plexomatic.utils.template_formatter import apply_template

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
        # Verify the mock was called
        mock_get_template.assert_called_once()

    @patch("plexomatic.utils.template_formatter.get_template")
    def test_apply_template_nonexistent(self, mock_get_template):
        """Test applying a nonexistent template."""
        from plexomatic.utils.template_formatter import apply_template

        mock_get_template.side_effect = ValueError("Template not found")

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            season=1,
            episodes=[1],
            extension=".mp4",
        )

        with pytest.raises(ValueError):
            apply_template(parsed, "nonexistent_template")

    @patch("plexomatic.utils.template_formatter.get_template")
    def test_apply_template_uses_registry(self, mock_get_template):
        """Test that apply_template uses the template registry."""
        mock_get_template.return_value = "{title}.custom{extension}"

        from plexomatic.utils.template_formatter import apply_template

        parsed = ParsedMediaName(media_type=MediaType.TV_SHOW, title="Test Show", extension=".mp4")

        result = apply_template(parsed, "custom")

        assert result == "Test.Show.custom.mp4"
        # Verify the mock was called with the right template name
        mock_get_template.assert_called_once_with("custom")

    @patch("plexomatic.utils.template_formatter.get_template")
    def test_apply_template(self, mock_get_template):
        """Test applying a template to a parsed media name."""
        from plexomatic.utils.template_formatter import apply_template

        mock_get_template.return_value = "{title}.S{season:02d}E{episode:02d}{extension}"

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            season=1,
            episodes=[1],
            extension=".mp4",
        )

        result = apply_template(parsed, "test_template")

        assert result == "Test.Show.S01E01.mp4"
        mock_get_template.assert_called_once_with("test_template")
