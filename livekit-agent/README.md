# LiveKit Voice Agent

A voice AI agent built using the LiveKit Agents framework with Deepgram for speech-to-text, Gemini for language understanding, and ElevenLabs for text-to-speech through LiveKit Inference.

## Features

- Real-time voice conversations using WebRTC
- Deepgram STT via LiveKit Inference
- Gemini LLM via LiveKit Inference
- ElevenLabs TTS via LiveKit Inference
- Web interface for easy interaction
- Docker deployment support
- FastAPI HTTP server

## Requirements

- Python >= 3.10, < 3.14
- Docker and Docker Compose (for containerized deployment)
- LiveKit Cloud account (or self-hosted LiveKit server)

## Docker Deployment

Build and run with Docker Compose (runs both services in separate containers):

```bash
cp .env.example .env
# Add your livekit credentials
docker-compose up --build
```

This starts two containers:
- **agent**: Connects to LiveKit and handles voice AI sessions
- **server**: Serves the web interface on port 7860

## Project Structure

```
livekit-agent/
├── agent.py           # Agent logic and voice pipeline
├── server.py          # FastAPI HTTP server
├── config.py          # Configuration management
├── index.html         # Web interface
├── Dockerfile         # Docker image definition
├── docker-compose.yml # Multi-container orchestration
├── pyproject.toml     # Python dependencies
├── .env.example       # Example environment variables
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

## How It Works

The application consists of two components that work together:

1. **Agent Server** (`agent.py`): Connects to LiveKit and handles voice AI sessions. When a room is created, the agent automatically joins and provides voice AI capabilities.

2. **HTTP Server** (`server.py`): Provides a web interface and REST API for creating rooms. When a user connects, it generates a LiveKit token that automatically dispatches the agent to the room.

## Configuration

All configuration is managed through environment variables. See `.env.example` for available options.

Key configuration options:
- `LIVEKIT_URL`: LiveKit server URL
- `LIVEKIT_API_KEY`: LiveKit API key
- `LIVEKIT_API_SECRET`: LiveKit API secret
- `SERVER_HOST`: HTTP server host (default: 0.0.0.0)
- `SERVER_PORT`: HTTP server port (default: 7860)
- `SYSTEM_INSTRUCTION`: Agent personality and behavior

## License

BSD 2-Clause License
