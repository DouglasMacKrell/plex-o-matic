"""Comprehensive tests for the name parser module."""

from plexomatic.utils.name_parser import (
    MediaType,
    ParsedMediaName,
    NameParser,
    detect_media_type,
    parse_tv_show,
    parse_movie,
    parse_anime,
    parse_media_name,
)
from tests.conftest import mark


class TestMediaTypeDetection:
    """Test detection of media types from filenames."""

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
        """Test detecting media types from various filenames."""
        result = detect_media_type(filename)
        assert result == expected_type, f"Expected {expected_type}, got {result} for {filename}"


class TestTVShowParsing:
    """Test parsing of TV show filenames."""

    def test_standard_format(self) -> None:
        """Test parsing a standard TV show format."""
        result = parse_tv_show("Show.Name.S01E02.Episode.Title.720p.HDTV.mp4")
        assert result.media_type == MediaType.TV_SHOW
        assert result.title == "Show Name"
        assert result.season == 1
        assert result.episodes == [2]
        assert result.episode_title == "Episode Title"
        assert result.quality == "720p HDTV"
        assert result.extension == ".mp4"
        assert result.confidence == 0.8

    def test_dash_format_with_quality(self) -> None:
        """Test parsing dash-separated format with quality."""
        result = parse_tv_show("Show Name - S01E02 - Episode Title - 1080p.mp4")
        assert result.media_type == MediaType.TV_SHOW
        assert result.title == "Show Name"
        assert result.season == 1
        assert result.episodes == [2]
        assert result.episode_title == "Episode Title"
        assert result.quality == "1080p"
        assert result.extension == ".mp4"
        assert result.confidence == 0.95

    def test_multi_episode_range(self) -> None:
        """Test parsing multi-episode range format."""
        result = parse_tv_show("Show.Name.S01E02-E04.mp4")
        assert result.media_type == MediaType.TV_SHOW
        assert result.title == "Show Name"
        assert result.season == 1
        assert result.episodes == [2, 3, 4]
        assert result.extension == ".mp4"
        assert result.confidence == 0.8

    def test_multi_episode_separate(self) -> None:
        """Test parsing multi-episode separate format."""
        result = parse_tv_show("Show.Name.S01E02E03E04.mp4")
        assert result.media_type == MediaType.TV_SHOW
        assert result.title == "Show Name"
        assert result.season == 1
        assert result.episodes == [2, 3, 4]
        assert result.extension == ".mp4"
        assert result.confidence == 0.8

    def test_alternative_formats(self) -> None:
        """Test parsing alternative TV show formats."""
        result = parse_tv_show("Show Name 1x01 Episode Title.mp4")
        assert result.media_type == MediaType.TV_SHOW
        assert result.title == "Show Name"
        assert result.season == 1
        assert result.episodes == [1]
        assert result.episode_title == "Episode Title"
        assert result.extension == ".mp4"
        assert result.confidence == 0.85


class TestMovieParsing:
    """Test parsing of movie filenames."""

    def test_standard_format(self) -> None:
        """Test parsing standard movie format."""
        result = parse_movie("Movie.Name.2020.1080p.BluRay.mp4")
        assert result.media_type == MediaType.MOVIE
        assert result.title == "Movie Name"
        assert result.year == 2020
        assert result.quality == "1080p BluRay"
        assert result.extension == ".mp4"
        assert result.confidence == 0.85

    def test_parentheses_format(self) -> None:
        """Test parsing movie with year in parentheses."""
        result = parse_movie("Movie Name (2020).mp4")
        assert result.media_type == MediaType.MOVIE
        assert result.title == "Movie Name"
        assert result.year == 2020
        assert result.extension == ".mp4"
        assert result.confidence == 0.95

    def test_brackets_format(self) -> None:
        """Test parsing movie with year in brackets."""
        result = parse_movie("Movie Name [2020] [1080p].mp4")
        assert result.media_type == MediaType.MOVIE
        assert result.title == "Movie Name"
        assert result.year == 2020
        assert result.quality == "1080p"
        assert result.extension == ".mp4"
        assert result.confidence == 0.9

    def test_quality_variants(self) -> None:
        """Test parsing movies with different quality variants."""
        variants = [
            ("Movie.Name.2020.720p.mp4", "720p"),
            ("Movie.Name.2020.1080p.WEB-DL.mp4", "1080p WEB-DL"),
            ("Movie.Name.2020.4K.x265.mp4", "4K x265"),
        ]
        for filename, expected_quality in variants:
            result = parse_movie(filename)
            assert result.quality == expected_quality


