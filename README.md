# Voice AI Landscape Demo

A comprehensive comparison of voice AI frameworks and deployment strategies, featuring implementations using LiveKit Agents and Pipecat. This project demonstrates different approaches to building real-time voice assistants, from cloud-managed services to fully local deployments.

## Overview

This repository contains two complete voice agent implementations, each showcasing different architectural approaches and trade-offs:

1. **LiveKit Agent** - Cloud-managed voice AI with enterprise features
2. **Pipecat Agent** - Local-first voice AI with full privacy control

## Project Structure

```
voice-ai-landscape-demo/
├── livekit-agent/          # LiveKit Agents implementation
│   ├── agent.py            # Agent logic with LiveKit pipeline
│   ├── server.py           # FastAPI server for web interface
│   ├── config.py           # Configuration management
│   ├── index.html          # Web interface
│   ├── docker-compose.yml  # Multi-container setup
│   └── README.md           # Detailed documentation
│
├── pipecat-agent/          # Pipecat implementation
    ├── bot.py              # Bot logic with Pipecat pipeline
    ├── server.py           # FastAPI server with WebRTC
    ├── config.py           # Configuration management
    ├── model_utils.py      # Model availability checks
    ├── kokoro_tts.py       # Custom TTS service
    ├── index.html          # Web interface
    ├── docker-compose.yml  # Multi-service orchestration
    ├── speaches/           # Speaches submodule (local STT/TTS)
    └── README.md           # Detailed documentation


```

## Getting Started

### LiveKit Agent (Cloud-Managed)

```bash
cd livekit-agent

# 1. Configure LiveKit credentials
cp .env.example .env
# Edit .env with your LiveKit Cloud credentials from https://cloud.livekit.io

# 2. Download required models
docker compose up --build
```

Then open the web interface at http://localhost:7860 to test your agent.

**Key Features:**
- Managed WebRTC infrastructure
- Built-in monitoring and analytics
- Global edge network for low latency

See [livekit-agent/README.md](livekit-agent/README.md) for detailed documentation.

### Pipecat Agent (Local-First)

```bash
cd pipecat-agent

# Start all services with Docker Compose
docker-compose up --build
```

This automatically sets up:
- Pipecat agent server
- Ollama for local LLM inference
- Speaches for local speech processing
- Web interface on http://localhost:7860

**Key Features:**
- Fully local processing (no data leaves your infrastructure)
- Complete control over models and configuration
- No per-usage costs (only infrastructure)
- Works offline after initial model download
- Customizable pipeline architecture

See [pipecat-agent/README.md](pipecat-agent/README.md) for detailed documentation.

## Architecture Comparison

### LiveKit Agent Architecture

```
User Browser
    ↓ WebRTC
LiveKit Cloud (managed infrastructure)
    ↓
Your Agent Server
    ↓ LiveKit Inference API
Deepgram STT → Gemini LLM → ElevenLabs TTS
```


### Pipecat Agent Architecture

```
User Browser
    ↓ WebRTC
Pipecat Agent Server
    ↓
Speaches (local) → Ollama (local) → Speaches (local)
    STT              LLM              TTS
```

## Technology Stack

### LiveKit Agent
- **Framework:** LiveKit Agents
- **Transport:** LiveKit WebRTC (managed)
- **STT:** Deepgram via LiveKit Inference
- **LLM:** Google Gemini via LiveKit Inference
- **TTS:** ElevenLabs via LiveKit Inference
- **VAD:** Silero
- **Server:** FastAPI + uvicorn
- **Deployment:** Docker + LiveKit Cloud

### Pipecat Agent
- **Framework:** Pipecat
- **Transport:** SmallWebRTCTransport
- **STT:** Speaches (Faster Whisper)
- **LLM:** Ollama (Llama 3.2)
- **TTS:** Speaches (Kokoro TTS)
- **VAD:** Silero
- **Server:** FastAPI + uvicorn
- **Deployment:** Docker Compose

## Requirements

### LiveKit Agent
- Python >= 3.10, < 3.14
- uv package manager
- LiveKit Cloud account (free tier available)
- API keys: Deepgram, Google Gemini, ElevenLabs

### Pipecat Agent
- Python >= 3.10
- Docker and Docker Compose
- 4GB+ RAM (8GB+ recommended)
- GPU optional but recommended for performance

## Resources

### Documentation
- [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
- [Pipecat Documentation](https://docs.pipecat.ai/)
- [Speaches Documentation](https://github.com/speaches-ai/speaches)
- [Ollama Documentation](https://ollama.ai/docs)

### Community
- [LiveKit Discord](https://livekit.io/discord)
- [Pipecat Discord](https://discord.gg/pipecat)

## License

BSD 2-Clause License

## Acknowledgments

- **LiveKit** for the excellent Agents framework and cloud infrastructure
- **Pipecat** for the flexible voice AI pipeline framework
- **Speaches** for local speech processing capabilities
- **Ollama** for easy local LLM deployment
