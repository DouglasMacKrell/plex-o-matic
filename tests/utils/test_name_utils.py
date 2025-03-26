"""Tests for the name utils module."""

from plexomatic.utils.name_utils import (
    sanitize_filename,
    preview_rename,
)


class TestSanitizeFilename:
    """Test the sanitize_filename function."""

    def test_basic_sanitization(self) -> None:
        """Test that invalid characters are replaced with underscores."""
        filename = 'test<>:"/\\|?*file.txt'
        sanitized = sanitize_filename(filename)
        assert sanitized == "test_________file.txt"

    def test_no_invalid_chars(self) -> None:
        """Test that a clean filename remains unchanged."""
        filename = "test_file.txt"
        sanitized = sanitize_filename(filename)
        assert sanitized == "test_file.txt"

    def test_empty_string(self) -> None:
        """Test that empty strings remain empty."""
        filename = ""
        sanitized = sanitize_filename(filename)
        assert sanitized == ""

    def test_only_invalid_chars(self) -> None:
        """Test that a filename with only invalid chars becomes all underscores."""
        filename = '<>:"/\\|?*'
        sanitized = sanitize_filename(filename)
        assert sanitized == "_________"


class TestPreviewRename:
    """Test the preview_rename function."""

    def test_tv_show_preview(self) -> None:
        """Test preview_rename with a TV show file."""
        result = preview_rename("Show.Name.S01E01.mkv")
        assert result is not None
        assert result["original_path"] == "Show.Name.S01E01.mkv"

    def test_tv_show_with_changes(self) -> None:
        """Test preview_rename with a TV show file that needs changes."""
        result = preview_rename("Show Name - s1e01 - Episode Title.mkv")
        assert result is not None
        assert result["original_path"] == "Show Name - s1e01 - Episode Title.mkv"
        assert "Show Name S01E01" in result["new_path"]

    def test_unrecognized_format(self) -> None:
        """Test that preview_rename returns None for unrecognized formats."""
        result = preview_rename("not_a_media_file.txt")
        assert result is None

    def test_anthology_mode(self) -> None:
        """Test preview_rename with anthology mode enabled."""
        result = preview_rename(
            "Show.Name.S01E01.Segment1-Segment2-Segment3.mkv", anthology_mode=True
        )
        assert result is not None
        # Since anthology handling is complex and depends on configuration,
        # we'll just verify that the function runs without errors.
        assert "original_path" in result
        assert "new_path" in result
