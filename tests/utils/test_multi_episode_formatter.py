"""Tests for the multi_episode_formatter module."""

import pytest

from plexomatic.core.constants import MediaType
from plexomatic.utils.name_parser import ParsedMediaName


class TestMultiEpisodeFormatter:
    """Tests for the multi-episode formatter module."""

    def test_ensure_episode_list(self):
        """Test ensuring that episode is a list."""
        from plexomatic.utils.multi_episode_formatter import ensure_episode_list

        # Test with a list
        result = ensure_episode_list([1, 2, 3])
        assert result == [1, 2, 3]

        # Test with a single integer
        result = ensure_episode_list(1)
        assert result == [1]

        # Test with None
        result = ensure_episode_list(None)
        assert result == []

        # Test with non-list, non-integer
        with pytest.raises(TypeError):
            ensure_episode_list("not a list or int")

    def test_format_multi_episode_empty(self):
        """Test formatting an empty episode list."""
        from plexomatic.utils.multi_episode_formatter import format_multi_episode

        result = format_multi_episode([], "E{:02d}")
        assert result == ""

    def test_format_multi_episode_single(self):
        """Test formatting a single episode."""
        from plexomatic.utils.multi_episode_formatter import format_multi_episode

        result = format_multi_episode([1], "E{:02d}")
        assert result == "E01"

    def test_format_multi_episode_sequential(self):
        """Test formatting sequential episodes."""
        from plexomatic.utils.multi_episode_formatter import format_multi_episode

        # Sequential episodes should be formatted as a range
        result = format_multi_episode([1, 2, 3], "E{:02d}")
        assert result == "E01-E03"

    def test_format_multi_episode_non_sequential(self):
        """Test formatting non-sequential episodes."""
        from plexomatic.utils.multi_episode_formatter import format_multi_episode

        # Non-sequential episodes should be comma separated
        result = format_multi_episode([1, 3, 5], "E{:02d}")
        assert result == "E01,E03,E05"

    def test_format_multi_episode_mixed(self):
        """Test formatting episodes with some sequential and some not."""
        from plexomatic.utils.multi_episode_formatter import format_multi_episode

        # Mixed sequential and non-sequential should be formatted appropriately
        result = format_multi_episode([1, 2, 3, 5, 7, 8, 9], "E{:02d}")
        assert result == "E01-E03,E05,E07-E09"

    def test_format_multi_episode_with_skip_range(self):
        """Test formatting episodes with skip_range parameter."""
        from plexomatic.utils.multi_episode_formatter import format_multi_episode

        # When skip_range is True, we should use the first and last episode
        result = format_multi_episode([1, 2, 3, 4, 5], "E{:02d}", skip_range=True)
        assert result == "E01,E02,E03,E04,E05"

        # With non-sequential episodes and skip_range=True
        result = format_multi_episode([1, 3, 5], "E{:02d}", skip_range=True)
        assert result == "E01,E03,E05"

    def test_get_formatted_episodes_single(self):
        """Test getting formatted episodes for a single episode."""
        from plexomatic.utils.multi_episode_formatter import get_formatted_episodes

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            season=1,
            episodes=[2],
            extension=".mp4",
        )

        result = get_formatted_episodes(parsed)
        assert result == "E02"

    def test_get_formatted_episodes_multi(self):
        """Test getting formatted episodes for multiple episodes."""
        from plexomatic.utils.multi_episode_formatter import get_formatted_episodes

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            season=1,
            episodes=[2, 3, 4],
            extension=".mp4",
        )

        result = get_formatted_episodes(parsed)
        assert result == "E02-E04"

    def test_get_formatted_episodes_custom_format(self):
        """Test getting formatted episodes with a custom format."""
        from plexomatic.utils.multi_episode_formatter import get_formatted_episodes

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW,
            title="Test Show",
            season=1,
            episodes=[2, 3, 4],
            extension=".mp4",
        )

        result = get_formatted_episodes(parsed, episode_format="EP{:02d}")
        assert result == "EP02-EP04"

    def test_get_formatted_episodes_none(self):
        """Test getting formatted episodes with no episodes."""
        from plexomatic.utils.multi_episode_formatter import get_formatted_episodes

        parsed = ParsedMediaName(
            media_type=MediaType.TV_SHOW, title="Test Show", season=1, extension=".mp4"
        )

        result = get_formatted_episodes(parsed)
        assert result == ""
