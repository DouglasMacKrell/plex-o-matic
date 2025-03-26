import pytest
from unittest.mock import patch
import os
import sys

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from plexomatic.utils.episode.parser import extract_show_info
from plexomatic.utils.episode.processor import split_title_by_separators, match_episode_titles_with_data


@pytest.mark.parametrize("filename, expected_show, expected_season, expected_episode, expected_title", [
    (
        "Show Name S01E02 Episode Title.mkv",
        "Show Name", 1, 2, "Episode Title"
    ),
    (
        "Show Name - S01E02 - Episode Title.mkv",
        "Show Name", 1, 2, "Episode Title"
    ),
    (
        "Show Name 1x02 Episode Title.mkv",
        "Show Name", 1, 2, "Episode Title"
    ),
])
def test_extract_show_info(filename, expected_show, expected_season, expected_episode, expected_title):
    """Test extracting show information from various filename formats."""
    info = extract_show_info(filename)
    assert info.get("show_name") == expected_show
    assert info.get("season") == expected_season
    assert info.get("episode") == expected_episode
    assert info.get("title") == expected_title


def test_extract_show_info_no_match():
    """Test extracting show info from a non-matching filename."""
    info = extract_show_info("Not a show episode.mkv")
    assert info == {}


@pytest.mark.parametrize("title, expected_segments", [
    (
        "Segment 1 & Segment 2 & Segment 3",
        ["Segment 1", "Segment 2", "Segment 3"]
    ),
    (
        "Segment 1, Segment 2, Segment 3",
        ["Segment 1", "Segment 2", "Segment 3"]
    ),
    (
        "Segment 1 + Segment 2 + Segment 3",
        ["Segment 1", "Segment 2", "Segment 3"]
    ),
    (
        "Segment 1 - Segment 2 - Segment 3",
        ["Segment 1", "Segment 2", "Segment 3"]
    ),
    (
        "Segment 1 and Segment 2 and Segment 3",
        ["Segment 1", "Segment 2", "Segment 3"]
    ),
    (
        "Single Segment",
        ["Single Segment"]
    ),
    (
        "First Segment Second Segment Third Segment",
        ["First Segment Second Segment Third Segment"]
    ),
])
def test_split_title_by_separators(title, expected_segments):
    """Test splitting titles by various separators."""
    segments = split_title_by_separators(title)
    assert segments == expected_segments


def test_match_episode_titles_with_data_exact_matches():
    """Test matching episode titles with exact matches in API data."""
    segments = ["Segment 1", "Segment 2", "Segment 3"]
    api_data = [
        {"name": "Segment 1", "episode_number": 1},
        {"name": "Segment 2", "episode_number": 2},
        {"name": "Segment 3", "episode_number": 3},
        {"name": "Segment 4", "episode_number": 4},
    ]

    result = match_episode_titles_with_data(segments, api_data)
    assert result == {"Segment 1": 1, "Segment 2": 2, "Segment 3": 3}


def test_match_episode_titles_with_data_partial_matches():
    """Test matching episode titles with partial matches in API data."""
    segments = ["First Segment", "Second Part", "Third Thing"]
    api_data = [
        {"name": "The First Segment", "episode_number": 1},
        {"name": "A Second Part", "episode_number": 2},
        {"name": "Some Third Thing", "episode_number": 3},
    ]

    result = match_episode_titles_with_data(segments, api_data)
    assert len(result) == 3
    assert result["First Segment"] == 1
    assert result["Second Part"] == 2
    assert result["Third Thing"] == 3


def test_match_episode_titles_with_data_empty_data():
    """Test matching episode titles with empty API data."""
    segments = ["Segment 1", "Segment 2"]
    api_data = []

    result = match_episode_titles_with_data(segments, api_data)
    assert result == {}


def test_match_episode_titles_with_data_empty_segments():
    """Test matching empty segments with API data."""
    segments = []
    api_data = [{"name": "Segment 1", "episode_number": 1}]

    result = match_episode_titles_with_data(segments, api_data)
    assert result == {}

# TODO: Implement proper tests for the following functions when mocking issues are resolved:
# - detect_segments
# - preprocess_anthology_episodes
# - fetch_season_episodes
