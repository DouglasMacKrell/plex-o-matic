"""Comprehensive tests for the name parser module."""

import pytest
from plexomatic.utils.name_parser import (
    MediaType,
    ParsedMediaName,
    detect_media_type,
    parse_tv_show,
    parse_movie,
    parse_anime,
    parse_media_name,
    NameParser,
)


class TestMediaTypeDetection:
    """Test media type detection functionality."""

    @pytest.mark.parametrize(
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
            # Anime Special formats
            ("[Group] Anime Name OVA [1080p].mkv", MediaType.ANIME_SPECIAL),
            ("[Group] Anime Name - Special1 [720p].mkv", MediaType.ANIME_SPECIAL),
            # Unknown formats
            ("random_file.mp4", MediaType.UNKNOWN),
            ("document.pdf", MediaType.UNKNOWN),
        ],
    )
    def test_detect_media_type(self, filename: str, expected_type: MediaType):
        """Test detection of various media types."""
        assert detect_media_type(filename) == expected_type


class TestTVShowParsing:
    """Test TV show parsing functionality."""

    def test_standard_format(self):
        """Test parsing standard TV show format."""
        result = parse_tv_show("Show.Name.S01E02.Episode.Title.720p.HDTV.mp4")
        assert result.title == "Show Name"
        assert result.season == 1
        assert result.episodes == [2]
        assert result.episode_title == "Episode Title"
        assert result.quality == "720p HDTV"
        assert result.extension == ".mp4"

    def test_dash_format_with_quality(self):
        """Test parsing dash-separated format with quality."""
        result = parse_tv_show("Show Name - S01E02 - Episode Title - 1080p.mp4")
        assert result.title == "Show Name"
        assert result.season == 1
        assert result.episodes == [2]
        assert result.episode_title == "Episode Title"
        assert result.quality == "1080p"
        assert result.extension == ".mp4"

    def test_multi_episode_range(self):
        """Test parsing multi-episode range format."""
        result = parse_tv_show("Show.Name.S01E02-E04.mp4")
        assert result.title == "Show Name"
        assert result.season == 1
        assert result.episodes == [2, 3, 4]
        assert result.extension == ".mp4"

    def test_multi_episode_separate(self):
        """Test parsing separate multi-episode format."""
        result = parse_tv_show("Show.Name.S01E02E03E04.mp4")
        assert result.title == "Show Name"
        assert result.season == 1
        assert result.episodes == [2, 3, 4]
        assert result.extension == ".mp4"

    def test_alternative_formats(self):
        """Test parsing alternative TV show formats."""
        # 1x01 format
        result = parse_tv_show("Show Name 1x01 Episode Title.mp4")
        assert result.title == "Show Name"
        assert result.season == 1
        assert result.episodes == [1]
        assert result.episode_title == "Episode Title"

        # Period separated format
        result = parse_tv_show("Show.Name.S01.E01.mp4")
        assert result.title == "Show Name"
        assert result.season == 1
        assert result.episodes == [1]


class TestMovieParsing:
    """Test movie parsing functionality."""

    def test_standard_format(self):
        """Test parsing standard movie format."""
        result = parse_movie("Movie.Name.2020.1080p.BluRay.mp4")
        assert result.title == "Movie Name"
        assert result.year == 2020
        assert result.quality == "1080p BluRay"
        assert result.extension == ".mp4"

    def test_parentheses_format(self):
        """Test parsing movie with year in parentheses."""
        result = parse_movie("Movie Name (2020).mp4")
        assert result.title == "Movie Name"
        assert result.year == 2020
        assert result.extension == ".mp4"

    def test_brackets_format(self):
        """Test parsing movie with year in brackets."""
        result = parse_movie("Movie Name [2020] 720p.mp4")
        assert result.title == "Movie Name"
        assert result.year == 2020
        assert result.quality == "720p"
        assert result.extension == ".mp4"

    def test_quality_variants(self):
        """Test parsing various quality formats."""
        variants = [
            ("Movie.2020.720p.mp4", "720p"),
            ("Movie.2020.1080p.BluRay.mp4", "1080p BluRay"),
            ("Movie.2020.2160p.WEB-DL.mp4", "2160p WEB-DL"),
            ("Movie.2020.BRRip.x264.mp4", "BRRip x264"),
        ]
        for filename, expected_quality in variants:
            result = parse_movie(filename)
            assert result.quality == expected_quality


