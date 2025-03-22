"""Tests for the file_utils module."""

from pathlib import Path

from plexomatic.utils.file_utils import (
    sanitize_filename,
    get_preview_rename,
)


class TestSanitizeFilename:
    """Tests for the sanitize_filename function."""

    def test_sanitize_filename_with_invalid_chars(self):
        """Test sanitizing a filename with invalid characters."""
        filename = 'test<>:"/\\|?*.txt'
        expected = "test_________.txt"
        assert sanitize_filename(filename) == expected

    def test_sanitize_filename_without_invalid_chars(self):
        """Test sanitizing a filename without invalid characters."""
        filename = "normal_filename.txt"
        assert sanitize_filename(filename) == filename


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
        assert preview["original_path"] == str(path)
        assert preview["new_path"] != str(path)  # Should change

    def test_multi_episode_preview_concatenated(self) -> None:
        """Test preview rename for a multi-episode file with concatenated format."""
        path = Path("/test/Show.Name.S01E01E02E03.mp4")
        preview = get_preview_rename(path, concatenated=True)
        assert preview["original_name"] == "Show.Name.S01E01E02E03.mp4"
        assert "E01-E03" in preview["new_name"] or "E01E02E03" in preview["new_name"]
        assert preview["original_path"] == str(path)
        assert preview["new_path"] != str(path)  # Should change
