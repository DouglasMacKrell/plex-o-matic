"""
Test file for TVMaze client show and episode functionality.
Tests for retrieving show details, episodes, and cast information.
"""

import pytest
from pytest_mock import MockerFixture

from plexomatic.api.tvmaze_client import TVMazeClient, TVMazeRequestError


class TestTVMazeShows:
    """Tests for the TVMaze show and episode functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.client = TVMazeClient()

    def test_get_show_by_id(self, mocker: MockerFixture) -> None:
        """Test getting show details by ID."""
        # Set up mock response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "name": "Breaking Bad",
            "type": "Scripted",
            "language": "English",
            "genres": ["Drama", "Crime", "Thriller"],
            "status": "Ended",
            "premiered": "2008-01-20",
            "summary": "<p>A high school chemistry teacher diagnosed with terminal cancer.</p>",
            "network": {"name": "AMC"},
        }
        mock_get.return_value = mock_response

        # Test successful show retrieval
        show = self.client.get_show_by_id(1)

        assert show["id"] == 1
        assert show["name"] == "Breaking Bad"
        assert "summary" in show
        assert show["status"] == "Ended"

        # Verify correct URL was called
        url = mock_get.call_args[0][0]
        assert "shows/1" in url

    def test_get_show_by_id_not_found(self, mocker: MockerFixture) -> None:
        """Test error handling when show is not found."""
        # Set up mock response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Test show not found
        with pytest.raises(TVMazeRequestError) as excinfo:
            self.client.get_show_by_id(99999)

        # Verify error message
        assert "Resource not found" in str(excinfo.value)

    def test_get_show_by_imdb_id(self, mocker: MockerFixture) -> None:
        """Test getting show details by IMDB ID."""
        # Set up mock response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "name": "Breaking Bad",
            "externals": {"imdb": "tt0903747", "tvrage": 18164},
        }
        mock_get.return_value = mock_response

        # Test successful show retrieval
        show = self.client.get_show_by_imdb_id("tt0903747")

        assert show["id"] == 1
        assert show["name"] == "Breaking Bad"
        assert show["externals"]["imdb"] == "tt0903747"

        # Verify correct URL was called with params
        url = mock_get.call_args[0][0]
        params = mock_get.call_args[1]["params"]
        assert "lookup/shows" in url
        assert params["imdb"] == "tt0903747"

    def test_get_show_by_imdb_id_not_found(self, mocker: MockerFixture) -> None:
        """Test error handling when IMDB ID is not found."""
        # Set up mock response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Test show not found
        with pytest.raises(TVMazeRequestError) as excinfo:
            self.client.get_show_by_imdb_id("tt9999999")

        # Verify error message
        assert "Resource not found" in str(excinfo.value)

    def test_get_episodes(self, mocker: MockerFixture) -> None:
        """Test getting episodes for a show."""
        # Set up mock response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 1,
                "name": "Pilot",
                "season": 1,
                "number": 1,
                "airdate": "2008-01-20",
                "runtime": 60,
                "summary": "<p>Walter White, a high school chemistry teacher.</p>",
            },
            {
                "id": 2,
                "name": "Cat's in the Bag...",
                "season": 1,
                "number": 2,
                "airdate": "2008-01-27",
                "runtime": 60,
                "summary": "<p>Walt and Jesse try to dispose of a body.</p>",
            },
        ]
        mock_get.return_value = mock_response

        # Test successful episode retrieval
        episodes = self.client.get_episodes(1)

        assert len(episodes) == 2
        assert episodes[0]["name"] == "Pilot"
        assert episodes[0]["season"] == 1
        assert episodes[0]["number"] == 1
        assert episodes[1]["name"] == "Cat's in the Bag..."

        # Verify correct URL was called
        url = mock_get.call_args[0][0]
        assert "shows/1/episodes" in url

    def test_get_episodes_not_found(self, mocker: MockerFixture) -> None:
        """Test error handling when show is not found for episodes."""
        # Set up mock response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Test show not found
        with pytest.raises(TVMazeRequestError) as excinfo:
            self.client.get_episodes(99999)

        # Verify error message
        assert "Resource not found" in str(excinfo.value)

    def test_get_episode_by_number(self, mocker: MockerFixture) -> None:
        """Test getting a specific episode by season and episode number."""
        # Set up mock response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "name": "Pilot",
            "season": 1,
            "number": 1,
            "airdate": "2008-01-20",
            "runtime": 60,
            "summary": "<p>Walter White, a high school chemistry teacher.</p>",
        }
        mock_get.return_value = mock_response

        # Test successful episode retrieval
        episode = self.client.get_episode_by_number(1, 1, 1)

        assert episode["id"] == 1
        assert episode["name"] == "Pilot"
        assert episode["season"] == 1
        assert episode["number"] == 1

        # Verify correct URL was called with params
        url = mock_get.call_args[0][0]
        params = mock_get.call_args[1]["params"]
        assert "shows/1/episodebynumber" in url
        assert params["season"] == 1
        assert params["number"] == 1

    def test_get_episode_by_number_not_found(self, mocker: MockerFixture) -> None:
        """Test error handling when episode is not found."""
        # Set up mock response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Test episode not found
        with pytest.raises(TVMazeRequestError) as excinfo:
            self.client.get_episode_by_number(1, 99, 99)

        # Verify error message
        assert "Resource not found" in str(excinfo.value)

    def test_get_show_cast(self, mocker: MockerFixture) -> None:
        """Test getting cast information for a show."""
        # Set up mock response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "person": {
                    "id": 1,
                    "name": "Bryan Cranston",
                    "birthday": "1956-03-07",
                },
                "character": {
                    "id": 1,
                    "name": "Walter White",
                },
            },
            {
                "person": {
                    "id": 2,
                    "name": "Aaron Paul",
                    "birthday": "1979-08-27",
                },
                "character": {
                    "id": 2,
                    "name": "Jesse Pinkman",
                },
            },
        ]
        mock_get.return_value = mock_response

        # Test successful cast retrieval
        cast = self.client.get_show_cast(1)

        assert len(cast) == 2
        assert cast[0]["person"]["name"] == "Bryan Cranston"
        assert cast[0]["character"]["name"] == "Walter White"
        assert cast[1]["person"]["name"] == "Aaron Paul"
        assert cast[1]["character"]["name"] == "Jesse Pinkman"

        # Verify correct URL was called
        url = mock_get.call_args[0][0]
        assert "shows/1/cast" in url

    def test_get_show_cast_not_found(self, mocker: MockerFixture) -> None:
        """Test error handling when show is not found for cast."""
        # Set up mock response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Test show not found
        with pytest.raises(TVMazeRequestError) as excinfo:
            self.client.get_show_cast(99999)

        # Verify error message
        assert "Resource not found" in str(excinfo.value)
