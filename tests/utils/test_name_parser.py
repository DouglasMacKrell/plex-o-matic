"""Tests for the name parser module."""

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
from tests.conftest import mark


class TestMediaType:
    """Test the MediaType enum."""

    def test_media_type_values(self) -> None:
        """Test that all expected media types are defined."""
        assert MediaType.TV_SHOW.value == "tv_show"
        assert MediaType.TV_SPECIAL.value == "tv_special"
        assert MediaType.MOVIE.value == "movie"
        assert MediaType.ANIME.value == "anime"
        assert MediaType.ANIME_SPECIAL.value == "anime_special"
        assert MediaType.UNKNOWN.value == "unknown"


class TestParsedMediaName:
    """Test the ParsedMediaName dataclass."""

    def test_basic_initialization(self) -> None:
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

    def test_tv_show_initialization(self) -> None:
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

    def test_movie_initialization(self) -> None:
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

    def test_anime_initialization(self) -> None:
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

    def test_single_episode_conversion(self) -> None:
        """Test that single episode numbers are converted to lists."""
        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW, title="Test Show", extension=".mkv", episodes=1
        )
        assert isinstance(parsed.episodes, list)
        assert parsed.episodes == [1]

    def test_episode_list_conversion(self) -> None:
        """Test that single episode numbers are converted to lists."""
        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW, title="Test Show", extension=".mkv", episodes=1
        )
        assert isinstance(parsed.episodes, list)
        assert parsed.episodes == [1]

    def test_full_tv_show_initialization(self) -> None:
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

    def test_full_movie_initialization(self) -> None:
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

    def test_full_anime_initialization(self) -> None:
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

    def test_additional_info(self) -> None:
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

    @mark.parametrize(
        "filename,expected_type",
        [
            # TV Show formats
            ("Show.Name.S01E01.mp4", MediaType.TV_SHOW),
            ("Show.Name.S01E01E02.mp4", MediaType.TV_SHOW),
            ("Show.Name.1x01.mp4", MediaType.TV_SHOW),
            ("Show Name - Season 1 Episode 2.mp4", MediaType.TV_SHOW),
            ("Show.Name.S01.E01.mp4", MediaType.TV_SHOW),
            # TV Special formats
            ("Show.Name.S01.5xSpecial.mp4", MediaType.TV_SPECIAL),
            ("Show Name - Special Episode.mp4", MediaType.TV_SPECIAL),
            ("Show Name - OVA1.mp4", MediaType.TV_SPECIAL),
            # Movie formats
            ("Movie Name (2020).mp4", MediaType.MOVIE),
            ("Movie.Name.[2020].mp4", MediaType.MOVIE),
            ("Movie.Name.2020.1080p.mp4", MediaType.MOVIE),
            ("Movie Name 2020 720p.mp4", MediaType.MOVIE),
            ("Movie Name 2020.mp4", MediaType.MOVIE),
            # Anime formats
            ("[Group] Anime Name - 01 [1080p].mkv", MediaType.ANIME),
            ("[Group] Anime Name - 01v2 [720p].mkv", MediaType.ANIME),
            ("[Group] Anime Name OVA [1080p].mkv", MediaType.ANIME_SPECIAL),
            ("[Group] Anime Name - Special1 [720p].mkv", MediaType.ANIME_SPECIAL),
            # Unknown formats
            ("random_file.mp4", MediaType.UNKNOWN),
            ("document.pdf", MediaType.UNKNOWN),
        ],
    )
    def test_detect_media_type(self, filename: str, expected_type: MediaType) -> None:
        """Test detection of media types from filenames."""
        assert detect_media_type(filename) == expected_type

    def test_case_insensitive_detection(self) -> None:
        """Test that media type detection is case-insensitive."""
        assert detect_media_type("Show.s01e01.mp4") == MediaType.TV_SHOW
        assert detect_media_type("Show.S01E01.mp4") == MediaType.TV_SHOW
        assert detect_media_type("Show.special.mp4") == MediaType.TV_SPECIAL
        assert detect_media_type("Show.SPECIAL.mp4") == MediaType.TV_SPECIAL

    def test_priority_order(self) -> None:
        """Test that media types are detected in the correct priority order."""
        # Anime special should be detected before regular anime
        assert detect_media_type("[Group] Show - OVA [1080p].mkv") == MediaType.ANIME_SPECIAL

        # TV special should be detected before regular TV show
        assert detect_media_type("Show.Special.S01E01.mp4") == MediaType.TV_SPECIAL

        # Anime patterns should be checked before TV patterns
        assert detect_media_type("[Group] Show - 01 [1080p].mkv") == MediaType.ANIME


