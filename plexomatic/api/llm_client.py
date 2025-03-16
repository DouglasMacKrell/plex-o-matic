"""Ollama LLM client for local AI inferencing with Deepseek R1 8b."""
import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

# Default Ollama API endpoints
DEFAULT_OLLAMA_URL = "http://localhost:11434"
LIST_MODELS_URL = "/api/tags"
GENERATE_URL = "/api/generate"


class LLMRequestError(Exception):
    """Raised when an LLM API request fails."""
    pass


class LLMModelNotAvailableError(Exception):
    """Raised when the requested LLM model is not available."""
    pass


class LLMClient:
    """Client for interacting with Ollama to use local language models."""

    def __init__(
        self, 
        model_name: str = "deepseek-r1:8b", 
        base_url: str = DEFAULT_OLLAMA_URL,
        default_max_tokens: int = 1024,
        default_temperature: float = 0.7,
    ):
        """Initialize the LLM client.
        
        Args:
            model_name: The name of the model to use for generation.
            base_url: The base URL of the Ollama API.
            default_max_tokens: Default maximum number of tokens to generate.
            default_temperature: Default temperature parameter for generation.
        """
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.default_max_tokens = default_max_tokens
        self.default_temperature = default_temperature
        
        self._list_models_url = f"{self.base_url}{LIST_MODELS_URL}"
        self._generate_url = f"{self.base_url}{GENERATE_URL}"
    
    def check_model_available(self) -> bool:
        """Check if the specified model is available in Ollama.
        
        Returns:
            True if the model is available, False otherwise.
        """
        try:
            response = requests.post(self._list_models_url)
            
            if response.status_code != 200:
                logger.warning(f"Failed to list models: {response.status_code} - {response.text}")
                return False
            
            models_data = response.json()
            available_models = [model["name"] for model in models_data.get("models", [])]
            
            return self.model_name in available_models
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking model availability: {e}")
            return False
    
    def generate_text(
        self, 
        prompt: str, 
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate text from the local LLM using Ollama.
        
        Args:
            prompt: The prompt to send to the model.
            system: Optional system prompt to set the context.
            **kwargs: Additional parameters to pass to the Ollama API.
            
        Returns:
            The generated text response.
            
        Raises:
            LLMModelNotAvailableError: If the model is not available.
            LLMRequestError: If the request fails.
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "max_tokens": kwargs.get("max_tokens", self.default_max_tokens),
            "temperature": kwargs.get("temperature", self.default_temperature),
        }
        
        # Add optional parameters if provided
        if system:
            payload["system"] = system
        
        for param in ["top_p", "top_k", "presence_penalty", "frequency_penalty"]:
            if param in kwargs:
                payload[param] = kwargs[param]
        
        try:
            response = requests.post(self._generate_url, json=payload)
            
            if response.status_code == 404:
                logger.error(f"Model not found: {self.model_name}")
                raise LLMModelNotAvailableError(f"Model {self.model_name} not available")
            
            if response.status_code != 200:
                logger.error(f"LLM request failed: {response.status_code} - {response.text}")
                raise LLMRequestError(f"Request failed: {response.status_code} - {response.text}")
            
            result = response.json()
            return result.get("response", "")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM request failed: {e}")
            raise LLMRequestError(f"Request failed: {e}")
    
    def analyze_filename(self, filename: str) -> Dict[str, Any]:
        """Analyze a media filename to extract metadata.
        
        Args:
            filename: The filename to analyze.
            
        Returns:
            A dictionary with extracted metadata (title, season, episode, etc.)
        """
        system_prompt = (
            "You are a media file analyzer specialized in extracting metadata from filenames. "
            "Analyze the given filename and extract relevant information about the media content. "
            "Respond only with a JSON object containing extracted information, with keys such as: "
            "title, season, episode, year, quality, resolution, codec, etc. "
            "Only include fields where you have high confidence. "
            "Never include explanations, be concise and accurate."
        )
        
        prompt = f"Extract information from this filename: {filename}"
        
        try:
            response = self.generate_text(
                prompt=prompt,
                system=system_prompt,
                temperature=0.2,  # Lower temperature for more deterministic output
                max_tokens=512    # Shorter response for just the JSON
            )
            
            # Try to parse the response as JSON
            result = json.loads(response)
            return result
            
        except json.JSONDecodeError:
            # If the model didn't return valid JSON, try to extract it
            try:
                # Look for content that might be JSON (between curly braces)
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    return json.loads(json_str)
            except (json.JSONDecodeError, IndexError):
                pass
            
            # Fallback to a basic response
            logger.warning(f"Failed to parse LLM response as JSON: {response}")
            return {"filename": filename, "parsed": False}
    
    def suggest_filename(
        self, 
        original_filename: str, 
        title: Optional[str] = None, 
        episode_title: Optional[str] = None
    ) -> str:
        """Suggest a standardized filename based on extracted metadata.
        
        Args:
            original_filename: The original filename.
            title: Optional title if already known.
            episode_title: Optional episode title if already known.
            
        Returns:
            A standardized filename suggestion.
        """
        system_prompt = (
            "You are a media file renaming assistant. Your task is to create standardized filenames "
            "for media files following this pattern: "
            "'Title - S##E## - Episode Title [Quality-Codec].ext' for TV shows, or "
            "'Title (Year) [Quality-Codec].ext' for movies. "
            "Preserve all relevant quality and codec information from the original filename. "
            "Output only the suggested filename, nothing else."
        )
        
        # Build the prompt with any available metadata
        prompt_parts = [f"Suggest a standardized filename for: {original_filename}"]
        if title:
            prompt_parts.append(f"The title is: {title}")
        if episode_title:
            prompt_parts.append(f"The episode title is: {episode_title}")
        
        prompt = " ".join(prompt_parts)
        
        return self.generate_text(
            prompt=prompt,
            system=system_prompt,
            temperature=0.3,
            max_tokens=256
        ) 