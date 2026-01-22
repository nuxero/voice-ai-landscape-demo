"""Agent module for LiveKit voice agent.

This module defines the voice AI agent logic using LiveKit Agents framework.
"""

import logging
from livekit import agents, rtc
from livekit.agents import (
    AgentServer,
    JobContext,
    cli,
    inference,
)
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Create agent server
server = AgentServer()


@server.rtc_session()
async def create_agent_session(ctx: JobContext) -> None:
    """Create and start an AgentSession for handling voice conversations.
    
    This function is decorated with @server.rtc_session() to register
    it as the entrypoint for new LiveKit room connections.
    
    Args:
        ctx: JobContext containing room and participant information
    """
    logger.info(f"Starting agent session for room: {ctx.room.name}")
    
    try:
        # Create agent session with configured models
        logger.debug("Creating agent session with STT, LLM, and TTS models")
        session = AgentSession(
            stt=inference.STT(model="deepgram/flux-general", language="en"),
            llm=inference.LLM(model="google/gemini-2.5-flash-lite"),
            tts=inference.TTS(model="elevenlabs/eleven_turbo_v2_5", voice="Xb7hH8MSUJpSbSDYk0k2"),
            vad=silero.VAD.load(),
            turn_detection=MultilingualModel(),
        )
        
        # Create agent with system instructions
        logger.debug("Creating agent with system instructions")
        agent = Agent(instructions=Config.SYSTEM_INSTRUCTION)
        
        # Start the session
        logger.info(f"Starting agent session for room: {ctx.room.name}")
        await session.start(
            room=ctx.room,
            agent=agent,
        )
        
        # Generate initial greeting
        await session.generate_reply(
            instructions="Greet the user and offer your assistance."
        )
        
        logger.info(f"Agent session successfully started for room: {ctx.room.name}")
        
        # Handle session lifecycle events
        @session.on("close")
        def on_session_close():
            """Handle session close event."""
            logger.info(f"Agent session closed for room: {ctx.room.name}")
    
    except Exception as e:
        logger.error(f"Failed to create agent session for room {ctx.room.name}: {str(e)}", exc_info=True)
        raise



if __name__ == "__main__":
    """Main entry point for the agent server."""
    # Start the agent server with CLI
    cli.run_app(server)
