"""
Pipecat Voice Agent - FastAPI Server

This module implements the FastAPI server that handles WebRTC signaling,
serves the web interface, and manages agent sessions.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.7, 9.3, 9.4
"""

from typing import Optional

from loguru import logger
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

# Pipecat WebRTC imports
from pipecat.transports.smallwebrtc.request_handler import (
    SmallWebRTCRequestHandler,
    SmallWebRTCRequest,
    SmallWebRTCPatchRequest,
)

# Configuration and bot runner
from config import config
from bot import run_bot

# Initialize FastAPI application (Requirement 10.1)
app = FastAPI(
    title="Pipecat Voice Agent",
    description="Voice AI agent with WebRTC support",
    version="0.1.0"
)

# Add CORS middleware for web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SmallWebRTC request handler (Requirement 10.1, 10.6)
small_webrtc_handler = SmallWebRTCRequestHandler()

logger.info("FastAPI server initialized")
logger.info(f"  Server will run on {config.SERVER_HOST}:{config.SERVER_PORT}")
logger.info(f"  Speaches URL: {config.SPEACHES_BASE_URL}")
logger.info(f"  Ollama URL: {config.OLLAMA_BASE_URL}")



# WebRTC Signaling Endpoints

@app.post("/api/offer")
async def offer(request: SmallWebRTCRequest, background_tasks: BackgroundTasks):
    """
    Handle WebRTC offer and create agent session.
    
    This endpoint receives a WebRTC offer from the client, processes it through
    the SmallWebRTC handler, and returns an SDP answer. It also spawns a new
    bot instance in the background to handle the conversation.
    
    Args:
        request: SmallWebRTCRequest containing SDP offer
        background_tasks: FastAPI background tasks for spawning bot
    
    Returns:
        SmallWebRTCResponse with SDP answer
    
    Requirements: 10.2, 10.5, 10.7
    """
    logger.info("Received WebRTC offer")
    
    # Define callback to spawn bot when connection is established
    async def webrtc_connection_callback(connection):
        """
        Callback invoked when WebRTC connection is established.
        
        Spawns the bot in a background task to handle the conversation.
        Each connection gets its own isolated bot instance.
        
        Requirement: 10.5, 10.7
        """
        logger.info("WebRTC connection established, spawning bot")
        background_tasks.add_task(run_bot, connection)
    
    try:
        # Handle the WebRTC offer and get answer
        answer = await small_webrtc_handler.handle_web_request(
            request=request,
            webrtc_connection_callback=webrtc_connection_callback
        )
        
        logger.info("WebRTC answer generated successfully")
        return answer
        
    except Exception as e:
        logger.error(f"Error handling WebRTC offer: {e}")
        raise



@app.patch("/api/offer")
async def ice_candidate(request: SmallWebRTCPatchRequest):
    """
    Handle ICE candidate exchange for WebRTC connection.
    
    This endpoint receives ICE candidates from the client during the WebRTC
    connection establishment process and forwards them to the handler.
    
    Args:
        request: SmallWebRTCPatchRequest containing ICE candidate
    
    Returns:
        Success status
    
    Requirements: 10.3, 3.6
    """
    logger.debug("Received ICE candidate")
    
    try:
        # Process the ICE candidate
        await small_webrtc_handler.handle_patch_request(request)
        
        logger.debug("ICE candidate processed successfully")
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error handling ICE candidate: {e}")
        raise



# Web Interface Endpoint

@app.get("/")
async def serve_index():
    """
    Serve the web interface HTML.
    
    This endpoint serves the main web interface that users interact with
    to start voice conversations with the agent.
    
    Returns:
        FileResponse with index.html
    
    Requirements: 10.4, 4.1
    """
    logger.debug("Serving web interface")
    return FileResponse("index.html")



# Health Check Endpoints

async def check_ollama_health() -> bool:
    """
    Check if Ollama service is reachable and responsive.
    
    Returns:
        True if Ollama is healthy, False otherwise
    
    Requirement: 9.3
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{config.OLLAMA_BASE_URL}/api/tags")
            return response.status_code == 200
    except Exception as e:
        logger.warning(f"Ollama health check failed: {e}")
        return False


async def check_speaches_health() -> bool:
    """
    Check if Speaches service is reachable and responsive.
    
    Returns:
        True if Speaches is healthy, False otherwise
    
    Requirement: 9.4
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{config.SPEACHES_BASE_URL}/v1/models")
            return response.status_code == 200
    except Exception as e:
        logger.warning(f"Speaches health check failed: {e}")
        return False


@app.get("/health")
async def health_check():
    """
    Overall system health check endpoint.
    
    Checks the health of all dependent services (Ollama and Speaches)
    and returns the overall system status.
    
    Returns:
        JSON with status and individual service checks
    
    Requirements: 9.3, 9.4
    """
    logger.debug("Running health check")
    
    # Check all services
    checks = {
        "ollama": await check_ollama_health(),
        "speaches": await check_speaches_health()
    }
    
    # Determine overall status
    all_healthy = all(checks.values())
    status = "healthy" if all_healthy else "degraded"
    
    logger.debug(f"Health check result: {status} - {checks}")
    
    return {
        "status": status,
        "checks": checks
    }



# Server Entry Point

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting Pipecat Voice Agent server on {config.SERVER_HOST}:{config.SERVER_PORT}")
    
    uvicorn.run(
        app,
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        log_level="info"
    )