class TestAnimeParsing:
    """Test anime parsing functionality."""

    def test_standard_format(self):
        """Test parsing standard anime format."""
        result = parse_anime("[Group] Anime Name - 01 [1080p].mkv")
        assert result.title == "Anime Name"
        assert result.group == "Group"
        assert result.episodes == [1]
        assert result.quality == "1080p"
        assert result.extension == ".mkv"

    def test_version_number(self):
        """Test parsing anime with version number."""
        result = parse_anime("[Group] Anime Name - 01v2 [720p].mkv")
        assert result.title == "Anime Name"
        assert result.group == "Group"
        assert result.episodes == [1]
        assert result.version == 2
        assert result.quality == "720p"

    def test_special_episode(self):
        """Test parsing anime special episode."""
        result = parse_anime("[Group] Anime Name - OVA2 [1080p].mkv")
        assert result.title == "Anime Name"
        assert result.group == "Group"
        assert result.special_type == "OVA"
        assert result.special_number == 2
        assert result.quality == "1080p"

    def test_multiple_groups(self):
        """Test parsing anime with multiple group tags."""
        result = parse_anime("[Group1][Group2] Anime Name - 01 [720p].mkv")
        assert result.title == "Anime Name"
        assert result.group == "Group1"  # Should take first group
        assert result.episodes == [1]
        assert result.quality == "720p"


class TestNameParser:
    """Test the NameParser class functionality."""

    def test_initialization(self):
        """Test parser initialization with different settings."""
        parser = NameParser(strict_mode=True, use_llm=False)
        assert parser.strict_mode is True
        assert parser.use_llm is False

    def test_parse_method(self):
        """Test the parse method with different file types."""
        parser = NameParser()

        # Test TV show
        tv_result = parser.parse("Show.Name.S01E02.mp4")
        assert tv_result.media_type == MediaType.TV_SHOW
        assert tv_result.title == "Show Name"

        # Test movie
        movie_result = parser.parse("Movie.Name.2020.mp4")
        assert movie_result.media_type == MediaType.MOVIE
        assert movie_result.title == "Movie Name"

        # Test anime
        anime_result = parser.parse("[Group] Anime - 01 [720p].mkv")
        assert anime_result.media_type == MediaType.ANIME
        assert anime_result.title == "Anime"

    def test_strict_mode(self):
        """Test parser behavior in strict mode."""
        parser = NameParser(strict_mode=True)

        # Should parse valid filename with episode title and quality
        result = parser.parse("Show.Name.S01E02.Episode.Title.720p.mp4")

        # Should have lower confidence for ambiguous filename
        result = parser.parse("Show Name.mp4")
        assert result.confidence < 0.5


class TestParsedMediaName:
    """Test ParsedMediaName class functionality."""

    def test_initialization(self):
        """Test initialization with different field combinations."""
        # Basic initialization
        media = ParsedMediaName(media_type=MediaType.TV_SHOW, title="Test Show", extension=".mp4")
        assert media.title == "Test Show"
        assert media.extension == ".mp4"
        assert media.episodes is None

        # Full TV show initialization
        tv_show = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            extension=".mp4",
            season=1,
            episodes=1,
            episode_title="Test Episode",
        )
        assert isinstance(tv_show.episodes, list)
        assert tv_show.episodes == [1]

    def test_post_init_processing(self):
        """Test post-initialization processing."""
        # Test episodes conversion
        media = ParsedMediaName(
            media_type=MediaType.TV_SHOW, title="Test", extension=".mp4", episodes=5
        )
        assert isinstance(media.episodes, list)
        assert media.episodes == [5]

        # Test with list of episodes
        media = ParsedMediaName(
            media_type=MediaType.TV_SHOW, title="Test", extension=".mp4", episodes=[1, 2, 3]
        )
        assert media.episodes == [1, 2, 3]


def test_parse_media_name():
    """Test the main parse_media_name function."""
    # Test TV show
    tv_result = parse_media_name("Show.Name.S01E02.720p.mp4")
    assert tv_result.media_type == MediaType.TV_SHOW
    assert tv_result.title == "Show Name"
    assert tv_result.season == 1
    assert tv_result.episodes == [2]
    assert tv_result.quality == "720p"

    # Test movie
    movie_result = parse_media_name("Movie.Name.2020.1080p.mp4")
    assert movie_result.media_type == MediaType.MOVIE
    assert movie_result.title == "Movie Name"
    assert movie_result.year == 2020
    assert movie_result.quality == "1080p"

    # Test anime
    anime_result = parse_media_name("[Group] Anime - 01 [720p].mkv")
    assert anime_result.media_type == MediaType.ANIME
    assert anime_result.title == "Anime"
    assert anime_result.group == "Group"
    assert anime_result.episodes == [1]
    assert anime_result.quality == "720p"

    # Test unknown format
    unknown_result = parse_media_name("random_file.mp4")
    assert unknown_result.media_type == MediaType.UNKNOWN
    assert unknown_result.title == "random_file"
    assert unknown_result.extension == ".mp4"
