"""Tests for the episode parser module."""

import pytest
from plexomatic.utils.episode.parser import (
    extract_show_info,
    detect_multi_episodes,
    parse_episode_range,
    are_sequential,
    detect_special_episodes,
    is_tv_show,
    split_title_by_separators,
)


@pytest.mark.parametrize(
    "filename, expected_show, expected_season, expected_episode, expected_title, expected_extension",
    [
        ("Show Name S01E02 Episode Title.mp4", "Show Name", 1, 2, "Episode Title", ".mp4"),
        ("Show.Name.S01E02.Episode.Title.mp4", "Show Name", 1, 2, "Episode Title", ".mp4"),
        ("Show-Name-S01E02-Episode-Title.mp4", "Show Name", 1, 2, "Episode Title", ".mp4"),
        ("Show Name 1x02 Episode Title.mp4", "Show Name", 1, 2, "Episode Title", ".mp4"),
        ("Show Name - S01E02 - Episode Title.mp4", "Show Name", 1, 2, "Episode Title", ".mp4"),
    ],
)
def test_extract_show_info_valid(
    filename, expected_show, expected_season, expected_episode, expected_title, expected_extension
):
    """Test extracting show info from valid filenames."""
    info = extract_show_info(filename)
    assert info["show_name"] == expected_show
    assert info["season"] == expected_season
    assert info["episode"] == expected_episode
    assert info["title"] == expected_title
    assert info["extension"] == expected_extension


@pytest.mark.parametrize(
    "filename, expected_multi_episodes",
    [
        ("Show Name S01E01E02 Episode Title.mp4", [1, 2]),
        ("Show Name S01E01-E02 Episode Title.mp4", [1, 2]),
    ],
)
def test_extract_show_info_with_multi_episodes(filename, expected_multi_episodes):
    """Test extracting show info with multi-episode detection."""
    info = extract_show_info(filename)
    assert info["show_name"] == "Show Name"
    assert info["season"] == 1
    assert info["episode"] == 1
    assert info["title"] == "Episode Title"
    assert info["extension"] == ".mp4"
    assert "multi_episodes" in info
    assert info["multi_episodes"] == expected_multi_episodes


@pytest.mark.parametrize(
    "filename",
    [
        "Not a TV show file.mp4",
        "",
    ],
)
def test_extract_show_info_invalid(filename):
    """Test extracting show info from invalid filenames."""
    info = extract_show_info(filename)
    assert info is None


@pytest.mark.parametrize(
    "filename, expected_episodes",
    [
        ("Show.Name.S01E01E02E03.mp4", [1, 2, 3]),
        ("Show.Name.S01E01-E03.mp4", [1, 2, 3]),
        ("Show.Name.S01E01-03.mp4", [1, 2, 3]),
        ("Show.Name.1x01-03.mp4", [1, 2, 3]),
        ("Show.Name.S01E01 E02 E03.mp4", [1, 2, 3]),
        ("Show.Name.S01E01 to E03.mp4", [1, 2, 3]),
        ("Show.Name.S01E01 & E03.mp4", [1, 3]),
        ("Show.Name.S01E01 + E03.mp4", [1, 3]),
        ("Show.Name.S01E01-E03E05E07-E09.mp4", [1, 2, 3, 5, 7, 8, 9]),
        ("Show.Name.S01E01.mp4", [1]),
        ("Not a TV show.mp4", []),
    ],
)
def test_detect_multi_episodes(filename, expected_episodes):
    """Test detecting multi-episodes in filenames."""
    assert detect_multi_episodes(filename) == expected_episodes


@pytest.mark.parametrize(
    "start, end, expected",
    [
        (1, 3, [1, 2, 3]),
        (5, 5, [5]),
        (1, 20, list(range(1, 21))),
    ],
)
def test_parse_episode_range_valid(start, end, expected):
    """Test parsing valid episode ranges."""
    assert parse_episode_range(start, end) == expected


@pytest.mark.parametrize(
    "start, end, error_type",
    [
        (3, 1, ValueError),  # End before start
        (0, 5, ValueError),  # Start not positive
        (5, 0, ValueError),  # End not positive
    ],
)
def test_parse_episode_range_invalid(start, end, error_type):
    """Test parsing invalid episode ranges."""
    with pytest.raises(error_type):
        parse_episode_range(start, end)


@pytest.mark.parametrize(
    "numbers, expected",
    [
        ([1, 2, 3, 4], True),
        ([5, 6, 7], True),
        ([10], True),
        ([], True),  # Empty list is considered sequential by convention
        ([1, 3, 5], False),
        ([1, 2, 4], False),
        ([5, 4, 3], False),
    ],
)
def test_are_sequential(numbers, expected):
    """Test checking if numbers are sequential."""
    assert are_sequential(numbers) == expected


@pytest.mark.parametrize(
    "filename, expected_type, expected_number",
    [
        ("Show.Name.S00E01.Special.Name.mp4", "special", 1),
        ("Show.Name.Special.02.mp4", "special", 2),
        ("Show.Name.OVA.03.mp4", "ova", 3),
        ("Show.Name.Movie.01.mp4", "movie", 1),
        ("Show.Name.Film.02.mp4", "movie", 2),
    ],
)
def test_detect_special_episodes(filename, expected_type, expected_number):
    """Test detecting special episodes."""
    special = detect_special_episodes(filename)
    assert special["type"] == expected_type
    assert special["number"] == expected_number


def test_detect_special_episodes_none():
    """Test detecting special episodes when none exist."""
    assert detect_special_episodes("Show.Name.S01E01.mp4") is None


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("Show.Name.S01E01.mp4", True),
        ("Show.Name.S1E1.mp4", True),
        ("Show_Name_S01E01.mp4", True),
        ("Show-Name-S01E01.mp4", True),
        ("Show Name S01E01.mp4", True),
        ("Show.Name.S01E01E02.mp4", True),
        ("Movie.Name.2023.mp4", False),
        ("Not a TV show.mp4", False),
        ("S01.mp4", False),
        ("E01.mp4", False),
    ],
)
def test_is_tv_show(filename, expected):
    """Test checking if a filename represents a TV show."""
    assert is_tv_show(filename) == expected


@pytest.mark.parametrize(
    "title, expected_segments",
    [
        ("First Segment & Second Segment", ["First Segment", "Second Segment"]),
        ("First Segment, Second Segment", ["First Segment", "Second Segment"]),
        ("First Segment + Second Segment", ["First Segment", "Second Segment"]),
        ("First Segment - Second Segment", ["First Segment", "Second Segment"]),
        ("First Segment and Second Segment", ["First Segment", "Second Segment"]),
        (
            "First Segment & Second Segment - Third Segment",
            ["First Segment", "Second Segment", "Third Segment"],
        ),
        ("Single Segment", ["Single Segment"]),
        ("", []),
    ],
)
def test_split_title_by_separators(title, expected_segments):
    """Test splitting titles by separators."""
    assert split_title_by_separators(title) == expected_segments
