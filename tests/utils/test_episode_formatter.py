"""Tests for the episode formatter module."""

import pytest
import os
from plexomatic.utils.episode.formatter import (
    sanitize_filename,
    format_show_name,
    format_episode_numbers,
    format_episode_title,
    format_multi_episode_title,
    format_filename,
    format_multi_episode_filename,
    construct_episode_path,
)


@pytest.mark.parametrize(
    "input_filename, expected",
    [
        ("Show Name: The Return?", "Show Name The Return"),
        ('File/With\\Bad:"Chars', "FileWithBadChars"),
        ("Trailing Spaces  . ", "Trailing Spaces"),
        ("ValidFileName", "ValidFileName"),
    ],
)
def test_sanitize_filename(input_filename, expected):
    """Test sanitizing filenames by removing invalid characters."""
    assert sanitize_filename(input_filename) == expected


@pytest.mark.parametrize(
    "show_name, style, expected",
    [
        ("Show Name", "dots", "ShowName"),
        ("The Walking Dead", "dots", "TheWalkingDead"),
        ("Show-Name", "spaces", "Show Name"),
        ("The.Walking.Dead", "spaces", "The Walking Dead"),
        ("Show:Name!", "mixed", "Show Name"),
    ],
)
def test_format_show_name(show_name, style, expected):
    """Test formatting show names with different styles."""
    assert format_show_name(show_name, style) == expected


@pytest.mark.parametrize(
    "episodes, season, expected",
    [
        ([5], 2, "S02E05"),
        ([1, 2, 3], 1, "S01E01-E03"),
        ([1, 3, 5], 1, "S01E01E03E05"),
        ([], 1, "S01E00"),
        ([3, 1, 2], 1, "S01E01-E03"),
    ],
)
def test_format_episode_numbers(episodes, season, expected):
    """Test formatting episode numbers."""
    assert format_episode_numbers(episodes, season) == expected


@pytest.mark.parametrize(
    "title, style, expected",
    [
        ("Episode Title", "dots", "Episode.Title"),
        ('Special: "The Return"', "dots", "Special.The.Return"),
        ("Episode-Title", "spaces", "Episode Title"),
        ('Special: "The Return"', "spaces", "Special The Return"),
        ("Special: The Return", "mixed", "Special The Return"),
        ("", "spaces", ""),
        (None, "spaces", ""),
    ],
)
def test_format_episode_title(title, style, expected):
    """Test formatting episode titles."""
    assert format_episode_title(title, style) == expected


@pytest.mark.parametrize(
    "segments, style, expected",
    [
        (
            ["First Segment", "Second Segment", "Third Segment"],
            "dots",
            "First.Segment.Second.Segment.Third.Segment",
        ),
        (
            ["First Segment", "Second Segment", "Third Segment"],
            "spaces",
            "First Segment - Second Segment - Third Segment",
        ),
        ([], "spaces", ""),
        (["Single Segment"], "spaces", "Single Segment"),
    ],
)
def test_format_multi_episode_title(segments, style, expected):
    """Test formatting titles for multi-episode files."""
    assert format_multi_episode_title(segments, style) == expected


@pytest.mark.parametrize(
    "show_name, season, episodes, title, extension, style, expected",
    [
        ("Show Name", 1, [5], "Episode Title", ".mp4", "dots", "ShowName.S01E05.Episode.Title.mp4"),
        (
            "Show Name",
            1,
            [5],
            "Episode Title",
            ".mp4",
            "spaces",
            "Show Name S01E05 Episode Title.mp4",
        ),
        (
            "Show Name",
            1,
            [1, 2, 3],
            "Multi Episode",
            ".mkv",
            "spaces",
            "Show Name S01E01-E03 Multi Episode.mkv",
        ),
        ("Show Name", 1, [5], None, ".mp4", "spaces", "Show Name S01E05.mp4"),
        ("Show Name", 1, [], "No Episodes", ".mp4", "spaces", "Show Name S01E00 No Episodes.mp4"),
    ],
)
def test_format_filename(show_name, season, episodes, title, extension, style, expected):
    """Test formatting complete filenames."""
    assert format_filename(show_name, season, episodes, title, extension, style) == expected


@pytest.mark.parametrize(
    "show_name, season, episodes, titles, extension, style, concatenated, expected",
    [
        (
            "Show Name",
            1,
            [1, 2, 3],
            ["First Episode", "Second Episode", "Third Episode"],
            ".mp4",
            "spaces",
            True,
            "Show Name S01E01-E03 First Episode - Second Episode - Third Episode.mp4",
        ),
        (
            "Show Name",
            1,
            [1, 2, 3],
            ["First Episode", "Second Episode", "Third Episode"],
            ".mp4",
            "spaces",
            False,
            "Show Name S01E01 First Episode - Second Episode - Third Episode.mp4",
        ),
        (
            "Show Name",
            1,
            [1, 2, 3],
            "Combined Episodes",
            ".mp4",
            "dots",
            True,
            "ShowName.S01E01-E03.Combined.Episodes.mp4",
        ),
        ("Show Name", 1, [1, 2, 3], None, ".mp4", "spaces", True, "Show Name S01E01-E03.mp4"),
    ],
)
def test_format_multi_episode_filename(
    show_name, season, episodes, titles, extension, style, concatenated, expected
):
    """Test formatting filenames for multi-episode files."""
    assert (
        format_multi_episode_filename(
            show_name, season, episodes, titles, extension, style, concatenated
        )
        == expected
    )


def test_construct_episode_path_basic():
    """Test basic episode path construction."""
    expected_path = os.path.join("Show Name", "Season 01", "Show Name S01E05 Episode Title.mp4")
    assert construct_episode_path("Show Name", 1, [5], "Episode Title") == expected_path


def test_construct_episode_path_with_base_dir():
    """Test episode path construction with a base directory."""
    base_dir = "/media/tv"
    expected_path = os.path.join(
        base_dir, "Show Name", "Season 01", "Show Name S01E05 Episode Title.mp4"
    )
    assert construct_episode_path("Show Name", 1, [5], "Episode Title", base_dir) == expected_path


def test_construct_episode_path_with_style():
    """Test episode path construction with a different style."""
    expected_path = os.path.join("Show Name", "Season 01", "ShowName.S01E05.Episode.Title.mp4")
    assert (
        construct_episode_path("Show Name", 1, [5], "Episode Title", style="dots") == expected_path
    )
