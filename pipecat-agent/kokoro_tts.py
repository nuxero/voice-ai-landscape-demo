"""
Kokoro TTS Service for Pipecat

This module provides a custom TTS service for Kokoro models via Speaches,
extending OpenAITTSService to bypass voice validation for Kokoro-specific voices.

Requirements: 2.4, 7.5
"""

from typing import Optional
from pipecat.services.openai import OpenAITTSService


class KokoroTTSService(OpenAITTSService):
    """
    Custom TTS service for Kokoro models that bypasses OpenAI voice validation.
    
    Kokoro models use different voice identifiers (e.g., af_heart, af_sky, etc.)
    that don't match OpenAI's standard voices. This service extends OpenAITTSService
    to allow any voice identifier to be used with Speaches/Kokoro.
    
    Requirements: 2.4, 7.5
    """
    
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        voice: str,
        **kwargs
    ):
        """
        Initialize the Kokoro TTS service.
        
        Args:
            api_key: API key for Speaches (can be any non-empty string)
            base_url: Base URL for Speaches API (e.g., "http://speaches:8000/v1")
            model: Kokoro model identifier (e.g., "speaches-ai/Kokoro-82M-v1.0-ONNX")
            voice: Kokoro voice identifier (e.g., "af_heart", "af_sky", etc.)
            **kwargs: Additional arguments passed to OpenAITTSService
        """
        # Store the actual Kokoro voice before calling parent init
        self._kokoro_voice = voice
        
        # Initialize parent with a valid OpenAI voice to pass validation
        # We'll override the actual voice used in requests
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model=model,
            voice="alloy",  # Use valid OpenAI voice for validation
            **kwargs
        )
        
        # Override the voice with the actual Kokoro voice after initialization
        self._voice = self._kokoro_voice
