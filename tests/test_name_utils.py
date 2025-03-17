"""Tests for the name utils module."""

from pathlib import Path
from plexomatic.utils.name_utils import (
    sanitize_filename,
    extract_show_info,
    generate_tv_filename,
    generate_movie_filename,
    get_preview_rename,
)


class TestSanitizeFilename:
    """Test the sanitize_filename function."""

    def test_basic_sanitization(self):
        """Test basic filename sanitization."""
        filename = 'test<>:"/\\|?*file.txt'
        sanitized = sanitize_filename(filename)
        assert sanitized == "test_________file.txt"
        assert len(sanitized) == len(filename)  # Length should be preserved

    def test_no_invalid_chars(self):
        """Test filename with no invalid characters."""
        filename = "normal-file.txt"
        assert sanitize_filename(filename) == filename

    def test_empty_string(self):
        """Test empty string."""
        assert sanitize_filename("") == ""

    def test_only_invalid_chars(self):
        """Test string with only invalid characters."""
        filename = '<>:"\\/|?*'
        assert sanitize_filename(filename) == "_________"


class TestExtractShowInfo:
    """Test the extract_show_info function."""

    def test_tv_show_standard_format(self):
        """Test extracting info from standard TV show format."""
        filename = "Show.Name.S01E02.Episode.Title.mp4"
        info = extract_show_info(filename)
        assert info["show_name"] == "Show Name"
        assert info["season"] == "01"
        assert info["episode"] == "02"
        assert info["title"] == "Episode Title"

    def test_tv_show_no_title(self):
        """Test TV show without episode title."""
        filename = "Show.Name.S01E02.mp4"
        info = extract_show_info(filename)
        assert info["show_name"] == "Show Name"
        assert info["season"] == "01"
        assert info["episode"] == "02"
        assert info["title"] is None

    def test_tv_show_multi_episode(self):
        """Test TV show with multiple episodes."""
        filename = "Show.Name.S01E02E03.Title.mp4"
        info = extract_show_info(filename)
        assert info["show_name"] == "Show Name"
        assert info["season"] == "01"
        assert info["episode"] == "02"  # Should capture first episode
        assert info["title"] == "Title"

    def test_movie_standard_format(self):
        """Test extracting info from standard movie format."""
        filename = "Movie.Name.2020.1080p.mp4"
        info = extract_show_info(filename)
        assert info["movie_name"] == "Movie Name"
        assert info["year"] == "2020"
        assert info["info"] == "1080p"

    def test_movie_no_info(self):
        """Test movie without additional info."""
        filename = "Movie.Name.2020.mp4"
        info = extract_show_info(filename)
        assert info["movie_name"] == "Movie Name"
        assert info["year"] == "2020"
        assert info["info"] is None

    def test_unrecognized_format(self):
        """Test unrecognized filename format."""
        filename = "random_file.mp4"
        info = extract_show_info(filename)
        assert info["name"] == "random_file"
        assert info["show_name"] is None
        assert info["movie_name"] is None
        assert info["season"] is None
        assert info["episode"] is None
        assert info["year"] is None
        assert info["title"] is None

    def test_tv_show_empty_title(self):
        """Test TV show with empty title."""
        filename = "Show.Name.S01E02..mp4"
        info = extract_show_info(filename)
        assert info["show_name"] == "Show Name"
        assert info["title"] is None

    def test_movie_empty_info(self):
        """Test movie with empty info."""
        filename = "Movie.Name.2020..mp4"
        info = extract_show_info(filename)
        assert info["movie_name"] == "Movie Name"
        assert info["info"] is None


class TestGenerateTVFilename:
    """Test the generate_tv_filename function."""

    def test_basic_generation(self):
        """Test basic TV filename generation."""
        filename = generate_tv_filename("Show Name", 1, 2)
        assert filename == "Show.Name.S01E02.mp4"

    def test_with_title(self):
        """Test generation with episode title."""
        filename = generate_tv_filename("Show Name", 1, 2, "Episode Title")
        assert filename == "Show.Name.S01E02.Episode.Title.mp4"

    def test_custom_extension(self):
        """Test generation with custom extension."""
        filename = generate_tv_filename("Show Name", 1, 2, extension=".mkv")
        assert filename == "Show.Name.S01E02.mkv"

    def test_multi_episode_concatenated(self):
        """Test generation with multiple episodes concatenated."""
        filename = generate_tv_filename("Show Name", 1, [2, 3], concatenated=True)
        assert filename == "Show.Name.S01E02+E03.mp4"

    def test_multi_episode_range(self):
        """Test generation with multiple episodes as range."""
        filename = generate_tv_filename("Show Name", 1, [2, 3, 4], concatenated=False)
        assert filename == "Show.Name.S01E02-E04.mp4"


class TestGenerateMovieFilename:
    """Test the generate_movie_filename function."""

    def test_basic_generation(self):
        """Test basic movie filename generation."""
        filename = generate_movie_filename("Movie Name", 2020)
        assert filename == "Movie.Name.2020.mp4"

    def test_custom_extension(self):
        """Test generation with custom extension."""
        filename = generate_movie_filename("Movie Name", 2020, ".mkv")
        assert filename == "Movie.Name.2020.mkv"

    def test_with_special_chars(self):
        """Test generation with special characters."""
        filename = generate_movie_filename("Movie: A Story", 2020)
        assert filename == "Movie_.A.Story.2020.mp4"


class TestGetPreviewRename:
    """Test the get_preview_rename function."""

    def test_tv_show_preview(self):
        """Test preview generation for TV show."""
        path = Path("Show.Name.S01E02.mp4")
        preview = get_preview_rename(path)
        assert preview["original_name"] == "Show.Name.S01E02.mp4"
        assert preview["new_name"] == "Show.Name.S01E02.mp4"
        assert preview["original_path"] == str(path)
        assert preview["new_path"] == str(path)

    def test_tv_show_with_changes(self):
        """Test preview with changes to TV show."""
        path = Path("Show.Name.S01E02.mp4")
        preview = get_preview_rename(path, name="New Show", season=2, episode=3, title="New Title")
        assert preview["new_name"] == "New.Show.S02E03.New.Title.mp4"

    def test_movie_preview(self):
        """Test preview generation for movie."""
        path = Path("Movie.Name.2020.mp4")
        preview = get_preview_rename(path)
        assert preview["original_name"] == "Movie.Name.2020.mp4"
        assert preview["new_name"] == "Movie.Name.2020.mp4"

    def test_movie_with_changes(self):
        """Test preview with changes to movie."""
        path = Path("Movie.Name.2020.mp4")
        preview = get_preview_rename(
            path, name="New Movie", season=2021  # season parameter is used for year in movies
        )
        assert preview["new_name"] == "New.Movie.2021.mp4"

    def test_unrecognized_format(self):
        """Test preview for unrecognized format."""
        path = Path("random_file.mp4")
        preview = get_preview_rename(path)
        assert preview["original_name"] == preview["new_name"]

    def test_multi_episode_preview(self):
        """Test preview for multi-episode file."""
        path = Path("Show.Name.S01E02E03.mp4")
        preview = get_preview_rename(path, concatenated=True)
        assert "E02+E03" in preview["new_name"]

        preview = get_preview_rename(path, concatenated=False)
        assert "E02-E03" in preview["new_name"]
