"""Tests for the default media formatters."""

from plexomatic.utils.name_parser import ParsedMediaName
from plexomatic.core.constants import MediaType
from plexomatic.utils.templates.template_types import TemplateType
from plexomatic.utils.default_formatters import (
    format_tv_show,
    format_movie,
    format_anime,
    get_default_formatter,
    DEFAULT_FORMATTERS,
)


class TestDefaultFormatters:
    """Tests for the default_formatters module."""

    def test_format_tv_show_basic(self):
        """Test formatting a basic TV show."""
        parsed = ParsedMediaName(
            title="Test Show",
            season=1,
            episodes=[2],
            extension=".mp4",
            media_type=MediaType.TV_SHOW,
        )
        result = format_tv_show(parsed)
        assert result == "Test.Show.S01E02.mp4"

    def test_format_tv_show_with_episode_title(self):
        """Test formatting a TV show with episode title."""
        parsed = ParsedMediaName(
            title="Test Show",
            season=1,
            episodes=[2],
            episode_title="Episode Title",
            extension=".mp4",
            media_type=MediaType.TV_SHOW,
        )
        result = format_tv_show(parsed)
        assert result == "Test.Show.S01E02.Episode.Title.mp4"

    def test_format_tv_show_with_quality(self):
        """Test formatting a TV show with quality."""
        parsed = ParsedMediaName(
            title="Test Show",
            season=1,
            episodes=[2],
            quality="720p",
            extension=".mp4",
            media_type=MediaType.TV_SHOW,
        )
        result = format_tv_show(parsed)
        assert result == "Test.Show.S01E02.720p.mp4"

    def test_format_tv_show_multi_episode(self):
        """Test formatting a TV show with multiple episodes."""
        parsed = ParsedMediaName(
            title="Test Show",
            season=1,
            episodes=[2, 3, 4],
            extension=".mp4",
            media_type=MediaType.TV_SHOW,
        )
        result = format_tv_show(parsed)
        assert result == "Test.Show.S01E02-E04.mp4"

    def test_format_movie_basic(self):
        """Test formatting a basic movie."""
        parsed = ParsedMediaName(
            title="Test Movie", year=2020, extension=".mp4", media_type=MediaType.MOVIE
        )
        result = format_movie(parsed)
        assert result == "Test.Movie.2020.mp4"

    def test_format_movie_with_quality(self):
        """Test formatting a movie with quality."""
        parsed = ParsedMediaName(
            title="Test Movie",
            year=2020,
            quality="1080p",
            extension=".mp4",
            media_type=MediaType.MOVIE,
        )
        result = format_movie(parsed)
        assert result == "Test.Movie.2020.1080p.mp4"

    def test_format_movie_without_year(self):
        """Test formatting a movie without a year."""
        parsed = ParsedMediaName(title="Test Movie", extension=".mp4", media_type=MediaType.MOVIE)
        result = format_movie(parsed)
        assert result == "Test.Movie.mp4"

    def test_format_anime_with_group(self):
        """Test formatting anime with a release group."""
        parsed = ParsedMediaName(
            title="Test Anime",
            episodes=[1],
            group="Group",
            quality="720p",
            extension=".mkv",
            media_type=MediaType.ANIME,
        )
        result = format_anime(parsed)
        assert result == "[Group] Test Anime - 01 [720p].mkv"

    def test_format_anime_without_group(self):
        """Test formatting anime without a release group."""
        parsed = ParsedMediaName(
            title="Test Anime",
            episodes=[1],
            quality="720p",
            extension=".mkv",
            media_type=MediaType.ANIME,
        )
        result = format_anime(parsed)
        assert result == "Test.Anime.E01.720p.mkv"

    def test_format_anime_multi_episode(self):
        """Test formatting anime with multiple episodes."""
        parsed = ParsedMediaName(
            title="Test Anime",
            episodes=[1, 2, 3],
            group="Group",
            extension=".mkv",
            media_type=MediaType.ANIME,
        )
        result = format_anime(parsed)
        assert result == "[Group] Test Anime - 01-03.mkv"

    def test_format_anime_special(self):
        """Test formatting an anime special."""
        parsed = ParsedMediaName(
            title="Test Anime",
            media_type=MediaType.ANIME_SPECIAL,
            special_type="OVA",
            special_number=1,
            extension=".mkv",
        )
        result = format_anime(parsed)
        assert result == "Test.Anime.EOVA1.mkv"

    def test_get_default_formatter_tv(self):
        """Test getting the default formatter for TV shows."""
        formatter = get_default_formatter(TemplateType.TV_SHOW)
        assert formatter == format_tv_show
        assert formatter is DEFAULT_FORMATTERS[TemplateType.TV_SHOW]

    def test_get_default_formatter_movie(self):
        """Test getting the default formatter for movies."""
        formatter = get_default_formatter(TemplateType.MOVIE)
        assert formatter == format_movie
        assert formatter is DEFAULT_FORMATTERS[TemplateType.MOVIE]

    def test_get_default_formatter_anime(self):
        """Test getting the default formatter for anime."""
        formatter = get_default_formatter(TemplateType.ANIME)
        assert formatter == format_anime
        assert formatter is DEFAULT_FORMATTERS[TemplateType.ANIME]

    def test_get_default_formatter_custom(self):
        """Test getting the default formatter for custom types."""
        formatter = get_default_formatter(TemplateType.CUSTOM)
        assert formatter == format_tv_show  # TV show is the default for custom types

    def test_get_default_formatter_none(self):
        """Test getting the default formatter for None type."""
        formatter = get_default_formatter(None)
        assert formatter == format_tv_show  # TV show is the default when None
