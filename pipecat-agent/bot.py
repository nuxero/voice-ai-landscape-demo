"""
Pipecat Voice Agent - Main Bot Implementation

This module implements the core voice AI agent using the Pipecat framework.
It orchestrates the pipeline connecting WebRTC transport, speech processing
(via Speaches), and LLM inference (via Ollama) for real-time voice conversations.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.3, 2.4, 3.1, 3.4, 3.5, 7.1, 8.1, 8.2
"""

from typing import Optional

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

# Configuration and utilities
from config import config
from model_utils import ensure_ollama_model, ensure_speaches_models


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
        await ensure_ollama_model(config.OLLAMA_BASE_URL, config.OLLAMA_MODEL)
        await ensure_speaches_models(config.SPEACHES_BASE_URL, config.STT_MODEL, config.TTS_MODEL)
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
        url=f"{config.SPEACHES_BASE_URL}/v1/audio/transcriptions",
        model=config.STT_MODEL,
    )
    logger.info(f"STT service initialized: {config.STT_MODEL}")
    
    # Initialize TTS service pointing to Speaches (Requirement 2.4)
    # Using OpenAI-compatible API format
    tts = OpenAITTSService(
        api_key="not-needed",  # Speaches doesn't require API key
        base_url=f"{config.SPEACHES_BASE_URL}/v1",
        model=config.TTS_MODEL,
        voice=config.TTS_VOICE,
    )
    logger.info(f"TTS service initialized: {config.TTS_MODEL} with voice {config.TTS_VOICE}")
    
    # Initialize LLM service with Ollama (Requirement 1.4)
    llm = OpenAILLMService(
        api_key="not-needed",  # Ollama doesn't require API key
        base_url=f"{config.OLLAMA_BASE_URL}/v1",
        model=config.OLLAMA_MODEL,
    )
    logger.info(f"LLM service initialized: {config.OLLAMA_MODEL}")
    
    # Create initial conversation context with greeting (Requirement 1.5, 3.4)
    messages = [
        {
            "role": "system",
            "content": config.SYSTEM_INSTRUCTION
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
