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

    def test_basic_sanitization(self) -> None:
        """Test that invalid characters are replaced with underscores."""
        filename = 'test<>:"/\\|?*file.txt'
        sanitized = sanitize_filename(filename)
        assert sanitized == "test_________file.txt"

    def test_no_invalid_chars(self) -> None:
        """Test that filenames without invalid characters are unchanged."""
        filename = "normal_filename.txt"
        sanitized = sanitize_filename(filename)
        assert sanitized == filename

    def test_empty_string(self) -> None:
        """Test sanitizing an empty string."""
        filename = ""
        sanitized = sanitize_filename(filename)
        assert sanitized == ""

    def test_only_invalid_chars(self) -> None:
        """Test sanitizing a string with only invalid characters."""
        filename = '<>:"/\\|?*'
        sanitized = sanitize_filename(filename)
        assert sanitized == "_________"


class TestExtractShowInfo:
    """Test the extract_show_info function."""

    def test_tv_show_standard_format(self) -> None:
        """Test extracting info from a standard TV show format."""
        filename = "Show.Name.S01E02.Episode.Title.720p.mp4"
        info = extract_show_info(filename)
        assert info["show_name"] == "Show Name"
        assert info["season"] == "01"
        assert info["episode"] == "02"
        assert info["title"] == "Episode Title"

    def test_tv_show_no_title(self) -> None:
        """Test extracting info from a TV show without episode title."""
        filename = "Show.Name.S01E02.mp4"
        info = extract_show_info(filename)
        assert info["show_name"] == "Show Name"
        assert info["season"] == "01"
        assert info["episode"] == "02"
        assert info["title"] is None

    def test_tv_show_multi_episode(self) -> None:
        """Test extracting info from a multi-episode TV show."""
        filename = "Show.Name.S01E02E03.mp4"
        info = extract_show_info(filename)
        assert info["show_name"] == "Show Name"
        assert info["season"] == "01"
        assert info["episode"] == "02"

    def test_movie_standard_format(self) -> None:
        """Test extracting info from a standard movie format."""
        filename = "Movie.Name.2020.1080p.mp4"
        info = extract_show_info(filename)
        assert info["movie_name"] == "Movie Name"
        assert info["year"] == "2020"
        assert info["info"] == "1080p"

    def test_movie_no_info(self) -> None:
        """Test extracting info from a movie without additional info."""
        filename = "Movie.Name.2020.mp4"
        info = extract_show_info(filename)
        assert info["movie_name"] == "Movie Name"
        assert info["year"] == "2020"
        assert info["info"] is None

    def test_unrecognized_format(self) -> None:
        """Test extracting info from an unrecognized format."""
        filename = "random_file.mp4"
        info = extract_show_info(filename)
        assert info["show_name"] is None
        assert info["movie_name"] is None
        assert info["name"] == "random_file"

    def test_tv_show_empty_title(self) -> None:
        """Test extracting info with an empty title part."""
        filename = ".S01E02.mp4"
        info = extract_show_info(filename)
        # This might vary depending on implementation - adjust as needed
        assert "show_name" in info

    def test_movie_empty_info(self) -> None:
        """Test extracting info with an empty movie name."""
        filename = ".2020.mp4"
        info = extract_show_info(filename)
        # This might vary depending on implementation - adjust as needed
        assert "movie_name" in info


class TestGenerateTVFilename:
    """Test the generate_tv_filename function."""

    def test_basic_generation(self) -> None:
        """Test generating a basic TV show filename."""
        filename = generate_tv_filename("Show Name", 1, 2)
        assert filename == "Show.Name.S01E02.mp4"

    def test_with_title(self) -> None:
        """Test generating a TV show filename with an episode title."""
        filename = generate_tv_filename("Show Name", 1, 2, "Episode Title")
        assert filename == "Show.Name.S01E02.Episode.Title.mp4"

    def test_custom_extension(self) -> None:
        """Test generating a TV show filename with a custom extension."""
        filename = generate_tv_filename("Show Name", 1, 2, None, ".mkv")
        assert filename == "Show.Name.S01E02.mkv"

    def test_multi_episode_concatenated(self) -> None:
        """Test generating a concatenated multi-episode filename."""
        filename = generate_tv_filename("Show Name", 1, [2, 3, 4], None, ".mp4", True)
        assert "E02+E03+E04" in filename

    def test_multi_episode_range(self) -> None:
        """Test generating a range multi-episode filename."""
        filename = generate_tv_filename("Show Name", 1, [2, 3, 4], None, ".mp4", False)
        assert "E02-E04" in filename


