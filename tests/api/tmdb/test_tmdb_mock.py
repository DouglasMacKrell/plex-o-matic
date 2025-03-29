"""
Test file for mocking the TMDB client.
This shows different ways to mock the TMDB client for testing other components.
"""

import pytest
from pytest_mock import MockerFixture

from plexomatic.api.tmdb_client import TMDBClient


class TestTMDBMocking:
    """Tests demonstrating how to mock the TMDB client."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.api_key = "test_api_key"
        self.client = TMDBClient(api_key=self.api_key)

    def test_mock_tmdb_client_directly(self, mocker: MockerFixture) -> None:
        """Test directly mocking the TMDBClient."""
        # Create a mock client
        mock_client = mocker.Mock(spec=TMDBClient)
        
        # Set up mock responses
        mock_client.search_movie.return_value = [
            {"id": 12345, "title": "Test Movie"}
        ]
        mock_client.get_movie_details.return_value = {
            "id": 12345,
            "title": "Test Movie",
            "overview": "Test overview"
        }
        
        # Test using the mock client
        movies = mock_client.search_movie("Test Movie")
        assert len(movies) == 1
        assert movies[0]["id"] == 12345
        
        movie = mock_client.get_movie_details(12345)
        assert movie["title"] == "Test Movie"
        
        # Verify the correct methods were called
        mock_client.search_movie.assert_called_once_with("Test Movie")
        mock_client.get_movie_details.assert_called_once_with(12345)

    def test_mock_specific_methods(self, mocker: MockerFixture) -> None:
        """Test mocking specific methods of the TMDBClient."""
        # Create a real client but mock specific methods
        client = TMDBClient(api_key=self.api_key)
        
        # Mock the search_tv and get_tv_details methods
        mocker.patch.object(
            client, 
            "search_tv", 
            return_value=[{"id": 12345, "name": "Test Show"}]
        )
        mocker.patch.object(
            client, 
            "get_tv_details", 
            return_value={"id": 12345, "name": "Test Show", "number_of_seasons": 3}
        )
        
        # Test using the partially mocked client
        shows = client.search_tv("Test Show")
        assert len(shows) == 1
        assert shows[0]["id"] == 12345
        
        show = client.get_tv_details(12345)
        assert show["name"] == "Test Show"
        assert show["number_of_seasons"] == 3

    def test_mock_with_side_effect(self, mocker: MockerFixture) -> None:
        """Test mocking with side_effect for dynamic responses."""
        # Create a mock client
        mock_client = mocker.Mock(spec=TMDBClient)
        
        # Set up a side_effect function to return different results based on input
        def mock_search_movie(query, year=None):
            if query == "Test Movie":
                return [{"id": 12345, "title": "Test Movie"}]
            elif query == "Another Movie":
                return [{"id": 67890, "title": "Another Movie"}]
            else:
                return []
                
        mock_client.search_movie.side_effect = mock_search_movie
        
        # Test using the mock client with different inputs
        results1 = mock_client.search_movie("Test Movie")
        assert len(results1) == 1
        assert results1[0]["id"] == 12345
        
        results2 = mock_client.search_movie("Another Movie")
        assert len(results2) == 1
        assert results2[0]["id"] == 67890
        
        results3 = mock_client.search_movie("Nonexistent Movie")
        assert results3 == []

    def test_mock_requests_for_tmdb_client(self, mocker: MockerFixture) -> None:
        """Test mocking the requests library to handle all TMDB API requests."""
        # Mock the requests.get method
        mock_get = mocker.patch("requests.get")
        
        # Configure mock responses based on URL patterns
        def mock_response(url, params=None, **kwargs):
            mock_resp = mocker.Mock()
            mock_resp.status_code = 200
            
            if "search/movie" in url:
                mock_resp.json.return_value = {
                    "results": [{"id": 12345, "title": "Test Movie"}]
                }
            elif "movie/" in url:
                movie_id = url.split("/")[-1]
                mock_resp.json.return_value = {
                    "id": int(movie_id),
                    "title": "Test Movie",
                    "overview": "Test overview"
                }
            else:
                mock_resp.json.return_value = {}
                
            return mock_resp
        
        mock_get.side_effect = mock_response
        
        # Create a real client that will use our mocked requests
        client = TMDBClient(api_key=self.api_key)
        
        # Test using the client with mocked request responses
        movies = client.search_movie("Test Movie")
        assert len(movies) == 1
        assert movies[0]["id"] == 12345
        
        movie = client.get_movie_details(12345)
        assert movie["id"] == 12345
        assert movie["title"] == "Test Movie" 