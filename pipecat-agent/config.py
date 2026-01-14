"""
Pipecat Voice Agent - Configuration Management

This module centralizes all configuration loading from environment variables
with sensible defaults. It ensures consistent configuration across all modules.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.7
"""

import os
from typing import Optional

from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Centralized configuration for the Pipecat Voice Agent.
    
    All configuration values are loaded from environment variables with
    sensible defaults. This ensures the system can run out-of-the-box
    while still being fully configurable.
    
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.7
    """
    
    # Speaches Configuration (Requirements 7.1, 7.2)
    SPEACHES_BASE_URL: str = os.getenv("SPEACHES_BASE_URL", "http://speaches:8000")
    
    # Ollama Configuration (Requirements 7.2, 7.3)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    
    # Speech-to-Text Configuration (Requirement 7.4)
    STT_MODEL: str = os.getenv("STT_MODEL", "Systran/faster-distil-whisper-small.en")
    
    # Text-to-Speech Configuration (Requirement 7.4, 7.5)
    TTS_MODEL: str = os.getenv("TTS_MODEL", "speaches-ai/Kokoro-82M-v1.0-ONNX")
    TTS_VOICE: str = os.getenv("TTS_VOICE", "af_heart")
    
    # Server Configuration
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "7860"))
    
    # Agent Configuration
    SYSTEM_INSTRUCTION: str = os.getenv(
        "SYSTEM_INSTRUCTION",
        "You are a helpful voice assistant. Provide clear, concise responses."
    )
    
    @classmethod
    def log_configuration(cls) -> None:
        """
        Log the current configuration for debugging and verification.
        
        This helps ensure that the configuration is loaded correctly and
        makes it easier to troubleshoot configuration issues.
        """
        logger.info("Configuration loaded:")
        logger.info(f"  Speaches URL: {cls.SPEACHES_BASE_URL}")
        logger.info(f"  Ollama URL: {cls.OLLAMA_BASE_URL}")
        logger.info(f"  Ollama Model: {cls.OLLAMA_MODEL}")
        logger.info(f"  STT Model: {cls.STT_MODEL}")
        logger.info(f"  TTS Model: {cls.TTS_MODEL}")
        logger.info(f"  TTS Voice: {cls.TTS_VOICE}")
        logger.info(f"  Server Host: {cls.SERVER_HOST}")
        logger.info(f"  Server Port: {cls.SERVER_PORT}")
        logger.info(f"  System Instruction: {cls.SYSTEM_INSTRUCTION[:50]}...")
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate that all required configuration values are present and valid.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        # Check that URLs are not empty
        if not cls.SPEACHES_BASE_URL or not cls.OLLAMA_BASE_URL:
            logger.error("Service URLs cannot be empty")
            return False
        
        # Check that model names are not empty
        if not cls.OLLAMA_MODEL or not cls.STT_MODEL or not cls.TTS_MODEL:
            logger.error("Model names cannot be empty")
            return False
        
        # Check that TTS voice is not empty
        if not cls.TTS_VOICE:
            logger.error("TTS voice cannot be empty")
            return False
        
        # Check that port is valid
        if cls.SERVER_PORT < 1 or cls.SERVER_PORT > 65535:
            logger.error(f"Invalid server port: {cls.SERVER_PORT}")
            return False
        
        logger.info("Configuration validation passed")
        return True


# Create a singleton instance for easy importing
config = Config()

# Log configuration on module import
config.log_configuration()

# Validate configuration
if not config.validate():
    logger.warning("Configuration validation failed - some features may not work correctly")
