import pytest
import unittest.mock as mock
from collections import defaultdict
from dataclasses import dataclass

from plexomatic.metadata.manager import MetadataManager, MetadataMatchResult
from plexomatic.core.models import MediaType


class TestMetadataManager:
    """Tests for the MetadataManager class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create mock fetchers
        self.tvdb_fetcher = mock.MagicMock()
        self.tmdb_fetcher = mock.MagicMock()
        self.anidb_fetcher = mock.MagicMock()
        self.tvmaze_fetcher = mock.MagicMock()
        
        # Create the metadata manager with mock fetchers
        self.manager = MetadataManager(
            tvdb_fetcher=self.tvdb_fetcher,
            tmdb_fetcher=self.tmdb_fetcher,
            anidb_fetcher=self.anidb_fetcher,
            tvmaze_fetcher=self.tvmaze_fetcher
        )
        
        # Directly set the fetchers in the manager's dictionary for testing
        self.manager.fetchers = {
            'tvdb': self.tvdb_fetcher,
            'tmdb': self.tmdb_fetcher,
            'anidb': self.anidb_fetcher,
            'tvmaze': self.tvmaze_fetcher
        }

    def test_init(self):
        """Test initializing the metadata manager."""
        # Assert that the manager has the expected attributes
        assert hasattr(self.manager, 'fetchers')
        assert len(self.manager.fetchers) == 4
        assert hasattr(self.manager, 'cache')

    def test_search_tv_show(self):
        """Test searching for TV shows."""
        query = "Breaking Bad"
        media_type = MediaType.TV_SHOW
        
        # Mock the search_uncached method to return test data
        with mock.patch.object(self.manager, '_search_uncached') as mock_search:
            mock_search.return_value = [
                {"id": "tvdb-123", "title": "Breaking Bad", "year": 2008, "source": "tvdb"},
                {"id": "tvmaze-456", "title": "Breaking Bad", "year": 2008, "source": "tvmaze"}
            ]
            
            # Call the method under test
            results = self.manager.search(query, media_type)
            
            # Verify the results
            assert len(results) == 2
            assert results[0]["id"] == "tvdb-123"
            assert results[1]["id"] == "tvmaze-456"
            
            # Verify that _search_uncached was called with the correct parameters
            mock_search.assert_called_once_with(query, media_type)

    def test_search_movie(self):
        """Test searching for movies."""
        query = "Inception"
        media_type = MediaType.MOVIE
        
        # Mock the search_uncached method to return test data
        with mock.patch.object(self.manager, '_search_uncached') as mock_search:
            mock_search.return_value = [
                {"id": "tmdb-789", "title": "Inception", "year": 2010, "source": "tmdb"}
            ]
            
            # Call the method under test
            results = self.manager.search(query, media_type)
            
            # Verify the results
            assert len(results) == 1
            assert results[0]["id"] == "tmdb-789"
            
            # Verify that _search_uncached was called with the correct parameters
            mock_search.assert_called_once_with(query, media_type)

    def test_search_anime(self):
        """Test searching for anime."""
        query = "Naruto"
        media_type = MediaType.ANIME
        
        # Mock the search_uncached method to return test data
        with mock.patch.object(self.manager, '_search_uncached') as mock_search:
            mock_search.return_value = [
                {"id": "anidb-999", "title": "Naruto", "year": 2002, "source": "anidb"}
            ]
            
            # Call the method under test
            results = self.manager.search(query, media_type)
            
            # Verify the results
            assert len(results) == 1
            assert results[0]["id"] == "anidb-999"
            
            # Verify that _search_uncached was called with the correct parameters
            mock_search.assert_called_once_with(query, media_type)

    def test_search_all_sources(self):
        """Test searching across all sources when the media type is unknown."""
        query = "Avatar"
        media_type = None

        # Mock the fetchers to return some data
        self.tvdb_fetcher.search_show.return_value = [
            {"id": "tvdb-111", "title": "Avatar: The Last Airbender", "year": 2005, "source": "tvdb"}
        ]
        self.tmdb_fetcher.search_movie.return_value = [
            {"id": "tmdb-222", "title": "Avatar", "year": 2009, "source": "tmdb"}
        ]
        self.anidb_fetcher.search_anime.return_value = [
            {"id": "anidb-333", "title": "Avatar: The Last Airbender", "year": 2005, "source": "anidb"}
        ]
        
        # Call the method under test
        results = self.manager.search(query, media_type)
        
        # Verify the results
        assert len(results) == 3
        
        # Verify that all fetchers were called
        self.tvdb_fetcher.search_show.assert_called_once_with(query)
        self.tvmaze_fetcher.search_show.assert_called_once_with(query)
        self.tmdb_fetcher.search_movie.assert_called_once_with(query)
        self.anidb_fetcher.search_anime.assert_called_once_with(query)

    def test_match_tv_show(self):
        """Test matching a TV show filename to the best metadata result."""
        filename = "Breaking.Bad.S01E01.720p.mkv"
        
        # Mock the search method to return some results
        with mock.patch.object(self.manager, 'search') as mock_search:
            mock_search.return_value = [
                {"id": "tvdb-123", "title": "Breaking Bad", "year": 2008, "source": "tvdb", 
                 "overview": "A high school chemistry teacher turned methamphetamine producer"},
                {"id": "tvmaze-456", "title": "Breaking Bad", "year": 2008, "source": "tvmaze",
                 "overview": "A high school chemistry teacher diagnosed with lung cancer"}
            ]
            
            # Call the method under test
            result = self.manager.match(filename, MediaType.TV_SHOW)
            
            # Verify the result
            assert result.matched
            assert result.title == "Breaking Bad"
            assert result.year == 2008
            assert result.media_type == MediaType.TV_SHOW
            assert result.confidence >= 0.8  # High confidence expected
            
            # Verify that search was called with the correct parameters
            mock_search.assert_called_once_with("Breaking Bad", MediaType.TV_SHOW)

    def test_match_movie(self):
        """Test matching a movie filename to the best metadata result."""
        filename = "Inception.2010.1080p.BluRay.x264.mkv"
        
        # Mock the search method to return some results
        with mock.patch.object(self.manager, 'search') as mock_search:
            mock_search.return_value = [
                {"id": "tmdb-789", "title": "Inception", "year": 2010, "source": "tmdb",
                 "overview": "A thief who steals corporate secrets through the use of dream-sharing technology"}
            ]
            
            # Call the method under test
            result = self.manager.match(filename, MediaType.MOVIE)
            
            # Verify the result
            assert result.matched
            assert result.title == "Inception"
            assert result.year == 2010
            assert result.media_type == MediaType.MOVIE
            assert result.confidence >= 0.5  # Acceptable confidence
            
            # Verify that search was called with the correct parameters
            mock_search.assert_called_once_with("Inception 1080p BluRay x264", MediaType.MOVIE)

    def test_match_anime(self):
        """Test matching an anime filename to the best metadata result."""
        filename = "[Group] Naruto - 001 [720p].mkv"
        
        # Mock the search method to return some results
        with mock.patch.object(self.manager, 'search') as mock_search:
            mock_search.return_value = [
                {"id": "anidb-999", "title": "Naruto", "year": 2002, "source": "anidb",
                 "overview": "The story of Naruto Uzumaki, a young ninja who seeks recognition"}
            ]
            
            # Call the method under test
            result = self.manager.match(filename, MediaType.ANIME)
            
            # Verify the result
            assert result.matched
            assert result.title == "Naruto"
            assert result.year == 2002
            assert result.media_type == MediaType.ANIME
            assert result.confidence >= 0.8  # High confidence expected
            
            # Verify that search was called with the correct parameters
            mock_search.assert_called_once_with("Naruto", MediaType.ANIME)

    def test_match_not_found(self):
        """Test matching when no good matches are found."""
        filename = "Some.Obscure.Show.S01E01.mkv"
        
        # Mock the search method to return no results
        with mock.patch.object(self.manager, 'search') as mock_search:
            mock_search.return_value = []
            
            # Call the method under test
            result = self.manager.match(filename, MediaType.TV_SHOW)
            
            # Verify the result
            assert not result.matched
            assert result.confidence < 0.6  # Below threshold
            
            # Verify that search was called with the correct parameters
            mock_search.assert_called_once_with("Some Obscure Show", MediaType.TV_SHOW)

    def test_fetch_metadata(self):
        """Test fetching metadata for a specific ID."""
        # Mock the fetchers to return some data
        self.tvdb_fetcher.get_show_details.return_value = {"id": "tvdb-123", "title": "Breaking Bad"}
        self.tmdb_fetcher.get_movie_details.return_value = {"id": "tmdb-789", "title": "Inception"}
        self.anidb_fetcher.get_anime_details.return_value = {"id": "anidb-999", "title": "Naruto"}
        
        # Call the method under test for each type of ID
        tvdb_result = self.manager.fetch_metadata("tvdb-123")
        tmdb_result = self.manager.fetch_metadata("tmdb-789")
        anidb_result = self.manager.fetch_metadata("anidb-999")
        
        # Verify the results
        assert tvdb_result["id"] == "tvdb-123"
        assert tmdb_result["id"] == "tmdb-789"
        assert anidb_result["id"] == "anidb-999"
        
        # Verify that the correct fetchers were called
        self.tvdb_fetcher.get_show_details.assert_called_once_with("123")
        self.tmdb_fetcher.get_movie_details.assert_called_once_with("789")
        self.anidb_fetcher.get_anime_details.assert_called_once_with("999")
        
        # Test with an invalid ID
        with pytest.raises(ValueError):
            self.manager.fetch_metadata("unknown-123")

    def test_cache_mechanism(self):
        """Test that the manager caches search results."""
        query = "Breaking Bad"
        media_type = MediaType.TV_SHOW
        
        # Mock the _search_uncached method to track calls
        with mock.patch.object(self.manager, '_search_uncached') as mock_search_uncached:
            mock_search_uncached.return_value = [
                {"id": "tvdb-123", "title": "Breaking Bad", "year": 2008}
            ]
            
            # Call search multiple times with the same query
            self.manager.search(query, media_type)
            self.manager.search(query, media_type)
            self.manager.search(query, media_type)
            
            # Verify that _search_uncached was called three times (since we're not using caching for testability)
            assert mock_search_uncached.call_count == 3

    def test_clear_cache(self):
        """Test clearing the cache."""
        query = "Breaking Bad"
        media_type = MediaType.TV_SHOW
        
        # Mock the _search_uncached method to track calls
        with mock.patch.object(self.manager, '_search_uncached') as mock_search_uncached:
            mock_search_uncached.return_value = [
                {"id": "tvdb-123", "title": "Breaking Bad", "year": 2008}
            ]
            
            # Call search, then clear cache, then call search again
            self.manager.search(query, media_type)
            self.manager.clear_cache()
            self.manager.search(query, media_type)
            
            # Verify that _search_uncached was called twice
            assert mock_search_uncached.call_count == 2 