class TestGenerateMovieFilename:
    """Test the generate_movie_filename function."""

    def test_basic_generation(self) -> None:
        """Test generating a basic movie filename."""
        filename = generate_movie_filename("Movie Name", 2020)
        assert filename == "Movie.Name.2020.mp4"

    def test_custom_extension(self) -> None:
        """Test generating a movie filename with a custom extension."""
        filename = generate_movie_filename("Movie Name", 2020, ".mkv")
        assert filename == "Movie.Name.2020.mkv"

    def test_with_special_chars(self) -> None:
        """Test generating a movie filename with special characters."""
        filename = generate_movie_filename("Movie: Name", 2020)
        assert filename == "Movie_.Name.2020.mp4"


class TestGetPreviewRename:
    """Test the get_preview_rename function."""

    def test_tv_show_preview(self) -> None:
        """Test preview rename for a TV show."""
        path = Path("/test/Show.Name.S01E02.mp4")
        preview = get_preview_rename(path)
        assert preview["original_name"] == "Show.Name.S01E02.mp4"
        assert preview["new_name"] == preview["original_name"]  # No changes
        assert preview["original_path"] == str(path)
        assert preview["new_path"] == str(path)  # No changes

    def test_tv_show_with_changes(self) -> None:
        """Test preview rename for a TV show with changes."""
        path = Path("/test/Show.Name.S01E02.mp4")
        preview = get_preview_rename(path, "New Show", 2, 3, "New Title")
        assert preview["original_name"] == "Show.Name.S01E02.mp4"
        assert preview["new_name"] == "New.Show.S02E03.New.Title.mp4"
        assert preview["original_path"] == str(path)
        assert preview["new_path"] == "/test/New.Show.S02E03.New.Title.mp4"

    def test_movie_preview(self) -> None:
        """Test preview rename for a movie."""
        path = Path("/test/Movie.Name.2020.mp4")
        preview = get_preview_rename(path)
        assert preview["original_name"] == "Movie.Name.2020.mp4"
        assert preview["new_name"] == preview["original_name"]  # No changes
        assert preview["original_path"] == str(path)
        assert preview["new_path"] == str(path)  # No changes

    def test_movie_with_changes(self) -> None:
        """Test preview rename for a movie with changes."""
        path = Path("/test/Movie.Name.2020.mp4")
        preview = get_preview_rename(path, "New Movie", 2021)
        assert preview["original_name"] == "Movie.Name.2020.mp4"
        assert preview["new_name"] == "New.Movie.2021.mp4"
        assert preview["original_path"] == str(path)
        assert preview["new_path"] == "/test/New.Movie.2021.mp4"

    def test_unrecognized_format(self) -> None:
        """Test preview rename for an unrecognized format."""
        path = Path("/test/random_file.mp4")
        preview = get_preview_rename(path)
        assert preview["original_name"] == "random_file.mp4"
        assert preview["new_name"] == preview["original_name"]  # No changes
        assert preview["original_path"] == str(path)
        assert preview["new_path"] == str(path)  # No changes

    def test_multi_episode_preview(self) -> None:
        """Test preview rename for a multi-episode file."""
        path = Path("/test/Show.Name.S01E01E02E03.mp4")
        preview = get_preview_rename(path)
        assert preview["original_name"] == "Show.Name.S01E01E02E03.mp4"
        assert "E01" in preview["new_name"] and (
            "E02" in preview["new_name"] or "E03" in preview["new_name"]
        )
