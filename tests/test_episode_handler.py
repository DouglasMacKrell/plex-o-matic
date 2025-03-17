"""Tests for the episode handling utilities."""

import pytest
from pathlib import Path
from plexomatic.utils.episode_handler import (
    detect_multi_episodes,
    parse_episode_range,
    format_multi_episode_filename,
    detect_special_episodes,
    organize_season_pack,
)


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
        assert filename == "Show.S01E01-E02.Title.mp4"

        # With multiple episodes
        filename = format_multi_episode_filename("Show", 1, [5, 6, 7], None, ".mp4")
        assert filename == "Show.S01E05-E07.mp4"

        # Single episode should use standard format
        filename = format_multi_episode_filename("Show", 1, [5], "Title", ".mp4")
        assert filename == "Show.S01E05.Title.mp4"

        # Empty episode list (should raise error)
        with pytest.raises(ValueError):
            format_multi_episode_filename("Show", 1, [], "Title", ".mp4")

        # Non-sequential episodes
        filename = format_multi_episode_filename(
            "Show", 1, [1, 3, 5], "Title", ".mp4", concatenated=True
        )
        assert filename == "Show.S01E01+E03+E05.Title.mp4"

        # Sanitize show name and title
        filename = format_multi_episode_filename(
            "Show: The Beginning", 1, [1, 2], "Title: Part 1", ".mp4"
        )
        assert "Show_.The.Beginning" in filename
        assert "Title_.Part.1" in filename


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
