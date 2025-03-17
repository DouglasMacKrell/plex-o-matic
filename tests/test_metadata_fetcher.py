import pytest
from unittest.mock import MagicMock

from plexomatic.metadata.fetcher import (
    MetadataFetcher,
    TVDBMetadataFetcher,
    TMDBMetadataFetcher,
    AniDBMetadataFetcher,
    TVMazeMetadataFetcher,
    MediaType,
)


class TestMetadataFetcher:
    """Test the base MetadataFetcher class and its functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.fetcher = MetadataFetcher()

    def test_init(self) -> None:
        """Test initialization of the base fetcher."""
        assert hasattr(self.fetcher, "cache")
        assert hasattr(self.fetcher, "clear_cache")

    def test_fetch_metadata_not_implemented(self) -> None:
        """Test that fetch_metadata raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            self.fetcher.fetch_metadata("test", MediaType.TV_SHOW)

    def test_search_not_implemented(self) -> None:
        """Test that search raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            self.fetcher.search("test", MediaType.TV_SHOW)


class TestTVDBMetadataFetcher:
    """Test the TVDB metadata fetcher."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_tvdb_client = MagicMock()
        self.fetcher = TVDBMetadataFetcher(client=self.mock_tvdb_client)

    def test_search_tv_show(self) -> None:
        """Test searching for TV shows."""
        # Mock TVDB client response
        self.mock_tvdb_client.get_series_by_name.return_value = [
            {
                "id": 1,
                "seriesName": "Breaking Bad",
                "overview": "A chemistry teacher diagnosed with cancer.",
            }
        ]

        # Test search method
        results = self.fetcher.search("Breaking Bad", MediaType.TV_SHOW)

        # Verify results
        assert len(results) == 1
        assert results[0].id == "tvdb:1"
        assert results[0].title == "Breaking Bad"
        assert results[0].overview == "A chemistry teacher diagnosed with cancer."
        assert results[0].media_type == MediaType.TV_SHOW
        assert results[0].source == "tvdb"

    def test_search_movie_not_supported(self) -> None:
        """Test that searching for movies is not supported by TVDB fetcher."""
        with pytest.raises(ValueError, match="TVDB only supports TV shows"):
            self.fetcher.search("The Matrix", MediaType.MOVIE)

    def test_fetch_tv_show_metadata(self) -> None:
        """Test fetching TV show metadata."""
        # Mock responses
        self.mock_tvdb_client.get_series_by_id.return_value = {
            "id": 1,
            "seriesName": "Breaking Bad",
            "overview": "A chemistry teacher diagnosed with cancer.",
            "firstAired": "2008-01-20",
            "network": "AMC",
        }

        self.mock_tvdb_client.get_episodes_by_series_id.return_value = [
            {
                "id": 101,
                "airedSeason": 1,
                "airedEpisodeNumber": 1,
                "episodeName": "Pilot",
                "overview": "Walter White, a high school chemistry teacher.",
                "firstAired": "2008-01-20",
            }
        ]

        # Test fetch method
        result = self.fetcher.fetch_metadata("tvdb:1", MediaType.TV_SHOW)

        # Verify result
        assert result.id == "tvdb:1"
        assert result.title == "Breaking Bad"
        assert result.media_type == MediaType.TV_SHOW
        assert result.source == "tvdb"
        assert "episodes" in result.extra_data
        assert len(result.extra_data["episodes"]) == 1
        assert result.extra_data["episodes"][0]["title"] == "Pilot"
        assert result.extra_data["episodes"][0]["season"] == 1
        assert result.extra_data["episodes"][0]["episode"] == 1

    def test_cache_mechanism(self) -> None:
        """Test that caching works properly."""
        # Set up mock
        self.mock_tvdb_client.get_series_by_id.return_value = {
            "id": 1,
            "seriesName": "Breaking Bad",
            "overview": "A chemistry teacher diagnosed with cancer.",
        }

        self.mock_tvdb_client.get_episodes_by_series_id.return_value = [
            {"id": 101, "airedSeason": 1, "airedEpisodeNumber": 1, "episodeName": "Pilot"}
        ]

        # First call should hit the API
        result1 = self.fetcher.fetch_metadata("tvdb:1", MediaType.TV_SHOW)
        assert result1.title == "Breaking Bad"

        # Second call should use cache
        result2 = self.fetcher.fetch_metadata("tvdb:1", MediaType.TV_SHOW)
        assert result2.title == "Breaking Bad"

        # Verify the client was only called once
        assert self.mock_tvdb_client.get_series_by_id.call_count == 1
        assert self.mock_tvdb_client.get_episodes_by_series_id.call_count == 1


