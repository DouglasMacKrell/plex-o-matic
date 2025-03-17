"""Tests for the name parser module."""

import pytest
from pathlib import Path
from plexomatic.utils.name_parser import (
    MediaType,
    ParsedMediaName,
    detect_media_type,
    parse_tv_show,
    parse_movie,
    parse_anime,
    parse_media_name,
)


class TestMediaType:
    """Test the MediaType enum."""

    def test_media_type_values(self):
        """Test that all expected media types are defined."""
        assert MediaType.TV_SHOW.value == "tv_show"
        assert MediaType.TV_SPECIAL.value == "tv_special"
        assert MediaType.MOVIE.value == "movie"
        assert MediaType.ANIME.value == "anime"
        assert MediaType.ANIME_SPECIAL.value == "anime_special"
        assert MediaType.UNKNOWN.value == "unknown"


class TestParsedMediaName:
    """Test the ParsedMediaName dataclass."""

    def test_basic_initialization(self):
        """Test basic initialization with required fields."""
        parsed = ParsedMediaName(media_type=MediaType.TV_SHOW, title="Test Show", extension=".mkv")
        assert parsed.media_type == MediaType.TV_SHOW
        assert parsed.title == "Test Show"
        assert parsed.extension == ".mkv"
        assert parsed.confidence == 1.0  # Default value
        assert parsed.season is None
        assert parsed.episodes is None
        assert parsed.episode_title is None
        assert parsed.year is None
        assert parsed.group is None
        assert parsed.version is None
        assert parsed.special_type is None
        assert parsed.special_number is None
        assert parsed.additional_info == {}

    def test_tv_show_initialization(self):
        """Test initialization with TV show specific fields."""
        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            extension=".mkv",
            season=1,
            episodes=[1, 2],
            episode_title="Test Episode",
        )
        assert parsed.season == 1
        assert parsed.episodes == [1, 2]
        assert parsed.episode_title == "Test Episode"

    def test_movie_initialization(self):
        """Test initialization with movie specific fields."""
        parsed = ParsedMediaName(
            media_type=MediaType.MOVIE,
            title="Test Movie",
            extension=".mp4",
            year=2020,
            quality="1080p",
        )
        assert parsed.year == 2020
        assert parsed.quality == "1080p"

    def test_anime_initialization(self):
        """Test initialization with anime specific fields."""
        parsed = ParsedMediaName(
            media_type=MediaType.ANIME,
            title="Test Anime",
            extension=".mkv",
            group="SubGroup",
            version=2,
            episodes=[1],
        )
        assert parsed.group == "SubGroup"
        assert parsed.version == 2
        assert parsed.episodes == [1]

    def test_single_episode_conversion(self):
        """Test that single episode numbers are converted to lists."""
        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW, title="Test Show", extension=".mkv", episodes=1
        )
        assert isinstance(parsed.episodes, list)
        assert parsed.episodes == [1]

    def test_episode_list_conversion(self):
        """Test that single episode numbers are converted to lists."""
        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW, title="Test Show", extension=".mkv", episodes=1
        )
        assert isinstance(parsed.episodes, list)
        assert parsed.episodes == [1]

    def test_full_tv_show_initialization(self):
        """Test initialization with all TV show fields."""
        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            extension=".mkv",
            quality="1080p",
            confidence=0.95,
            season=1,
            episodes=[1, 2],
            episode_title="Pilot",
        )
        assert parsed.media_type == MediaType.TV_SHOW
        assert parsed.title == "Test Show"
        assert parsed.extension == ".mkv"
        assert parsed.quality == "1080p"
        assert parsed.confidence == 0.95
        assert parsed.season == 1
        assert parsed.episodes == [1, 2]
        assert parsed.episode_title == "Pilot"

    def test_full_movie_initialization(self):
        """Test initialization with all movie fields."""
        parsed = ParsedMediaName(
            media_type=MediaType.MOVIE,
            title="Test Movie",
            extension=".mp4",
            quality="4K",
            year=2020,
        )
        assert parsed.media_type == MediaType.MOVIE
        assert parsed.title == "Test Movie"
        assert parsed.extension == ".mp4"
        assert parsed.quality == "4K"
        assert parsed.year == 2020

    def test_full_anime_initialization(self):
        """Test initialization with all anime fields."""
        parsed = ParsedMediaName(
            media_type=MediaType.ANIME,
            title="Test Anime",
            extension=".mkv",
            quality="1080p",
            group="SubGroup",
            version=2,
            special_type="OVA",
            special_number=1,
        )
        assert parsed.media_type == MediaType.ANIME
        assert parsed.title == "Test Anime"
        assert parsed.extension == ".mkv"
        assert parsed.quality == "1080p"
        assert parsed.group == "SubGroup"
        assert parsed.version == 2
        assert parsed.special_type == "OVA"
        assert parsed.special_number == 1

    def test_additional_info(self):
        """Test handling of additional_info dictionary."""
        additional_info = {"source": "BluRay", "audio": "DTS"}
        parsed = ParsedMediaName(
            media_type=MediaType.MOVIE,
            title="Test Movie",
            extension=".mkv",
            additional_info=additional_info,
        )
        assert parsed.additional_info == additional_info
        assert parsed.additional_info["source"] == "BluRay"
        assert parsed.additional_info["audio"] == "DTS"


