"""
Example file demonstrating how to effectively mock the AniDB client for testing.

This includes examples of:
- Mocking the AniDBClient directly
- Mocking the UDP and HTTP clients separately
- Setting up mock responses for different API calls
"""

import pytest
from pytest_mock import MockerFixture

from plexomatic.api.anidb_client import AniDBClient, AniDBUDPClient, AniDBHTTPClient


# Sample response data for mock tests
ANIME_DATA = {
    "aid": "1",
    "name": "Cowboy Bebop",
    "episodes": "26",
    "type": "TV Series",
    "startdate": "1998-04-03",
    "enddate": "1999-04-24",
}

EPISODES_DATA = [
    {
        "eid": "1",
        "aid": "1",
        "epno": "1",
        "length": "24",
        "airdate": "1998-04-03",
        "english": "Asteroid Blues",
        "romaji": "Asteroidoburusu",
    },
    {
        "eid": "2",
        "aid": "1",
        "epno": "2",
        "length": "24",
        "airdate": "1998-04-10",
        "english": "Stray Dog Strut",
        "romaji": "Nora Inu Sutoratto",
    }
]

ANIME_TITLES = [
    {
        "aid": "1",
        "titles": [
            {"title": "Cowboy Bebop", "lang": "en", "type": "official"},
            {"title": "カウボーイビバップ", "lang": "ja", "type": "official"},
        ]
    }
]

ANIME_DESCRIPTION = {
    "id": "1",
    "titles": [{"title": "Cowboy Bebop", "lang": "en", "type": "official"}],
    "description": "In 2071, roughly fifty years after an accident with a hyperspace gateway...",
    "picture": "12345.jpg",
}


class TestAniDBMocking:
    """Examples of how to mock the AniDB client for testing."""

    def test_mock_anidb_client_directly(self, mocker: MockerFixture) -> None:
        """Demo mocking the entire AniDB client."""
        # Create a mock AniDBClient
        mock_client = mocker.Mock(spec=AniDBClient)
        
        # Configure mock to return sample data for different methods
        mock_client.get_anime_by_name.return_value = ANIME_DATA
        mock_client.get_episodes_with_titles.return_value = EPISODES_DATA
        
        # Now use the mock client in your tests
        result = mock_client.get_anime_by_name("Cowboy Bebop")
        assert result == ANIME_DATA
        mock_client.get_anime_by_name.assert_called_once_with("Cowboy Bebop")
        
        episodes = mock_client.get_episodes_with_titles(1)
        assert episodes == EPISODES_DATA
        mock_client.get_episodes_with_titles.assert_called_once_with(1)

    def test_mock_udp_and_http_clients(self, mocker: MockerFixture) -> None:
        """Demo mocking the UDP and HTTP clients separately."""
        # Create mock UDP and HTTP clients
        mock_udp = mocker.Mock(spec=AniDBUDPClient)
        mock_http = mocker.Mock(spec=AniDBHTTPClient)
        
        # Configure mock responses
        mock_udp.get_anime_by_name.return_value = ANIME_DATA
        mock_udp.get_episodes.return_value = EPISODES_DATA
        mock_http.get_anime_titles.return_value = ANIME_TITLES
        mock_http.get_anime_description.return_value = ANIME_DESCRIPTION
        
        # Create AniDBClient with mocked components
        client = AniDBClient(username="test", password="test")
        client.udp_client = mock_udp
        client.http_client = mock_http
        
        # Test anime retrieval using the mocked components
        result = client.get_anime_by_name("Cowboy Bebop")
        assert result == ANIME_DATA
        mock_udp.get_anime_by_name.assert_called_once_with("Cowboy Bebop")
        
        # Test title mapping using mocked HTTP client
        aid = client.map_title_to_series("Cowboy Bebop")
        assert aid == "1"
        mock_http.get_anime_titles.assert_called_once()

    def test_mock_socket_for_udp_client(self, mocker: MockerFixture) -> None:
        """Demo mocking the socket used by the UDP client."""
        # Mock socket module
        mock_socket = mocker.patch("socket.socket")
        mock_socket_instance = mocker.Mock()
        mock_socket.return_value = mock_socket_instance
        
        # Set up mock socket to return authentication response
        mock_socket_instance.recvfrom.return_value = (
            b"200 LOGIN ACCEPTED s=fakesession",
            ("127.0.0.1", 9000),
        )
        
        # Create real UDP client that will use the mocked socket
        udp_client = AniDBUDPClient(
            username="test_user",
            password="test_password",
            client_name="plexomatic",
            client_version="1",
        )
        
        # Test authentication
        udp_client.authenticate()
        assert udp_client.session == "fakesession"
        
        # Configure socket for next call
        mock_socket_instance.recvfrom.return_value = (
            b"230 ANIME\n"
            b"aid|1|name|Cowboy Bebop|episodes|26|"
            b"type|TV Series|startdate|1998-04-03|enddate|1999-04-24",
            ("127.0.0.1", 9000),
        )
        
        # Test anime retrieval
        anime = udp_client.get_anime_by_name("Cowboy Bebop")
        assert anime["aid"] == "1"
        assert anime["name"] == "Cowboy Bebop"

    def test_mock_requests_for_http_client(self, mocker: MockerFixture) -> None:
        """Demo mocking requests used by the HTTP client."""
        # Mock requests.get
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        
        # Set up mock response for anime titles
        mock_response.status_code = 200
        mock_response.content = """
        <animetitles>
          <anime aid="1">
            <title xml:lang="en" type="official">Cowboy Bebop</title>
            <title xml:lang="ja" type="official">カウボーイビバップ</title>
          </anime>
        </animetitles>
        """.encode()
        mock_get.return_value = mock_response
        
        # Create HTTP client
        http_client = AniDBHTTPClient(client_name="plexomatic")
        
        # Test title retrieval
        titles = http_client.get_anime_titles()
        assert len(titles) == 1
        assert titles[0]["aid"] == "1"
        assert titles[0]["titles"][0]["title"] == "Cowboy Bebop" 