"""
Test file for the AniDB HTTP client functionality.

This includes tests for:
- Retrieving anime titles
- Retrieving anime descriptions
"""

import pytest
from pytest_mock import MockerFixture
import requests
import xml.etree.ElementTree as ET

from plexomatic.api.anidb_client import AniDBHTTPClient


class TestAniDBHTTPClient:
    """Tests for the AniDB HTTP API client."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.client = AniDBHTTPClient(client_name="plexomatic")

    def test_get_anime_titles(self, mocker: MockerFixture) -> None:
        """Test retrieving anime titles from the HTTP API."""
        # Mock HTTP response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.content = """
        <animetitles>
          <anime aid="1">
            <title xml:lang="en" type="official">Cowboy Bebop</title>
            <title xml:lang="ja" type="official">カウボーイビバップ</title>
          </anime>
          <anime aid="2">
            <title xml:lang="en" type="official">Trigun</title>
          </anime>
        </animetitles>
        """.encode()
        mock_get.return_value = mock_response

        # Test successful title retrieval
        titles = self.client.get_anime_titles()
        assert len(titles) == 2
        assert titles[0]["aid"] == "1"
        assert titles[0]["titles"][0]["title"] == "Cowboy Bebop"
        assert titles[0]["titles"][0]["lang"] == "en"
        assert titles[0]["titles"][1]["title"] == "カウボーイビバップ"
        assert titles[0]["titles"][1]["lang"] == "ja"
        assert titles[1]["aid"] == "2"

        # Verify correct URL was requested
        assert "animetitles.xml" in mock_get.call_args[0][0]

    def test_get_anime_titles_http_error(self, mocker: MockerFixture) -> None:
        """Test error handling when HTTP request fails for anime titles."""
        # Mock HTTP response with error
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Test handling of HTTP error
        titles = self.client.get_anime_titles()
        assert titles == []
        assert "animetitles.xml" in mock_get.call_args[0][0]

    def test_get_anime_titles_request_exception(self, mocker: MockerFixture) -> None:
        """Test handling of request exceptions for anime titles."""
        # Mock requests.get to raise an exception
        mock_get = mocker.patch("requests.get")
        mock_get.side_effect = requests.RequestException("Connection error")

        # Test handling of request exception
        titles = self.client.get_anime_titles()
        assert titles == []

    def test_get_anime_titles_xml_parse_error(self, mocker: MockerFixture) -> None:
        """Test handling of XML parsing errors for anime titles."""
        # Mock HTTP response with invalid XML
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.content = b"<invalid>XML<syntax>"
        mock_get.return_value = mock_response

        # Test handling of XML parsing error
        titles = self.client.get_anime_titles()
        assert titles == []

    def test_get_anime_description(self, mocker: MockerFixture) -> None:
        """Test retrieving anime description from the HTTP API."""
        # Mock HTTP response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.content = """
        <anime id="1">
          <titles>
            <title xml:lang="en" type="official">Cowboy Bebop</title>
          </titles>
          <description>In the year 2071, humanity has colonized the entire Solar System...</description>
          <picture>12345.jpg</picture>
        </anime>
        """.encode()
        mock_get.return_value = mock_response

        # Test successful description retrieval
        info = self.client.get_anime_description(1)
        assert info["id"] == "1"
        assert info["titles"][0]["title"] == "Cowboy Bebop"
        assert "colonized the entire Solar System" in info["description"]
        assert info["picture"] == "12345.jpg"

        # Verify correct URL was requested
        called_url = mock_get.call_args[0][0]
        assert "anime-desc.xml" in called_url
        assert "aid=1" in called_url

    def test_get_anime_description_http_error(self, mocker: MockerFixture) -> None:
        """Test error handling when HTTP request fails for anime description."""
        # Mock HTTP response with error
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Test handling of HTTP error
        info = self.client.get_anime_description(1)
        assert info == {}
        
        # Verify correct URL was requested
        called_url = mock_get.call_args[0][0]
        assert "anime-desc.xml" in called_url
        assert "aid=1" in called_url

    def test_get_anime_description_request_exception(self, mocker: MockerFixture) -> None:
        """Test handling of request exceptions for anime description."""
        # Mock requests.get to raise an exception
        mock_get = mocker.patch("requests.get")
        mock_get.side_effect = requests.RequestException("Connection error")

        # Test handling of request exception
        info = self.client.get_anime_description(1)
        assert info == {}

    def test_get_anime_description_xml_parse_error(self, mocker: MockerFixture) -> None:
        """Test handling of XML parsing errors for anime description."""
        # Mock HTTP response with invalid XML
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.content = b"<invalid>XML<syntax>"
        mock_get.return_value = mock_response

        # Test handling of XML parsing error
        info = self.client.get_anime_description(1)
        assert info == {}

    def test_get_anime_description_missing_elements(self, mocker: MockerFixture) -> None:
        """Test handling of missing elements in anime description XML."""
        # Mock HTTP response with missing elements
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.content = """
        <anime id="1">
          <!-- Missing titles element -->
          <!-- Missing description element -->
          <!-- Missing picture element -->
        </anime>
        """.encode()
        mock_get.return_value = mock_response

        # Test handling of missing elements
        info = self.client.get_anime_description(1)
        assert info["id"] == "1"
        assert "titles" in info
        assert info["titles"] == []
        assert "description" not in info
        assert "picture" not in info 