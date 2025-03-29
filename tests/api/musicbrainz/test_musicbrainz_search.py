"""Tests for the MusicBrainz API client search functionality."""

import pytest
from pytest_mock import MockerFixture

from plexomatic.api.musicbrainz_client import MusicBrainzClient


class TestMusicBrainzSearch:
    """Tests for the MusicBrainz API client search functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.client = MusicBrainzClient(
            app_name="Test App",
            app_version="1.0",
            contact_email="test@example.com",
        )

    def test_search_artist_success(self, mocker: MockerFixture) -> None:
        """Test successful artist search."""
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "artists": [
                {
                    "id": "123",
                    "name": "Test Artist",
                    "type": "Person",
                    "country": "US",
                }
            ]
        }
        mock_get.return_value = mock_response

        result = self.client.search_artist("Test Artist")
        assert len(result) == 1
        assert result[0]["name"] == "Test Artist"
        assert result[0]["id"] == "123"
        mock_get.assert_called_once()

    def test_search_artist_no_results(self, mocker: MockerFixture) -> None:
        """Test artist search with no results."""
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"artists": []}
        mock_get.return_value = mock_response

        result = self.client.search_artist("Nonexistent Artist")
        assert result == []
        mock_get.assert_called_once()

    def test_search_release_success(self, mocker: MockerFixture) -> None:
        """Test successful release search."""
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "releases": [
                {
                    "id": "456",
                    "title": "Test Album",
                    "date": "2020-01-01",
                    "artist-credit": [{"name": "Test Artist"}],
                }
            ]
        }
        mock_get.return_value = mock_response

        result = self.client.search_release("Test Album")
        assert len(result) == 1
        assert result[0]["title"] == "Test Album"
        assert result[0]["id"] == "456"
        mock_get.assert_called_once()

    def test_search_release_no_results(self, mocker: MockerFixture) -> None:
        """Test release search with no results."""
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"releases": []}
        mock_get.return_value = mock_response

        result = self.client.search_release("Nonexistent Album")
        assert result == []
        mock_get.assert_called_once()

    def test_search_track_success(self, mocker: MockerFixture) -> None:
        """Test successful track search."""
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "recordings": [
                {
                    "id": "789",
                    "title": "Test Track",
                    "artist-credit": [{"name": "Test Artist"}],
                    "length": 180000,  # 3 minutes in milliseconds
                }
            ]
        }
        mock_get.return_value = mock_response

        result = self.client.search_track("Test Track")
        assert len(result) == 1
        assert result[0]["title"] == "Test Track"
        assert result[0]["id"] == "789"
        mock_get.assert_called_once()

    def test_search_track_no_results(self, mocker: MockerFixture) -> None:
        """Test track search with no results."""
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"recordings": []}
        mock_get.return_value = mock_response

        result = self.client.search_track("Nonexistent Track")
        assert result == []
        mock_get.assert_called_once()

    def test_search_with_query_parameters(self, mocker: MockerFixture) -> None:
        """Test search with query parameters."""
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"artists": []}
        mock_get.return_value = mock_response

        # Call the method
        self.client.search_artist("Test Artist")
        
        # Check the call
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        
        # Check that fmt=json is in params
        assert kwargs["params"]["fmt"] == "json"
        
        # Check that the query parameter was set correctly
        assert kwargs["params"]["query"] == "Test Artist"
        
        # Check that the User-Agent header was set
        assert "User-Agent" in kwargs["headers"]
        assert "Test App/1.0" in kwargs["headers"]["User-Agent"] 