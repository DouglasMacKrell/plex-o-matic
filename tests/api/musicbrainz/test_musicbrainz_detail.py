"""Tests for the MusicBrainz API client detail retrieval functionality."""

import pytest
from pytest_mock import MockerFixture

from plexomatic.api.musicbrainz_client import MusicBrainzClient


class TestMusicBrainzDetail:
    """Tests for the MusicBrainz API client's detail retrieval functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.client = MusicBrainzClient(
            app_name="Test App",
            app_version="1.0",
            contact_email="test@example.com",
        )

    def test_get_artist_success(self, mocker: MockerFixture) -> None:
        """Test successful artist retrieval."""
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123",
            "name": "Test Artist",
            "type": "Person",
            "country": "US",
            "life-span": {"begin": "1990", "end": None},
        }
        mock_get.return_value = mock_response

        result = self.client.get_artist("123")
        assert result["name"] == "Test Artist"
        assert result["id"] == "123"
        mock_get.assert_called_once()

    def test_get_artist_with_releases(self, mocker: MockerFixture) -> None:
        """Test artist retrieval with releases included."""
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123",
            "name": "Test Artist",
            "releases": [
                {
                    "id": "456",
                    "title": "Test Album",
                    "date": "2020-01-01",
                }
            ],
        }
        mock_get.return_value = mock_response

        result = self.client.get_artist("123", include_releases=True)
        assert result["name"] == "Test Artist"
        assert len(result["releases"]) == 1
        assert result["releases"][0]["title"] == "Test Album"
        
        # Verify that the include parameter was used
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert kwargs["params"]["inc"] == "releases"

    def test_get_release_success(self, mocker: MockerFixture) -> None:
        """Test successful release retrieval."""
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "456",
            "title": "Test Album",
            "date": "2020-01-01",
            "artist-credit": [{"name": "Test Artist"}],
        }
        mock_get.return_value = mock_response

        result = self.client.get_release("456")
        assert result["title"] == "Test Album"
        assert result["id"] == "456"
        mock_get.assert_called_once()

    def test_get_release_with_recordings(self, mocker: MockerFixture) -> None:
        """Test release retrieval with recordings included."""
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "456",
            "title": "Test Album",
            "recordings": [
                {
                    "id": "789",
                    "title": "Test Track",
                    "length": 180000,
                }
            ],
        }
        mock_get.return_value = mock_response

        result = self.client.get_release("456", include_recordings=True)
        assert result["title"] == "Test Album"
        assert len(result["recordings"]) == 1
        assert result["recordings"][0]["title"] == "Test Track"
        
        # Verify that the include parameter was used
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert kwargs["params"]["inc"] == "recordings"

    def test_get_track_success(self, mocker: MockerFixture) -> None:
        """Test successful track retrieval."""
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "789",
            "title": "Test Track",
            "length": 180000,
            "artist-credit": [{"name": "Test Artist"}],
        }
        mock_get.return_value = mock_response

        result = self.client.get_track("789")
        assert result["title"] == "Test Track"
        assert result["id"] == "789"
        assert result["length"] == 180000
        mock_get.assert_called_once()

    def test_url_format(self, mocker: MockerFixture) -> None:
        """Test that API URLs are formatted correctly."""
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123", "name": "Test"}
        mock_get.return_value = mock_response

        # Test artist URL
        self.client.get_artist("123")
        args, _ = mock_get.call_args
        assert args[0] == "https://musicbrainz.org/ws/2/artist/123"
        mock_get.reset_mock()

        # Test release URL
        self.client.get_release("456")
        args, _ = mock_get.call_args
        assert args[0] == "https://musicbrainz.org/ws/2/release/456"
        mock_get.reset_mock()

        # Test track URL
        self.client.get_track("789")
        args, _ = mock_get.call_args
        assert args[0] == "https://musicbrainz.org/ws/2/recording/789" 