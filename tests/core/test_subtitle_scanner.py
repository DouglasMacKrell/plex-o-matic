"""Tests for the subtitle scanner module."""

import pytest
from pathlib import Path

from plexomatic.core.subtitle_scanner import SubtitleFile, scan_for_subtitles
from plexomatic.core.file_scanner import FileScanner


# Test fixtures
@pytest.fixture
def sample_subtitle_files():
    """Create a sample of subtitle filenames."""
    return [
        "Movie.Title.2020.en.srt",
        "TV.Show.S01E01.en.srt",
        "Anime.Show.01.fr.srt",
        "Documentary.2019.en.forced.srt",
        "Comedy.Show.S02E03.en.sdh.srt",
        "Foreign.Film.2021.en.forced.sdh.srt",
        "Mixed.Case.Show.S01E02.En.sSa",
    ]


@pytest.fixture
def temp_subtitle_dir(tmp_path):
    """Create a temporary directory with subtitle files."""
    subtitle_dir = tmp_path / "subtitles"
    subtitle_dir.mkdir()

    # Create sample subtitle files
    for filename in [
        "Movie.2020.en.srt",
        "Show.S01E01.en.srt",
        "Show.S01E01.fr.srt",
        "Show.S01E01.de.forced.srt",
        "Show.S01E01.en.sdh.srt",
    ]:
        subtitle_path = subtitle_dir / filename
        subtitle_path.write_text("Dummy subtitle content")

    return subtitle_dir


@pytest.fixture
def mixed_media_dir(tmp_path):
    """Create a temporary directory with mixed media and subtitle files."""
    media_dir = tmp_path / "media"
    media_dir.mkdir()

    # Create sample media files
    for filename in [
        "Movie.2020.mp4",
        "Show.S01E01.mkv",
        "Documentary.2019.avi",
    ]:
        file_path = media_dir / filename
        file_path.write_text("Dummy media content")

    # Create matching subtitle files
    for filename in [
        "Movie.2020.en.srt",
        "Movie.2020.fr.srt",
        "Show.S01E01.en.srt",
        "Show.S01E01.en.forced.srt",
        "Documentary.2019.en.sdh.srt",
    ]:
        file_path = media_dir / filename
        file_path.write_text("Dummy subtitle content")

    # Create some non-media, non-subtitle files
    for filename in [
        "readme.txt",
        "info.nfo",
        "thumbs.db",
    ]:
        file_path = media_dir / filename
        file_path.write_text("Dummy file content")

    return media_dir


class TestSubtitleFile:
    """Tests for the SubtitleFile class."""

    def test_initialization(self):
        """Test basic initialization of a SubtitleFile."""
        path = Path("example/path/Movie.2020.en.srt")
        subtitle = SubtitleFile(path)

        assert subtitle.path == path
        assert subtitle.extension == ".srt"
        assert subtitle.filename == "Movie.2020.en"

    def test_language_detection(self):
        """Test language detection from filename."""
        test_cases = [
            ("Movie.en.srt", "en"),
            ("Show.S01E01.fr.srt", "fr"),
            ("Anime.01.de.srt", "de"),
            ("Movie.eng.srt", "eng"),  # 3-letter code
            ("Show.S01E01.srt", "und"),  # No language code
            ("Movie.en.forced.srt", "en"),  # With forced tag
            ("Show.S01E01.en.sdh.srt", "en"),  # With SDH tag
        ]

        for filename, expected_lang in test_cases:
            subtitle = SubtitleFile(Path(filename))
            assert subtitle.language == expected_lang, f"Failed on {filename}"

    def test_forced_detection(self):
        """Test detection of forced subtitles."""
        test_cases = [
            ("Movie.en.forced.srt", True),
            ("Show.S01E01.en.Forced.srt", True),  # Case insensitive
            ("Movie.forced.en.srt", True),  # Different order
            ("Show.S01E01.en.srt", False),  # Not forced
            ("Movie.en.sdh.srt", False),  # Different flag
        ]

        for filename, expected in test_cases:
            subtitle = SubtitleFile(Path(filename))
            assert subtitle.is_forced == expected, f"Failed on {filename}"

    def test_sdh_detection(self):
        """Test detection of SDH subtitles."""
        test_cases = [
            ("Movie.en.sdh.srt", True),
            ("Show.S01E01.en.SDH.srt", True),  # Case insensitive
            ("Movie.sdh.en.srt", True),  # Different order
            ("Show.S01E01.en.srt", False),  # Not SDH
            ("Movie.en.forced.srt", False),  # Different flag
        ]

        for filename, expected in test_cases:
            subtitle = SubtitleFile(Path(filename))
            assert subtitle.is_sdh == expected, f"Failed on {filename}"

    def test_media_name_extraction(self):
        """Test extraction of media filename without language and flags."""
        test_cases = [
            ("Movie.en.srt", "Movie"),
            ("Show.S01E01.fr.srt", "Show.S01E01"),
            ("Anime.01.de.forced.srt", "Anime.01"),
            ("Documentary.2019.en.sdh.srt", "Documentary.2019"),
            ("Comedy.S02E03.en.forced.sdh.srt", "Comedy.S02E03"),
        ]

        for filename, expected in test_cases:
            subtitle = SubtitleFile(Path(filename))
            assert subtitle.media_name == expected, f"Failed on {filename}"