class TestAnimeParsing:
    """Test parsing of anime filenames."""

    def test_standard_format(self) -> None:
        """Test parsing standard anime format."""
        result = parse_anime("[Group] Anime Name - 01 [1080p].mkv")
        assert result.media_type == MediaType.ANIME
        assert result.title == "Anime Name"
        assert result.group == "Group"
        assert result.episodes == [1]
        assert result.quality == "1080p"
        assert result.extension == ".mkv"
        assert result.confidence >= 0.9

    def test_version_number(self) -> None:
        """Test parsing anime with version number."""
        result = parse_anime("[Group] Anime Name - 01v2 [720p].mkv")
        assert result.media_type == MediaType.ANIME
        assert result.title == "Anime Name"
        assert result.group == "Group"
        assert result.episodes == [1]
        assert result.version == 2
        assert result.quality == "720p"
        assert result.extension == ".mkv"
        assert result.confidence >= 0.9

    def test_special_episode(self) -> None:
        """Test parsing anime special episode."""
        result = parse_anime("[Group] Anime Name - OVA2 [1080p].mkv", MediaType.ANIME_SPECIAL)
        assert result.media_type == MediaType.ANIME_SPECIAL
        assert result.title == "Anime Name"
        assert result.group == "Group"
        assert result.special_type == "OVA"
        assert result.special_number == 2
        assert result.quality == "1080p"
        assert result.extension == ".mkv"
        assert result.confidence >= 0.9

    def test_multiple_groups(self) -> None:
        """Test parsing anime with multiple release groups."""
        result = parse_anime("[Group1][Group2] Anime Name - 01 [720p].mkv")
        assert result.media_type == MediaType.ANIME
        assert result.title == "Anime Name"
        assert result.group == "Group1"  # Should use the first group
        assert result.episodes == [1]
        assert result.quality == "720p"
        assert result.extension == ".mkv"
        assert result.confidence >= 0.9


class TestNameParser:
    """Test the NameParser class."""

    def test_initialization(self) -> None:
        """Test initialization of the NameParser class."""
        parser = NameParser()
        assert parser.strict_mode is False
        assert parser.use_llm is True
        assert parser.confidence_threshold == 0.5

        parser = NameParser(strict_mode=True)
        assert parser.strict_mode is True
        assert parser.confidence_threshold == 0.8

    def test_parse_method(self) -> None:
        """Test the parse method."""
        parser = NameParser()

        # Test TV show parsing
        tv_result = parser.parse("Show.Name.S01E02.mp4")
        assert tv_result.media_type == MediaType.TV_SHOW
        assert tv_result.title == "Show Name"

        # Test movie parsing
        movie_result = parser.parse("Movie.Name.2020.mp4")
        assert movie_result.media_type == MediaType.MOVIE
        assert movie_result.title == "Movie Name"

        # Test anime parsing
        anime_result = parser.parse("[Group] Anime - 01 [720p].mkv")
        assert anime_result.media_type == MediaType.ANIME
        assert anime_result.title == "Anime"

    def test_strict_mode(self) -> None:
        """Test the strict mode functionality."""
        # Initialize parser with strict mode
        parser = NameParser(strict_mode=True)

        # Should parse successfully even in strict mode
        result = parser.parse("Show.Name.S01E02.Episode.Title.720p.mp4")
        assert result.media_type == MediaType.TV_SHOW
        assert result.confidence == 0.8

        # Test with an ambiguous filename in strict mode
        result = parser.parse("Show Name.mp4")
        assert (
            result.media_type == MediaType.UNKNOWN
        )  # Should mark as unknown due to low confidence


class TestParsedMediaName:
    """Test the ParsedMediaName class."""

    def test_initialization(self) -> None:
        """Test initialization of the ParsedMediaName class."""
        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            extension=".mp4",
            season=1,
            episodes=[1, 2],
            quality="720p",
            confidence=0.9,
        )

        assert parsed.media_type == MediaType.TV_SHOW
        assert parsed.title == "Test Show"
        assert parsed.extension == ".mp4"
        assert parsed.season == 1
        assert parsed.episodes == [1, 2]
        assert parsed.quality == "720p"
        assert parsed.confidence == 0.9

    def test_post_init_processing(self) -> None:
        """Test the post-initialization processing."""
        # Test conversion of single episode to list
        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            extension=".mp4",
            episodes=1,
        )

        assert isinstance(parsed.episodes, list)
        assert parsed.episodes == [1]


def test_parse_media_name() -> None:
    """Test the parse_media_name function with various media types."""
    # TV Show
    tv_result = parse_media_name("Show.Name.S01E02.720p.mp4")
    assert tv_result.media_type == MediaType.TV_SHOW
    assert tv_result.title == "Show Name"
    assert tv_result.season == 1
    assert tv_result.episodes == [2]

    # Movie
    movie_result = parse_media_name("Movie.Name.2020.1080p.mp4")
    assert movie_result.media_type == MediaType.MOVIE
    assert movie_result.title == "Movie Name"
    assert movie_result.year == 2020

    # Anime
    anime_result = parse_media_name("[Group] Anime - 01 [720p].mkv")
    assert anime_result.media_type == MediaType.ANIME
    assert anime_result.title == "Anime"
    assert anime_result.group == "Group"

    # Unknown
    unknown_result = parse_media_name("random_file.mp4")
    assert unknown_result.media_type == MediaType.UNKNOWN
    assert unknown_result.title == "random_file"
