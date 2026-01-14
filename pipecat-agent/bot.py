"""
Pipecat Voice Agent - Main Bot Implementation

This module implements the core voice AI agent using the Pipecat framework.
It orchestrates the pipeline connecting WebRTC transport, speech processing
(via Speaches), and LLM inference (via Ollama) for real-time voice conversations.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.3, 2.4, 3.1, 3.4, 3.5, 7.1, 8.1, 8.2
"""

import os
from typing import Optional

from dotenv import load_dotenv
from loguru import logger

# Pipecat core imports
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams

# Pipecat transport
from pipecat.transports.network.small_webrtc_transport import (
    SmallWebRTCTransport,
    SmallWebRTCTransportParams,
)

# Pipecat processors
from pipecat.processors.aggregators.llm_response import (
    LLMAssistantContextAggregator,
    LLMUserContextAggregator,
)
from pipecat.processors.frame_processor import FrameDirection

# Pipecat services
from pipecat.services.openai import OpenAILLMService, OpenAITTSService
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.audio.vad.silero import SileroVADAnalyzer

# Pipecat frames
from pipecat.frames.frames import (
    EndFrame,
    LLMMessagesFrame,
    TextFrame,
)

# Model management utilities
from model_utils import ensure_ollama_model, ensure_speaches_models

# Load environment variables
load_dotenv()

# Configuration from environment variables (Requirement 7.1)
SPEACHES_BASE_URL = os.getenv("SPEACHES_BASE_URL", "http://speaches:8000")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
STT_MODEL = os.getenv("STT_MODEL", "Systran/faster-distil-whisper-small.en")
TTS_MODEL = os.getenv("TTS_MODEL", "speaches-ai/Kokoro-82M-v1.0-ONNX")
TTS_VOICE = os.getenv("TTS_VOICE", "af_heart")
SYSTEM_INSTRUCTION = os.getenv(
    "SYSTEM_INSTRUCTION",
    "You are a helpful voice assistant. Provide clear, concise responses."
)

logger.info("Bot configuration loaded:")
logger.info(f"  Speaches URL: {SPEACHES_BASE_URL}")
logger.info(f"  Ollama URL: {OLLAMA_BASE_URL}")
logger.info(f"  Ollama Model: {OLLAMA_MODEL}")
logger.info(f"  STT Model: {STT_MODEL}")
logger.info(f"  TTS Model: {TTS_MODEL}")
logger.info(f"  TTS Voice: {TTS_VOICE}")


async def run_bot(webrtc_connection) -> None:
    """
    Main bot entry point that sets up and runs the Pipecat pipeline.
    
    This function initializes all components of the voice agent pipeline:
    - WebRTC transport for real-time audio streaming
    - Voice Activity Detection (VAD) for speech detection
    - Speech-to-Text (STT) via Speaches
    - Language Model (LLM) via Ollama
    - Text-to-Speech (TTS) via Speaches
    - Context aggregators for conversation management
    
    The pipeline processes audio in this flow:
    1. User speaks → WebRTC → VAD detects speech
    2. Audio → STT → Text transcription
    3. Text → LLM → Response generation
    4. Response → TTS → Audio synthesis
    5. Audio → WebRTC → User hears response
    
    Args:
        webrtc_connection: WebRTC connection object from SmallWebRTCTransport
    
    Requirements: 1.2, 1.3, 1.4, 1.5, 2.3, 2.4, 3.1, 3.4, 3.5
    """
    logger.info("Initializing Pipecat bot")
    
    # Ensure models are available before starting (Requirements 8.1, 8.2)
    try:
        await ensure_ollama_model(OLLAMA_BASE_URL, OLLAMA_MODEL)
        await ensure_speaches_models(SPEACHES_BASE_URL, STT_MODEL, TTS_MODEL)
    except Exception as e:
        logger.error(f"Failed to ensure models are available: {e}")
        raise
    
    # Initialize transport with VAD (Requirements 1.2, 1.3)
    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=SmallWebRTCTransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
            vad_audio_passthrough=True,
        )
    )
    logger.info("WebRTC transport initialized with Silero VAD")
    
    # Initialize STT service pointing to Speaches (Requirement 2.3)
    # Using OpenAI-compatible API format
    stt = DeepgramSTTService(
        api_key="not-needed",  # Speaches doesn't require API key
        url=f"{SPEACHES_BASE_URL}/v1/audio/transcriptions",
        model=STT_MODEL,
    )
    logger.info(f"STT service initialized: {STT_MODEL}")
    
    # Initialize TTS service pointing to Speaches (Requirement 2.4)
    # Using OpenAI-compatible API format
    tts = OpenAITTSService(
        api_key="not-needed",  # Speaches doesn't require API key
        base_url=f"{SPEACHES_BASE_URL}/v1",
        model=TTS_MODEL,
        voice=TTS_VOICE,
    )
    logger.info(f"TTS service initialized: {TTS_MODEL} with voice {TTS_VOICE}")
    
    # Initialize LLM service with Ollama (Requirement 1.4)
    llm = OpenAILLMService(
        api_key="not-needed",  # Ollama doesn't require API key
        base_url=f"{OLLAMA_BASE_URL}/v1",
        model=OLLAMA_MODEL,
    )
    logger.info(f"LLM service initialized: {OLLAMA_MODEL}")
    
    # Create initial conversation context with greeting (Requirement 1.5, 3.4)
    messages = [
        {
            "role": "system",
            "content": SYSTEM_INSTRUCTION
        },
        {
            "role": "system",
            "content": "Start by greeting the user warmly and introducing yourself as a voice assistant."
        }
    ]
    
    # Create context aggregators for managing conversation (Requirement 1.5)
    context_aggregator_user = LLMUserContextAggregator(messages)
    context_aggregator_assistant = LLMAssistantContextAggregator(messages)
    
    logger.info("Context aggregators initialized with system instruction")
    
    # Build the pipeline (Requirement 3.1)
    # Flow: Audio In → STT → User Context → LLM → Assistant Context → TTS → Audio Out
    pipeline = Pipeline([
        transport.input(),           # Audio input from WebRTC
        stt,                         # Speech-to-text
        context_aggregator_user,     # Add user message to context
        llm,                         # Generate LLM response
        tts,                         # Text-to-speech
        transport.output(),          # Audio output to WebRTC
        context_aggregator_assistant # Add assistant message to context
    ])
    logger.info("Pipeline built with all components")
    
    # Create pipeline task with metrics enabled
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
            enable_usage_metrics=True,
        )
    )
    logger.info("Pipeline task created with metrics enabled")
    
    # Event handler: Client connected (Requirement 3.4)
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        """
        Handle client connection event.
        
        When a client connects, we queue an initial LLM message frame to
        trigger the greeting. This ensures the agent speaks first.
        
        Requirement: 3.4
        """
        logger.info(f"Client connected: {client}")
        # Trigger initial greeting by queuing the system messages
        await task.queue_frames([LLMMessagesFrame(messages)])
    
    # Event handler: Client disconnected (Requirement 3.5)
    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        """
        Handle client disconnection event.
        
        When a client disconnects, we gracefully terminate the pipeline task
        to clean up resources.
        
        Requirement: 3.5
        """
        logger.info(f"Client disconnected: {client}")
        await task.queue_frames([EndFrame()])
    
    logger.info("Event handlers registered")
    
    # Run the pipeline
    logger.info("Starting pipeline runner")
    runner = PipelineRunner()
    
    try:
        await runner.run(task)
        logger.info("Pipeline completed successfully")
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise
    finally:
        logger.info("Pipeline runner finished")