class TestSubtitleScanner:
    """Tests for subtitle scanning functionality."""

    def test_scan_for_subtitles(self, temp_subtitle_dir):
        """Test scanning for subtitle files."""
        # Test with a list of common subtitle extensions
        subtitle_extensions = [".srt", ".sub", ".vtt", ".ass", ".ssa"]

        # Scan for subtitle files
        subtitles = scan_for_subtitles(temp_subtitle_dir, subtitle_extensions)

        # Check the results
        assert len(subtitles) == 5
        assert all(isinstance(sub, SubtitleFile) for sub in subtitles)

        # Check some specific files
        file_names = [sub.path.name for sub in subtitles]
        assert "Movie.2020.en.srt" in file_names
        assert "Show.S01E01.fr.srt" in file_names
        assert "Show.S01E01.de.forced.srt" in file_names

    def test_exclude_non_subtitle_files(self, mixed_media_dir):
        """Test that non-subtitle files are excluded from scan results."""
        subtitle_extensions = [".srt", ".sub", ".vtt", ".ass", ".ssa"]

        # Scan for subtitle files
        subtitles = scan_for_subtitles(mixed_media_dir, subtitle_extensions)

        # Check we only get subtitle files
        file_extensions = {sub.extension for sub in subtitles}
        assert all(ext in subtitle_extensions for ext in file_extensions)
        assert len(subtitles) == 5  # There are 5 subtitle files in the fixture

        # Check no media or other files were included
        file_names = [sub.path.name for sub in subtitles]
        assert "Movie.2020.mp4" not in file_names
        assert "readme.txt" not in file_names
        assert "info.nfo" not in file_names

    def test_match_subtitles_to_media(self, mixed_media_dir):
        """Test matching subtitle files to media files."""
        # First scan for media files

        # Get media files
        scanner = FileScanner(
            base_path=str(mixed_media_dir), allowed_extensions=[".mp4", ".mkv", ".avi"]
        )
        media_files = list(scanner.scan())

        # Get subtitle files
        subtitle_extensions = [".srt", ".sub", ".vtt", ".ass", ".ssa"]
        subtitles = scan_for_subtitles(mixed_media_dir, subtitle_extensions)

        # Match subtitles to media
        from plexomatic.core.subtitle_scanner import match_subtitles_to_media

        matches = match_subtitles_to_media(media_files, subtitles)

        # Check we have the right number of media files with subtitles
        assert len(matches) == 3  # All 3 media files have subtitles

        # Check specific matches
        for media_file in media_files:
            if "Movie.2020" in media_file.path.name:
                # Movie.2020.mp4 should match 2 subtitle files (en, fr)
                assert len(matches[media_file]) == 2
                languages = {sub.language for sub in matches[media_file]}
                assert "en" in languages
                assert "fr" in languages

            elif "Show.S01E01" in media_file.path.name:
                # Show.S01E01.mkv should match 2 subtitle files (en, en.forced)
                assert len(matches[media_file]) == 2
                # Check we have one normal and one forced subtitle
                has_forced = any(sub.is_forced for sub in matches[media_file])
                assert has_forced

            elif "Documentary.2019" in media_file.path.name:
                # Documentary.2019.avi should match 1 subtitle file (en.sdh)
                assert len(matches[media_file]) == 1
                assert matches[media_file][0].is_sdh


class TestSubtitleNaming:
    """Tests for subtitle naming conventions."""

    def test_generate_subtitle_filename(self):
        """Test generating subtitle filenames for media files."""
        from plexomatic.core.subtitle_scanner import generate_subtitle_filename

        # Test basic case with language only
        filename = generate_subtitle_filename("Movie.Title.2020.mp4", language="en")
        assert filename == "Movie.Title.2020.en.srt"

        # Test with language and forced flag
        filename = generate_subtitle_filename("TV.Show.S01E01.mkv", language="fr", forced=True)
        assert filename == "TV.Show.S01E01.fr.forced.srt"

        # Test with language and SDH flag
        filename = generate_subtitle_filename("Documentary.2019.mp4", language="en", sdh=True)
        assert filename == "Documentary.2019.en.sdh.srt"

        # Test with all flags
        filename = generate_subtitle_filename(
            "Movie.2020.mp4", language="es", forced=True, sdh=True
        )
        assert filename == "Movie.2020.es.forced.sdh.srt"

        # Test with custom extension
        filename = generate_subtitle_filename("Movie.2020.mp4", language="en", extension=".vtt")
        assert filename == "Movie.2020.en.vtt"
