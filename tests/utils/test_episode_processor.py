"""Tests for the episode processor module."""

from unittest.mock import patch, MagicMock

from plexomatic.utils.episode.processor import (
    process_anthology_episode,
    process_episode,
    determine_episode_type,
    EpisodeType,
)


class TestEpisodeTypeDetection:
    """Tests for episode type detection."""

    def test_determine_episode_type_standard(self) -> None:
        """Test determining standard episode type."""
        file_info = {"show_name": "Show Name", "season": 1, "episode": 1, "title": "Episode Title"}

        episode_type = determine_episode_type(file_info, segments=None)
        assert episode_type == EpisodeType.STANDARD

    def test_determine_episode_type_anthology(self) -> None:
        """Test determining anthology episode type."""
        file_info = {"show_name": "Show Name", "season": 1, "episode": 1, "title": "Episode Title"}

        segments = ["Segment 1", "Segment 2", "Segment 3"]
        episode_type = determine_episode_type(file_info, segments=segments)
        assert episode_type == EpisodeType.ANTHOLOGY

    def test_determine_episode_type_multi_episode(self) -> None:
        """Test determining multi-episode type."""
        file_info = {
            "show_name": "Show Name",
            "season": 1,
            "episode": 1,
            "title": "Episode Title",
            "multi_episodes": [1, 2, 3],
        }

        episode_type = determine_episode_type(file_info, segments=None)
        assert episode_type == EpisodeType.MULTI_EPISODE


class TestAnthologyEpisodeProcessing:
    """Tests for anthology episode processing."""

    @patch("plexomatic.utils.episode.processor.extract_show_info")
    @patch("plexomatic.utils.episode.processor.detect_segments_from_file")
    def test_process_anthology_episode_basic(
        self, mock_detect_segments: MagicMock, mock_extract_info: MagicMock
    ) -> None:
        """Test basic anthology episode processing."""
        # Setup
        original_path = "Show Name S01E01.mp4"
        mock_extract_info.return_value = {
            "show_name": "Show Name",
            "season": 1,
            "episode": 1,
            "title": "Episode Title",
        }
        mock_detect_segments.return_value = ["Segment 1", "Segment 2", "Segment 3"]

        # Test
        result = process_anthology_episode(original_path=original_path, use_llm=True)

        # Assert
        assert result is not None
        assert result["is_anthology"] is True
        assert result["show_name"] == "Show Name"
        assert result["season"] == 1
        assert result["episode_numbers"] == [1, 2, 3]
        assert result["segments"] == ["Segment 1", "Segment 2", "Segment 3"]

        # Verify mock calls
        mock_extract_info.assert_called_once_with(original_path)
        mock_detect_segments.assert_called_once_with(original_path, use_llm=True, max_segments=10)

    @patch("plexomatic.utils.episode.processor.extract_show_info")
    @patch("plexomatic.utils.episode.processor.detect_segments_from_file")
    def test_process_anthology_episode_with_unknown_segments(
        self, mock_detect_segments: MagicMock, mock_extract_info: MagicMock
    ) -> None:
        """Test anthology episode processing with unknown segments."""
        # Setup
        original_path = "Show Name S01E01.mp4"
        mock_extract_info.return_value = {
            "show_name": "Show Name",
            "season": 1,
            "episode": 1,
            "title": "Episode Title",
        }
        mock_detect_segments.return_value = ["Unknown", "Unknown", "Unknown"]

        # Test
        result = process_anthology_episode(original_path=original_path, use_llm=True)

        # Assert
        assert result is not None
        assert result["is_anthology"] is True
        assert result["show_name"] == "Show Name"
        assert result["season"] == 1
        assert result["episode_numbers"] == [1, 2, 3]
        assert result["segments"] == ["Unknown", "Unknown", "Unknown"]

    @patch("plexomatic.utils.episode.processor.extract_show_info")
    @patch("plexomatic.utils.episode.processor.detect_segments_from_file")
    def test_process_anthology_episode_with_missing_info(
        self, mock_detect_segments: MagicMock, mock_extract_info: MagicMock
    ) -> None:
        """Test anthology episode processing with missing file info."""
        # Setup
        original_path = "Invalid Filename.mp4"
        mock_extract_info.return_value = None

        # Test
        result = process_anthology_episode(original_path=original_path, use_llm=True)

        # Assert
        assert result is None

        # Verify mock calls
        mock_extract_info.assert_called_once_with(original_path)
        mock_detect_segments.assert_not_called()


