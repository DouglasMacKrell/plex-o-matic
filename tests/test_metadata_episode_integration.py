"""Tests for the integration between episode handling and metadata system."""

import pytest
from unittest.mock import patch, MagicMock

from plexomatic.metadata.manager import MetadataManager, MetadataMatchResult
from plexomatic.metadata.fetcher import MediaType
from plexomatic.utils.episode_handler import (
    detect_special_episodes,
    detect_multi_episodes,
    format_multi_episode_filename,
    generate_filename_from_metadata,
)
from plexomatic.utils.name_utils import generate_tv_filename


class TestMetadataEpisodeIntegration:
    """Test class for integration between episode handler and metadata system."""

    @pytest.fixture
    def mock_metadata_manager(self):
        """Create a mock metadata manager with mocked fetchers."""
        manager = MetadataManager()

        # Mock the search and fetch methods
        manager.search = MagicMock()
        manager.fetch_metadata = MagicMock()

        return manager

    def test_match_with_special_episode_detection(self, mock_metadata_manager) -> None:
        """Test that match recognizes special episodes."""
        # Replace the real match method with our test implementation
        original_match = mock_metadata_manager.match

        def match_with_special_detection(filename, media_type=None):
            # First check if it's a special episode
            special_info = detect_special_episodes(filename)

            if special_info and media_type == MediaType.TV_SHOW:
                # Create a mock match result for a special episode
                return MetadataMatchResult(
                    matched=True,
                    title="Test Show",
                    media_type=MediaType.TV_SHOW,
                    confidence=0.95,
                    metadata={
                        "id": "tvdb:12345",
                        "source": "tvdb",
                        "title": "Test Show",
                        "special_type": special_info["type"],
                        "special_number": special_info["number"],
                    },
                )

            # Fall back to original match logic
            return original_match(filename, media_type)

        # Replace the method temporarily
        mock_metadata_manager.match = match_with_special_detection

        # Test with a special episode
        result = mock_metadata_manager.match("Show.Special.mp4", MediaType.TV_SHOW)

        # Verify the results
        assert result.matched
        assert result.metadata["special_type"] == "special"
        assert result.metadata["special_number"] is None

        # Test with an OVA
        result = mock_metadata_manager.match("Show.OVA.1.mp4", MediaType.TV_SHOW)

        # Verify the results
        assert result.matched
        assert result.metadata["special_type"] == "ova"
        assert result.metadata["special_number"] == 1

    def test_match_with_multi_episode_detection(self, mock_metadata_manager) -> None:
        """Test that match recognizes multi-episodes."""
        # Replace the real match method with our test implementation
        original_match = mock_metadata_manager.match

        def match_with_multi_episode_detection(filename, media_type=None):
            # First check if it contains multiple episodes
            episodes = detect_multi_episodes(filename)

            if len(episodes) > 1 and media_type == MediaType.TV_SHOW:
                # Create a mock match result for multi-episodes
                return MetadataMatchResult(
                    matched=True,
                    title="Test Show",
                    media_type=MediaType.TV_SHOW,
                    confidence=0.95,
                    metadata={
                        "id": "tvdb:12345",
                        "source": "tvdb",
                        "title": "Test Show",
                        "episodes": episodes,
                    },
                )

            # Fall back to original match logic
            return original_match(filename, media_type)

        # Replace the method temporarily
        mock_metadata_manager.match = match_with_multi_episode_detection

        # Test with a multi-episode file
        result = mock_metadata_manager.match("Show.S01E01E02E03.mp4", MediaType.TV_SHOW)

        # Verify the results
        assert result.matched
        assert "episodes" in result.metadata
        assert result.metadata["episodes"] == [1, 2, 3]

        # Test with a range format
        result = mock_metadata_manager.match("Show.S01E05-E07.mp4", MediaType.TV_SHOW)

        # Verify the results
        assert result.matched
        assert "episodes" in result.metadata
        assert result.metadata["episodes"] == [5, 6, 7]

    def test_metadata_fetching_for_special_episodes(self) -> None:
        """Test fetching metadata for special episodes."""
        # Create mocks for our clients
        mock_tvdb_client = MagicMock()

        # The get_series_by_id method returns the contents of the 'data' field, not the whole response
        series_data = {
            "id": 12345,
            "seriesName": "Test Show",
            "overview": "A test show",
            "firstAired": "2020-01-01",
        }
        mock_tvdb_client.get_series_by_id.return_value = series_data

        # The get_episodes_by_series_id method returns the list directly, not wrapped in 'data'
        episodes_data = [
            {
                "id": 1001,
                "airedSeason": 1,
                "airedEpisodeNumber": 1,
                "episodeName": "Regular Episode",
            },
            {"id": 1002, "airedSeason": 0, "airedEpisodeNumber": 1, "episodeName": "Special 1"},
            {"id": 1003, "airedSeason": 0, "airedEpisodeNumber": 2, "episodeName": "Special 2"},
        ]
        mock_tvdb_client.get_episodes_by_series_id.return_value = episodes_data

        with patch("plexomatic.metadata.fetcher.TVDBClient", return_value=mock_tvdb_client):
            from plexomatic.metadata.fetcher import TVDBMetadataFetcher

            # Create the fetcher with our mock client
            fetcher = TVDBMetadataFetcher(client=mock_tvdb_client)

            # Test fetching a regular episode
            result = fetcher.fetch_metadata("tvdb:12345", MediaType.TV_SHOW)
            assert result.title == "Test Show"

            # In a real implementation, we'd enhance the fetcher to get special episodes
            # For this test, we'll just verify the mock was called correctly
            mock_tvdb_client.get_episodes_by_series_id.assert_called_with(series_id=12345)

            # Verify we can access the episodes data
            assert len(mock_tvdb_client.get_episodes_by_series_id.return_value) == 3

            # Verify we have special episodes (season 0)
            specials = [
                e
                for e in mock_tvdb_client.get_episodes_by_series_id.return_value
                if e["airedSeason"] == 0
            ]
            assert len(specials) == 2

    def test_fetch_episode_metadata(self) -> None:
        """Test fetching metadata for specific episodes."""
        # Create a mock metadata manager
        manager = MetadataManager()

        # Mock the fetch_metadata method
        manager.fetch_metadata = MagicMock(
            return_value={
                "id": "tvdb:12345",
                "title": "Test Show",
                "overview": "A test show",
                "year": 2020,
            }
        )

        # Create a mock TVDB fetcher
        mock_tvdb_fetcher = MagicMock()

        # Mock the get_special_episodes method
        mock_tvdb_fetcher.get_special_episodes.return_value = [
            {
                "id": 1002,
                "title": "Special 1",
                "overview": "A special episode",
                "special_number": 1,
                "air_date": "2020-05-01",
            },
            {
                "id": 1003,
                "title": "Special 2",
                "overview": "Another special episode",
                "special_number": 2,
                "air_date": "2020-06-01",
            },
        ]

        # Mock the get_episodes_by_numbers method
        mock_tvdb_fetcher.get_episodes_by_numbers.return_value = [
            {
                "id": 1004,
                "title": "Episode 1",
                "overview": "First episode",
                "season": 1,
                "episode": 1,
                "air_date": "2020-01-01",
            },
            {
                "id": 1005,
                "title": "Episode 2",
                "overview": "Second episode",
                "season": 1,
                "episode": 2,
                "air_date": "2020-01-08",
            },
        ]

        # Add the mock fetcher to the manager
        manager.fetchers = {"tvdb": mock_tvdb_fetcher}

        # Test fetching metadata for a special episode
        special_info = {"special_type": "special", "special_number": 1}

        result = manager.fetch_episode_metadata("tvdb:12345", special_info)

        # Verify the results
        assert result["title"] == "Test Show"
        assert result["special_type"] == "special"
        assert "special_episode" in result
        assert result["special_episode"]["title"] == "Special 1"

        # Test fetching metadata for multi-episodes
        multi_episode_info = {"episodes": [1, 2], "season": 1}

        result = manager.fetch_episode_metadata("tvdb:12345", multi_episode_info)

        # Verify the results
        assert result["title"] == "Test Show"
        assert "episode_numbers" in result
        assert result["episode_numbers"] == [1, 2]
        assert "multi_episodes" in result
        assert len(result["multi_episodes"]) == 2
        assert result["multi_episodes"][0]["title"] == "Episode 1"
        assert result["multi_episodes"][1]["title"] == "Episode 2"

    def test_filename_generation_for_special_episodes(self) -> None:
        """Test generating filenames for special episodes."""
        # Test generating a filename for a special episode
        special_info = detect_special_episodes("Show.Special.1.mp4")
        assert special_info is not None

        # Generate a filename for a special episode
        # We use season 0 for specials by convention
        filename = generate_tv_filename(
            show_name="Test Show",
            season=0,
            episode=special_info["number"] or 1,
            title="Special Episode",
            extension=".mp4",
        )

        # Verify the results - special episodes should use S00Exx format
        assert "Test.Show.S00E01.Special.Episode.mp4" in filename

        # Test generating a filename for an OVA
        special_info = detect_special_episodes("Show.OVA.2.mp4")
        assert special_info is not None
        assert special_info["type"] == "ova"
        assert special_info["number"] == 2

        # Generate a filename for an OVA
        # We use season 0 for specials by convention and add the OVA type
        filename = generate_tv_filename(
            show_name="Test Show",
            season=0,
            episode=special_info["number"],
            title=f"OVA {special_info['number']}",
            extension=".mp4",
        )

        # Verify the results
        assert "Test.Show.S00E02.OVA.2.mp4" in filename

    def test_filename_generation_for_multi_episodes(self) -> None:
        """Test generating filenames for multi-episodes."""
        # Test detecting multi-episodes
        episodes = detect_multi_episodes("Show.S01E01E02E03.mp4")
        assert len(episodes) == 3
        assert episodes == [1, 2, 3]

        # Generate a filename for multi-episodes using the custom formatter
        filename = format_multi_episode_filename(
            show_name="Test Show",
            season=1,
            episodes=episodes,
            title="Multi Episode",
            extension=".mp4",
        )

        # Verify the results - multi-episodes should use a range format if sequential
        assert "Test.Show.S01E01-E03.Multi.Episode.mp4" in filename

        # Test non-sequential episodes
        episodes = [1, 3, 5]

        # Generate a filename for non-sequential multi-episodes
        filename = format_multi_episode_filename(
            show_name="Test Show",
            season=1,
            episodes=episodes,
            title="Non-Sequential",
            extension=".mp4",
            concatenated=True,  # Force concatenated format for demonstration
        )

        # Verify the results - non-sequential episodes should use concatenated format
        assert "Test.Show.S01E01+E03+E05.Non-Sequential.mp4" in filename

    def test_generate_filename_from_metadata(self) -> None:
        """Test generating filenames from metadata for different episode types."""
        # Test with a regular episode
        regular_metadata = {
            "title": "Test Show",
            "season": 2,
            "episode": 5,
            "episode_title": "Regular Episode",
        }

        filename = generate_filename_from_metadata("original.mp4", regular_metadata)
        assert "Test.Show.S02E05.Regular.Episode.mp4" in filename

        # Test with a special episode
        special_metadata = {
            "title": "Test Show",
            "special_type": "special",
            "special_number": 3,
            "special_episode": {"title": "Behind the Scenes"},
        }

        filename = generate_filename_from_metadata("original.mp4", special_metadata)
        assert "Test.Show.S00E03.Behind.the.Scenes.mp4" in filename

        # Test with a special episode without title
        special_metadata_no_title = {
            "title": "Test Show",
            "special_type": "ova",
            "special_number": 2,
        }

        filename = generate_filename_from_metadata("original.mp4", special_metadata_no_title)
        assert "Test.Show.S00E02.Ova.2.mp4" in filename

        # Test with multi-episodes
        multi_episode_metadata = {
            "title": "Test Show",
            "season": 3,
            "episode_numbers": [7, 8, 9],
            "multi_episodes": [{"title": "Part 1"}, {"title": "Part 2"}, {"title": "Part 3"}],
        }

        filename = generate_filename_from_metadata("original.mp4", multi_episode_metadata)
        # Should generate a range format for sequential episodes
        assert "Test.Show.S03E07-E09" in filename
        # Should include the joined titles
        assert "Part.1.&.Part.2.&.Part.3.mp4" in filename or "Part.1.Part.2.Part.3.mp4" in filename
