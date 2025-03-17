import pytest
from unittest.mock import patch, MagicMock

from plexomatic.api.tvmaze_client import TVMazeClient, TVMazeRequestError, TVMazeRateLimitError


class TestTVMazeClient:
    """Tests for the TVMaze API client."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.client = TVMazeClient()

    @patch("plexomatic.api.tvmaze_client.requests.get")
    def test_search_shows(self, mock_get) -> None:
        """Test searching for shows by name."""
        # Set up mock response
        mock_response = MagicMock()
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

        # Test empty results
        mock_response.json.return_value = []
        results = self.client.search_shows("Nonexistent Show")
        assert len(results) == 0

    @patch("plexomatic.api.tvmaze_client.requests.get")
    def test_get_show_by_id(self, mock_get) -> None:
        """Test getting show details by ID."""
        # Set up mock response
        mock_response = MagicMock()
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

        # Verify correct URL was called
        url = mock_get.call_args[0][0]
        assert "shows/1" in url

        # Test show not found
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(TVMazeRequestError):
            self.client.get_show_by_id(99999)

    @patch("plexomatic.api.tvmaze_client.requests.get")
    def test_get_show_by_imdb_id(self, mock_get) -> None:
        """Test getting show details by IMDB ID."""
        # Set up mock response
        mock_response = MagicMock()
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

        # Test show not found
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(TVMazeRequestError):
            self.client.get_show_by_imdb_id("tt9999999")

    @patch("plexomatic.api.tvmaze_client.requests.get")
    def test_get_episodes(self, mock_get) -> None:
        """Test getting episodes for a show."""
        # Set up mock response
        mock_response = MagicMock()
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

        # Verify correct URL was called
        url = mock_get.call_args[0][0]
        assert "shows/1/episodes" in url

        # Test show not found
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(TVMazeRequestError):
            self.client.get_episodes(99999)

    @patch("plexomatic.api.tvmaze_client.requests.get")
    def test_get_episode_by_number(self, mock_get) -> None:
        """Test getting a specific episode by season and episode number."""
        # Set up mock response
        mock_response = MagicMock()
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

        # Test episode not found
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(TVMazeRequestError):
            self.client.get_episode_by_number(1, 99, 99)

    @patch("plexomatic.api.tvmaze_client.requests.get")
    def test_search_people(self, mock_get) -> None:
        """Test searching for people by name."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "score": 0.9,
                "person": {
                    "id": 1,
                    "name": "Bryan Cranston",
                    "birthday": "1956-03-07",
                    "gender": "Male",
                    "country": {"name": "United States"},
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

    @patch("plexomatic.api.tvmaze_client.requests.get")
    def test_get_show_cast(self, mock_get) -> None:
        """Test getting the cast for a show."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "person": {"id": 1, "name": "Bryan Cranston"},
                "character": {"id": 1, "name": "Walter White"},
            },
            {
                "person": {"id": 2, "name": "Aaron Paul"},
                "character": {"id": 2, "name": "Jesse Pinkman"},
            },
        ]
        mock_get.return_value = mock_response

        # Test successful cast retrieval
        cast = self.client.get_show_cast(1)

        assert len(cast) == 2
        assert cast[0]["person"]["name"] == "Bryan Cranston"
        assert cast[0]["character"]["name"] == "Walter White"

        # Verify correct URL was called
        url = mock_get.call_args[0][0]
        assert "shows/1/cast" in url

    @patch("plexomatic.api.tvmaze_client.requests.get")
    def test_rate_limiting(self, mock_get) -> None:
        """Test handling of rate limiting."""
        # Set up mock response for rate limit
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.side_effect = ValueError(
            "No JSON in response"
        )  # Rate limit responses may not have JSON
        mock_get.return_value = mock_response

        # Test rate limit handling
        with pytest.raises(TVMazeRateLimitError):
            self.client.search_shows("Breaking Bad")

    @patch("plexomatic.api.tvmaze_client.requests.get")
    def test_caching(self, mock_get) -> None:
        """Test request caching functionality."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"show": {"id": 1, "name": "Breaking Bad"}}]
        mock_get.return_value = mock_response

        # First call should hit the API
        results1 = self.client.search_shows("Breaking Bad")

        # Second call with same params should use cache
        results2 = self.client.search_shows("Breaking Bad")

        # Mock should be called only once if caching works
        assert mock_get.call_count == 1

        # Results should be identical
        assert results1 == results2

        # Different query should hit the API again
        mock_response.json.return_value = [{"show": {"id": 2, "name": "Better Call Saul"}}]
        results3 = self.client.search_shows("Better Call Saul")

        assert mock_get.call_count == 2
        assert results3[0]["show"]["name"] == "Better Call Saul"
