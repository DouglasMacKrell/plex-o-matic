"""Integration tests for API clients.

These tests make real API calls and should be run with:
pytest tests/api/test_api_integration.py -v --run-integration
"""

import pytest
from typing import Generator

from plexomatic.api.musicbrainz_client import MusicBrainzClient
from plexomatic.api.tvdb_client import TVDBClient
from plexomatic.api.tmdb_client import TMDBClient
from plexomatic.api.tvmaze_client import TVMazeClient
from plexomatic.api.anidb_client import AniDBClient
from plexomatic.config.config_manager import ConfigManager
from plexomatic.api.anidb_client import AniDBError


def pytest_addoption(parser):
    """Add command line option to run integration tests."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests against real APIs",
    )


def pytest_configure(config):
    """Add marker for integration tests."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test that makes real API calls",
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless --run-integration is specified."""
    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="Need --run-integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


@pytest.fixture(scope="session")
def config() -> ConfigManager:
    """Create a config manager for testing."""
    return ConfigManager()


@pytest.fixture
def musicbrainz_client() -> MusicBrainzClient:
    """Create a MusicBrainz client for testing."""
    return MusicBrainzClient(
        app_name="Plex-o-matic-test",
        app_version="1.0",
        contact_email="test@example.com",
        auto_retry=True,
    )


@pytest.fixture
def tvdb_client(config: ConfigManager) -> TVDBClient:
    """Create a TVDB client for testing."""
    api_config = config.get("api", {}).get("tvdb", {})
    api_key = api_config.get("api_key")
    if not api_key:
        pytest.skip("TVDB API key not found in config")
    return TVDBClient(api_key=api_key)


@pytest.fixture
def tmdb_client(config: ConfigManager) -> TMDBClient:
    """Create a TMDB client for testing."""
    api_config = config.get("api", {}).get("tmdb", {})
    api_key = api_config.get("api_key")
    if not api_key:
        pytest.skip("TMDB API key not found in config")
    return TMDBClient(api_key=api_key)


@pytest.fixture
def tvmaze_client() -> TVMazeClient:
    """Create a TVMaze client for testing."""
    return TVMazeClient()


@pytest.fixture
def anidb_client(config: ConfigManager) -> AniDBClient:
    """Create an AniDB client for testing."""
    api_config = config.get("api", {}).get("anidb", {})
    username = api_config.get("username")
    password = api_config.get("password")
    if not username or not password:
        pytest.skip("AniDB credentials not found in config")
    return AniDBClient(username=username, password=password)


class TestAPIIntegration:
    """Integration tests for API clients."""

    @pytest.mark.integration
    def test_musicbrainz_api(self, musicbrainz_client: MusicBrainzClient) -> None:
        """Test MusicBrainz API with real requests."""
        # Test artist search
        artists = musicbrainz_client.search_artist("The Beatles")
        assert artists
        assert any(a["name"] == "The Beatles" for a in artists)

        # Test release search
        releases = musicbrainz_client.search_release("Abbey Road")
        assert releases
        assert any(r["title"] == "Abbey Road" for r in releases)

        # Test full verification
        result, confidence = musicbrainz_client.verify_music_file(
            artist="The Beatles",
            album="Abbey Road",
            track="Come Together",
        )
        assert result["artist"] == "The Beatles"
        assert result["album"] == "Abbey Road"
        assert result["track"] == "Come Together"
        assert confidence > 0.5

    @pytest.mark.integration
    def test_tvdb_api(self, tvdb_client: TVDBClient) -> None:
        """Test TVDB API with real requests."""
        # Test series search
        series = tvdb_client.get_series_by_name("Breaking Bad")
        assert series
        assert any(s["name"] == "Breaking Bad" for s in series)

        # Test series details
        series_id = next(s["id"] for s in series if s["name"] == "Breaking Bad")
        details = tvdb_client.get_series(series_id)
        assert details["name"] == "Breaking Bad"

    @pytest.mark.integration
    def test_tmdb_api(self, tmdb_client: TMDBClient) -> None:
        """Test TMDB API with real requests."""
        # Test movie search
        movies = tmdb_client.search_movie("The Matrix")
        assert movies
        assert any(m["title"] == "The Matrix" for m in movies)

        # Test movie details
        movie_id = next(m["id"] for m in movies if m["title"] == "The Matrix")
        details = tmdb_client.get_movie_details(movie_id)
        assert details["title"] == "The Matrix"

    @pytest.mark.integration
    def test_tvmaze_api(self, tvmaze_client: TVMazeClient) -> None:
        """Test TVMaze API with real requests."""
        # Test show search
        shows = tvmaze_client.search_shows("The Office US")
        assert shows
        assert any("The Office" in s["show"]["name"] for s in shows)

        # Test show details
        show_id = next(s["show"]["id"] for s in shows if "The Office" in s["show"]["name"])
        details = tvmaze_client.get_show_by_id(show_id)
        assert "The Office" in details["name"]

    @pytest.mark.integration
    def test_anidb_api(self, anidb_client: AniDBClient) -> None:
        """Test AniDB API with real requests."""
        try:
            # Test anime search
            result = anidb_client.get_anime_by_name("Cowboy Bebop")
            assert result
            assert "Cowboy Bebop" in result["title"]

            # Test anime details
            anime_id = result["id"]
            details = anidb_client.get_anime_details(anime_id)
            assert "Cowboy Bebop" in details["title"]
        except AniDBError as e:
            if "CLIENT BANNED" in str(e):
                pytest.skip("AniDB client is temporarily banned - this is normal")
            else:
                raise 