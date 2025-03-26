"""Tests for the episode handling utilities."""

import re
import os
import sys
import pytest
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from the new module structure
from plexomatic.utils.episode import (
    extract_show_info,
    detect_multi_episodes,
    parse_episode_range,
    are_sequential,
    detect_special_episodes,
    split_title_by_separators,
    format_show_name,
    format_episode_title,
    sanitize_filename,
    format_new_name,
    format_episode_filename,
    is_anthology_episode,
    get_segment_count,
    detect_season_finale,
    detect_season_premiere,
    is_multi_part_episode,
    get_episode_type,
    process_anthology_episode,
    detect_segments_with_llm,
    match_episode_titles,
    process_episode,
)

# These functions haven't been moved to the new structure yet
# Import them directly from episode_handler until they are migrated
from plexomatic.utils.episode.formatter import format_multi_episode_filename
from plexomatic.utils.episode.processor import organize_season_pack


class TestMultiEpisodeDetection:
    """Test class for multi-episode detection functionalities."""

    def test_detect_multi_episodes_standard_format(self) -> None:
        """Test detection of multi-episodes in standard format (S01E01E02)."""
        # Standard multi-episode format
        assert detect_multi_episodes("Show.S01E01E02.mp4") == [1, 2]
        assert detect_multi_episodes("Show.S01E05E06E07.mp4") == [5, 6, 7]

        # Hyphen format
        assert detect_multi_episodes("Show.S01E01-E02.mp4") == [1, 2]
        assert detect_multi_episodes("Show.S01E05-E07.mp4") == [5, 6, 7]

        # Single episode (should return a list with one episode)
        assert detect_multi_episodes("Show.S01E01.mp4") == [1]

        # No episode found
        assert detect_multi_episodes("Show.2020.mp4") == []

    def test_detect_multi_episodes_alternative_formats(self) -> None:
        """Test detection of multi-episodes in alternative formats."""
        # Space separator format
        assert detect_multi_episodes("Show S01E01 E02.mp4") == [1, 2]

        # Multiple episodes with spaces
        assert detect_multi_episodes("Show S01 E01 E02.mp4") == [1, 2]

        # Dash format with no E
        assert detect_multi_episodes("Show.S01E01-02.mp4") == [1, 2]

        # x format (common in anime)
        assert detect_multi_episodes("Show 01x02-03.mp4") == [2, 3]

        # Episode range with "to" text
        assert detect_multi_episodes("Show S01E05 to E07.mp4") == [5, 6, 7]

        # Episode range with "&" text
        assert detect_multi_episodes("Show S01E05 & E06.mp4") == [5, 6]

        # Episode range with "+" text
        assert detect_multi_episodes("Show S01E05+E06.mp4") == [5, 6]

        # Episodes separated by comma
        assert detect_multi_episodes("Show S01E05,E06.mp4") == [5, 6]

    def test_parse_episode_range(self) -> None:
        """Test parsing of episode ranges."""
        # Simple range
        assert parse_episode_range(1, 3) == [1, 2, 3]

        # Same start and end (single episode)
        assert parse_episode_range(5, 5) == [5]

        # Invalid range (end < start)
        with pytest.raises(ValueError):
            parse_episode_range(5, 3)

        # Large range (should be limited)
        assert len(parse_episode_range(1, 50)) <= 20

        # Zero or negative values
        with pytest.raises(ValueError):
            parse_episode_range(0, 5)
        with pytest.raises(ValueError):
            parse_episode_range(-1, 5)
        with pytest.raises(ValueError):
            parse_episode_range(1, -5)

    def test_format_multi_episode_filename(self) -> None:
        """Test formatting of multi-episode filenames."""
        # Standard multi-episode format
        filename = format_multi_episode_filename("Show", 1, [1, 2], "Title", ".mp4")
        assert filename == "Show S01E01-E02 Title.mp4"

        # With multiple episodes
        filename = format_multi_episode_filename("Show", 1, [5, 6, 7], None, ".mp4")
        assert filename == "Show S01E05-E07.mp4"

        # Single episode should use standard format
        filename = format_multi_episode_filename("Show", 1, [5], "Title", ".mp4")
        assert filename == "Show S01E05 Title.mp4"

        # Empty episode list (should raise error)
        with pytest.raises(ValueError):
            format_multi_episode_filename("Show", 1, [], "Title", ".mp4")

        # Test with dots style explicitly
        filename = format_multi_episode_filename("Show", 1, [1, 2], "Title", ".mp4", style="dots")
        assert filename == "Show.S01E01-E02.Title.mp4"

        # Sanitize show name and title - this is a special test case that uses underscores
        filename = format_multi_episode_filename(
            "Show: The Beginning", 1, [1, 2], "Title: Part 1", ".mp4"
        )
        assert "Show_" in filename
        assert "Title_" in filename


