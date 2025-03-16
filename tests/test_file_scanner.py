"""Tests for the file scanner module."""
import os
import pytest
from pathlib import Path
from plexomatic.core.file_scanner import FileScanner, MediaFile

@pytest.fixture
def temp_media_dir(tmp_path):
    """Create a temporary directory with test media files."""
    # Create test directory structure
    tv_dir = tmp_path / "TV Shows" / "Test Show" / "Season 01"
    tv_dir.mkdir(parents=True)
    
    # Create test files
    test_files = [
        tv_dir / "Test.Show.S01E01.mp4",
        tv_dir / "Test.Show.S01E02E03.mkv",  # Multi-episode file
        tv_dir / "test_show_s01e04.avi",
        tv_dir / ".DS_Store",  # Hidden file to be ignored
        tv_dir / "Thumbs.db"   # System file to be ignored
    ]
    
    for file_path in test_files:
        file_path.touch()
    
    return tmp_path

def test_file_scanner_initialization():
    """Test that FileScanner initializes with correct parameters."""
    scanner = FileScanner(
        base_path="/test/path",
        allowed_extensions=[".mp4", ".mkv", ".avi"],
        ignore_patterns=[r"^\.", r"Thumbs\.db$"]
    )
    
    assert scanner.base_path == Path("/test/path")
    assert scanner.allowed_extensions == {".mp4", ".mkv", ".avi"}
    assert scanner.ignore_patterns == [r"^\.", r"Thumbs\.db$"]

def test_file_scanner_finds_media_files(temp_media_dir):
    """Test that FileScanner correctly identifies media files."""
    scanner = FileScanner(
        base_path=str(temp_media_dir),
        allowed_extensions=[".mp4", ".mkv", ".avi"]
    )
    
    media_files = list(scanner.scan())
    
    # Should find 3 media files (ignoring .DS_Store and Thumbs.db)
    assert len(media_files) == 3
    
    # Verify all returned items are MediaFile objects
    assert all(isinstance(f, MediaFile) for f in media_files)
    
    # Check file extensions
    extensions = {os.path.splitext(f.path)[1] for f in media_files}
    assert extensions == {".mp4", ".mkv", ".avi"}

def test_file_scanner_ignores_system_files(temp_media_dir):
    """Test that FileScanner correctly ignores system and hidden files."""
    scanner = FileScanner(
        base_path=str(temp_media_dir),
        allowed_extensions=[".mp4", ".mkv", ".avi"],
        ignore_patterns=[r"^\.", r"Thumbs\.db$"]
    )
    
    media_files = list(scanner.scan())
    
    # Check that no ignored files are included
    file_names = [f.path.name for f in media_files]
    assert ".DS_Store" not in file_names
    assert "Thumbs.db" not in file_names

def test_media_file_properties():
    """Test that MediaFile objects correctly parse file information."""
    file_path = Path("/TV Shows/Test Show/Season 01/Test.Show.S01E02E03.mkv")
    media_file = MediaFile(file_path)
    
    assert media_file.path == file_path
    assert media_file.extension == ".mkv"
    assert media_file.size == 0  # Since it's a test file
    assert media_file.is_multi_episode  # Should detect E02E03 pattern 