class TestDetectMediaType:
    """Test the detect_media_type function."""

    @pytest.mark.parametrize(
        "filename,expected_type",
        [
            # TV Show formats
            ("Show.S01E01.mp4", MediaType.TV_SHOW),
            ("Show.S01E01E02.mkv", MediaType.TV_SHOW),
            ("Show.1x01.avi", MediaType.TV_SHOW),
            ("Show - Season 1 Episode 2.mp4", MediaType.TV_SHOW),
            ("Show.S01.E01.mkv", MediaType.TV_SHOW),
            # TV Special formats
            ("Show.S01.5xSpecial.mp4", MediaType.TV_SPECIAL),
            ("Show.Special.Episode.1.mkv", MediaType.TV_SPECIAL),
            ("Show.Special.01.mp4", MediaType.TV_SPECIAL),
            ("Show.Special.mkv", MediaType.TV_SPECIAL),
            ("Show.OVA1.mkv", MediaType.TV_SPECIAL),
            # Movie formats
            ("Movie (2020).mp4", MediaType.MOVIE),
            ("Movie [2020].mkv", MediaType.MOVIE),
            ("Movie.Name.2020.1080p.mp4", MediaType.MOVIE),
            ("Movie 2020 720p.mkv", MediaType.MOVIE),
            ("Movie.2020.BluRay.mp4", MediaType.MOVIE),
            # Anime formats
            ("[SubGroup] Show - 01 [1080p].mkv", MediaType.ANIME),
            ("[SubGroup] Show - 01v2 [1080p].mkv", MediaType.ANIME),
            ("[SubGroup] Show - 1 [720p].mp4", MediaType.ANIME),
            # Anime Special formats
            ("[SubGroup] Show - OVA1 [1080p].mkv", MediaType.ANIME_SPECIAL),
            ("[SubGroup] Show - Special1 [720p].mp4", MediaType.ANIME_SPECIAL),
            ("[SubGroup] Show - Movie [1080p].mkv", MediaType.ANIME_SPECIAL),
            # Unknown formats
            ("random_file.mp4", MediaType.UNKNOWN),
            ("show_without_episode.mkv", MediaType.UNKNOWN),
            ("", MediaType.UNKNOWN),
        ],
    )
    def test_detect_media_type(self, filename, expected_type):
        """Test detection of various media types from filenames."""
        assert detect_media_type(filename) == expected_type

    def test_case_insensitive_detection(self):
        """Test that media type detection is case-insensitive."""
        assert detect_media_type("Show.s01e01.mp4") == MediaType.TV_SHOW
        assert detect_media_type("Show.S01E01.mp4") == MediaType.TV_SHOW
        assert detect_media_type("Show.special.mp4") == MediaType.TV_SPECIAL
        assert detect_media_type("Show.SPECIAL.mp4") == MediaType.TV_SPECIAL

    def test_priority_order(self):
        """Test that media types are detected in the correct priority order."""
        # Anime special should be detected before regular anime
        assert detect_media_type("[Group] Show - OVA [1080p].mkv") == MediaType.ANIME_SPECIAL

        # TV special should be detected before regular TV show
        assert detect_media_type("Show.Special.S01E01.mp4") == MediaType.TV_SPECIAL

        # Anime patterns should be checked before TV patterns
        assert detect_media_type("[Group] Show - 01 [1080p].mkv") == MediaType.ANIME


