from unittest.mock import Mock

from plexomatic.api.tvdb_client import TVDBClient


class TestTVDBSeries:
    """Tests for TVDB series-related functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a client with token already set
        self.client = TVDBClient(api_key="test_key")
        self.client._token = "test_token"  # Set token directly to avoid auth

        # Create mock session that we'll use in tests
        self.mock_session = Mock()

        # Replace the client's session with our mock
        self.client._session = self.mock_session

        # Standard test data for series
        self.series_data = {
            "data": {
                "id": 12345,
                "name": "Test Show",
                "status": "Continuing",
                "firstAired": "2020-01-01",
                "network": "Test Network",
            }
        }

        # Extended series data including seasons
        self.extended_series_data = {
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

        # Series seasons data
        self.seasons_data = {
            "data": [
                {"id": 1001, "number": 1, "name": "Season 1", "episodeCount": 10},
                {"id": 1002, "number": 2, "name": "Season 2", "episodeCount": 8},
            ]
        }

    def test_get_series_by_name(self) -> None:
        """Test retrieving series by name."""
        # Create mock response for series search
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "data": [
                {
                    "id": 12345,
                    "name": "Test Show",
                    "status": "Continuing",
                    "firstAired": "2020-01-01",
                    "network": "Test Network",
                }
            ]
        }

        # Set up the mock session to return our response
        self.client._session.get.return_value = mock_response

        # Test successful series search
        result = self.client.get_series_by_name("Test Show")

        # Verify results
        assert result[0]["id"] == 12345
        assert result[0]["name"] == "Test Show"

        # Verify the correct API call was made
        self.client._session.get.assert_called_once()
        url_arg = self.client._session.get.call_args[0][0]
        assert "search?query=Test%20Show" in url_arg

        # Test series not found scenario
        self.client._session.get.reset_mock()
        mock_response.json.return_value = {"data": []}

        # Add empty result to cache to avoid real API call
        self.client._cache["search?query=Nonexistent%20Show&type=series"] = {"data": []}

        # Make the API call for a nonexistent show
        result = self.client.get_series_by_name("Nonexistent Show")

        # Verify empty results
        assert result == []

    def test_get_series_by_id(self) -> None:
        """Test retrieving series details by ID."""
        # Create mock response for series details
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = self.series_data

        # Set up the mock session to return our response
        self.client._session.get.return_value = mock_response

        # Test successful series details retrieval
        result = self.client.get_series(12345)

        # Verify results
        assert result["id"] == 12345
        assert result["name"] == "Test Show"

        # Verify the correct API call was made
        self.client._session.get.assert_called_once()
        url_arg = self.client._session.get.call_args[0][0]
        assert "series/12345" in url_arg

    def test_get_series_extended(self) -> None:
        """Test retrieving extended series details by ID."""
        # Create mock response for extended series details
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = self.extended_series_data

        # Set up the mock session to return our response
        self.client._session.get.return_value = mock_response

        # Test successful extended series details retrieval
        result = self.client.get_series_extended(12345)

        # Verify results
        assert result["id"] == 12345
        assert result["name"] == "Test Show"
        assert "seasons" in result
        assert len(result["seasons"]) == 2

        # Verify the correct API call was made
        self.client._session.get.assert_called_once()
        url_arg = self.client._session.get.call_args[0][0]
        assert "series/12345/extended" in url_arg

    def test_get_series_seasons(self) -> None:
        """Test retrieving seasons for a TV series."""
        # Create mock response for series seasons
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = self.seasons_data

        # Set up the mock session to return our response
        self.client._session.get.return_value = mock_response

        # Test successful seasons retrieval
        result = self.client.get_series_seasons(12345)

        # Verify results
        assert len(result) == 2
        assert result[0]["id"] == 1001
        assert result[0]["number"] == 1
        assert result[1]["id"] == 1002
        assert result[1]["number"] == 2

        # Verify the correct API call was made
        self.client._session.get.assert_called_once()
        url_arg = self.client._session.get.call_args[0][0]
        assert "seasons" in url_arg