class TestTMDBMetadataFetcher:
    """Test the TMDB metadata fetcher."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_tmdb_client = MagicMock()
        self.fetcher = TMDBMetadataFetcher(client=self.mock_tmdb_client)

    def test_search_movie(self) -> None:
        """Test searching for movies."""
        # Mock TMDB client response
        self.mock_tmdb_client.search_movie.return_value = {
            "results": [
                {
                    "id": 603,
                    "title": "The Matrix",
                    "overview": "A computer hacker learns about the true nature of reality.",
                    "release_date": "1999-03-31",
                }
            ]
        }

        # Test search method
        results = self.fetcher.search("The Matrix", MediaType.MOVIE)

        # Verify results
        assert len(results) == 1
        assert results[0].id == "tmdb:603"
        assert results[0].title == "The Matrix"
        assert results[0].overview == "A computer hacker learns about the true nature of reality."
        assert results[0].media_type == MediaType.MOVIE
        assert results[0].source == "tmdb"
        assert results[0].extra_data["release_date"] == "1999-03-31"

    def test_search_tv_show(self) -> None:
        """Test searching for TV shows using TMDB."""
        # Mock TMDB client response
        self.mock_tmdb_client.search_tv.return_value = {
            "results": [
                {
                    "id": 66732,
                    "name": "Stranger Things",
                    "overview": "When a young boy disappears...",
                    "first_air_date": "2016-07-15",
                }
            ]
        }

        # Test search method
        results = self.fetcher.search("Stranger Things", MediaType.TV_SHOW)

        # Verify results
        assert len(results) == 1
        assert results[0].id == "tmdb:66732"
        assert results[0].title == "Stranger Things"
        assert results[0].media_type == MediaType.TV_SHOW
        assert results[0].source == "tmdb"
        assert results[0].extra_data["first_air_date"] == "2016-07-15"

    def test_fetch_movie_metadata(self) -> None:
        """Test fetching movie metadata."""
        # Mock responses
        self.mock_tmdb_client.get_movie_details.return_value = {
            "id": 603,
            "title": "The Matrix",
            "overview": "A computer hacker learns about the true nature of reality.",
            "release_date": "1999-03-31",
            "runtime": 136,
            "genres": [{"id": 28, "name": "Action"}, {"id": 878, "name": "Science Fiction"}],
        }

        # Test fetch method
        result = self.fetcher.fetch_metadata("tmdb:603", MediaType.MOVIE)

        # Verify result
        assert result.id == "tmdb:603"
        assert result.title == "The Matrix"
        assert result.media_type == MediaType.MOVIE
        assert result.source == "tmdb"
        assert result.extra_data["release_date"] == "1999-03-31"
        assert result.extra_data["runtime"] == 136
        assert "Action" in result.extra_data["genres"]

    def test_fetch_tv_show_metadata(self) -> None:
        """Test fetching TV show metadata."""
        # Mock responses
        self.mock_tmdb_client.get_tv_details.return_value = {
            "id": 66732,
            "name": "Stranger Things",
            "overview": "When a young boy disappears...",
            "first_air_date": "2016-07-15",
            "number_of_seasons": 4,
        }

        self.mock_tmdb_client.get_tv_season.return_value = {
            "season_number": 1,
            "episodes": [
                {
                    "episode_number": 1,
                    "name": "Chapter One: The Vanishing of Will Byers",
                    "overview": "On his way home from a friend's house...",
                }
            ],
        }

        # Test fetch method
        result = self.fetcher.fetch_metadata("tmdb:66732", MediaType.TV_SHOW)

        # Verify result
        assert result.id == "tmdb:66732"
        assert result.title == "Stranger Things"
        assert result.media_type == MediaType.TV_SHOW
        assert result.source == "tmdb"
        assert result.extra_data["first_air_date"] == "2016-07-15"
        assert result.extra_data["number_of_seasons"] == 4
        assert result.extra_data["seasons"][0]["season_number"] == 1
        assert (
            result.extra_data["seasons"][0]["episodes"][0]["name"]
            == "Chapter One: The Vanishing of Will Byers"
        )


class TestAniDBMetadataFetcher:
    """Test the AniDB metadata fetcher."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_anidb_client = MagicMock()
        self.fetcher = AniDBMetadataFetcher(client=self.mock_anidb_client)

    def test_search_anime(self) -> None:
        """Test searching for anime."""
        # Mock AniDB client response
        self.mock_anidb_client.get_anime_by_name.return_value = [
            {
                "aid": 1,
                "title": "Cowboy Bebop",
                "description": "The futuristic misadventures of a crew of bounty hunters.",
                "type": "TV Series",
                "episodes": 26,
            }
        ]

        # Test search method
        results = self.fetcher.search("Cowboy Bebop", MediaType.ANIME)

        # Verify results
        assert len(results) == 1
        assert results[0].id == "anidb:1"
        assert results[0].title == "Cowboy Bebop"
        assert results[0].overview == "The futuristic misadventures of a crew of bounty hunters."
        assert results[0].media_type == MediaType.ANIME
        assert results[0].source == "anidb"
        assert results[0].extra_data["episodes"] == 26

    def test_fetch_anime_metadata(self) -> None:
        """Test fetching anime metadata."""
        # Mock responses
        self.mock_anidb_client.get_anime_details.return_value = {
            "aid": 1,
            "title": "Cowboy Bebop",
            "description": "The futuristic misadventures of a crew of bounty hunters.",
            "type": "TV Series",
            "episodes": 26,
        }

        self.mock_anidb_client.get_episodes_with_titles.return_value = [
            {"epno": 1, "title": "Asteroid Blues", "length": 25}
        ]

        # Test fetch method
        result = self.fetcher.fetch_metadata("anidb:1", MediaType.ANIME)

        # Verify result
        assert result.id == "anidb:1"
        assert result.title == "Cowboy Bebop"
        assert result.media_type == MediaType.ANIME
        assert result.source == "anidb"
        assert result.extra_data["type"] == "TV Series"
        assert result.extra_data["episodes_count"] == 26
        assert result.extra_data["episodes"][0]["title"] == "Asteroid Blues"
        assert result.extra_data["episodes"][0]["number"] == 1