class TestEpisodeProcessing:
    """Tests for general episode processing."""

    @patch("plexomatic.utils.episode.processor.extract_show_info")
    @patch("plexomatic.utils.episode.processor.determine_episode_type")
    @patch("plexomatic.utils.episode.processor.process_anthology_episode")
    def test_process_episode_anthology(
        self,
        mock_process_anthology: MagicMock,
        mock_determine_type: MagicMock,
        mock_extract_info: MagicMock,
    ) -> None:
        """Test processing an anthology episode."""
        # Setup
        original_path = "Show Name S01E01.mp4"
        file_info = {"show_name": "Show Name", "season": 1, "episode": 1, "title": "Episode Title"}
        mock_extract_info.return_value = file_info
        mock_determine_type.return_value = EpisodeType.ANTHOLOGY

        anthology_result = {
            "is_anthology": True,
            "show_name": "Show Name",
            "season": 1,
            "episode_numbers": [1, 2, 3],
            "segments": ["Segment 1", "Segment 2", "Segment 3"],
        }
        mock_process_anthology.return_value = anthology_result

        # Test
        result = process_episode(original_path=original_path, use_llm=True, anthology_mode=True)

        # Assert
        assert result is not None
        assert result["is_anthology"] is True
        assert result["show_name"] == "Show Name"
        assert result["episode_numbers"] == [1, 2, 3]

        # Verify mock calls
        mock_extract_info.assert_called_once_with(original_path)
        mock_determine_type.assert_called_once_with(file_info, segments=None, anthology_mode=True)
        mock_process_anthology.assert_called_once_with(
            original_path=original_path, use_llm=True, max_segments=10
        )

    @patch("plexomatic.utils.episode.processor.extract_show_info")
    @patch("plexomatic.utils.episode.processor.determine_episode_type")
    def test_process_episode_standard(
        self, mock_determine_type: MagicMock, mock_extract_info: MagicMock
    ) -> None:
        """Test processing a standard episode."""
        # Setup
        original_path = "Show Name S01E01 Episode Title.mp4"
        file_info = {"show_name": "Show Name", "season": 1, "episode": 1, "title": "Episode Title"}
        mock_extract_info.return_value = file_info
        mock_determine_type.return_value = EpisodeType.STANDARD

        # Test
        result = process_episode(original_path=original_path, use_llm=True, anthology_mode=False)

        # Assert
        assert result is not None
        assert result.get("is_anthology") is None  # Not an anthology
        assert result["show_name"] == "Show Name"
        assert result["season"] == 1
        assert result["episode"] == 1
        assert result["title"] == "Episode Title"

        # Verify mock calls
        mock_extract_info.assert_called_once_with(original_path)
        mock_determine_type.assert_called_once_with(file_info, segments=None, anthology_mode=False)

    @patch("plexomatic.utils.episode.processor.extract_show_info")
    def test_process_episode_missing_info(self, mock_extract_info: MagicMock) -> None:
        """Test processing an episode with missing file info."""
        # Setup
        original_path = "Invalid Filename.mp4"
        mock_extract_info.return_value = None

        # Test
        result = process_episode(original_path=original_path, use_llm=True)

        # Assert
        assert result is None

        # Verify mock calls
        mock_extract_info.assert_called_once_with(original_path)
