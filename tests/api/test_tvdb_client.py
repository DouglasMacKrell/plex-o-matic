import pytest
from unittest.mock import patch, MagicMock, ANY
from datetime import datetime, timezone, timedelta
import requests

from plexomatic.api.tvdb_client import (
    TVDBClient,
    TVDBAuthenticationError,
    TVDBRequestError,
    TVDBRateLimitError,
    SERIES_URL,
    SERIES_EXTENDED_URL,
    SEASON_EPISODES_URL,
)


class TestTVDBClient:
    """Tests for the TVDB API client."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.api_key = "test_api_key"
        self.pin = "test_pin"
        self.client = TVDBClient(api_key=self.api_key, pin=self.pin)
        # Pre-set a token to avoid automatic authentication
        self.client.token = "pre_auth_token"
        self.client.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    @patch("plexomatic.api.tvdb_client.requests.post")
    def test_authentication_success(self, mock_post: MagicMock) -> None:
        """Test successful authentication process."""
        # Reset the token for authentication testing
        self.client.token = None
        self.client.token_expires_at = None

        # Test successful authentication
        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {"data": {"token": "mock_token"}}
        mock_post.return_value = mock_success_response

        self.client.authenticate()
        mock_post.assert_called_once()
        assert self.client.token == "mock_token"
        assert self.client.token_expires_at is not None

    @patch("plexomatic.api.tvdb_client.requests.post")
    def test_authentication_v4(self, mock_post: MagicMock) -> None:
        """Test that authenticate method correctly uses the v4 API."""
        # Reset the token for authentication testing
        self.client.token = None
        self.client.token_expires_at = None
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "token": "test_token"
            }
        }
        mock_post.return_value = mock_response
        
        # Call the authenticate method
        self.client.authenticate()
        
        # Verify correct endpoint and payload
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        
        # Verify the URL is v4
        assert args[0] == "https://api4.thetvdb.com/v4/login"
        
        # Verify the payload contains both api_key and pin
        payload = kwargs.get('json', {})
        assert payload["apikey"] == self.api_key
        assert payload["pin"] == self.pin
        
        # Verify token is stored
        assert self.client.token == "test_token"
        assert self.client.token_expires_at is not None

    @patch("plexomatic.api.tvdb_client.requests.post")
    def test_authentication_no_pin(self, mock_post: MagicMock) -> None:
        """Test authentication without a PIN."""
        # Create client without PIN
        client_no_pin = TVDBClient(api_key=self.api_key)
        
        # Reset the token for authentication testing
        client_no_pin.token = None
        client_no_pin.token_expires_at = None
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "token": "test_token"
            }
        }
        mock_post.return_value = mock_response
        
        # Call the authenticate method
        client_no_pin.authenticate()
        
        # Verify payload only contains api_key
        args, kwargs = mock_post.call_args
        payload = kwargs.get('json', {})
        assert payload["apikey"] == self.api_key
        assert "pin" not in payload

    @patch("plexomatic.api.tvdb_client.requests.post")
    def test_authentication_failure(self, mock_post: MagicMock) -> None:
        """Test authentication failure."""
        # Reset the token for authentication testing
        self.client.token = None
        self.client.token_expires_at = None

        mock_failure_response = MagicMock()
        mock_failure_response.status_code = 401
        # Mock both text and json response to ensure compatibility
        mock_failure_response.text = "Invalid API key"
        mock_failure_response.json.return_value = {"error": "Invalid credentials"}
        mock_post.return_value = mock_failure_response

        with pytest.raises(TVDBAuthenticationError):
            self.client.authenticate()

    def test_is_authenticated(self) -> None:
        """Test the is_authenticated method."""
        # Not authenticated
        self.client.token = None
        self.client.token_expires_at = None
        assert not self.client.is_authenticated()
        
        # Token but no expiration
        self.client.token = "test_token"
        self.client.token_expires_at = None
        assert not self.client.is_authenticated()
        
        # Expired token
        self.client.token = "test_token"
        self.client.token_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        assert not self.client.is_authenticated()
        
        # Valid token
        self.client.token = "test_token"
        self.client.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        assert self.client.is_authenticated()

    @patch("plexomatic.api.tvdb_client.requests.get")
    def test_get_series_by_name(self, mock_get: MagicMock) -> None:
        """Test retrieving series by name."""
        # Mock successful series search response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": 12345,
                    "seriesName": "Test Show",
                    "status": "Continuing",
                    "firstAired": "2020-01-01",
                    "network": "Test Network",
                }
            ]
        }
        mock_get.return_value = mock_response

        # Test successful series search
        result = self.client.get_series_by_name("Test Show")
        assert result[0]["id"] == 12345
        assert result[0]["seriesName"] == "Test Show"
        mock_get.assert_called_once()

        # Test series not found
        mock_response.json.return_value = {"data": []}
        mock_get.reset_mock()
        self.client.clear_cache()  # Clear cache to ensure the mock is called again
        result = self.client.get_series_by_name("Nonexistent Show")
        assert result == []

    @patch("plexomatic.api.tvdb_client.requests.get")
    def test_get_series_by_id(self, mock_get: MagicMock) -> None:
        """Test retrieving series details by ID."""
        # Mock successful series details response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": 12345,
                "seriesName": "Test Show",
                "status": "Continuing",
                "firstAired": "2020-01-01",
                "network": "Test Network",
                "overview": "Test overview",
            }
        }
        mock_get.return_value = mock_response

        # Test successful series details retrieval
        result = self.client.get_series(12345)

        assert result["id"] == 12345
        assert result["seriesName"] == "Test Show"

        # Verify get was called with correct URL
        mock_get.assert_called_once_with(f"{SERIES_URL}/12345", headers=ANY)

    @patch("plexomatic.api.tvdb_client.requests.get")
    def test_get_episodes_by_series_id(self, mock_get: MagicMock) -> None:
        """Test retrieving episodes for a series."""
        # Mock successful episodes response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "episodes": [
                    {
                        "id": 1001,
                        "seasonNumber": 1,
                        "episodeNumber": 1,
                        "name": "Pilot",
                        "aired": "2020-01-01",
                    },
                    {
                        "id": 1002,
                        "seasonNumber": 1,
                        "episodeNumber": 2,
                        "name": "Episode 2",
                        "aired": "2020-01-08",
                    },
                ]
            }
        }
        mock_get.return_value = mock_response

        # Test successful episodes retrieval
        result = self.client.get_episodes_by_series_id(12345)

        assert len(result) == 2
        assert result[0]["id"] == 1001
        assert result[0]["seasonNumber"] == 1

        # Verify the API URL is correctly constructed
        mock_get.assert_called_once()

    @patch("plexomatic.api.tvdb_client.requests.get")
    def test_rate_limiting(self, mock_get: MagicMock) -> None:
        """Test handling of rate limiting."""
        # First response is rate limited
        rate_limited_response = MagicMock()
        rate_limited_response.status_code = 429
        rate_limited_response.headers = {"Retry-After": "60"}
        rate_limited_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "429 Client Error: Too Many Requests", response=rate_limited_response
        )

        # Configure the mock
        mock_get.return_value = rate_limited_response

        # Get series (should handle the rate limit)
        result = self.client.get_series_by_name("Test Show")

        # We should have an empty result
        assert result == []

        # Verify the response is appropriately handled
        mock_get.assert_called_once()

    @patch("time.sleep")
    @patch("plexomatic.api.tvdb_client.requests.get")
    def test_automatic_retry_after_rate_limit(
        self, mock_get: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Test automatic retry after rate limiting when auto_retry is enabled."""
        # Initialize client with auto_retry
        self.client = TVDBClient(api_key="test_key", auto_retry=True)

        # First response is rate limited
        rate_limited_response = MagicMock()
        rate_limited_response.status_code = 429
        rate_limited_response.headers = {"Retry-After": "60"}
        rate_limited_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "429 Client Error: Too Many Requests", response=rate_limited_response
        )

        # Second response is successful
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {"data": [{"id": 12345, "seriesName": "Test Show"}]}

        # Configure the mock to return rate_limited_response first, then success_response
        mock_get.side_effect = [rate_limited_response, success_response]

        # Get series (should automatically retry)
        with patch.object(self.client, "authenticate"):  # Mock authenticate to avoid actual auth
            result = self.client.get_series_by_name("Test Show")

        # We should get the successful result
        assert result == [{"id": 12345, "seriesName": "Test Show"}]

        # Verify get was called twice and sleep was called once
        assert mock_get.call_count == 2
        mock_sleep.assert_not_called()  # We're not using sleep anymore, we return error data instead

    @patch("plexomatic.api.tvdb_client.requests.get")
    def test_cache_mechanism(self, mock_get: MagicMock) -> None:
        """Test that the cache mechanism works properly."""
        # Mock successful series response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": 12345, "seriesName": "Test Show"}]}
        mock_get.return_value = mock_response

        # Call get_series_by_name twice with the same query
        result1 = self.client.get_series_by_name("Test Show")
        result2 = self.client.get_series_by_name("Test Show")

        # Verify mock was called only once (second call used cache)
        assert mock_get.call_count == 1
        assert result1 == result2

        # Now test a different query
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {"data": [{"id": 67890, "seriesName": "Another Show"}]}
        mock_get.return_value = mock_response2

        # Call with a different query
        result3 = self.client.get_series_by_name("Another Show")

        # Verify mock was called again
        assert mock_get.call_count == 2
        assert result3 != result1
        assert result3[0]["id"] == 67890

        # Clear cache and verify that the mock is called again for the first query
        self.client.clear_cache()
        self.client.get_series_by_name("Test Show")
        assert mock_get.call_count == 3

    @patch("plexomatic.api.tvdb_client.requests.get")
    def test_get_series_extended(self, mock_get: MagicMock) -> None:
        """Test retrieving extended series details by ID."""
        # Mock successful series extended response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": 12345,
                "name": "Test Show",
                "status": "Continuing",
                "firstAired": "2020-01-01",
                "network": "Test Network",
                "overview": "Test overview",
                "seasons": [
                    {"id": 1001, "number": 1, "name": "Season 1", "episodeCount": 10},
                    {"id": 1002, "number": 2, "name": "Season 2", "episodeCount": 8},
                ],
            }
        }
        mock_get.return_value = mock_response

        # Test successful extended series details retrieval
        result = self.client.get_series_extended(12345)

        assert result["id"] == 12345
        assert result["name"] == "Test Show"
        assert "seasons" in result
        assert len(result["seasons"]) == 2

        # Verify get was called with correct URL
        mock_get.assert_called_once()

    @patch("plexomatic.api.tvdb_client.requests.get")
    def test_get_series_seasons(self, mock_get: MagicMock) -> None:
        """Test retrieving seasons for a TV series."""
        # Mock successful seasons response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": 1001, "number": 1, "name": "Season 1", "episodeCount": 10},
                {"id": 1002, "number": 2, "name": "Season 2", "episodeCount": 8},
            ]
        }
        mock_get.return_value = mock_response

        # Test successful seasons retrieval
        result = self.client.get_series_seasons(12345)

        assert len(result) == 2
        assert result[0]["id"] == 1001
        assert result[0]["number"] == 1
        assert result[1]["id"] == 1002

        # Verify get was called with correct URL
        mock_get.assert_called_once()

    @patch("plexomatic.api.tvdb_client.requests.get")
    def test_get_season_episodes(self, mock_get: MagicMock) -> None:
        """Test retrieving episodes for a specific season."""
        # Mock responses for series extended and season episodes
        series_extended_response = MagicMock()
        series_extended_response.status_code = 200
        series_extended_response.json.return_value = {
            "data": {
                "id": 12345,
                "name": "Test Show",
                "seasons": [
                    {"id": 1001, "number": 1, "name": "Season 1"},
                    {"id": 1002, "number": 2, "name": "Season 2"},
                ],
            }
        }

        season_episodes_response = MagicMock()
        season_episodes_response.status_code = 200
        season_episodes_response.json.return_value = {
            "data": {
                "episodes": [
                    {"id": 5001, "name": "Episode 1", "seasonNumber": 1, "episodeNumber": 1},
                    {"id": 5002, "name": "Episode 2", "seasonNumber": 1, "episodeNumber": 2},
                ]
            }
        }

        # Configure mock to return different responses based on URL
        def side_effect(url, headers):
            if SERIES_EXTENDED_URL.format(series_id=12345) in url:
                return series_extended_response
            if SEASON_EPISODES_URL.format(season_id=1001) in url:
                return season_episodes_response
            # Return a default empty response for unexpected calls
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {"data": {}}
            return response

        mock_get.side_effect = side_effect

        # Test successful season episodes retrieval
        result = self.client.get_season_episodes(12345, 1)

        assert len(result) == 2
        assert result[0]["id"] == 5001
        assert result[0]["name"] == "Episode 1"
        assert result[1]["id"] == 5002

        # Verify get was called twice (once for extended series, once for season episodes)
        assert mock_get.call_count == 2

    @patch("plexomatic.api.tvdb_client.requests.get")
    def test_get_season_episodes_with_type(self, mock_get: MagicMock) -> None:
        """Test retrieving episodes for a specific season with different season types."""
        # Mock responses for series extended and season episodes
        series_extended_response = MagicMock()
        series_extended_response.status_code = 200
        series_extended_response.json.return_value = {
            "data": {
                "id": 12345,
                "name": "Test Show",
                "seasons": [
                    {"id": 1001, "number": 1, "type": "Aired Order", "name": "Season 1 (Aired)"},
                    {"id": 1002, "number": 1, "type": "DVD Order", "name": "Season 1 (DVD)"},
                ],
            }
        }

        # Aired order episodes response
        aired_episodes_response = MagicMock()
        aired_episodes_response.status_code = 200
        aired_episodes_response.json.return_value = {
            "data": {
                "episodes": [
                    {"id": 5001, "name": "Aired Episode 1", "seasonNumber": 1, "episodeNumber": 1}
                ]
            }
        }

        # DVD order episodes response
        dvd_episodes_response = MagicMock()
        dvd_episodes_response.status_code = 200
        dvd_episodes_response.json.return_value = {
            "data": {
                "episodes": [
                    {"id": 6001, "name": "DVD Episode 1", "seasonNumber": 1, "episodeNumber": 1}
                ]
            }
        }

        # Configure mock to return different responses based on URL
        def side_effect(url, headers):
            if SERIES_EXTENDED_URL.format(series_id=12345) in url:
                return series_extended_response
            if SEASON_EPISODES_URL.format(season_id=1001) in url:
                return aired_episodes_response
            if SEASON_EPISODES_URL.format(season_id=1002) in url:
                return dvd_episodes_response
            # Return a default empty response for unexpected calls
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {"data": {}}
            return response

        mock_get.side_effect = side_effect

        # Test with default (Aired Order)
        result_default = self.client.get_season_episodes(12345, 1)
        assert len(result_default) == 1
        assert result_default[0]["name"] == "Aired Episode 1"

        # Test with explicit DVD Order
        result_dvd = self.client.get_season_episodes(12345, 1, season_type="DVD Order")
        assert len(result_dvd) == 1
        assert result_dvd[0]["name"] == "DVD Episode 1"

        # Verify get was called multiple times (once for extended series, once for each season type)
        assert mock_get.call_count == 3
