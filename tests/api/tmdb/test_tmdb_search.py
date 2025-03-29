"""
Test file for TMDB client search functionality.
Tests for movie and TV show search methods.
"""

import pytest
from pytest_mock import MockerFixture
import json

from plexomatic.api.tmdb_client import TMDBClient, TMDBRequestError


class TestTMDBSearch:
    """Tests for the TMDB search functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.api_key = "test_api_key"
        self.client = TMDBClient(api_key=self.api_key)

    def test_search_movie(self, mocker: MockerFixture) -> None:
        """Test searching for movies."""
        # Mock HTTP response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "page": 1,
            "results": [
                {
                    "id": 12345,
                    "title": "Test Movie",
                    "release_date": "2020-01-01",
                    "overview": "A test movie description",
                    "poster_path": "/abcdef.jpg",
                    "vote_average": 7.5,
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
        assert results[0]["release_date"] == "2020-01-01"
        
        # Verify correct URL and parameters were used
        called_url = mock_get.call_args[0][0]
        called_params = mock_get.call_args[1]["params"]
        assert "search/movie" in called_url
        assert called_params["api_key"] == self.api_key
        assert called_params["query"] == "Test Movie"

    def test_search_movie_with_year(self, mocker: MockerFixture) -> None:
        """Test searching for movies with year filter."""
        # Mock HTTP response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "page": 1,
            "results": [
                {
                    "id": 12345,
                    "title": "Test Movie",
                    "release_date": "2020-01-01",
                }
            ],
            "total_results": 1,
            "total_pages": 1,
        }
        mock_get.return_value = mock_response

        # Test search with year
        results = self.client.search_movie("Test Movie", year=2020)
        assert len(results) == 1
        assert results[0]["id"] == 12345
        
        # Verify year parameter was included
        called_params = mock_get.call_args[1]["params"]
        assert called_params["query"] == "Test Movie"
        assert called_params["year"] == "2020"

    def test_search_movie_not_found(self, mocker: MockerFixture) -> None:
        """Test searching for movies with no results."""
        # Mock HTTP response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "page": 1,
            "results": [],
            "total_results": 0,
            "total_pages": 0,
        }
        mock_get.return_value = mock_response

        # Test no results
        results = self.client.search_movie("Nonexistent Movie")
        assert results == []

    def test_search_tv(self, mocker: MockerFixture) -> None:
        """Test searching for TV shows."""
        # Mock HTTP response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "page": 1,
            "results": [
                {
                    "id": 12345,
                    "name": "Test Show",
                    "first_air_date": "2020-01-01",
                    "overview": "A test show description",
                    "poster_path": "/abcdef.jpg",
                    "vote_average": 8.0,
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
        assert results[0]["first_air_date"] == "2020-01-01"
        
        # Verify correct URL and parameters were used
        called_url = mock_get.call_args[0][0]
        called_params = mock_get.call_args[1]["params"]
        assert "search/tv" in called_url
        assert called_params["api_key"] == self.api_key
        assert called_params["query"] == "Test Show"

    def test_search_tv_with_year(self, mocker: MockerFixture) -> None:
        """Test searching for TV shows with year filter."""
        # Mock HTTP response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "page": 1,
            "results": [
                {
                    "id": 12345,
                    "name": "Test Show",
                    "first_air_date": "2020-01-01",
                }
            ],
            "total_results": 1,
            "total_pages": 1,
        }
        mock_get.return_value = mock_response

        # Test search with year
        results = self.client.search_tv("Test Show", first_air_date_year=2020)
        assert len(results) == 1
        assert results[0]["id"] == 12345
        
        # Verify year parameter was included
        called_params = mock_get.call_args[1]["params"]
        assert called_params["query"] == "Test Show"
        assert called_params["first_air_date_year"] == "2020"

    def test_search_tv_not_found(self, mocker: MockerFixture) -> None:
        """Test searching for TV shows with no results."""
        # Mock HTTP response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "page": 1,
            "results": [],
            "total_results": 0,
            "total_pages": 0,
        }
        mock_get.return_value = mock_response

        # Test no results
        results = self.client.search_tv("Nonexistent Show")
        assert results == []

    def test_cache_mechanism(self, mocker: MockerFixture) -> None:
        """Test that search responses are properly cached."""
        # Mock HTTP response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "page": 1,
            "results": [{"id": 12345, "title": "Test Movie"}],
            "total_results": 1,
            "total_pages": 1,
        }
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
        mock_response.json.return_value = {
            "page": 1,
            "results": [{"id": 67890, "title": "Another Movie"}],
            "total_results": 1,
            "total_pages": 1,
        }
        results3 = self.client.search_movie("Another Movie")
        assert mock_get.call_count == 2
        assert results3[0]["id"] == 67890 