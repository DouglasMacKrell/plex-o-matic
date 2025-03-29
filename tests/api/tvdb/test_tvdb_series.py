import pytest
# Removed unittest.mock imports: patch, MagicMock, ANY, Mock

from plexomatic.api.tvdb_client import TVDBClient, SERIES_URL, SERIES_EXTENDED_URL


class TestTVDBSeries:
    """Tests for TVDB series-related functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.client = TVDBClient(api_key="test_key")
        self.client.token = "test_token"
        
        # Mock authentication response
        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.json.return_value = {"data": {"token": "test_token"}}
        
        # Mock series data
        self.series_data = {
            "data": {
                "id": 1,
                "name": "Test Show",
                "status": "Continuing",
                "type": "Scripted",
                "year": 2020,
                "seasons": [
                    {
                        "id": 1,
                        "name": "Season 1",
                        "number": 1,
                        "type": "regular"
                    }
                ]
            }
        }
        
        series_response = Mock()
        series_response.status_code = 200
        series_response.json.return_value = self.series_data
        
        # Set up the mock for requests
        self.mock_patcher = patch('plexomatic.api.tvdb_client.requests')
        self.mock_requests = self.mock_patcher.start()
        self.mock_requests.post.return_value = auth_response
        self.mock_requests.get.return_value = series_response

    def teardown_method(self):
        self.mock_patcher.stop()

    # Converted from @patch("plexomatic.api.tvdb_client.requests.get")
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

    # Converted from @patch("plexomatic.api.tvdb_client.requests.get")
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

    # Converted from @patch("plexomatic.api.tvdb_client.requests.get")
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

    # Converted from @patch("plexomatic.api.tvdb_client.requests.get")
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