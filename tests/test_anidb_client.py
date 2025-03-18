import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

from plexomatic.api.anidb_client import AniDBClient, AniDBUDPClient, AniDBHTTPClient
from plexomatic.api.anidb_client import AniDBRateLimitError, AniDBAuthenticationError


class TestAniDBUDPClient:
    """Tests for the AniDB UDP API client."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.username = "test_user"
        self.password = "test_password"
        self.client_name = "plexomatic"
        self.client_version = "1"
        self.udp_client = AniDBUDPClient(
            username=self.username,
            password=self.password,
            client_name=self.client_name,
            client_version=self.client_version,
        )
        # Pre-set a session value to avoid automatic authentication
        self.udp_client.session = "fake_session_key"
        self.udp_client.session_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    @patch("plexomatic.api.anidb_client.socket.socket")
    def test_authentication(self, mock_socket: MagicMock) -> None:
        """Test authentication with AniDB."""
        # Mock socket instance
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance

        # Set up mock socket to return successful auth response
        mock_socket_instance.recvfrom.return_value = (
            b"200 LOGIN ACCEPTED s=sessionkey",
            ("127.0.0.1", 9000),
        )

        # Reset the session for this test
        self.udp_client.session = None

        # Test successful authentication
        self.udp_client.authenticate()
        assert self.udp_client.session == "sessionkey"
        assert self.udp_client.session_expires_at is not None

        # Verify correct command was sent
        args, _ = mock_socket_instance.sendto.call_args
        assert b"AUTH" in args[0]
        assert b"user=test_user" in args[0]
        assert b"client=plexomatic" in args[0]

        # Test failed authentication
        mock_socket_instance.recvfrom.return_value = (b"500 LOGIN FAILED", ("127.0.0.1", 9000))
        self.udp_client.session = None
        with pytest.raises(AniDBAuthenticationError):
            self.udp_client.authenticate()

    @patch("plexomatic.api.anidb_client.socket.socket")
    def test_get_anime_by_name(self, mock_socket: MagicMock) -> None:
        """Test retrieving anime by name."""
        # Mock socket instance
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance

        # Set up mock response
        mock_socket_instance.recvfrom.return_value = (
            b"230 ANIME\n"
            b"aid|1|name|Cowboy Bebop|episodes|26|"
            b"type|TV Series|startdate|1998-04-03|enddate|1999-04-24",
            ("127.0.0.1", 9000),
        )

        # Test successful anime retrieval
        anime = self.udp_client.get_anime_by_name("Cowboy Bebop")
        assert anime["aid"] == "1"
        assert anime["name"] == "Cowboy Bebop"
        assert anime["episodes"] == "26"
        assert anime["type"] == "TV Series"

        # Verify correct command was sent
        args, _ = mock_socket_instance.sendto.call_args
        assert b"ANIME" in args[0]
        assert b"aname=Cowboy Bebop" in args[0]

    @patch("plexomatic.api.anidb_client.socket.socket")
    def test_get_anime_by_id(self, mock_socket: MagicMock) -> None:
        """Test retrieving anime by ID."""
        # Mock socket instance
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance

        # Set up mock response
        mock_socket_instance.recvfrom.return_value = (
            b"230 ANIME\n"
            b"aid|1|name|Cowboy Bebop|episodes|26|"
            b"type|TV Series|startdate|1998-04-03|enddate|1999-04-24",
            ("127.0.0.1", 9000),
        )

        # Test successful anime retrieval
        anime = self.udp_client.get_anime_by_id(1)
        assert anime["aid"] == "1"
        assert anime["name"] == "Cowboy Bebop"
        assert anime["episodes"] == "26"

        # Verify correct command was sent
        args, _ = mock_socket_instance.sendto.call_args
        assert b"ANIME" in args[0]
        assert b"aid=1" in args[0]

    @patch("plexomatic.api.anidb_client.socket.socket")
    def test_get_episodes(self, mock_socket: MagicMock) -> None:
        """Test retrieving episodes for an anime."""
        # Mock socket instance
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance

        # Set up mock response
        mock_socket_instance.recvfrom.return_value = (
            b"240 FILE\n"
            b"eid|1|aid|1|epno|1|length|24|airdate|1998-04-03|"
            b"english|Asteroid Blues|romaji|Asteroidoburusu",
            ("127.0.0.1", 9000),
        )

        # Test successful episode retrieval
        episodes = self.udp_client.get_episodes(1)
        assert episodes[0]["eid"] == "1"
        assert episodes[0]["epno"] == "1"
        assert episodes[0]["english"] == "Asteroid Blues"

        # Verify correct command was sent
        args, _ = mock_socket_instance.sendto.call_args
        assert b"EPISODE" in args[0]
        assert b"aid=1" in args[0]

    @patch("plexomatic.api.anidb_client.socket.socket")
    def test_rate_limiting(self, mock_socket: MagicMock) -> None:
        """Test handling of rate limiting."""
        # Mock socket instance
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance

        # Set up mock response for rate limit
        mock_socket_instance.recvfrom.return_value = (
            b"555 BANNED - SERVERSIDE RATE LIMIT REACHED",
            ("127.0.0.1", 9000),
        )

        # Test rate limit handling
        with pytest.raises(AniDBRateLimitError):
            self.udp_client.get_anime_by_name("Cowboy Bebop")


class TestAniDBHTTPClient:
    """Tests for the AniDB HTTP API client."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.client = AniDBHTTPClient(client_name="plexomatic")

    @patch("plexomatic.api.anidb_client.requests.get")
    def test_get_anime_titles(self, mock_get: MagicMock) -> None:
        """Test retrieving anime titles from the HTTP API."""
        # Mock XML response
        mock_response = MagicMock()
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

    @patch("plexomatic.api.anidb_client.requests.get")
    def test_get_anime_description(self, mock_get: MagicMock) -> None:
        """Test retrieving anime description from the HTTP API."""
        # Mock XML response
        mock_response = MagicMock()
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


