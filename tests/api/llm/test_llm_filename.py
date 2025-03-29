"""
Test file for the LLM client filename analysis functionality.

This includes tests for:
- Analyzing filenames to extract metadata
- Suggesting standardized filenames
- Handling JSON parsing from LLM responses
"""

import pytest
from pytest_mock import MockerFixture
import json

from plexomatic.api.llm_client import LLMClient


class TestLLMFilenameAnalysis:
    """Tests for the LLM client's filename analysis capabilities."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.client = LLMClient(model_name="deepseek-r1:8b")

    def test_analyze_filename(self, mocker: MockerFixture) -> None:
        """Test analyzing a filename with the LLM."""
        # Mock successful analysis response
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "deepseek-r1:8b",
            "created_at": "2023-04-01T12:00:00Z",
            "response": json.dumps(
                {
                    "title": "Breaking Bad",
                    "season": 1,
                    "episode": 1,
                    "quality": "HDTV",
                    "codec": "x264",
                }
            ),
            "done": True,
        }
        mock_post.return_value = mock_response

        # Test successful filename analysis
        result = self.client.analyze_filename("BreakingBad.S01E01.HDTV.x264")
        assert result["title"] == "Breaking Bad"
        assert result["season"] == 1
        assert result["episode"] == 1
        assert result["quality"] == "HDTV"
        assert result["codec"] == "x264"

        # Check that the system prompt was included
        request_args = mock_post.call_args.kwargs
        assert "system" in request_args["json"]
        assert "media file analyzer" in request_args["json"]["system"]
        assert "Extract information from this filename" in request_args["json"]["prompt"]

    def test_analyze_movie_filename(self, mocker: MockerFixture) -> None:
        """Test analyzing a movie filename."""
        # Mock successful analysis response for a movie
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "deepseek-r1:8b",
            "created_at": "2023-04-01T12:00:00Z",
            "response": json.dumps(
                {
                    "title": "Inception",
                    "year": 2010,
                    "quality": "1080p",
                    "codec": "x265",
                    "audio": "DTS",
                }
            ),
            "done": True,
        }
        mock_post.return_value = mock_response

        # Test successful movie filename analysis
        result = self.client.analyze_filename("Inception.2010.1080p.x265.DTS")
        assert result["title"] == "Inception"
        assert result["year"] == 2010
        assert result["quality"] == "1080p"
        assert result["codec"] == "x265"
        assert result["audio"] == "DTS"

    def test_analyze_complex_filename(self, mocker: MockerFixture) -> None:
        """Test analyzing a complex filename with extra information."""
        # Mock successful analysis response for a complex filename
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "deepseek-r1:8b",
            "created_at": "2023-04-01T12:00:00Z",
            "response": json.dumps(
                {
                    "title": "Game of Thrones",
                    "season": 8,
                    "episode": 6,
                    "episode_title": "The Iron Throne",
                    "quality": "1080p",
                    "source": "BluRay",
                    "codec": "x264",
                    "release_group": "RARBG",
                }
            ),
            "done": True,
        }
        mock_post.return_value = mock_response

        # Test successful complex filename analysis
        result = self.client.analyze_filename(
            "Game.of.Thrones.S08E06.The.Iron.Throne.1080p.BluRay.x264-RARBG.mkv"
        )
        assert result["title"] == "Game of Thrones"
        assert result["season"] == 8
        assert result["episode"] == 6
        assert result["episode_title"] == "The Iron Throne"
        assert result["quality"] == "1080p"
        assert result["source"] == "BluRay"
        assert result["codec"] == "x264"
        assert result["release_group"] == "RARBG"

    def test_json_parsing_error(self, mocker: MockerFixture) -> None:
        """Test handling JSON parsing errors in LLM responses."""
        # Mock response with invalid JSON
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "deepseek-r1:8b",
            "created_at": "2023-04-01T12:00:00Z",
            "response": "This is not valid JSON",
            "done": True,
        }
        mock_post.return_value = mock_response

        # Test fallback behavior
        result = self.client.analyze_filename("BreakingBad.S01E01.HDTV.x264")
        assert result["filename"] == "BreakingBad.S01E01.HDTV.x264"
        assert result["parsed"] is False

    def test_partial_json_extraction(self, mocker: MockerFixture) -> None:
        """Test extracting JSON from a text response with surrounding content."""
        # Mock response with JSON embedded in text
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "deepseek-r1:8b",
            "created_at": "2023-04-01T12:00:00Z",
            "response": 'Here is the analysis: {"title": "Breaking Bad", "season": 1, "episode": 1} Hope this helps!',
            "done": True,
        }
        mock_post.return_value = mock_response

        # Test JSON extraction
        result = self.client.analyze_filename("BreakingBad.S01E01.HDTV.x264")
        assert result["title"] == "Breaking Bad"
        assert result["season"] == 1
        assert result["episode"] == 1

    def test_suggest_filename(self, mocker: MockerFixture) -> None:
        """Test suggesting a standardized filename with the LLM."""
        # Mock successful suggestion response
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "deepseek-r1:8b",
            "created_at": "2023-04-01T12:00:00Z",
            "response": "Breaking Bad - S01E01 - Pilot [HDTV-x264].mp4",
            "done": True,
        }
        mock_post.return_value = mock_response

        # Test successful filename suggestion
        result = self.client.suggest_filename(
            "BreakingBad.S01E01.HDTV.x264.mp4", "Breaking Bad", "Pilot"
        )
        assert "Breaking Bad" in result
        assert "S01E01" in result
        assert "Pilot" in result
        assert "[HDTV-x264]" in result
        assert ".mp4" in result

        # Check that the system prompt was included
        request_args = mock_post.call_args.kwargs
        assert "system" in request_args["json"]
        assert "media file renaming assistant" in request_args["json"]["system"]

    def test_suggest_movie_filename(self, mocker: MockerFixture) -> None:
        """Test suggesting a standardized movie filename."""
        # Mock successful suggestion response for a movie
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "deepseek-r1:8b",
            "created_at": "2023-04-01T12:00:00Z",
            "response": "Inception (2010) [1080p-x265-DTS].mkv",
            "done": True,
        }
        mock_post.return_value = mock_response

        # Test successful movie filename suggestion
        result = self.client.suggest_filename("Inception.2010.1080p.x265.DTS.mkv", "Inception")
        assert "Inception (2010)" in result
        assert "[1080p-x265-DTS]" in result
        assert ".mkv" in result 