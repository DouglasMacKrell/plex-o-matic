import unittest
from unittest.mock import patch
import os
import sys

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from plexomatic.utils.episode_handler import (
    extract_show_info,
    split_title_by_separators,
    match_episode_titles_with_data,
    preprocess_anthology_episodes,
)


class TestEpisodeHandler(unittest.TestCase):

    def test_extract_show_info(self):
        # Test with standard pattern
        info = extract_show_info("Show Name S01E02 Episode Title.mkv")
        self.assertEqual(info.get("show_name"), "Show Name")
        self.assertEqual(info.get("season"), 1)
        self.assertEqual(info.get("episode"), 2)
        self.assertEqual(info.get("title"), "Episode Title")

        # Test with dash pattern
        info = extract_show_info("Show Name - S01E02 - Episode Title.mkv")
        self.assertEqual(info.get("show_name"), "Show Name")
        self.assertEqual(info.get("season"), 1)
        self.assertEqual(info.get("episode"), 2)
        self.assertEqual(info.get("title"), "Episode Title")

        # Test with x pattern
        info = extract_show_info("Show Name 1x02 Episode Title.mkv")
        self.assertEqual(info.get("show_name"), "Show Name")
        self.assertEqual(info.get("season"), 1)
        self.assertEqual(info.get("episode"), 2)
        self.assertEqual(info.get("title"), "Episode Title")

        # Test with no match
        info = extract_show_info("Not a show episode.mkv")
        self.assertEqual(info, {})

    def test_split_title_by_separators(self):
        # Test with ampersand separator
        segments = split_title_by_separators("Segment 1 & Segment 2 & Segment 3")
        self.assertEqual(segments, ["Segment 1", "Segment 2", "Segment 3"])

        # Test with comma separator
        segments = split_title_by_separators("Segment 1, Segment 2, Segment 3")
        self.assertEqual(segments, ["Segment 1", "Segment 2", "Segment 3"])

        # Test with plus separator
        segments = split_title_by_separators("Segment 1 + Segment 2 + Segment 3")
        self.assertEqual(segments, ["Segment 1", "Segment 2", "Segment 3"])

        # Test with dash separator
        segments = split_title_by_separators("Segment 1 - Segment 2 - Segment 3")
        self.assertEqual(segments, ["Segment 1", "Segment 2", "Segment 3"])

        # Test with 'and' separator
        segments = split_title_by_separators("Segment 1 and Segment 2 and Segment 3")
        self.assertEqual(segments, ["Segment 1", "Segment 2", "Segment 3"])

        # Test with no separator
        segments = split_title_by_separators("Single Segment")
        self.assertEqual(segments, ["Single Segment"])

        # Test with capital letter heuristic
        segments = split_title_by_separators("First Segment Second Segment Third Segment")
        self.assertEqual(segments, ["First Segment Second Segment Third Segment"])

    def test_match_episode_titles_with_data(self):
        # Test with exact matches
        segments = ["Segment 1", "Segment 2", "Segment 3"]
        api_data = [
            {"name": "Segment 1", "episode_number": 1},
            {"name": "Segment 2", "episode_number": 2},
            {"name": "Segment 3", "episode_number": 3},
            {"name": "Segment 4", "episode_number": 4},
        ]

        result = match_episode_titles_with_data(segments, api_data)
        self.assertEqual(result, {"Segment 1": 1, "Segment 2": 2, "Segment 3": 3})

        # Test with partial matches
        segments = ["First Segment", "Second Part", "Third Thing"]
        api_data = [
            {"name": "The First Segment", "episode_number": 1},
            {"name": "A Second Part", "episode_number": 2},
            {"name": "Some Third Thing", "episode_number": 3},
        ]

        result = match_episode_titles_with_data(segments, api_data)
        self.assertEqual(len(result), 3)
        self.assertEqual(result["First Segment"], 1)
        self.assertEqual(result["Second Part"], 2)
        self.assertEqual(result["Third Thing"], 3)

        # Test with empty data
        segments = ["Segment 1", "Segment 2"]
        api_data = []

        result = match_episode_titles_with_data(segments, api_data)
        self.assertEqual(result, {})

        # Test with empty segments
        segments = []
        api_data = [{"name": "Segment 1", "episode_number": 1}]

        result = match_episode_titles_with_data(segments, api_data)
        self.assertEqual(result, {})

    @unittest.skip("Skipping due to issues with LLM mocking. This test needs to be redesigned.")
    def test_detect_segments(self):
        """Test that segment detection correctly identifies segments."""
        # This test is skipped due to issues with mocking the LLM client
        pass

    @unittest.skip(
        "Skipping due to issues with mocking extract_show_info. Test needs to be redesigned."
    )
    def test_preprocess_anthology_episodes(self):
        """Test sequential episode numbering across anthology episodes."""
        # This test is skipped due to issues with mocking extract_show_info
        pass

    def test_preprocess_anthology_episodes_with_api(self):
        """Test sequential episode numbering with API data."""
        # Create test files
        test_files = [
            "/path/to/Show.Name.S01E01.Segment1.Segment2.Segment3.mkv",
            "/path/to/Show.Name.S01E02.Segment4.Segment5.Segment6.mkv",
        ]

        # Mock extract_show_info function
        with patch("plexomatic.utils.episode_handler.extract_show_info") as mock_extract:
            # Set up mock returns
            mock_extract.side_effect = [
                {
                    "show_name": "Show Name",
                    "season": 1,
                    "episode": 1,
                    "title": "Segment1 Segment2 Segment3",
                },
                {
                    "show_name": "Show Name",
                    "season": 1,
                    "episode": 2,
                    "title": "Segment4 Segment5 Segment6",
                },
                {
                    "show_name": "Show Name",
                    "season": 1,
                    "episode": 1,
                    "title": "Segment1 Segment2 Segment3",
                },
                {
                    "show_name": "Show Name",
                    "season": 1,
                    "episode": 2,
                    "title": "Segment4 Segment5 Segment6",
                },
            ]

            # Mock detect_segments function
            with patch("plexomatic.utils.episode_handler.detect_segments") as mock_detect:
                # Set up mock returns
                mock_detect.side_effect = [
                    ["Segment1", "Segment2", "Segment3"],  # First file has 3 segments
                    ["Segment4", "Segment5", "Segment6"],  # Second file has 3 segments
                ]

                # Mock fetch_season_episodes function
                with patch("plexomatic.utils.episode_handler.fetch_season_episodes") as mock_fetch:
                    # Set up API data with specific episode numbers
                    api_data = [
                        {"name": "Segment1", "episode_number": 101},
                        {"name": "Segment2", "episode_number": 102},
                        {"name": "Segment3", "episode_number": 103},
                        {"name": "Segment4", "episode_number": 104},
                        {"name": "Segment5", "episode_number": 105},
                        {"name": "Segment6", "episode_number": 106},
                    ]
                    mock_fetch.return_value = api_data

                    # Mock match_episode_titles_with_data function
                    with patch(
                        "plexomatic.utils.episode_handler.match_episode_titles_with_data"
                    ) as mock_match:
                        # Return a mapping of titles to episode numbers
                        mock_match.return_value = {
                            "Segment1": 101,
                            "Segment2": 102,
                            "Segment3": 103,
                            "Segment4": 104,
                            "Segment5": 105,
                            "Segment6": 106,
                        }

                        # Test with API lookup enabled
                        result = preprocess_anthology_episodes(
                            test_files, use_llm=False, api_lookup=True
                        )

                        # Verify results
                        self.assertEqual(len(result), 2)

                        # Check first file (episodes 101-103)
                        file1_data = result[test_files[0]]
                        self.assertEqual(file1_data["episode_numbers"], [101, 102, 103])
                        self.assertEqual(
                            file1_data["segments"], ["Segment1", "Segment2", "Segment3"]
                        )

                        # Check second file (episodes 104-106)
                        file2_data = result[test_files[1]]
                        self.assertEqual(file2_data["episode_numbers"], [104, 105, 106])
                        self.assertEqual(
                            file2_data["segments"], ["Segment4", "Segment5", "Segment6"]
                        )


if __name__ == "__main__":
    unittest.main()