class TestTVMazeMetadataFetcher:
    """Test the TVMaze metadata fetcher."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_tvmaze_client = MagicMock()
        self.fetcher = TVMazeMetadataFetcher(client=self.mock_tvmaze_client)

    def test_search_tv_show(self) -> None:
        """Test searching for TV shows."""
        # Mock TVMaze client response
        self.mock_tvmaze_client.search_shows.return_value = [
            {
                "score": 0.9,
                "show": {
                    "id": 1,
                    "name": "Breaking Bad",
                    "summary": "<p>A chemistry teacher diagnosed with cancer.</p>",
                    "premiered": "2008-01-20",
                    "network": {"name": "AMC"},
                },
            }
        ]

        # Test search method
        results = self.fetcher.search("Breaking Bad", MediaType.TV_SHOW)

        # Verify results
        assert len(results) == 1
        assert results[0].id == "tvmaze:1"
        assert results[0].title == "Breaking Bad"
        assert results[0].overview == "A chemistry teacher diagnosed with cancer."
        assert results[0].media_type == MediaType.TV_SHOW
        assert results[0].source == "tvmaze"
        assert results[0].extra_data["premiered"] == "2008-01-20"

    def test_fetch_tv_show_metadata(self) -> None:
        """Test fetching TV show metadata."""
        # Mock responses
        self.mock_tvmaze_client.get_show_by_id.return_value = {
            "id": 1,
            "name": "Breaking Bad",
            "summary": "<p>A chemistry teacher diagnosed with cancer.</p>",
            "premiered": "2008-01-20",
            "network": {"name": "AMC"},
        }

        self.mock_tvmaze_client.get_episodes.return_value = [
            {
                "id": 1,
                "name": "Pilot",
                "summary": "<p>Walter White, a high school chemistry teacher.</p>",
                "season": 1,
                "number": 1,
                "airdate": "2008-01-20",
            }
        ]

        self.mock_tvmaze_client.get_show_cast.return_value = [
            {
                "person": {"id": 1, "name": "Bryan Cranston"},
                "character": {"id": 1, "name": "Walter White"},
            }
        ]

        # Test fetch method
        result = self.fetcher.fetch_metadata("tvmaze:1", MediaType.TV_SHOW)

        # Verify result
        assert result.id == "tvmaze:1"
        assert result.title == "Breaking Bad"
        assert result.media_type == MediaType.TV_SHOW
        assert result.source == "tvmaze"
        assert result.extra_data["premiered"] == "2008-01-20"
        assert result.extra_data["network"] == "AMC"
        assert len(result.extra_data["episodes"]) == 1
        assert result.extra_data["episodes"][0]["title"] == "Pilot"
        assert result.extra_data["episodes"][0]["season"] == 1
        assert result.extra_data["episodes"][0]["episode"] == 1
        assert result.extra_data["cast"][0]["actor"] == "Bryan Cranston"
        assert result.extra_data["cast"][0]["character"] == "Walter White"