class TestAniDBClient:
    """Tests for the main AniDB client that combines UDP and HTTP."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.username = "test_user"
        self.password = "test_password"
        self.client = AniDBClient(
            username=self.username,
            password=self.password,
            client_name="plexomatic",
            client_version="1",
        )

        # Patch the UDP and HTTP clients with MagicMock objects
        self.client.udp_client = MagicMock()
        self.client.http_client = MagicMock()

    def test_get_anime_by_name(self) -> None:
        """Test retrieving anime by name."""
        # Set up mock responses
        mock_anime_data = {
            "aid": "1",
            "name": "Cowboy Bebop",
            "episodes": "26",
            "type": "TV Series",
        }

        # Configure the mock to return the test data
        self.client.udp_client.get_anime_by_name.return_value = mock_anime_data  # type: ignore[attr-defined]

        # Test the method
        result = self.client.get_anime_by_name("Cowboy Bebop")

        # Verify results and calls
        assert result == mock_anime_data
        self.client.udp_client.get_anime_by_name.assert_called_with("Cowboy Bebop")  # type: ignore[attr-defined]

    def test_get_anime_details(self) -> None:
        """Test retrieving detailed anime information."""
        # Set up mock responses
        udp_data = {
            "aid": "1",
            "name": "Cowboy Bebop",
            "episodes": "26",
            "type": "TV Series",
        }
        http_data = {
            "id": "1",
            "description": "Space cowboys and bounty hunters...",
            "picture": "12345.jpg",
            "titles": [{"title": "Cowboy Bebop", "lang": "en", "type": "official"}],
        }

        # Configure the mocks to return test data
        self.client.udp_client.get_anime_by_id.return_value = udp_data  # type: ignore[attr-defined]
        self.client.http_client.get_anime_description.return_value = http_data  # type: ignore[attr-defined]

        # Test the method
        result = self.client.get_anime_details(1)

        # Verify results
        assert result["aid"] == "1"
        assert result["name"] == "Cowboy Bebop"
        assert result["episodes"] == "26"
        assert result["description"] == "Space cowboys and bounty hunters..."
        assert result["picture"] == "12345.jpg"

        # Verify calls
        self.client.udp_client.get_anime_by_id.assert_called_with(1)  # type: ignore[attr-defined]
        self.client.http_client.get_anime_description.assert_called_with(1)  # type: ignore[attr-defined]

    def test_get_episodes_with_titles(self) -> None:
        """Test retrieving episodes with title information."""
        # Set up mock responses
        episodes_data = [
            {
                "eid": "1",
                "epno": "1",
                "english": "Episode 1",
                "romaji": "Episode 1 JP",
                "title": "Episode 1",
            },
            {
                "eid": "2",
                "epno": "2",
                "english": "Episode 2",
                "romaji": "Episode 2 JP",
                "title": "Episode 2",
            },
        ]

        # Configure the mock to return test data
        self.client.udp_client.get_episodes.return_value = episodes_data  # type: ignore[attr-defined]

        # Test the method
        result = self.client.get_episodes_with_titles(1)

        # Verify results
        assert len(result) == 2
        assert result[0]["title"] == "Episode 1"
        assert result[0]["epno"] == "1"
        assert result[1]["title"] == "Episode 2"

        # Verify calls
        self.client.udp_client.get_episodes.assert_called_with(1)  # type: ignore[attr-defined]

    def test_map_title_to_series(self) -> None:
        """Test mapping a title to its series information."""
        # Set up mock responses
        titles_data = [
            {
                "aid": "1",
                "titles": [
                    {"title": "Cowboy Bebop", "lang": "en", "type": "official"},
                    {"title": "カウボーイビバップ", "lang": "ja", "type": "official"},
                ],
            },
            {
                "aid": "2",
                "titles": [{"title": "Trigun", "lang": "en", "type": "official"}],
            },
        ]

        # Configure the mock for get_anime_titles
        self.client.http_client.get_anime_titles.return_value = titles_data  # type: ignore[attr-defined]

        # Test finding a series
        result = self.client.map_title_to_series("Cowboy Bebop")

        # Verify result
        assert result == "1"

        # Verify calls
        self.client.http_client.get_anime_titles.assert_called_once()  # type: ignore[attr-defined]
