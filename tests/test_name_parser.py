"""Tests for the advanced name parser functionality."""

import pytest
from pathlib import Path
from typing import Dict, List, Optional

# These imports will be implemented later
from plexomatic.utils.name_parser import (
    NameParser,
    ParsedMediaName,
    parse_media_name,
    detect_media_type,
    MediaType,
)


class TestNameParser:
    """Test class for the NameParser functionality."""

    def test_media_type_detection(self):
        """Test that media types are correctly detected."""
        # TV shows
        assert detect_media_type("Show.Name.S01E02.mp4") == MediaType.TV_SHOW
        assert detect_media_type("Show Name - S01E02 - Episode Name.mp4") == MediaType.TV_SHOW
        assert detect_media_type("Show.Name.1x02.mp4") == MediaType.TV_SHOW
        assert detect_media_type("Show Name - Season 1 Episode 2.mp4") == MediaType.TV_SHOW
        assert detect_media_type("Show_Name_S01E02E03.mp4") == MediaType.TV_SHOW  # Multi-episode
        assert detect_media_type("Show.Name.S01.E02.720p.mp4") == MediaType.TV_SHOW  # Separated
        assert (
            detect_media_type("Show Name - S01.5xSpecial - Special Name.mp4")
            == MediaType.TV_SPECIAL
        )

        # Movies
        assert detect_media_type("Movie.Name.2020.mp4") == MediaType.MOVIE
        assert detect_media_type("Movie Name (2020).mp4") == MediaType.MOVIE
        assert detect_media_type("Movie Name [2020] 1080p.mp4") == MediaType.MOVIE
        assert detect_media_type("Movie Name 2020 720p BluRay.mp4") == MediaType.MOVIE

        # Anime
        assert detect_media_type("[Group] Anime Name - 01 [720p].mkv") == MediaType.ANIME
        assert detect_media_type("[Group] Anime Name - 01v2 [720p].mkv") == MediaType.ANIME
        assert detect_media_type("[Group] Anime Name - OVA1 [1080p].mkv") == MediaType.ANIME_SPECIAL

        # Uncertain or unknown
        assert detect_media_type("random_file.mp4") == MediaType.UNKNOWN

    def test_parse_tv_show(self):
        """Test parsing TV show filenames."""
        # Standard format
        result = parse_media_name("Show.Name.S01E02.Episode.Title.mp4")
        assert result.media_type == MediaType.TV_SHOW
        assert result.title == "Show Name"
        assert result.season == 1
        assert result.episodes == [2]
        assert result.episode_title == "Episode Title"
        assert result.extension == ".mp4"
        assert result.quality is None

        # Alternative format with quality
        result = parse_media_name("Show Name - S01E02 - Episode Name - 720p HDTV.mp4")
        assert result.media_type == MediaType.TV_SHOW
        assert result.title == "Show Name"
        assert result.season == 1
        assert result.episodes == [2]
        assert result.episode_title == "Episode Name"
        assert result.quality == "720p HDTV"

        # Format with year in show name
        result = parse_media_name("Show Name (2018) - S01E02.mp4")
        assert result.media_type == MediaType.TV_SHOW
        assert result.title == "Show Name (2018)"
        assert result.season == 1
        assert result.episodes == [2]

        # Multi-episode
        result = parse_media_name("Show.Name.S01E02E03.mp4")
        assert result.media_type == MediaType.TV_SHOW
        assert result.episodes == [2, 3]

        # Alternative multi-episode format
        result = parse_media_name("Show.Name.S01E02-E03.mp4")
        assert result.media_type == MediaType.TV_SHOW
        assert result.episodes == [2, 3]

    def test_parse_movie(self):
        """Test parsing movie filenames."""
        # Standard format
        result = parse_media_name("Movie.Name.2020.720p.mp4")
        assert result.media_type == MediaType.MOVIE
        assert result.title == "Movie Name"
        assert result.year == 2020
        assert result.quality == "720p"
        assert result.extension == ".mp4"

        # Format with parenthesis
        result = parse_media_name("Movie Name (2020) 1080p BluRay.mkv")
        assert result.media_type == MediaType.MOVIE
        assert result.title == "Movie Name"
        assert result.year == 2020
        assert result.quality == "1080p BluRay"
        assert result.extension == ".mkv"

        # Format with brackets
        result = parse_media_name("Movie Name [2020] [1080p].mp4")
        assert result.media_type == MediaType.MOVIE
        assert result.title == "Movie Name"
        assert result.year == 2020
        assert result.quality == "1080p"

    def test_parse_anime(self):
        """Test parsing anime filenames."""
        # Standard fansub format
        result = parse_media_name("[Group] Anime Name - 01 [720p].mkv")
        assert result.media_type == MediaType.ANIME
        assert result.title == "Anime Name"
        assert result.group == "Group"
        assert result.episodes == [1]
        assert result.quality == "720p"
        assert result.extension == ".mkv"

        # Version notation
        result = parse_media_name("[Group] Anime Name - 01v2 [1080p].mkv")
        assert result.media_type == MediaType.ANIME
        assert result.title == "Anime Name"
        assert result.episodes == [1]
        assert result.version == 2

        # Special episode
        result = parse_media_name("[Group] Anime Name - OVA1 [1080p].mkv")
        assert result.media_type == MediaType.ANIME_SPECIAL
        assert result.title == "Anime Name"
        assert result.special_type == "OVA"
        assert result.special_number == 1

    def test_name_parser_class(self):
        """Test the NameParser class."""
        parser = NameParser()

        # Test with TV show
        result = parser.parse("Show.Name.S01E02.mp4")
        assert result.media_type == MediaType.TV_SHOW
        assert result.title == "Show Name"

        # Test with movie
        result = parser.parse("Movie Name (2020).mp4")
        assert result.media_type == MediaType.MOVIE
        assert result.title == "Movie Name"

        # Test with configuration
        parser = NameParser(strict_mode=True)
        result = parser.parse("ambiguous_file.mp4")
        assert result.media_type == MediaType.UNKNOWN
        assert result.confidence < 0.5

    def test_llm_verification(self):
        """Test LLM-based verification of parsed names."""
        parser = NameParser(use_llm=True)

        # This would use a mocked LLM in tests
        # Setting up a mock is outside the scope of this initial implementation
        # but would be added when the actual LLM integration is implemented

        # For now, just test that the method exists
        assert hasattr(parser, "verify_with_llm")