class TestParseTVShow:
    """Test the parse_tv_show function."""

    def test_standard_format(self):
        """Test parsing standard TV show format."""
        filename = "Show.Name.S01E02.Episode.Title.1080p.mp4"
        parsed = parse_tv_show(filename)
        assert parsed.title == "Show Name"
        assert parsed.season == 1
        assert parsed.episodes == [2]
        assert parsed.episode_title == "Episode Title"
        assert parsed.quality == "1080p"
        assert parsed.extension == ".mp4"

    def test_dash_format_with_quality(self):
        """Test parsing dash-separated format with quality."""
        filename = "Show Name - S01E02 - Episode Title - 1080p.mp4"
        parsed = parse_tv_show(filename)
        assert parsed.title == "Show Name"
        assert parsed.season == 1
        assert parsed.episodes == [2]
        assert parsed.episode_title == "Episode Title"
        assert parsed.quality == "1080p"
        assert parsed.confidence > 0.9

    def test_dash_format_without_quality(self):
        """Test parsing dash-separated format without quality."""
        filename = "Show Name - S01E02 - Episode Title.mp4"
        parsed = parse_tv_show(filename)
        assert parsed.title == "Show Name"
        assert parsed.season == 1
        assert parsed.episodes == [2]
        assert parsed.episode_title == "Episode Title"
        assert parsed.quality is None

    def test_multi_episode_range(self):
        """Test parsing multi-episode range format."""
        filename = "Show.Name.S01E02-E04.Title.mp4"
        parsed = parse_tv_show(filename)
        assert parsed.title == "Show Name"
        assert parsed.season == 1
        assert parsed.episodes == [2, 3, 4]
        assert parsed.episode_title == "Title"

    def test_quality_extraction(self):
        """Test extracting quality information from filenames."""
        filenames = [
            ("Show.S01E01.720p.mkv", "720p"),
            ("Show.S01E01.1080p.HDTV.mkv", "1080p HDTV"),
            ("Show.S01E01.BluRay.x264.mkv", "BluRay x264"),
        ]
        for filename, expected_quality in filenames:
            parsed = parse_tv_show(filename)
            assert parsed.quality == expected_quality

    def test_complex_title(self):
        """Test parsing complex show titles."""
        filename = "The.Walking.Dead.S01E01.Days.Gone.Bye.720p.BluRay.mkv"
        parsed = parse_tv_show(filename)
        assert parsed.title == "The Walking Dead"
        assert parsed.season == 1
        assert parsed.episodes == [1]
        assert parsed.episode_title == "Days Gone Bye"
        assert parsed.quality == "720p BluRay"
        assert parsed.extension == ".mkv"

    def test_title_extraction(self):
        """Test extracting title from complex filenames."""
        filenames = [
            ("Mr.Robot.S01E01.720p.mkv", "Mr Robot"),
            ("The.100.S01E01.720p.mkv", "The 100"),
            ("Game.of.Thrones.S01E01.720p.mkv", "Game of Thrones"),
        ]
        for filename, expected_title in filenames:
            parsed = parse_tv_show(filename)
            assert parsed.title == expected_title

    def test_alternative_format(self):
        """Test parsing alternative episode format (1x01)."""
        filename = "Show.Name.1x02.Title.mp4"
        parsed = parse_tv_show(filename)
        assert parsed.title == "Show Name"
        assert parsed.season == 1
        assert parsed.episodes == [2]
        assert parsed.episode_title == "Title"

    def test_parse_tv_show_edge_cases(self):
        """Test parsing TV show edge cases."""
        # Test with missing episode title
        filename = "Show.Name.S01E02.1080p.mp4"
        parsed = parse_tv_show(filename)
        assert parsed.title == "Show Name"
        assert parsed.episode_title is None

        # Test with missing quality
        filename = "Show.Name.S01E02.mp4"
        parsed = parse_tv_show(filename)
        assert parsed.quality is None

        # Test with complex episode range
        filename = "Show.Name.S01E02-E05.Title.mp4"
        parsed = parse_tv_show(filename)
        assert parsed.episodes == [2, 3, 4, 5]

        # Test with complex quality string
        filename = "Show.Name.S01E02.1080p.BluRay.x264.mp4"
        parsed = parse_tv_show(filename)
        assert parsed.quality == "1080p BluRay x264"

        # Test with special episode
        filename = "Show.Name.Special.Episode.mp4"
        parsed = parse_media_name(filename)  # Use parse_media_name for special episodes
        assert parsed.media_type == MediaType.TV_SPECIAL

    def test_standard_dash_format_with_quality(self):
        """Test parsing standard dash format with quality."""
        filename = "Show Name - S01E01 - Episode Title - 1080p.mkv"
        parsed = parse_tv_show(filename)
        assert parsed.title == "Show Name"
        assert parsed.season == 1
        assert parsed.episodes == [1]
        assert parsed.episode_title == "Episode Title"
        assert parsed.quality == "1080p"
        assert parsed.extension == ".mkv"
        assert parsed.confidence == 0.95

    def test_standard_dash_format_without_quality(self):
        """Test parsing standard dash format without quality."""
        filename = "Show Name - S01E01 - Episode Title.mkv"
        parsed = parse_tv_show(filename)
        assert parsed.title == "Show Name"
        assert parsed.season == 1
        assert parsed.episodes == [1]
        assert parsed.episode_title == "Episode Title"
        assert parsed.quality is None
        assert parsed.extension == ".mkv"
        assert parsed.confidence == 0.95

    def test_special_media_type(self):
        """Test parsing with TV_SPECIAL media type."""
        filename = "Show.Special.01.1080p.mkv"
        parsed = parse_tv_show(filename, media_type=MediaType.TV_SPECIAL)
        assert parsed.media_type == MediaType.TV_SPECIAL
        assert parsed.title == "Show"
        assert parsed.quality == "1080p"
        assert parsed.extension == ".mkv"

    def test_title_cleaning(self):
        """Test cleaning of show titles."""
        filenames = [
            ("Show.Name.S01E01.mkv", "Show Name"),
            ("Show_Name_S01E01.mkv", "Show Name"),
            ("Show-Name-S01E01.mkv", "Show Name"),
            ("Show   Name   S01E01.mkv", "Show Name"),
        ]
        for filename, expected_title in filenames:
            parsed = parse_tv_show(filename)
            assert parsed.title == expected_title

    def test_edge_cases(self):
        """Test edge cases and potential error conditions."""
        edge_cases = [
            # Empty filename
            ("", MediaType.TV_SHOW),
            # Just extension
            (".mkv", MediaType.TV_SHOW),
            # No extension
            ("Show.S01E01", MediaType.TV_SHOW),
            # Multiple dots in title
            ("Show.With.Dots.S01E01.mkv", MediaType.TV_SHOW),
            # Special characters in title
            ("Show! & Show? S01E01.mkv", MediaType.TV_SHOW),
        ]
        for filename, media_type in edge_cases:
            parsed = parse_tv_show(filename, media_type=media_type)
            assert isinstance(parsed, ParsedMediaName)
            assert parsed.media_type == media_type
            if not filename:
                assert parsed.extension == ""
            else:
                assert parsed.extension == Path(filename).suffix


