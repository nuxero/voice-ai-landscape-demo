"""Configuration module for LiveKit voice agent.

This module manages environment variables and provides typed access to configuration values.
"""

import logging
import os
import sys
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


class Config:
    """Configuration class for managing environment variables."""

    # LiveKit connection details
    LIVEKIT_URL: str = os.getenv("LIVEKIT_URL", "")
    LIVEKIT_API_KEY: str = os.getenv("LIVEKIT_API_KEY", "")
    LIVEKIT_API_SECRET: str = os.getenv("LIVEKIT_API_SECRET", "")

    # Server configuration
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "7860"))

    # Agent configuration
    SYSTEM_INSTRUCTION: str = os.getenv(
        "SYSTEM_INSTRUCTION",
        """You are a friendly, helpful voice AI assistant.

Your goal is to demonstrate your capabilities in a succinct way.

Your output will be converted to audio so don't include special characters in your answers.

Respond to what the user said in a creative and helpful way. Keep your responses brief. One or two sentences at most.""",
    )

    @classmethod
    def validate(cls) -> bool:
        """Validate all required configuration values.

        Returns:
            bool: True if all required configuration is valid, False otherwise.
        """
        required_fields = {
            "LIVEKIT_URL": cls.LIVEKIT_URL,
            "LIVEKIT_API_KEY": cls.LIVEKIT_API_KEY,
            "LIVEKIT_API_SECRET": cls.LIVEKIT_API_SECRET,
        }

        missing_fields = []
        invalid_fields = []

        for field_name, field_value in required_fields.items():
            if not field_value:
                missing_fields.append(field_name)
                logger.error(
                    f"Configuration error: {field_name} is not set. "
                    f"Please set this environment variable in your .env file or environment."
                )
            elif not isinstance(field_value, str) or not field_value.strip():
                invalid_fields.append(field_name)
                logger.error(
                    f"Configuration error: {field_name} has an invalid value. "
                    f"This variable must be a non-empty string."
                )

        if missing_fields or invalid_fields:
            logger.error(
                "Configuration validation failed. Please check the errors above and update your configuration."
            )
            return False

        logger.info("Configuration validation successful")
        return True

    @classmethod
    def log_configuration(cls) -> None:
        """Log current configuration for debugging (without exposing secrets)."""
        logger.info("Configuration loaded:")
        logger.info(f"  LIVEKIT_URL: {cls.LIVEKIT_URL}")
        logger.info(f"  LIVEKIT_API_KEY: {'*' * 8 if cls.LIVEKIT_API_KEY else '(not set)'}")
        logger.info(
            f"  LIVEKIT_API_SECRET: {'*' * 8 if cls.LIVEKIT_API_SECRET else '(not set)'}"
        )
        logger.info(f"  SERVER_HOST: {cls.SERVER_HOST}")
        logger.info(f"  SERVER_PORT: {cls.SERVER_PORT}")
        logger.info(f"  SYSTEM_INSTRUCTION: {cls.SYSTEM_INSTRUCTION[:50]}...")
