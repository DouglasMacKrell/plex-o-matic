"""Tests for the episode_detector module."""

import pytest
from pathlib import Path

from plexomatic.utils.episode.episode_detector import (
    is_anthology_episode,
    get_segment_count,
    detect_season_finale,
    detect_season_premiere,
    is_multi_part_episode,
    get_episode_type,
)


@pytest.mark.parametrize("filename,expected", [
    ("Show.S01E01E02.Title.mp4", True),
    ("Show.S01E01E02.Title1.Title2.mp4", True),
    ("Show.S01E01.Title.mp4", False),
    ("Show S01E01-E02 Title.mp4", True),
    ("Show.S01E01-E03.Title.mp4", True),
    ("Show.1x01-03.Title.mp4", True),
])
def test_is_anthology_episode(filename, expected):
    """Test the is_anthology_episode function with various filenames."""
    assert is_anthology_episode(filename) == expected


@pytest.mark.parametrize("filename,expected", [
    ("Show.S01E01E02.Title.mp4", 2),
    ("Show.S01E01E02E03.Title.mp4", 3),
    ("Show.S01E01.Title.mp4", 1),
    ("Show S01E01-E02 Title.mp4", 2),
    ("Show.S01E01-E03.Title.mp4", 3),
])
def test_get_segment_count(filename, expected):
    """Test the get_segment_count function with various filenames."""
    assert get_segment_count(filename) == expected


@pytest.mark.parametrize("filename,expected", [
    ("Show.S01E13.Finale.mp4", True),
    ("Show.S01E13.Season.Finale.mp4", True),
    ("Show.S01E13.Series.Finale.mp4", True),
    ("Show.S01E13.Final.Episode.mp4", True),
    ("Show.S01E12.mp4", False),
    ("Show.S01E13.mp4", False),
])
def test_detect_season_finale(filename, expected):
    """Test the detect_season_finale function with various filenames."""
    assert detect_season_finale(filename) == expected


@pytest.mark.parametrize("filename,expected", [
    ("Show.S01E01.Premiere.mp4", True),
    ("Show.S01E01.Season.Premiere.mp4", True),
    ("Show.S01E01.Series.Premiere.mp4", True),
    ("Show.S01E01.Pilot.mp4", True),
    ("Show.S01E02.mp4", False),
    ("Show.S01E01.mp4", False),
])
def test_detect_season_premiere(filename, expected):
    """Test the detect_season_premiere function with various filenames."""
    assert detect_season_premiere(filename) == expected


@pytest.mark.parametrize("filename,expected", [
    ("Show.S01E01.Part.1.mp4", True),
    ("Show.S01E01.Part.One.mp4", True),
    ("Show.S01E01.Pt.1.mp4", True),
    ("Show.S01E01.Pt.I.mp4", True),
    ("Show.S01E01.Part.1.of.2.mp4", True),
    ("Show.S01E01.(1.of.2).mp4", True),
    ("Show.S01E01.mp4", False),
])
def test_is_multi_part_episode(filename, expected):
    """Test the is_multi_part_episode function with various filenames."""
    assert is_multi_part_episode(filename) == expected


def test_get_episode_type():
    """Test that get_episode_type returns comprehensive information about an episode."""
    # Test a standard episode
    episode_type = get_episode_type("Show.S01E01.mp4")
    assert episode_type["is_anthology"] is False
    assert episode_type["segment_count"] == 1
    assert episode_type["is_premiere"] is False
    assert episode_type["is_finale"] is False
    assert episode_type["is_multi_part"] is False
    
    # Test a complex case
    episode_type = get_episode_type("Show.S01E01E02.Season.Premiere.Part.1.of.2.mp4")
    assert episode_type["is_anthology"] is True
    assert episode_type["segment_count"] == 2
    assert episode_type["is_premiere"] is True
    assert episode_type["is_finale"] is False
    assert episode_type["is_multi_part"] is True 