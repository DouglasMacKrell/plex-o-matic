"""Tests for the name template system."""

# These imports will be implemented later
from plexomatic.utils.name_templates import (
    TemplateManager,
    TemplateType,
    apply_template,
    register_template,
    get_available_templates,
    _format_multi_episode,
    _ensure_episode_list,
    _default_formatter,
)
from plexomatic.utils.name_parser import ParsedMediaName, MediaType


class TestNameTemplates:
    """Test class for the name templates functionality."""

    def test_tv_show_template(self) -> None:
        """Test applying templates to TV show names."""
        # Create a parsed media name object for testing
        show = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Show Name",
            season=1,
            episodes=[2],
            episode_title="Episode Title",
            extension=".mp4",
            quality="720p",
        )

        # Test default template
        result = apply_template(show, "default")
        assert result == "Show.Name.S01E02.Episode.Title.mp4"

        # Test Plex template
        result = apply_template(show, "plex")
        assert result == "Show Name - S01E02 - Episode Title.mp4"

        # Test Kodi template
        result = apply_template(show, "kodi")
        assert result == "Show Name/Season 01/Show Name - S01E02 - Episode Title.mp4"

        # Test quality template
        result = apply_template(show, "quality")
        assert result == "Show.Name.S01E02.Episode.Title.720p.mp4"

    def test_movie_template(self) -> None:
        """Test applying templates to movie names."""
        # Create a parsed media name object for testing
        movie = ParsedMediaName(
            media_type=MediaType.MOVIE,
            title="Movie Name",
            year=2020,
            extension=".mp4",
            quality="1080p",
        )

        # Test default template
        result = apply_template(movie, "default")
        assert result == "Movie.Name.2020.mp4"

        # Test Plex template
        result = apply_template(movie, "plex")
        assert result == "Movie Name (2020).mp4"

        # Test Kodi template
        result = apply_template(movie, "kodi")
        assert result == "Movie Name (2020)/Movie Name (2020).mp4"

        # Test quality template
        result = apply_template(movie, "quality")
        assert result == "Movie.Name.2020.1080p.mp4"

    def test_anime_template(self) -> None:
        """Test applying templates to anime names."""
        # Create a parsed media name object for testing
        anime = ParsedMediaName(
            media_type=MediaType.ANIME,
            title="Anime Name",
            episodes=[1],
            group="Fansub",
            quality="720p",
            extension=".mkv",
        )

        # Test default template
        result = apply_template(anime, "default")
        assert result == "Anime.Name.E01.720p.mkv"

        # Test fansub template
        result = apply_template(anime, "fansub")
        assert result == "[Fansub] Anime Name - 01 [720p].mkv"

        # Test Plex template
        result = apply_template(anime, "plex")
        assert result == "Anime Name - S01E01.mkv"

    def test_custom_template_registration(self) -> None:
        """Test registering and using custom templates."""
        # Define a custom template format
        custom_format = "{title} - {year} - {quality}{extension}"

        # Register the template
        register_template("custom_movie", TemplateType.MOVIE, custom_format)

        # Create a parsed media name object for testing
        movie = ParsedMediaName(
            media_type=MediaType.MOVIE,
            title="Movie Name",
            year=2020,
            extension=".mp4",
            quality="1080p",
        )

        # Apply the custom template
        result = apply_template(movie, "custom_movie")
        assert result == "Movie Name - 2020 - 1080p.mp4"

        # Make sure the template is in the available templates
        templates = get_available_templates(TemplateType.MOVIE)
        assert "custom_movie" in templates

    def test_template_manager(self) -> None:
        """Test the TemplateManager class."""
        # Create a template manager
        manager = TemplateManager()

        # Add a custom template
        manager.add_template(
            "minimal_tv", TemplateType.TV_SHOW, "{title}.S{season:02d}E{episode:02d}{extension}"
        )

        # Create a parsed media name object for testing
        show = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Show Name",
            season=1,
            episodes=[2],
            episode_title="Episode Title",
            extension=".mp4",
        )

        # Apply the template using the manager
        result = manager.apply_template(show, "minimal_tv")
        assert result == "Show Name.S01E02.mp4"

        # Test with a multi-episode show
        show.episodes = [2, 3, 4]
        result = manager.apply_template(show, "minimal_tv")
        assert result == "Show Name.S01E02-E04.mp4"

        # Get list of available templates
        tv_templates = manager.get_templates(TemplateType.TV_SHOW)
        assert "minimal_tv" in tv_templates
        assert "plex" in tv_templates  # Should include default templates too

    def test_multi_episode_formatting(self) -> None:
        """Test different multi-episode formatting options."""
        # Test sequential episodes with range format
        assert _format_multi_episode([1, 2, 3], "range") == "E01-E03"

        # Test non-sequential episodes with range format
        assert _format_multi_episode([1, 3, 5], "range") == "E01E03E05"

        # Test plus format
        assert _format_multi_episode([1, 2, 3], "plus") == "E01+E02+E03"

        # Test list format
        assert _format_multi_episode([1, 2, 3], "list") == "E01E02E03"

        # Test single episode
        assert _format_multi_episode([1]) == "E01"

        # Test empty list
        assert _format_multi_episode([]) == "E00"

    def test_ensure_episode_list(self) -> None:
        """Test episode list conversion function."""
        # Test None input
        assert _ensure_episode_list(None) == []

        # Test integer input
        assert _ensure_episode_list(1) == [1]

        # Test list input
        assert _ensure_episode_list([1, 2, 3]) == [1, 2, 3]

    def test_template_error_handling(self) -> None:
        """Test error handling in template application."""
        # Test with missing required template values
        show = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Show Name",
            extension=".mp4",
        )

        # Should handle missing season/episode gracefully
        result = apply_template(show, "default")
        assert result == "Show.Name.S01E00.mp4"

        # Test with invalid template name
        try:
            apply_template(show, "nonexistent_template")
            assert False, "Should raise ValueError"
        except ValueError:
            pass

    def test_anime_special_handling(self) -> None:
        """Test handling of anime specials."""
        # Create an anime special
        special = ParsedMediaName(
            media_type=MediaType.ANIME_SPECIAL,
            title="Anime Name",
            special_type="OVA",
            special_number=2,
            group="Fansub",
            quality="1080p",
            extension=".mkv",
        )

        # Test with fansub template
        result = apply_template(special, "fansub")
        assert "[Fansub] Anime Name" in result
        assert "1080p" in result

        # Test with no special number
        special.special_number = None
        result = apply_template(special, "default")
        assert "Anime.Name" in result

        # Test with no group
        special.group = None
        result = apply_template(special, "fansub")
        assert "Anime Name" in result

    def test_template_manager_fallbacks(self) -> None:
        """Test template manager fallback behavior."""
        manager = TemplateManager()

        # Test fallback to default template
        show = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Show Name",
            season=1,
            episodes=[2],
            extension=".mp4",
        )

        result = manager.apply_template(show, "nonexistent_template")
        assert result == "Show.Name.S01E02.mp4"  # Should use default template

        # Test with unknown media type
        unknown = ParsedMediaName(
            media_type=MediaType.UNKNOWN,
            title="Unknown Media",
            extension=".mp4",
        )

        result = manager.apply_template(unknown)
        assert result == "Unknown Media.mp4"  # Should use simple fallback

    def test_default_formatter_edge_cases(self) -> None:
        """Test edge cases in the default formatter."""
        # Test with missing required values
        show = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            extension=".mp4",
        )

        # Test with a template that uses unavailable keys
        result = _default_formatter(show, "{title}{nonexistent}{extension}")
        assert result == "Test.Show.S01E00.mp4"  # Should fall back to simple format

        # Test with index error in template
        result = _default_formatter(show, "{title}{episodes[5]}{extension}")
        assert result == "Test.Show.S01E00.mp4"  # Should fall back to simple format

        # Test with movie missing year
        movie = ParsedMediaName(
            media_type=MediaType.MOVIE,
            title="Test Movie",
            extension=".mp4",
        )
        result = _default_formatter(movie, "{title}.{year}{extension}")
        assert result == "Test.Movie.mp4"  # Should handle missing year gracefully

    def test_template_registration_edge_cases(self) -> None:
        """Test edge cases in template registration."""
        # Test registering template with same name but different type
        register_template("test_template", TemplateType.TV_SHOW, "{title}{extension}")
        register_template("test_template", TemplateType.MOVIE, "{title}{extension}")

        # Both templates should be accessible via their combined keys
        tv_templates = get_available_templates(TemplateType.TV_SHOW)
        movie_templates = get_available_templates(TemplateType.MOVIE)
        assert "test_template" in tv_templates
        assert "test_template" in movie_templates

        # Test registering template with empty format string
        register_template("empty_template", TemplateType.UNKNOWN, "")

    def test_template_manager_initialization(self) -> None:
        """Test template manager initialization and customization."""
        # Create a new manager
        manager = TemplateManager()

        # Verify default templates are loaded
        assert manager.get_templates(TemplateType.TV_SHOW)
        assert manager.get_templates(TemplateType.MOVIE)
        assert manager.get_templates(TemplateType.ANIME)

        # Test adding a custom template with spaces
        manager.add_template(
            "custom_spaces",
            TemplateType.TV_SHOW,
            "{title_spaces} - {episode_title_spaces}{extension}",
        )

        show = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            episode_title="Test Episode",
            extension=".mp4",
        )

        result = manager.apply_template(show, "custom_spaces")
        assert result == "Test Show - Test Episode.mp4"

        # Test template type inference
        result = manager.apply_template(show)  # Should use default TV show template
        assert "Test.Show" in result
