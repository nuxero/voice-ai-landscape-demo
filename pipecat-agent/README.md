# Pipecat Voice Agent

A voice AI agent built using the Pipecat framework with Speaches for speech processing and Ollama for language understanding. 

## Features

- Real-time voice conversations using WebRTC
- Local speech-to-text via Speaches (Faster Whisper)
- Local text-to-speech via Speaches (Kokoro TTS)
- Local LLM inference via Ollama (Llama 3.2)
- Web interface for easy interaction
- Docker deployment with automatic model management
- FastAPI HTTP server with health checks

## Requirements

- Python >= 3.10
- Docker and Docker Compose (for containerized deployment)

## Quick Start with Docker

The easiest way to run the agent is using Docker Compose, which automatically sets up all services:

```bash
# Start all services (Pipecat agent, Ollama, Speaches)
docker-compose up --build
```

This will:
- Build and start the Pipecat agent server
- Start Ollama for LLM inference
- Start Speaches for speech processing
- Automatically download required models on first run
- Serve the web interface on http://localhost:7860

Models should be manually downloaded


## Manual Model Download

If you want to pre-download models before starting the agent, or if automatic download fails:

### Ollama Models

```bash
docker compose exec ollama "ollama pull llama3.2:3b"
```

### Speaches Models

Speaches automatically downloads models on first use, but you can pre-download them:

```bash
# If running Speaches locally with Python
export SPEACHES_BASE_URL="http://localhost:8000"

uvx speaches-cli model download Systran/faster-distil-whisper-small.en
# Download TTS model (~80MB)
uvx speaches-cli model download speaches-ai/Kokoro-82M-v1.0-ONNX
```

### Verify Models

```bash
# Check Ollama models
curl http://localhost:11434/api/tags

# Check Speaches models
curl http://localhost:8000/v1/models
```

## Project Structure

```
pipecat-agent/
├── bot.py              # Agent logic and pipeline
├── server.py           # FastAPI HTTP server
├── config.py           # Configuration management
├── model_utils.py      # Model availability checks
├── kokoro_tts.py       # Custom Kokoro TTS service
├── index.html          # Web interface
├── Dockerfile          # Docker image definition
├── docker-compose.yml  # Multi-service orchestration
├── pyproject.toml      # Python dependencies
├── .env.example        # Example environment variables
├── .gitignore          # Git ignore rules
├── speaches/           # Speaches submodule
└── README.md           # This file
```

## How It Works

### Pipeline Flow

1. **User speaks** → Audio captured via WebRTC
2. **VAD detects speech** → Silero VAD identifies voice activity
3. **STT transcribes** → Speaches converts speech to text
4. **LLM processes** → Ollama generates response
5. **TTS synthesizes** → Speaches converts text to speech
6. **User hears response** → Audio streamed via WebRTC

### Service Architecture

The application consists of three services:

1. **Pipecat Agent** - Orchestrates the voice pipeline and handles WebRTC connections
2. **Ollama** - Provides local LLM inference
3. **Speaches** - Provides local speech-to-text and text-to-speech

All services communicate over a Docker network and can be scaled independently.

## GPU Support

To enable GPU acceleration for Ollama:

1. Uncomment the GPU configuration in `docker-compose.yml`:
```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
```

2. For Speaches GPU support, set `SPEACHES_MODE=cuda` in `.env`

## License

BSD 2-Clause License
