"""Tests for the name template system."""

import pytest
from pathlib import Path
from typing import Dict, List, Optional

# These imports will be implemented later
from plexomatic.utils.name_templates import (
    NameTemplate,
    TemplateManager,
    TemplateType,
    apply_template,
    register_template,
    get_available_templates,
)
from plexomatic.utils.name_parser import ParsedMediaName, MediaType


class TestNameTemplates:
    """Test class for the name templates functionality."""

    def test_tv_show_template(self):
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

    def test_movie_template(self):
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

    def test_anime_template(self):
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

    def test_custom_template_registration(self):
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

    def test_template_manager(self):
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