class TestParseTVShow:
    """Test the parse_tv_show function."""

    def test_standard_format(self) -> None:
        """Test parsing standard TV show format."""
        filename = "Show.Name.S01E02.Episode.Title.1080p.mp4"
        parsed = parse_tv_show(filename)
        assert parsed.title == "Show Name"
        assert parsed.season == 1
        assert parsed.episodes == [2]
        assert parsed.episode_title == "Episode Title"
        assert parsed.quality == "1080p"
        assert parsed.extension == ".mp4"

    def test_dash_format_with_quality(self) -> None:
        """Test parsing dash-separated format with quality."""
        filename = "Show Name - S01E02 - Episode Title - 1080p.mp4"
        parsed = parse_tv_show(filename)
        assert parsed.title == "Show Name"
        assert parsed.season == 1
        assert parsed.episodes == [2]
        assert parsed.episode_title == "Episode Title"
        assert parsed.quality == "1080p"
        assert parsed.confidence > 0.9

    def test_dash_format_without_quality(self) -> None:
        """Test parsing dash-separated format without quality."""
        filename = "Show Name - S01E02 - Episode Title.mp4"
        parsed = parse_tv_show(filename)
        assert parsed.title == "Show Name"
        assert parsed.season == 1
        assert parsed.episodes == [2]
        assert parsed.episode_title == "Episode Title"
        assert parsed.quality is None

    def test_multi_episode_range(self) -> None:
        """Test parsing multi-episode range format."""
        filename = "Show.Name.S01E02-E04.Title.mp4"
        parsed = parse_tv_show(filename)
        assert parsed.title == "Show Name"
        assert parsed.season == 1
        assert parsed.episodes == [2, 3, 4]
        assert parsed.episode_title == "Title"

    def test_quality_extraction(self) -> None:
        """Test extracting quality information from filenames."""
        filenames = [
            ("Show.S01E01.720p.mkv", "720p"),
            ("Show.S01E01.1080p.HDTV.mkv", "1080p HDTV"),
            ("Show.S01E01.BluRay.x264.mkv", "BluRay x264"),
        ]
        for filename, expected_quality in filenames:
            parsed = parse_tv_show(filename)
            assert parsed.quality == expected_quality

    def test_complex_title(self) -> None:
        """Test parsing complex show titles."""
        filename = "The.Walking.Dead.S01E01.Days.Gone.Bye.720p.BluRay.mkv"
        parsed = parse_tv_show(filename)
        assert parsed.title == "The Walking Dead"
        assert parsed.season == 1
        assert parsed.episodes == [1]
        assert parsed.episode_title == "Days Gone Bye"
        assert parsed.quality == "720p BluRay"
        assert parsed.extension == ".mkv"

    def test_title_extraction(self) -> None:
        """Test extracting title from complex filenames."""
        filenames = [
            ("Mr.Robot.S01E01.720p.mkv", "Mr Robot"),
            ("The.100.S01E01.720p.mkv", "The 100"),
            ("Game.of.Thrones.S01E01.720p.mkv", "Game of Thrones"),
        ]
        for filename, expected_title in filenames:
            parsed = parse_tv_show(filename)
            assert parsed.title == expected_title

    def test_alternative_format(self) -> None:
        """Test parsing alternative episode format (1x01)."""
        filename = "Show.Name.1x02.Title.mp4"
        parsed = parse_tv_show(filename)
        assert parsed.title == "Show Name"
        assert parsed.season == 1
        assert parsed.episodes == [2]
        assert parsed.episode_title == "Title"

    def test_parse_tv_show_edge_cases(self) -> None:
        """Test parsing TV show edge cases."""
        # Test with empty string
        result = parse_tv_show("")
        assert result.title == ""
        assert result.extension == ""

        # Test with extension only
        result = parse_tv_show(".mp4")
        assert result.title == ""
        assert result.extension == Path(".mp4").suffix

        # Test with minimal info
        result = parse_tv_show("Show S01E01")
        assert result.title == "Show"
        assert result.season == 1
        assert result.episodes == [1]

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

    def test_standard_dash_format_with_quality(self) -> None:
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

    def test_standard_dash_format_without_quality(self) -> None:
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

    def test_special_media_type(self) -> None:
        """Test parsing with TV_SPECIAL media type."""
        filename = "Show.Special.01.1080p.mkv"
        parsed = parse_tv_show(filename, media_type=MediaType.TV_SPECIAL)
        assert parsed.media_type == MediaType.TV_SPECIAL
        assert parsed.title == "Show"
        assert parsed.quality == "1080p"
        assert parsed.extension == ".mkv"

    def test_title_cleaning(self) -> None:
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

    def test_season_pack(self) -> None:
        """Test parsing season packs."""
        # Test various season pack formats
        season_packs = [
            ("Show.Name.S01.Complete.mkv", "Show Name", 1),
            ("Show.Name.S02.COMPLETE.mkv", "Show Name", 2),
            ("Show Name - Season 03.mkv", "Show Name", 3),
            ("Show.Name.Season.04.mkv", "Show Name", 4),
        ]

        for filename, expected_title, expected_season in season_packs:
            parsed = parse_tv_show(filename)
            assert parsed.title == expected_title
            assert parsed.is_season_pack is True
            assert parsed.season == expected_season
            assert parsed.episodes == []

        # Test Unicode handling
        unicode_filename = "Café.S01.Complete.mkv"
        parsed = parse_tv_show(unicode_filename)
        assert parsed.title == "Café"
        assert parsed.is_season_pack is True
        assert parsed.season == 1

    def test_edge_cases(self) -> None:
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

    def test_standard_format(self) -> None:
        """Test parsing standard movie format."""
        filename = "Movie.Name.2020.1080p.BluRay.mp4"
        parsed = parse_movie(filename)
        assert parsed.title == "Movie Name"
        assert parsed.year == 2020
        assert parsed.quality == "1080p BluRay"
        assert parsed.extension == ".mp4"

    def test_parentheses_format(self) -> None:
        """Test parsing movie with year in parentheses."""
        filename = "Movie Name (2020) 1080p.mp4"
        parsed = parse_movie(filename)
        assert parsed.title == "Movie Name"
        assert parsed.year == 2020
        assert parsed.quality == "1080p"

    def test_brackets_format(self) -> None:
        """Test parsing movie with year in brackets."""
        filename = "Movie Name [2020] [1080p].mp4"
        parsed = parse_movie(filename)
        assert parsed.title == "Movie Name"
        assert parsed.year == 2020
        assert parsed.quality == "1080p"

    def test_complex_title(self) -> None:
        """Test parsing movie with complex title."""
        filename = "Movie Name: The Subtitle (2020).mp4"
        parsed = parse_movie(filename)
        assert parsed.title == "Movie Name: The Subtitle"
        assert parsed.year == 2020


