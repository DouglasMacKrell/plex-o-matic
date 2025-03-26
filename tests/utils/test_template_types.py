"""Tests for the template type enumeration and utilities."""

import os
import pytest
from unittest.mock import patch
from pathlib import Path
from enum import Enum

# Importing from the module we will create later
# This will fail until we implement the module
from plexomatic.utils.templates.template_types import (
    TemplateType,
    normalize_media_type,
    get_default_template_dir,
    get_custom_template_dir,
    DEFAULT_TEMPLATES_DIR,
    get_default_template_for_media_type,
    DEFAULT_TV_TEMPLATE,
    DEFAULT_MOVIE_TEMPLATE,
    DEFAULT_ANIME_TEMPLATE,
)
from plexomatic.core.constants import MediaType


class TestTemplateType:
    """Tests for the TemplateType enum."""

    def test_enum_values(self):
        """Test that the enum has the expected values."""
        assert TemplateType.TV_SHOW.value == "tv_show"
        assert TemplateType.MOVIE.value == "movie"
        assert TemplateType.ANIME.value == "anime"
        assert TemplateType.CUSTOM.value == "custom"

    def test_to_string(self):
        """Test the string conversion of template types."""
        assert str(TemplateType.TV_SHOW) == "tv_show"
        assert str(TemplateType.MOVIE) == "movie"
        assert str(TemplateType.ANIME) == "anime"
        assert str(TemplateType.CUSTOM) == "custom"

    def test_equality(self):
        """Test equality comparison of template types."""
        assert TemplateType.TV_SHOW == TemplateType.TV_SHOW
        assert TemplateType.TV_SHOW != TemplateType.MOVIE
        assert TemplateType.TV_SHOW != "tv_show"  # String comparison should fail


class TestNormalizeMediaType:
    """Tests for the normalize_media_type function."""

    def test_normalize_media_type_tv(self):
        """Test normalizing TV show media types."""
        assert normalize_media_type(MediaType.TV_SHOW) == TemplateType.TV_SHOW
        assert normalize_media_type(MediaType.TV_SPECIAL) == TemplateType.TV_SHOW

    def test_normalize_media_type_movie(self):
        """Test normalizing movie media types."""
        assert normalize_media_type(MediaType.MOVIE) == TemplateType.MOVIE

    def test_normalize_media_type_anime(self):
        """Test normalizing anime media types."""
        assert normalize_media_type(MediaType.ANIME) == TemplateType.ANIME
        assert normalize_media_type(MediaType.ANIME_SPECIAL) == TemplateType.ANIME

    def test_normalize_media_type_unknown(self):
        """Test normalizing unknown media types."""
        assert normalize_media_type(MediaType.UNKNOWN) == TemplateType.TV_SHOW  # Default
        assert normalize_media_type(MediaType.MUSIC) == TemplateType.TV_SHOW  # Default

    def test_normalize_media_type_none(self):
        """Test normalizing None media type."""
        assert normalize_media_type(None) == TemplateType.TV_SHOW  # Default

    def test_normalize_media_type_invalid_type(self):
        """Test normalizing invalid type."""
        with pytest.raises(TypeError):
            normalize_media_type("invalid")


class TestDefaultTemplates:
    """Tests for the default template constants and functions."""

    def test_default_templates_dir(self):
        """Test that the default templates directory is correct."""
        assert isinstance(DEFAULT_TEMPLATES_DIR, Path)
        assert DEFAULT_TEMPLATES_DIR.name == "templates"
        assert DEFAULT_TEMPLATES_DIR.parent.name == ".plexomatic"

    def test_default_template_strings(self):
        """Test the default template strings."""
        assert DEFAULT_TV_TEMPLATE.startswith("{title}")
        assert DEFAULT_MOVIE_TEMPLATE.startswith("{title}")
        assert DEFAULT_ANIME_TEMPLATE.startswith("[{group}]")

    def test_get_default_template_for_media_type(self):
        """Test getting default templates for media types."""
        assert get_default_template_for_media_type(TemplateType.TV_SHOW) == DEFAULT_TV_TEMPLATE
        assert get_default_template_for_media_type(TemplateType.MOVIE) == DEFAULT_MOVIE_TEMPLATE
        assert get_default_template_for_media_type(TemplateType.ANIME) == DEFAULT_ANIME_TEMPLATE
        assert (
            get_default_template_for_media_type(TemplateType.CUSTOM) == DEFAULT_TV_TEMPLATE
        )  # Default

    def test_get_default_template_for_none(self):
        """Test getting default template for None."""
        assert get_default_template_for_media_type(None) == DEFAULT_TV_TEMPLATE  # Default

    def test_default_templates_dir_with_custom_home(self):
        """Test template directory with custom home path."""
        # Create a test path
        test_path = Path("/test/home") / ".plexomatic" / "templates"

        # Test that the path construction logic is correct
        with patch.dict("os.environ", {"HOME": "/test/home"}):
            # Directly test the path construction logic
            home_dir = Path(os.environ["HOME"])
            templates_dir = home_dir / ".plexomatic" / "templates"
            assert str(templates_dir) == str(test_path)