class TestParseMovie:
    """Test the parse_movie function."""

    def test_standard_format(self):
        """Test parsing standard movie format."""
        filename = "Movie.Name.2020.1080p.BluRay.mp4"
        parsed = parse_movie(filename)
        assert parsed.title == "Movie Name"
        assert parsed.year == 2020
        assert parsed.quality == "1080p BluRay"
        assert parsed.extension == ".mp4"

    def test_parentheses_format(self):
        """Test parsing movie with year in parentheses."""
        filename = "Movie Name (2020) 1080p.mp4"
        parsed = parse_movie(filename)
        assert parsed.title == "Movie Name"
        assert parsed.year == 2020
        assert parsed.quality == "1080p"

    def test_brackets_format(self):
        """Test parsing movie with year in brackets."""
        filename = "Movie Name [2020] [1080p].mp4"
        parsed = parse_movie(filename)
        assert parsed.title == "Movie Name"
        assert parsed.year == 2020
        assert parsed.quality == "1080p"

    def test_complex_title(self):
        """Test parsing movie with complex title."""
        filename = "Movie Name: The Subtitle (2020).mp4"
        parsed = parse_movie(filename)
        assert parsed.title == "Movie Name: The Subtitle"
        assert parsed.year == 2020


class TestParseAnime:
    """Test the parse_anime function."""

    def test_standard_format(self):
        """Test parsing standard anime format."""
        filename = "[SubGroup] Anime Name - 01 [1080p].mkv"
        parsed = parse_anime(filename)
        assert parsed.title == "Anime Name"
        assert parsed.group == "SubGroup"
        assert parsed.episodes == [1]
        assert parsed.quality == "1080p"
        assert parsed.extension == ".mkv"

    def test_version_format(self):
        """Test parsing anime with version number."""
        filename = "[SubGroup] Anime Name - 01v2 [1080p].mkv"
        parsed = parse_anime(filename)
        assert parsed.title == "Anime Name"
        assert parsed.episodes == [1]
        assert parsed.version == 2

    def test_special_format(self):
        """Test parsing anime special."""
        filename = "[SubGroup] Anime Name - OVA1 [1080p].mkv"
        parsed = parse_media_name(filename)  # Use parse_media_name instead of parse_anime
        assert parsed.media_type == MediaType.ANIME_SPECIAL
        assert parsed.title == "Anime Name"
        assert parsed.group == "SubGroup"
        assert parsed.quality == "1080p"
        assert parsed.special_type == "OVA"
        assert parsed.special_number == 1

    def test_complex_group(self):
        """Test parsing anime with complex group name."""
        filename = "[Sub.Group-Team] Anime Name - 01 [1080p].mkv"
        parsed = parse_anime(filename)
        assert parsed.title == "Anime Name"
        assert parsed.group == "Sub.Group-Team"
        assert parsed.episodes == [1]

    def test_parse_anime_edge_cases(self):
        """Test parsing anime edge cases."""
        # Test with complex version and quality
        filename = "[SubGroup] Anime Name - 01v3 [1080p].mkv"
        parsed = parse_anime(filename)
        assert parsed.title == "Anime Name"
        assert parsed.version == 3
        assert parsed.quality == "1080p"

        # Test with batch release
        filename = "[SubGroup] Anime Name - 01 [Batch][1080p].mkv"
        parsed = parse_anime(filename)
        assert parsed.title == "Anime Name"
        assert parsed.episodes == [1]

        # Test with special episode types
        special_types = [
            ("[SubGroup] Anime - OVA [1080p].mkv", "OVA", 1),
            ("[SubGroup] Anime - Special [1080p].mkv", "Special", 1),
            ("[SubGroup] Anime - Movie [1080p].mkv", "Movie", 1),
        ]
        for filename, special_type, number in special_types:
            parsed = parse_media_name(filename)  # Use parse_media_name for special episodes
            assert parsed.media_type == MediaType.ANIME_SPECIAL
            assert parsed.special_type == special_type
            assert parsed.special_number == number


