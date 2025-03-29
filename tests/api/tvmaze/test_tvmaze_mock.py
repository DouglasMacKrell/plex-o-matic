"""
Test file for mocking the TVMaze client.
This demonstrates different ways to mock the TVMaze client for testing other components.
"""

import pytest
from pytest_mock import MockerFixture

from plexomatic.api.tvmaze_client import TVMazeClient


class TestTVMazeMocking:
    """Tests demonstrating how to mock the TVMaze client."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.client = TVMazeClient()

    def test_mock_tvmaze_client_directly(self, mocker: MockerFixture) -> None:
        """Test directly mocking the TVMazeClient."""
        # Create a mock client
        mock_client = mocker.Mock(spec=TVMazeClient)

        # Set up mock responses
        mock_client.search_shows.return_value = [
            {
                "score": 0.9,
                "show": {
                    "id": 1,
                    "name": "Breaking Bad",
                },
            }
        ]
        mock_client.get_show_by_id.return_value = {
            "id": 1,
            "name": "Breaking Bad",
            "summary": "Test summary",
        }

        # Test using the mock client
        results = mock_client.search_shows("Breaking Bad")
        assert len(results) == 1
        assert results[0]["show"]["id"] == 1

        show = mock_client.get_show_by_id(1)
        assert show["name"] == "Breaking Bad"

        # Verify the correct methods were called
        mock_client.search_shows.assert_called_once_with("Breaking Bad")
        mock_client.get_show_by_id.assert_called_once_with(1)

    def test_mock_specific_methods(self, mocker: MockerFixture) -> None:
        """Test mocking specific methods of the TVMazeClient."""
        # Create a real client but mock specific methods
        client = TVMazeClient()

        # Mock the get_episodes and get_episode_by_number methods
        mocker.patch.object(
            client,
            "get_episodes",
            return_value=[
                {"id": 1, "name": "Pilot", "season": 1, "number": 1},
                {"id": 2, "name": "Episode 2", "season": 1, "number": 2},
            ],
        )
        mocker.patch.object(
            client,
            "get_episode_by_number",
            return_value={"id": 1, "name": "Pilot", "season": 1, "number": 1},
        )

        # Test using the partially mocked client
        episodes = client.get_episodes(1)
        assert len(episodes) == 2
        assert episodes[0]["name"] == "Pilot"

        episode = client.get_episode_by_number(1, 1, 1)
        assert episode["name"] == "Pilot"
        assert episode["season"] == 1
        assert episode["number"] == 1

    def test_mock_with_side_effect(self, mocker: MockerFixture) -> None:
        """Test mocking with side_effect for dynamic responses."""
        # Create a mock client
        mock_client = mocker.Mock(spec=TVMazeClient)

        # Set up a side_effect function to return different results based on input
        def mock_get_show_by_id(show_id):
            shows = {
                1: {"id": 1, "name": "Breaking Bad"},
                2: {"id": 2, "name": "Better Call Saul"},
            }
            if show_id in shows:
                return shows[show_id]
            raise Exception(f"Show with ID {show_id} not found")

        mock_client.get_show_by_id.side_effect = mock_get_show_by_id

        # Test using the mock client with different inputs
        show1 = mock_client.get_show_by_id(1)
        assert show1["id"] == 1
        assert show1["name"] == "Breaking Bad"

        show2 = mock_client.get_show_by_id(2)
        assert show2["id"] == 2
        assert show2["name"] == "Better Call Saul"

        # Test with invalid ID
        with pytest.raises(Exception) as excinfo:
            mock_client.get_show_by_id(999)
        assert "not found" in str(excinfo.value)

    def test_mock_requests_for_tvmaze_client(self, mocker: MockerFixture) -> None:
        """Test mocking the requests library to handle all TVMaze API requests."""
        # Mock the requests.get method
        mock_get = mocker.patch("requests.get")

        # Configure mock responses based on URL patterns
        def mock_response(url, params=None, **kwargs):
            mock_resp = mocker.Mock()
            mock_resp.status_code = 200

            if "search/shows" in url:
                mock_resp.json.return_value = [
                    {"score": 0.9, "show": {"id": 1, "name": "Breaking Bad"}}
                ]
            elif "shows/1" in url and "/episodes" not in url and "/cast" not in url:
                mock_resp.json.return_value = {
                    "id": 1,
                    "name": "Breaking Bad",
                    "summary": "Test summary",
                }
            elif "shows/1/episodes" in url:
                mock_resp.json.return_value = [
                    {"id": 1, "name": "Pilot", "season": 1, "number": 1},
                    {"id": 2, "name": "Episode 2", "season": 1, "number": 2},
                ]
            else:
                mock_resp.json.return_value = {}

            return mock_resp

        mock_get.side_effect = mock_response

        # Create a real client that will use our mocked requests
        client = TVMazeClient()

        # Test using the client with mocked request responses
        shows = client.search_shows("Breaking Bad")
        assert len(shows) == 1
        assert shows[0]["show"]["name"] == "Breaking Bad"

        show = client.get_show_by_id(1)
        assert show["id"] == 1
        assert show["name"] == "Breaking Bad"

        episodes = client.get_episodes(1)
        assert len(episodes) == 2
        assert episodes[0]["name"] == "Pilot"
