"""
Test file for TVMaze client search functionality.
Tests for searching shows and people.
"""

from pytest_mock import MockerFixture

from plexomatic.api.tvmaze_client import TVMazeClient


class TestTVMazeSearch:
    """Tests for the TVMaze search functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.client = TVMazeClient()

    def test_search_shows(self, mocker: MockerFixture) -> None:
        """Test searching for shows by name."""
        # Set up mock response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "score": 0.9,
                "show": {
                    "id": 1,
                    "name": "Breaking Bad",
                    "type": "Scripted",
                    "language": "English",
                    "genres": ["Drama", "Crime", "Thriller"],
                    "status": "Ended",
                    "premiered": "2008-01-20",
                    "network": {"name": "AMC"},
                },
            }
        ]
        mock_get.return_value = mock_response

        # Test successful show search
        results = self.client.search_shows("Breaking Bad")

        assert len(results) == 1
        assert results[0]["show"]["id"] == 1
        assert results[0]["show"]["name"] == "Breaking Bad"

        # Verify correct URL was called with params
        url = mock_get.call_args[0][0]
        params = mock_get.call_args[1]["params"]
        assert "search/shows" in url
        assert params["q"] == "Breaking Bad"

    def test_search_shows_multiple_results(self, mocker: MockerFixture) -> None:
        """Test searching for shows with multiple results."""
        # Set up mock response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "score": 0.9,
                "show": {
                    "id": 1,
                    "name": "Breaking Bad",
                    "premiered": "2008-01-20",
                },
            },
            {
                "score": 0.8,
                "show": {
                    "id": 2,
                    "name": "Breaking In",
                    "premiered": "2011-04-06",
                },
            },
            {
                "score": 0.7,
                "show": {
                    "id": 3,
                    "name": "Break",
                    "premiered": "2013-05-01",
                },
            },
        ]
        mock_get.return_value = mock_response

        # Test successful show search with multiple results
        results = self.client.search_shows("break")

        assert len(results) == 3
        assert results[0]["show"]["id"] == 1
        assert results[1]["show"]["id"] == 2
        assert results[2]["show"]["id"] == 3

        # Verify scores are in descending order
        assert results[0]["score"] > results[1]["score"]
        assert results[1]["score"] > results[2]["score"]

    def test_search_shows_empty_results(self, mocker: MockerFixture) -> None:
        """Test searching for shows with no results."""
        # Set up mock response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        # Test empty results
        results = self.client.search_shows("Nonexistent Show")
        assert len(results) == 0
        assert isinstance(results, list)

    def test_search_people(self, mocker: MockerFixture) -> None:
        """Test searching for people by name."""
        # Set up mock response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "score": 0.9,
                "person": {
                    "id": 1,
                    "name": "Bryan Cranston",
                    "country": {"name": "United States", "code": "US"},
                    "birthday": "1956-03-07",
                    "gender": "Male",
                },
            }
        ]
        mock_get.return_value = mock_response

        # Test successful people search
        results = self.client.search_people("Bryan Cranston")

        assert len(results) == 1
        assert results[0]["person"]["id"] == 1
        assert results[0]["person"]["name"] == "Bryan Cranston"

        # Verify correct URL was called with params
        url = mock_get.call_args[0][0]
        params = mock_get.call_args[1]["params"]
        assert "search/people" in url
        assert params["q"] == "Bryan Cranston"

    def test_search_people_multiple_results(self, mocker: MockerFixture) -> None:
        """Test searching for people with multiple results."""
        # Set up mock response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "score": 0.9,
                "person": {
                    "id": 1,
                    "name": "Bryan Cranston",
                },
            },
            {
                "score": 0.8,
                "person": {
                    "id": 2,
                    "name": "Aaron Paul",
                },
            },
        ]
        mock_get.return_value = mock_response

        # Test successful people search with multiple results
        results = self.client.search_people("breaking bad actor")

        assert len(results) == 2
        assert results[0]["person"]["id"] == 1
        assert results[1]["person"]["id"] == 2

        # Verify scores are in descending order
        assert results[0]["score"] > results[1]["score"]

    def test_search_people_empty_results(self, mocker: MockerFixture) -> None:
        """Test searching for people with no results."""
        # Set up mock response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        # Test empty results
        results = self.client.search_people("Nonexistent Person")
        assert len(results) == 0
        assert isinstance(results, list)