class TestSpecialEpisodeHandling:
    """Test class for special episode detection and handling."""

    def test_detect_special_episodes(self) -> None:
        """Test detection of special episodes."""
        # Standard special episode markers
        assert detect_special_episodes("Show.S00E01.Special.mp4") == {
            "type": "special",
            "number": 1,
        }
        assert detect_special_episodes("Show.Special.mp4") == {"type": "special", "number": None}
        assert detect_special_episodes("Show.OVA.mp4") == {"type": "ova", "number": None}
        assert detect_special_episodes("Show.OVA1.mp4") == {"type": "ova", "number": 1}
        assert detect_special_episodes("Show.OVA.1.mp4") == {"type": "ova", "number": 1}

        # Movie/Film special
        assert detect_special_episodes("Show.Movie.mp4") == {"type": "movie", "number": None}
        assert detect_special_episodes("Show.Film.mp4") == {"type": "movie", "number": None}
        assert detect_special_episodes("Show.Movie.1.mp4") == {"type": "movie", "number": 1}

        # Not a special episode
        assert detect_special_episodes("Show.S01E01.mp4") is None
        assert detect_special_episodes("Show.2020.mp4") is None


class TestSeasonPackOrganization:
    """Test class for season pack organization functionality."""

    def test_organize_season_pack(self) -> None:
        """Test organizing files from a season pack."""
        # Create a list of paths for testing
        files = [
            Path("/test/Show.S01E01.mp4"),
            Path("/test/Show.S01E02.mp4"),
            Path("/test/Show.S01E03.mp4"),
            Path("/test/Show.S02E01.mp4"),
            Path("/test/Show.Special.mp4"),
            Path("/test/extras/Behind.The.Scenes.mp4"),
        ]

        # Organize by season
        result = organize_season_pack(files)

        # Season folders should be created
        assert "Season 1" in result
        assert "Season 2" in result
        assert "Specials" in result

        # Files should be organized by season
        assert len(result["Season 1"]) == 3
        assert len(result["Season 2"]) == 1
        assert len(result["Specials"]) == 1

        # Unknown files should be in the Unknown category
        assert "Unknown" in result
        assert len(result["Unknown"]) == 1