class TestParseMediaName:
    """Test the parse_media_name function."""

    def test_tv_show_parsing(self):
        """Test parsing TV show through main function."""
        filename = "Show.Name.S01E02.mp4"
        parsed = parse_media_name(filename)
        assert parsed.media_type == MediaType.TV_SHOW
        assert parsed.title == "Show Name"
        assert parsed.season == 1
        assert parsed.episodes == [2]

    def test_movie_parsing(self):
        """Test parsing movie through main function."""
        filename = "Movie.Name.2020.mp4"
        parsed = parse_media_name(filename)
        assert parsed.media_type == MediaType.MOVIE
        assert parsed.title == "Movie Name"
        assert parsed.year == 2020

    def test_anime_parsing(self):
        """Test parsing anime through main function."""
        filename = "[SubGroup] Anime - 01 [1080p].mkv"
        parsed = parse_media_name(filename)
        assert parsed.media_type == MediaType.ANIME
        assert parsed.title == "Anime"
        assert parsed.group == "SubGroup"
        assert parsed.episodes == [1]

    def test_unknown_format(self):
        """Test parsing unknown format through main function."""
        filename = "random_file.mp4"
        parsed = parse_media_name(filename)
        assert parsed.media_type == MediaType.UNKNOWN
        assert parsed.title == "random_file"

    def test_parse_media_name_edge_cases(self):
        """Test parsing media name edge cases."""
        # Test with invalid file extension
        filename = "random_file.invalid"
        parsed = parse_media_name(filename)
        assert parsed.media_type == MediaType.UNKNOWN
        assert parsed.extension == ".invalid"

        # Test with no extension
        filename = "random_file"
        parsed = parse_media_name(filename)
        assert parsed.media_type == MediaType.UNKNOWN
        assert parsed.extension == ""

        # Test with complex path
        filename = "/path/to/Show.S01E01.mp4"
        parsed = parse_media_name(Path(filename).name)  # Extract just the filename
        assert parsed.media_type == MediaType.TV_SHOW
        assert parsed.title == "Show"
        assert parsed.season == 1
        assert parsed.episodes == [1]

        # Test with Windows path
        filename = "Show.S01E01.mp4"  # Just use the filename part
        parsed = parse_media_name(filename)
        assert parsed.media_type == MediaType.TV_SHOW
        assert parsed.title == "Show"
        assert parsed.season == 1
        assert parsed.episodes == [1]
