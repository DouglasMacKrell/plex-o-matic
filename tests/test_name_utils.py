"""Tests for the name utilities."""

import pytest
from pathlib import Path
from plexomatic.utils.name_utils import (
    sanitize_filename,
    extract_show_info,
    generate_tv_filename,
    generate_movie_filename,
    get_preview_rename,
)


def test_sanitize_filename():
    """Test that sanitize_filename properly handles invalid characters."""
    # Test with invalid characters
    assert sanitize_filename('test<>:"/\\|?*test') == "test_________test"

    # Test with valid characters
    assert sanitize_filename("test123.mp4") == "test123.mp4"


def test_extract_show_info_tv_show():
    """Test extracting information from TV show filenames."""
    # Standard TV show format
    info = extract_show_info("The.Show.S01E02.Episode.Title.mp4")
    assert info["show_name"] == "The Show"
    assert info["season"] == "01"
    assert info["episode"] == "02"
    assert "Title" in info["title"]

    # Different separator format
    info = extract_show_info("The_Show_S01E02_Episode_Title.mp4")
    assert info["show_name"] == "The Show"
    assert info["season"] == "01"
    assert info["episode"] == "02"

    # Multi-episode format
    info = extract_show_info("The.Show.S01E02E03.Episode.Title.mp4")
    assert info["show_name"] == "The Show"
    assert info["season"] == "01"
    assert info["episode"] == "02"


def test_extract_show_info_movie():
    """Test extracting information from movie filenames."""
    # Standard movie format
    info = extract_show_info("The.Movie.2020.mp4")
    assert info["movie_name"] == "The Movie"
    assert info["year"] == "2020"

    # With additional info
    info = extract_show_info("The.Movie.2020.1080p.mp4")
    assert info["movie_name"] == "The Movie"
    assert info["year"] == "2020"
    assert "info" in info


def test_extract_show_info_unrecognized():
    """Test extracting information from unrecognized filenames."""
    # Unrecognized format
    info = extract_show_info("random_file.mp4")
    assert info["name"] == "random_file"
    assert info["show_name"] is None
    assert info["movie_name"] is None


def test_generate_tv_filename():
    """Test generating standardized TV show filenames."""
    # Basic test
    filename = generate_tv_filename("The Show", 1, 2, extension=".mp4")
    assert filename == "The.Show.S01E02.mp4"

    # With title
    filename = generate_tv_filename("The Show", 1, 2, "Episode Title", ".mp4")
    assert filename == "The.Show.S01E02.Episode.Title.mp4"

    # With spaces in name
    filename = generate_tv_filename("The Amazing Show", 1, 2, extension=".mkv")
    assert filename == "The.Amazing.Show.S01E02.mkv"

    # With invalid characters
    filename = generate_tv_filename("The Show: Part 2", 1, 2, extension=".mp4")
    assert filename == "The.Show_.Part.2.S01E02.mp4"


def test_generate_movie_filename():
    """Test generating standardized movie filenames."""
    # Basic test
    filename = generate_movie_filename("The Movie", 2020, extension=".mp4")
    assert filename == "The.Movie.2020.mp4"

    # With spaces in name
    filename = generate_movie_filename("The Amazing Movie", 2020, extension=".mkv")
    assert filename == "The.Amazing.Movie.2020.mkv"

    # With invalid characters
    filename = generate_movie_filename("The Movie: Part 2", 2020, extension=".mp4")
    assert filename == "The.Movie_.Part.2.2020.mp4"


def test_get_preview_rename():
    """Test generating preview renames."""
    # TV show that needs renaming
    original = Path("/tmp/The Show S1E2 Episode.mp4")
    result = get_preview_rename(original)

    assert result["original_name"] == "The Show S1E2 Episode.mp4"
    assert "The.Show.S01E02" in result["new_name"]
    assert result["original_path"] == str(original)
    assert result["new_path"] != result["original_path"]

    # Movie that needs renaming
    original = Path("/tmp/Movie Name 2020.mp4")
    result = get_preview_rename(original)

    assert result["original_name"] == "Movie Name 2020.mp4"
    assert "Movie.Name.2020" in result["new_name"]

    # File that wouldn't be renamed
    original = Path("/tmp/unknown_file.txt")
    result = get_preview_rename(original)

    assert result["original_name"] == "unknown_file.txt"
    assert result["new_name"] == "unknown_file.txt"
    assert result["original_path"] == str(original)
    assert result["new_path"] == str(original.parent / "unknown_file.txt")

    # Test with custom name and season/episode
    original = Path("/tmp/Wrong.Show.S01E05.mp4")
    result = get_preview_rename(
        original, name="Correct Show", season=2, episode=10, title="Better Title"
    )

    assert "Correct.Show.S02E10.Better.Title.mp4" in result["new_name"]

    # Test with multi-episode
    original = Path("/tmp/Show.S01E01E02.mp4")
    result = get_preview_rename(original)

    assert "S01E01-E02" in result["new_name"]

    # Test with multi-episode and custom episodes
    original = Path("/tmp/Show.S01E01.mp4")
    result = get_preview_rename(original, episode=[1, 2, 3], title="Triple Episode")

    assert "S01E01-E03.Triple.Episode" in result["new_name"]

    # Test with concatenated
    original = Path("/tmp/Show.S01E01.mp4")
    result = get_preview_rename(original, episode=[1, 3, 5], concatenated=True)

    assert "S01E01+E03+E05" in result["new_name"]