class TestAnthologyEpisodeHandling:
    """Test class for anthology episode handling functionality."""

    def test_process_anthology_episode_disabled(self) -> None:
        """Test process_anthology_episode when anthology mode is disabled."""
        filename = "Chip N Dale Park Life-S01E01-Thou Shall Nut Steal The Baby Whisperer It Takes Two To Tangle.mp4"
        result = process_anthology_episode(filename, anthology_mode=False)

        # Should just detect the episode number without splitting
        assert result["episode_numbers"] == [1]
        assert result["segments"] == []

    def test_process_anthology_episode_enabled(self) -> None:
        """Test process_anthology_episode when anthology mode is enabled."""
        filename = "Chip N Dale Park Life-S01E01-Thou Shall Nut Steal The Baby Whisperer It Takes Two To Tangle.mp4"
        result = process_anthology_episode(filename, anthology_mode=True)

        # Should detect multiple segments and assign sequential episode numbers
        assert result["episode_numbers"] == [1, 2, 3]
        assert len(result["segments"]) == 3
        assert "Thou Shall Nut Steal" in result["segments"]
        assert "The Baby Whisperer" in result["segments"]
        assert "It Takes Two To Tangle" in result["segments"]

    def test_process_anthology_episode_with_ampersand(self) -> None:
        """Test process_anthology_episode with ampersand-separated titles."""
        filename = "Show-S01E01-First Segment & Second Segment & Third Segment.mp4"
        result = process_anthology_episode(filename, anthology_mode=True)

        assert result["episode_numbers"] == [1, 2, 3]
        assert len(result["segments"]) == 3
        assert "First Segment" in result["segments"]
        assert "Second Segment" in result["segments"]
        assert "Third Segment" in result["segments"]

    def test_process_anthology_episode_with_comma(self) -> None:
        """Test process_anthology_episode with comma-separated titles."""
        filename = "Show-S01E01-First Segment, Second Segment, Third Segment.mp4"
        result = process_anthology_episode(filename, anthology_mode=True)

        assert result["episode_numbers"] == [1, 2, 3]
        assert len(result["segments"]) == 3
        assert "First Segment" in result["segments"]
        assert "Second Segment" in result["segments"]
        assert "Third Segment" in result["segments"]

    def test_process_anthology_episode_with_plus(self) -> None:
        """Test process_anthology_episode with plus-separated titles."""
        filename = "Show-S01E01-First Segment + Second Segment + Third Segment.mp4"
        result = process_anthology_episode(filename, anthology_mode=True)

        assert result["episode_numbers"] == [1, 2, 3]
        assert len(result["segments"]) == 3
        assert "First Segment" in result["segments"]
        assert "Second Segment" in result["segments"]
        assert "Third Segment" in result["segments"]

    def test_process_anthology_episode_with_dash(self) -> None:
        """Test process_anthology_episode with dash-separated titles."""
        filename = "Show-S01E01-First Segment-Second Segment-Third Segment.mp4"
        result = process_anthology_episode(filename, anthology_mode=True)

        assert result["episode_numbers"] == [1, 2, 3]
        assert len(result["segments"]) == 3
        assert "First Segment" in result["segments"]
        assert "Second Segment" in result["segments"]
        assert "Third Segment" in result["segments"]

    @pytest.mark.skip("Requires TVDB API key for testing")
    def test_match_episode_titles(self) -> None:
        """Test matching segment titles against official episode listings."""
        segment_titles = ["Segment One", "Segment Two", "Segment Three"]
        matches = match_episode_titles(segment_titles, "12345", 1)

        assert len(matches) == 3
        assert "Segment One" in matches
        assert "Segment Two" in matches
        assert "Segment Three" in matches

    def test_universal_anthology_formatting(self) -> None:
        """Test that anthology episode handling works universally for different show names."""
        # Test various show names with anthology episodes
        test_cases = [
            {
                "filename": "Rick N Morty-S01E01-Pilot The Wedding Squanchers.mp4",
                "expected_segments": ["Pilot", "The Wedding Squanchers"],
                "expected_episode_numbers": [1, 2],
            },
            {
                "filename": "Love Death And Robots-S01E01-Three Robots The Witness Beyond The Aquila Rift.mp4",
                "expected_segments": ["Three Robots", "The Witness Beyond", "The Aquila Rift"],
                "expected_episode_numbers": [1, 2, 3],
            },
            {
                "filename": "SomeShow-S01E01-First Story & Second Part & Third Chapter.mp4",
                "expected_segments": ["First Story", "Second Part", "Third Chapter"],
                "expected_episode_numbers": [1, 2, 3],
            },
        ]

        for test_case in test_cases:
            result = process_anthology_episode(test_case["filename"], anthology_mode=True)

            # Verify the segments match what we expect
            assert len(result["segments"]) == len(test_case["expected_segments"])
            for expected_segment in test_case["expected_segments"]:
                assert (
                    expected_segment in result["segments"]
                ), f"Expected segment '{expected_segment}' not found in result: {result['segments']}"

            # Verify episode numbers match what we expect
            assert result["episode_numbers"] == test_case["expected_episode_numbers"]

    @pytest.mark.skip("Requires LLM model for testing")
    def test_process_anthology_episode_with_llm(self) -> None:
        """Test that processing with anthology mode and LLM assistance works."""
        # This test will be skipped if LLM is not available
        try:
            from plexomatic.api.llm_client import LLMClient

            client = LLMClient()
            if not client.check_model_available():
                pytest.skip("LLM model not available for testing")

            # Test a file with multiple segments
            filename = "Chip n Dale Park Life-S02E17-Hamster Paradise Puppy Papas The Adorables.mp4"
            result = process_anthology_episode(filename, anthology_mode=True, use_llm=True)

            # Verify that we get multiple segments
            assert len(result["segments"]) > 1
            assert len(result["episode_numbers"]) == len(result["segments"])

            # Check that segments start with the expected titles
            segments = result["segments"]
            segment_starts = ["Hamster Paradise", "Puppy Papas", "The Adorables"]

            # Check each segment contains its expected title component
            for i, start in enumerate(segment_starts):
                if i < len(segments):
                    assert start in segments[i]

        except ImportError:
            pytest.skip("LLM client not available")

    @pytest.mark.skip("Requires LLM model for testing")
    def test_detect_segments_with_llm(self) -> None:
        """Test the LLM-based segment detection function."""
        # This test will be skipped if LLM is not available
        try:
            from plexomatic.api.llm_client import LLMClient

            client = LLMClient()
            if not client.check_model_available():
                pytest.skip("LLM model not available for testing")

            # Test with a clear multi-segment title
            title_part = "Hamster Paradise Puppy Papas The Adorables"
            segments = detect_segments_with_llm(title_part, 1)

            # Verify we get segments back
            assert isinstance(segments, list)
            assert len(segments) > 1

            # Check for expected segment names
            segment_keywords = ["Hamster", "Puppy", "Adorables"]
            for keyword in segment_keywords:
                found = False
                for segment in segments:
                    if keyword in segment:
                        found = True
                        break
                assert found, f"Segment containing '{keyword}' not found"

        except ImportError:
            pytest.skip("LLM client not available")
