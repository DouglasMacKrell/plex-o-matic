import pytest
from unittest.mock import patch, MagicMock
import json
import os
from datetime import datetime, timezone, timedelta

from plexomatic.api.llm_client import LLMClient, LLMRequestError, LLMModelNotAvailableError


class TestLLMClient:
    """Tests for the Ollama-based LLM client."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.model_name = "deepseek-r1:8b"
        self.client = LLMClient(model_name=self.model_name, base_url="http://localhost:11434")
    
    @patch('plexomatic.api.llm_client.requests.post')
    def test_check_model_available(self, mock_post):
        """Test checking if a model is available."""
        # Mock successful model list response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {
                    "name": "deepseek-r1:8b",
                    "modified_at": "2023-04-01T12:00:00Z",
                    "size": 4000000000
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Test successful model availability check
        assert self.client.check_model_available() is True
        mock_post.assert_called_once()
        
        # Test model not found
        mock_response.json.return_value = {"models": [{"name": "llama2"}]}
        mock_post.reset_mock()
        assert self.client.check_model_available() is False
    
    @patch('plexomatic.api.llm_client.requests.post')
    def test_generate_text(self, mock_post):
        """Test generating text with the LLM."""
        # Mock successful generation response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "deepseek-r1:8b",
            "created_at": "2023-04-01T12:00:00Z",
            "response": "The show 'Breaking Bad' is about a high school chemistry teacher who turns to producing and selling methamphetamine.",
            "done": True
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
    
    @patch('plexomatic.api.llm_client.requests.post')
    def test_generate_text_with_parameters(self, mock_post):
        """Test generating text with custom parameters."""
        # Mock successful generation response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "deepseek-r1:8b",
            "created_at": "2023-04-01T12:00:00Z",
            "response": "The file 'BreakingBad.S01E01.HDTV.x264' contains information about the TV show Breaking Bad, Season 1, Episode 1.",
            "done": True
        }
        mock_post.return_value = mock_response
        
        # Test with custom parameters
        params = {
            "temperature": 0.5,
            "top_p": 0.9,
            "max_tokens": 100
        }
        result = self.client.generate_text("Parse this filename: BreakingBad.S01E01.HDTV.x264", **params)
        assert "Breaking Bad" in result
        assert "Season 1, Episode 1" in result
        
        # Check that parameters were passed correctly
        request_args = mock_post.call_args.kwargs
        assert request_args["json"]["temperature"] == 0.5
        assert request_args["json"]["top_p"] == 0.9
        assert request_args["json"]["max_tokens"] == 100
    
    @patch('plexomatic.api.llm_client.requests.post')
    def test_request_error(self, mock_post):
        """Test handling of request errors."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_post.return_value = mock_response
        
        # Test error handling
        with pytest.raises(LLMRequestError):
            self.client.generate_text("This should fail")
    
    @patch('plexomatic.api.llm_client.requests.post')
    def test_model_not_available_error(self, mock_post):
        """Test handling of model not available errors."""
        # Mock error response for model not found
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Model not found"
        mock_post.return_value = mock_response
        
        # Test error handling
        with pytest.raises(LLMModelNotAvailableError):
            self.client.generate_text("This should fail with model not available")
    
    @patch('plexomatic.api.llm_client.requests.post')
    def test_analyze_filename(self, mock_post):
        """Test analyzing a filename with the LLM."""
        # Mock successful analysis response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "deepseek-r1:8b",
            "created_at": "2023-04-01T12:00:00Z",
            "response": json.dumps({
                "title": "Breaking Bad",
                "season": 1,
                "episode": 1,
                "quality": "HDTV",
                "codec": "x264"
            }),
            "done": True
        }
        mock_post.return_value = mock_response
        
        # Test successful filename analysis
        result = self.client.analyze_filename("BreakingBad.S01E01.HDTV.x264")
        assert result["title"] == "Breaking Bad"
        assert result["season"] == 1
        assert result["episode"] == 1
        assert result["quality"] == "HDTV"
        
        # Check that the system prompt was included
        request_args = mock_post.call_args.kwargs
        assert "system" in request_args["json"]
        assert "JSON object" in request_args["json"]["system"]
    
    @patch('plexomatic.api.llm_client.requests.post')
    def test_suggest_filename(self, mock_post):
        """Test suggesting a standardized filename with the LLM."""
        # Mock successful suggestion response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "deepseek-r1:8b",
            "created_at": "2023-04-01T12:00:00Z",
            "response": "Breaking Bad - S01E01 - Pilot [HDTV-x264].mp4",
            "done": True
        }
        mock_post.return_value = mock_response
        
        # Test successful filename suggestion
        result = self.client.suggest_filename("BreakingBad.S01E01.HDTV.x264.mp4", "Breaking Bad", "Pilot")
        assert "Breaking Bad" in result
        assert "S01E01" in result
        assert "Pilot" in result
        assert ".mp4" in result 