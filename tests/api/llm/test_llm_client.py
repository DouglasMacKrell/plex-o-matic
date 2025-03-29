"""
Test file for the LLM client basic functionality.

This includes tests for:
- Model availability checking
- Text generation
- Custom parameters
- Error handling
"""

import pytest
from pytest_mock import MockerFixture
import json
import requests

from plexomatic.api.llm_client import LLMClient, LLMRequestError, LLMModelNotAvailableError


class TestLLMClient:
    """Tests for the Ollama-based LLM client."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.model_name = "deepseek-r1:8b"
        self.client = LLMClient(model_name=self.model_name, base_url="http://localhost:11434")

    def test_check_model_available(self, mocker: MockerFixture) -> None:
        """Test checking if a model is available."""
        # Mock successful model list response
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {
                    "name": "deepseek-r1:8b",
                    "modified_at": "2023-04-01T12:00:00Z",
                    "size": 4000000000,
                }
            ]
        }
        mock_get.return_value = mock_response

        # Test successful model availability check
        assert self.client.check_model_available() is True
        mock_get.assert_called_once()

        # Test model not found
        mock_response.json.return_value = {"models": [{"name": "llama2"}]}
        mock_get.reset_mock()
        assert self.client.check_model_available() is False

    def test_generate_text(self, mocker: MockerFixture) -> None:
        """Test generating text with the LLM."""
        # Mock successful generation response
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "deepseek-r1:8b",
            "created_at": "2023-04-01T12:00:00Z",
            "response": "The show 'Breaking Bad' is about a high school chemistry teacher who turns to producing and selling methamphetamine.",
            "done": True,
        }
        mock_post.return_value = mock_response

        # Test successful text generation
        prompt = "What is the show 'Breaking Bad' about?"
        result = self.client.generate_text(prompt)
        assert "chemistry teacher" in result
        assert "methamphetamine" in result
        mock_post.assert_called_once()

        # Check that the correct request was made
        request_args = mock_post.call_args.kwargs
        assert request_args["json"]["model"] == "deepseek-r1:8b"
        assert request_args["json"]["prompt"] == prompt

    def test_generate_text_with_parameters(self, mocker: MockerFixture) -> None:
        """Test generating text with custom parameters."""
        # Mock successful generation response
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "deepseek-r1:8b",
            "created_at": "2023-04-01T12:00:00Z",
            "response": "The file 'BreakingBad.S01E01.HDTV.x264' contains information about the TV show Breaking Bad, Season 1, Episode 1.",
            "done": True,
        }
        mock_post.return_value = mock_response

        # Test with custom parameters
        result = self.client.generate_text(
            "Parse this filename: BreakingBad.S01E01.HDTV.x264",
            temperature=0.5,
            top_p=0.9,
            max_tokens=100,
        )
        assert "Breaking Bad" in result
        assert "Season 1, Episode 1" in result

        # Check that parameters were passed correctly
        request_args = mock_post.call_args.kwargs
        assert request_args["json"]["temperature"] == 0.5
        assert request_args["json"]["top_p"] == 0.9
        assert request_args["json"]["max_tokens"] == 100

    def test_generate_text_with_system_prompt(self, mocker: MockerFixture) -> None:
        """Test generating text with a system prompt."""
        # Mock successful generation response
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "deepseek-r1:8b",
            "created_at": "2023-04-01T12:00:00Z",
            "response": "Inception is a 2010 science fiction action film directed by Christopher Nolan.",
            "done": True,
        }
        mock_post.return_value = mock_response

        # Test with system prompt
        system_prompt = "You are a helpful movie database assistant. Keep answers brief and factual."
        result = self.client.generate_text(
            "What is the movie Inception about?",
            system=system_prompt,
        )
        assert "Inception" in result
        assert "Christopher Nolan" in result

        # Check that system prompt was passed correctly
        request_args = mock_post.call_args.kwargs
        assert request_args["json"]["system"] == system_prompt

    def test_request_error(self, mocker: MockerFixture) -> None:
        """Test handling of request errors."""
        # Mock error response
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_post.return_value = mock_response

        # Test error handling
        with pytest.raises(LLMRequestError):
            self.client.generate_text("This should fail")

    def test_connection_error(self, mocker: MockerFixture) -> None:
        """Test handling of connection errors."""
        # Mock connection error with a specific RequestException
        mock_post = mocker.patch("requests.post")
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        # Test error handling
        with pytest.raises(LLMRequestError) as exc:
            self.client.generate_text("This should fail with connection error")
        assert "Connection refused" in str(exc.value)

    def test_model_not_available_error(self, mocker: MockerFixture) -> None:
        """Test handling of model not available errors."""
        # Mock error response for model not found
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.status_code = 404
        mock_response.text = "Model not found"
        mock_post.return_value = mock_response

        # Test error handling
        with pytest.raises(LLMModelNotAvailableError):
            self.client.generate_text("This should fail with model not available") 