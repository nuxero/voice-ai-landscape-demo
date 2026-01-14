"""
Model management utilities for Ollama and Speaches services.

This module provides functions to ensure models are available before
the agent starts, with automatic pulling/downloading as needed.
"""

import httpx
from loguru import logger


async def ensure_ollama_model(base_url: str, model: str, timeout: float = 600.0) -> None:
    """
    Ensure Ollama model is pulled and available.
    
    Automatically pulls the model if not present. This function checks if the
    specified model exists in the Ollama service, and if not, triggers a pull
    operation to download it.
    
    Args:
        base_url: Ollama service URL (e.g., "http://ollama:11434")
        model: Model name to ensure is available (e.g., "llama3.2:3b")
        timeout: Maximum time in seconds to wait for model pull (default: 600)
    
    Raises:
        httpx.HTTPError: If the Ollama service is unreachable or returns an error
        httpx.TimeoutException: If the model pull operation exceeds the timeout
    
    Requirements: 8.1, 8.5, 8.6
    """
    client = httpx.AsyncClient(base_url=base_url, timeout=timeout)
    
    try:
        logger.info(f"Checking Ollama model availability: {model}")
        
        # Check if model exists
        response = await client.get("/api/tags")
        response.raise_for_status()
        models = response.json().get("models", [])
        
        model_exists = any(m.get("name") == model for m in models)
        
        if not model_exists:
            logger.info(f"Pulling Ollama model: {model} (this may take a few minutes)...")
            logger.info(f"Model size varies: llama3.2:1b (~1GB), llama3.2:3b (~2GB)")
            
            # Pull model - this is a streaming endpoint but we'll wait for completion
            pull_response = await client.post(
                "/api/pull",
                json={"name": model},
                timeout=timeout
            )
            pull_response.raise_for_status()
            
            logger.info(f"Model {model} pulled successfully")
        else:
            logger.info(f"Ollama model {model} already available")
            
    except httpx.TimeoutException as e:
        logger.error(f"Timeout while pulling Ollama model {model}: {e}")
        logger.error(f"Consider increasing timeout or pulling model manually: ollama pull {model}")
        raise
    except httpx.HTTPError as e:
        logger.error(f"HTTP error while checking/pulling Ollama model {model}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while ensuring Ollama model {model}: {e}")
        raise
    finally:
        await client.aclose()


async def ensure_speaches_models(
    base_url: str,
    stt_model: str,
    tts_model: str,
    timeout: float = 600.0
) -> None:
    """
    Check Speaches model availability.
    
    Speaches automatically downloads models on first API request, so this function
    primarily checks and logs model status. If models are not yet downloaded, they
    will be automatically fetched when first used.
    
    Args:
        base_url: Speaches service URL (e.g., "http://speaches:8000")
        stt_model: STT model name (e.g., "Systran/faster-distil-whisper-small.en")
        tts_model: TTS model name (e.g., "speaches-ai/Kokoro-82M-v1.0-ONNX")
        timeout: Maximum time in seconds to wait for API response (default: 600)
    
    Raises:
        httpx.HTTPError: If the Speaches service is unreachable or returns an error
        httpx.TimeoutException: If the request exceeds the timeout
    
    Requirements: 8.2, 8.5, 8.6
    """
    client = httpx.AsyncClient(base_url=base_url, timeout=timeout)
    
    try:
        logger.info("Checking Speaches model availability")
        
        # Check available models via OpenAI-compatible endpoint
        response = await client.get("/v1/models")
        response.raise_for_status()
        models_data = response.json().get("data", [])
        model_ids = [m.get("id") for m in models_data]
        
        # Check STT model
        if stt_model in model_ids:
            logger.info(f"STT model {stt_model} is available")
        else:
            logger.info(f"STT model {stt_model} will be downloaded on first use (~150MB)")
        
        # Check TTS model
        if tts_model in model_ids:
            logger.info(f"TTS model {tts_model} is available")
        else:
            logger.info(f"TTS model {tts_model} will be downloaded on first use (~80MB)")
            
    except httpx.TimeoutException as e:
        logger.error(f"Timeout while checking Speaches models: {e}")
        logger.error("Speaches service may be slow to respond or unavailable")
        raise
    except httpx.HTTPError as e:
        logger.error(f"HTTP error while checking Speaches models: {e}")
        logger.error("Ensure Speaches service is running and accessible")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while checking Speaches models: {e}")
        raise
    finally:
        await client.aclose()
