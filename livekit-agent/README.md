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
- uv package manager
- LiveKit Cloud account (or self-hosted LiveKit server)

## Setup

1. Install dependencies:

```bash
uv sync
```

2. Copy the example environment file and configure it:

```bash
cp .env.example .env
```

3. Edit `.env` and add your LiveKit credentials:
   - Get your credentials from https://cloud.livekit.io
   - Set `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET`

4. Download required model files:

```bash
uv run agent.py download-files
```

## Running the Agent

### Development Mode

Start the agent in development mode:

```bash
uv run agent.py dev
```

Then open the Agents Playground at https://cloud.livekit.io to test your agent.

### Console Mode

Run the agent in your terminal:

```bash
uv run agent.py console
```

### Production Mode

Start both the agent server and HTTP server:

```bash
# Option 1: Run both manually in separate terminals
# Terminal 1 - Agent server
uv run agent.py

# Terminal 2 - HTTP server
uv run server.py
```

Then open http://localhost:7860 in your browser.

## Docker Deployment

Build and run with Docker Compose (runs both services in separate containers):

```bash
docker-compose up --build
```

This starts two containers:
- **agent**: Connects to LiveKit and handles voice AI sessions
- **server**: Serves the web interface on port 7860

To run only one service:
```bash
# Run only the agent
docker-compose up agent

# Run only the server
docker-compose up server
```

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
