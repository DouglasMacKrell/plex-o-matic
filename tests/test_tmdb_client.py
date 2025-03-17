import pytest
from unittest.mock import patch, MagicMock
import time
import os
from datetime import datetime, timezone, timedelta

from plexomatic.api.tmdb_client import TMDBClient, TMDBRequestError, TMDBRateLimitError


class TestTMDBClient:
    """Tests for the TMDB API client."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.api_key = "test_api_key"
        self.client = TMDBClient(api_key=self.api_key)

    @patch("plexomatic.api.tmdb_client.requests.get")
    def test_get_configuration(self, mock_get):
        """Test retrieving API configuration."""
        # Mock successful configuration response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "images": {
                "base_url": "http://image.tmdb.org/t/p/",
                "secure_base_url": "https://image.tmdb.org/t/p/",
                "backdrop_sizes": ["w300", "w780", "w1280", "original"],
                "poster_sizes": ["w92", "w154", "w185", "w342", "w500", "w780", "original"],
                "profile_sizes": ["w45", "w185", "h632", "original"],
            },
            "change_keys": ["adult", "air_date", "also_known_as", "biography"],
        }
        mock_get.return_value = mock_response

        # Test successful configuration retrieval
        config = self.client.get_configuration()
        assert config["images"]["secure_base_url"] == "https://image.tmdb.org/t/p/"
        assert "poster_sizes" in config["images"]
        mock_get.assert_called_once()

    @patch("plexomatic.api.tmdb_client.requests.get")
    def test_search_movie(self, mock_get):
        """Test searching for movies."""
        # Mock successful movie search response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "page": 1,
            "results": [
                {
                    "id": 12345,
                    "title": "Test Movie",
                    "release_date": "2020-01-01",
                    "overview": "A test movie description",
                }
            ],
            "total_results": 1,
            "total_pages": 1,
        }
        mock_get.return_value = mock_response

        # Test successful movie search
        results = self.client.search_movie("Test Movie")
        assert len(results) == 1
        assert results[0]["id"] == 12345
        assert results[0]["title"] == "Test Movie"
        mock_get.assert_called_once()

        # Test movie not found
        mock_response.json.return_value = {"results": []}
        mock_get.reset_mock()
        self.client.clear_cache()  # Clear cache to ensure the mock is called again
        results = self.client.search_movie("Nonexistent Movie")
        assert results == []

    @patch("plexomatic.api.tmdb_client.requests.get")
    def test_search_tv(self, mock_get):
        """Test searching for TV shows."""
        # Mock successful TV search response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "page": 1,
            "results": [
                {
                    "id": 12345,
                    "name": "Test Show",
                    "first_air_date": "2020-01-01",
                    "overview": "A test show description",
                }
            ],
            "total_results": 1,
            "total_pages": 1,
        }
        mock_get.return_value = mock_response

        # Test successful TV search
        results = self.client.search_tv("Test Show")
        assert len(results) == 1
        assert results[0]["id"] == 12345
        assert results[0]["name"] == "Test Show"
        mock_get.assert_called_once()

    @patch("plexomatic.api.tmdb_client.requests.get")
    def test_get_movie_details(self, mock_get):
        """Test retrieving movie details."""
        # Mock successful movie details response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 12345,
            "title": "Test Movie",
            "release_date": "2020-01-01",
            "overview": "A test movie description",
            "genres": [{"id": 28, "name": "Action"}],
            "runtime": 120,
            "vote_average": 7.5,
        }
        mock_get.return_value = mock_response

        # Test successful movie details retrieval
        movie = self.client.get_movie_details(12345)
        assert movie["id"] == 12345
        assert movie["title"] == "Test Movie"
        assert movie["runtime"] == 120
        mock_get.assert_called_once()

        # Test movie not found
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "success": False,
            "status_code": 34,
            "status_message": "The resource you requested could not be found.",
        }
        mock_get.reset_mock()
        self.client.clear_cache()  # Clear cache to ensure the mock is called again
        with pytest.raises(TMDBRequestError):
            self.client.get_movie_details(99999)

    @patch("plexomatic.api.tmdb_client.requests.get")
    def test_get_tv_details(self, mock_get):
        """Test retrieving TV show details."""
        # Mock successful TV details response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 12345,
            "name": "Test Show",
            "first_air_date": "2020-01-01",
            "overview": "A test show description",
            "genres": [{"id": 18, "name": "Drama"}],
            "number_of_seasons": 3,
            "number_of_episodes": 30,
            "vote_average": 8.0,
        }
        mock_get.return_value = mock_response

        # Test successful TV details retrieval
        show = self.client.get_tv_details(12345)
        assert show["id"] == 12345
        assert show["name"] == "Test Show"
        assert show["number_of_seasons"] == 3
        mock_get.assert_called_once()

    @patch("plexomatic.api.tmdb_client.requests.get")
    def test_get_tv_season(self, mock_get):
        """Test retrieving TV show season details."""
        # Mock successful season details response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 12345,
            "air_date": "2020-01-01",
            "name": "Season 1",
            "overview": "First season",
            "season_number": 1,
            "episodes": [
                {"id": 1001, "episode_number": 1, "name": "Pilot", "air_date": "2020-01-01"},
                {"id": 1002, "episode_number": 2, "name": "Episode 2", "air_date": "2020-01-08"},
            ],
        }
        mock_get.return_value = mock_response

        # Test successful season details retrieval
        season = self.client.get_tv_season(12345, 1)
        assert season["name"] == "Season 1"
        assert len(season["episodes"]) == 2
        assert season["episodes"][0]["name"] == "Pilot"
        mock_get.assert_called_once()

    @patch("plexomatic.api.tmdb_client.requests.get")
    def test_rate_limiting(self, mock_get):
        """Test handling of rate limiting."""
        # Mock rate limit exceeded response
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "10"}
        mock_get.return_value = mock_response

        # Test rate limit handling
        with pytest.raises(TMDBRateLimitError):
            self.client.search_movie("Test Movie")

    @patch("plexomatic.api.tmdb_client.requests.get")
    @patch("time.sleep")
    def test_automatic_retry_after_rate_limit(self, mock_sleep, mock_get):
        """Test automatic retry after rate limit with backoff."""
        # Setup mock responses for rate limit then success
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "5"}

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {"results": [{"id": 12345, "title": "Test Movie"}]}

        # Return rate limit on first call, success on second
        mock_get.side_effect = [rate_limit_response, success_response]

        # Test with auto_retry=True
        self.client.auto_retry = True
        self.client.clear_cache()  # Clear cache to ensure the mock is called
        results = self.client.search_movie("Test Movie")

        # Verify the client respected the retry-after header
        mock_sleep.assert_called_once_with(5)
        assert len(mock_get.call_args_list) == 2
        assert results[0]["id"] == 12345

    @patch("plexomatic.api.tmdb_client.requests.get")
    def test_cache_mechanism(self, mock_get):
        """Test that responses are properly cached."""
        # Setup mock for first call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [{"id": 12345, "title": "Test Movie"}]}
        mock_get.return_value = mock_response

        # Clear the cache before starting the test
        self.client.clear_cache()

        # First call should hit the API
        results1 = self.client.search_movie("Test Movie")
        assert mock_get.call_count == 1

        # Second call with same params should use cache
        results2 = self.client.search_movie("Test Movie")
        # Verify mock wasn't called again
        assert mock_get.call_count == 1

        # Results should be identical
        assert results1 == results2

        # Different query should hit the API again
        mock_response.json.return_value = {"results": [{"id": 67890, "title": "Another Movie"}]}
        results3 = self.client.search_movie("Another Movie")
        assert mock_get.call_count == 2
        assert results3[0]["id"] == 67890