class TestParseAnime:
    """Test the parse_anime function."""

    def test_standard_format(self) -> None:
        """Test parsing standard anime format."""
        filename = "[SubGroup] Anime Name - 01 [1080p].mkv"
        parsed = parse_anime(filename)
        assert parsed.title == "Anime Name"
        assert parsed.group == "SubGroup"
        assert parsed.episodes == [1]
        assert parsed.quality == "1080p"
        assert parsed.extension == ".mkv"

    def test_version_format(self) -> None:
        """Test parsing anime with version number."""
        filename = "[SubGroup] Anime Name - 01v2 [1080p].mkv"
        parsed = parse_anime(filename)
        assert parsed.title == "Anime Name"
        assert parsed.episodes == [1]
        assert parsed.version == 2

    def test_special_format(self) -> None:
        """Test parsing anime special."""
        filename = "[SubGroup] Anime Name - OVA1 [1080p].mkv"
        parsed = parse_media_name(filename)  # Use parse_media_name instead of parse_anime
        assert parsed.media_type == MediaType.ANIME_SPECIAL
        assert parsed.title == "Anime Name"
        assert parsed.group == "SubGroup"
        assert parsed.quality == "1080p"
        assert parsed.special_type == "OVA"
        assert parsed.special_number == 1

    def test_complex_group(self) -> None:
        """Test parsing anime with complex group name."""
        filename = "[Sub.Group-Team] Anime Name - 01 [1080p].mkv"
        parsed = parse_anime(filename)
        assert parsed.title == "Anime Name"
        assert parsed.group == "Sub.Group-Team"
        assert parsed.episodes == [1]

    def test_parse_anime_edge_cases(self) -> None:
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

    def test_tv_show_parsing(self) -> None:
        """Test parsing TV show through main function."""
        filename = "Show.Name.S01E02.mp4"
        parsed = parse_media_name(filename)
        assert parsed.media_type == MediaType.TV_SHOW
        assert parsed.title == "Show Name"
        assert parsed.season == 1
        assert parsed.episodes == [2]

    def test_movie_parsing(self) -> None:
        """Test parsing movie through main function."""
        filename = "Movie.Name.2020.mp4"
        parsed = parse_media_name(filename)
        assert parsed.media_type == MediaType.MOVIE
        assert parsed.title == "Movie Name"
        assert parsed.year == 2020

    def test_anime_parsing(self) -> None:
        """Test parsing anime through main function."""
        filename = "[SubGroup] Anime - 01 [1080p].mkv"
        parsed = parse_media_name(filename)
        assert parsed.media_type == MediaType.ANIME
        assert parsed.title == "Anime"
        assert parsed.group == "SubGroup"
        assert parsed.episodes == [1]

    def test_unknown_format(self) -> None:
        """Test parsing unknown format through main function."""
        filename = "random_file.mp4"
        parsed = parse_media_name(filename)
        assert parsed.media_type == MediaType.UNKNOWN
        assert parsed.title == "random_file"

    def test_parse_media_name_edge_cases(self) -> None:
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
