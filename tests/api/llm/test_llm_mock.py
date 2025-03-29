"""
Example file demonstrating how to effectively mock the LLM client for testing.

This includes examples of:
- Mocking the LLMClient directly
- Mocking the requests module used by LLMClient
- Setting up mock responses for different API calls
"""

import pytest
from pytest_mock import MockerFixture
import json
import requests

from plexomatic.api.llm_client import LLMClient, LLMRequestError, LLMModelNotAvailableError


# Sample response data for mock tests
MODEL_LIST_RESPONSE = {
    "models": [
        {
            "name": "deepseek-r1:8b",
            "modified_at": "2023-04-01T12:00:00Z",
            "size": 4000000000,
        }
    ]
}

GENERATE_TEXT_RESPONSE = {
    "model": "deepseek-r1:8b",
    "created_at": "2023-04-01T12:00:00Z",
    "response": "The show 'Breaking Bad' is about a high school chemistry teacher who turns to producing and selling methamphetamine.",
    "done": True,
}

ANALYZE_FILENAME_RESPONSE = {
    "model": "deepseek-r1:8b",
    "created_at": "2023-04-01T12:00:00Z",
    "response": json.dumps({
        "title": "Breaking Bad",
        "season": 1,
        "episode": 1,
        "quality": "HDTV",
        "codec": "x264",
    }),
    "done": True,
}

SUGGEST_FILENAME_RESPONSE = {
    "model": "deepseek-r1:8b",
    "created_at": "2023-04-01T12:00:00Z",
    "response": "Breaking Bad - S01E01 - Pilot [HDTV-x264].mp4",
    "done": True,
}


class TestLLMMocking:
    """Examples of how to mock the LLM client for testing."""

    def test_mock_llm_client_directly(self, mocker: MockerFixture) -> None:
        """Demo mocking the entire LLM client."""
        # Create a mock LLMClient
        mock_client = mocker.Mock(spec=LLMClient)
        
        # Configure mock to return sample data for different methods
        mock_client.check_model_available.return_value = True
        mock_client.generate_text.return_value = "The show 'Breaking Bad' is about a high school chemistry teacher..."
        mock_client.analyze_filename.return_value = {
            "title": "Breaking Bad",
            "season": 1,
            "episode": 1,
        }
        
        # Now use the mock client in your tests
        assert mock_client.check_model_available() is True
        
        result = mock_client.generate_text("What is the show 'Breaking Bad' about?")
        assert "chemistry teacher" in result
        mock_client.generate_text.assert_called_once_with("What is the show 'Breaking Bad' about?")
        
        analysis = mock_client.analyze_filename("BreakingBad.S01E01.HDTV.x264")
        assert analysis["title"] == "Breaking Bad"
        assert analysis["season"] == 1
        mock_client.analyze_filename.assert_called_once_with("BreakingBad.S01E01.HDTV.x264")

    def test_mock_requests_module(self, mocker: MockerFixture) -> None:
        """Demo mocking the requests module used by LLMClient."""
        # Mock the requests.get and requests.post methods
        mock_get = mocker.patch("requests.get")
        mock_post = mocker.patch("requests.post")
        
        # Create response objects for different API calls
        mock_get_response = mocker.Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = MODEL_LIST_RESPONSE
        mock_get.return_value = mock_get_response
        
        mock_post_response = mocker.Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = GENERATE_TEXT_RESPONSE
        mock_post.return_value = mock_post_response
        
        # Create a real LLMClient that will use the mocked requests
        client = LLMClient(model_name="deepseek-r1:8b")
        
        # Test model availability check
        assert client.check_model_available() is True
        mock_get.assert_called_once()
        
        # Test text generation
        result = client.generate_text("What is Breaking Bad about?")
        assert "chemistry teacher" in result
        assert "methamphetamine" in result
        
        # Verify the request was made correctly
        mock_post.assert_called_once()
        post_data = mock_post.call_args.kwargs["json"]
        assert post_data["model"] == "deepseek-r1:8b"
        assert post_data["prompt"] == "What is Breaking Bad about?"

    def test_filename_analysis(self, mocker: MockerFixture) -> None:
        """Demo mocking for the analyze_filename method."""
        # Mock only the requests.post method
        mock_post = mocker.patch("requests.post")
        
        # Setup mock response for file analysis
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = ANALYZE_FILENAME_RESPONSE
        mock_post.return_value = mock_response
        
        # Create client and test filename analysis
        client = LLMClient()
        result = client.analyze_filename("BreakingBad.S01E01.HDTV.x264")
        
        # Verify results
        assert result["title"] == "Breaking Bad"
        assert result["season"] == 1
        assert result["episode"] == 1
        assert result["quality"] == "HDTV"
        
        # Verify the correct system prompt was sent
        post_data = mock_post.call_args.kwargs["json"]
        assert "system" in post_data
        assert "media file analyzer" in post_data["system"]
        assert "Extract information from this filename" in post_data["prompt"]

    def test_error_handling(self, mocker: MockerFixture) -> None:
        """Demo mocking error responses."""
        # Mock requests.post to simulate errors
        mock_post = mocker.patch("requests.post")
        
        # First test: connection error
        # Use a specific requests exception instead of a generic exception
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        client = LLMClient()
        
        # Verify the error is properly caught and raised as LLMRequestError
        with pytest.raises(LLMRequestError) as exc_info:
            client.generate_text("This should fail")
        assert "Connection refused" in str(exc_info.value)
        
        # Second test: model not found error
        mock_response = mocker.Mock()
        mock_response.status_code = 404
        mock_response.text = "Model not found"
        mock_post.side_effect = None  # Clear the previous side effect
        mock_post.return_value = mock_response
        
        # Verify the 404 error is caught and raised as LLMModelNotAvailableError
        with pytest.raises(LLMModelNotAvailableError) as exc_info:
            client.generate_text("This should fail with model not available")
        assert "Model" in str(exc_info.value)
        assert "not available" in str(exc_info.value) 