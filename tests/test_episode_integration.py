"""Integration tests for the episode handling and name utils."""

import pytest
from pathlib import Path
from plexomatic.utils.name_utils import extract_show_info, generate_tv_filename, get_preview_rename
from plexomatic.utils.episode_handler import (
    detect_multi_episodes,
    detect_special_episodes,
    organize_season_pack,
)


class TestEpisodeIntegration:
    """Test class for integration between episode handler and name utils."""

    def test_extract_and_detect_integration(self):
        """Test that extract_show_info and detect_multi_episodes work together."""
        # Standard TV show filename
        filename = "Show.S01E01.Title.mp4"
        show_info = extract_show_info(filename)
        assert show_info.get("show_name") == "Show"
        assert show_info.get("season") == "01"
        assert show_info.get("episode") == "01"

        # Should detect as a single episode
        episodes = detect_multi_episodes(filename)
        assert episodes == [1]

        # Multi-episode filename
        filename = "Show.S01E01E02.Title.mp4"
        episodes = detect_multi_episodes(filename)
        assert episodes == [1, 2]

        # Special episode
        filename = "Show.S00E01.Special.mp4"
        special_info = detect_special_episodes(filename)
        assert special_info is not None
        assert special_info["type"] == "special"
        assert special_info["number"] == 1

    def test_generate_tv_filename_with_multi_episode(self):
        """Test generating filenames for multi-episode files."""
        # Generate filename for single episode
        filename = generate_tv_filename("Show Name", 1, 5, "Episode Title")
        assert filename == "Show.Name.S01E05.Episode.Title.mp4"

        # Generate filename for multi-episode (sequential)
        filename = generate_tv_filename("Show Name", 1, [5, 6, 7], "Multi Episode")
        assert filename == "Show.Name.S01E05-E07.Multi.Episode.mp4"

        # Generate filename for multi-episode (non-sequential)
        filename = generate_tv_filename(
            "Show Name", 1, [1, 3, 5], "Multi Episode", concatenated=True
        )
        assert "S01E01+E03+E05" in filename

        # Special characters in title
        filename = generate_tv_filename("Show: A Story", 1, [1, 2], "Episode: Part 1")
        assert "Show_.A.Story" in filename
        assert "Episode_.Part.1" in filename

    def test_preview_rename_with_multi_episode(self):
        """Test preview rename functionality with multi-episode files."""
        # Create a path with a multi-episode filename
        path = Path("/test/Some.Show.S01E01E02E03.mp4")

        # Generate a preview rename
        result = get_preview_rename(path, "New Show", 1, [1, 2, 3], "Triple Episode")

        # Verify the preview shows correct information
        assert "New.Show.S01E01-E03.Triple.Episode.mp4" in result["new_name"]
        assert "/test/New.Show.S01E01-E03.Triple.Episode.mp4" in result["new_path"]
