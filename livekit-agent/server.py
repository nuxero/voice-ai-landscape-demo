"""HTTP server module for LiveKit voice agent.

This module provides FastAPI endpoints for the web interface and LiveKit room management.
"""

import logging
import sys
from datetime import datetime
from typing import Optional
import uuid
import httpx

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from livekit import api
from pydantic import BaseModel

from config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(title="LiveKit Voice Agent")

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions globally.
    
    This ensures the server continues operating after non-fatal errors.
    """
    logger.error(f"Unhandled exception on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."}
    )


# Request/Response models
class ConnectRequest(BaseModel):
    """Request model for room connection."""
    participant_identity: str = "user"


class ConnectResponse(BaseModel):
    """Response model for room connection."""
    url: str
    token: str
    room_name: str


class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str
    livekit: bool
    timestamp: str


@app.get("/")
async def serve_index():
    """Serve the web interface HTML.
    
    Returns:
        FileResponse: The index.html file
    """
    logger.debug("Serving web interface")
    return FileResponse("index.html")


@app.post("/connect", response_model=ConnectResponse, status_code=201)
async def connect(request: ConnectRequest):
    """Create a LiveKit room and return connection details.
    
    Args:
        request: ConnectRequest containing participant identity
        
    Returns:
        ConnectResponse: Connection details including URL, token, and room name
        
    Raises:
        HTTPException: If room creation or token generation fails
    """
    try:
        # Generate a unique room name
        room_name = f"voice-agent-{uuid.uuid4().hex[:8]}"
        
        logger.info(f"Creating room '{room_name}' for participant '{request.participant_identity}'")
        
        # Validate configuration before creating token
        if not Config.LIVEKIT_API_KEY or not Config.LIVEKIT_API_SECRET:
            logger.error("Cannot create room: LiveKit API credentials not configured")
            raise HTTPException(
                status_code=503,
                detail="LiveKit API credentials not configured. Please check server configuration."
            )
        
        # Create access token with agent dispatch
        try:
            token = (
                api.AccessToken(
                    Config.LIVEKIT_API_KEY,
                    Config.LIVEKIT_API_SECRET
                )
                .with_identity(request.participant_identity)
                .with_name(request.participant_identity)
                .with_grants(
                    api.VideoGrants(
                        room_join=True,
                        room=room_name,
                    )
                )
                .with_room_config(
                    api.RoomConfiguration(
                        agents=[
                            api.RoomAgentDispatch()
                        ]
                    )
                )
            )
            
            # Generate JWT token
            jwt_token = token.to_jwt()
            
        except Exception as token_error:
            logger.error(f"Failed to generate access token: {str(token_error)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Failed to generate access token. Please try again."
            )
        
        logger.info(f"Successfully created room '{room_name}' for participant '{request.participant_identity}'")
        
        return ConnectResponse(
            url=Config.LIVEKIT_URL,
            token=jwt_token,
            room_name=room_name
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating room for participant '{request.participant_identity}': {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again later."
        )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Check system health and service availability.
    
    Returns:
        HealthCheckResponse: Health status including LiveKit server reachability
    """
    livekit_healthy = False
    
    try:
        # Validate LiveKit URL is configured
        if not Config.LIVEKIT_URL:
            logger.warning("Health check: LiveKit URL not configured")
            livekit_healthy = False
        else:
            # Check LiveKit server reachability
            # Convert ws:// or wss:// URL to http:// or https://
            check_url = Config.LIVEKIT_URL.replace("ws://", "http://").replace("wss://", "https://")
            
            logger.debug(f"Checking LiveKit server health at {check_url}")
            
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(check_url)
                    livekit_healthy = response.status_code < 500
            except httpx.TimeoutException:
                logger.warning("LiveKit health check timed out")
                livekit_healthy = False
            except httpx.ConnectError as e:
                logger.warning(f"LiveKit health check connection failed: {str(e)}")
                livekit_healthy = False
            
    except Exception as e:
        logger.error(f"Unexpected error during health check: {str(e)}", exc_info=True)
        livekit_healthy = False
    
    # Determine overall status
    status = "healthy" if livekit_healthy else "degraded"
    
    logger.info(f"Health check completed: status={status}, livekit={livekit_healthy}")
    
    return HealthCheckResponse(
        status=status,
        livekit=livekit_healthy,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


if __name__ == "__main__":
    # Validate configuration on startup
    logger.info("Validating configuration...")
    if not Config.validate():
        logger.error("Configuration validation failed. Exiting.")
        sys.exit(1)
    
    logger.info("Configuration validation successful")
    Config.log_configuration()
    
    # Run the server
    logger.info(f"Starting server on {Config.SERVER_HOST}:{Config.SERVER_PORT}")
    try:
        uvicorn.run(
            app,
            host=Config.SERVER_HOST,
            port=Config.SERVER_PORT,
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)
