# Design Document: Pipecat Voice Agent with Speaches Integration

## Overview

This design describes a voice AI agent system built using the Pipecat framework with Speaches integration for local speech-to-text (STT) and text-to-speech (TTS) processing. The system enables real-time voice conversations through a web interface using WebRTC transport, all running in a containerized Docker Compose environment.

The architecture follows a modular design with clear separation between:
- **Transport layer**: WebRTC-based real-time communication
- **Processing pipeline**: Pipecat orchestration of audio, LLM, and speech services
- **Speech services**: Speaches for local STT/TTS processing
- **LLM inference**: Ollama for local LLM processing
- **Web interface**: Browser-based user interaction
- **Orchestration**: Docker Compose for service management

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│  Web Browser    │
│  (Web Interface)│
└────────┬────────┘
         │ WebRTC
         │
┌────────▼────────────────────────────────────────┐
│         Pipecat Agent Container                 │
│  ┌──────────────────────────────────────────┐  │
│  │  FastAPI Server                          │  │
│  │  - WebRTC Signaling (/api/offer)        │  │
│  │  - ICE Candidate Exchange (/api/patch)  │  │
│  │  - Web Interface Serving (/)            │  │
│  └──────────────┬───────────────────────────┘  │
│                 │                                │
│  ┌──────────────▼───────────────────────────┐  │
│  │  Pipecat Pipeline                        │  │
│  │  ┌────────────────────────────────────┐  │  │
│  │  │ SmallWebRTCTransport               │  │  │
│  │  │ - Audio Input/Output               │  │  │
│  │  │ - VAD (Silero)                     │  │  │
│  │  └────────┬───────────────────────────┘  │  │
│  │           │                                │  │
│  │  ┌────────▼───────────────────────────┐  │  │
│  │  │ LLM Context Aggregator             │  │  │
│  │  └────────┬───────────────────────────┘  │  │
│  │           │                                │  │
│  │  ┌────────▼───────────────────────────┐  │  │
│  │  │ Speech Processing (via Speaches)   │  │  │
│  │  │ - STT: Audio → Text                │  │  │
│  │  │ - TTS: Text → Audio                │  │  │
│  │  └────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────┘  │
└─────────────────┬───────────────┬───────────────┘
                  │ HTTP API      │ HTTP API
                  │               │
┌─────────────────▼─────────┐   ┌▼─────────────────────────────┐
│  Speaches Container       │   │  Ollama Container            │
│  ┌─────────────────────┐  │   │  ┌────────────────────────┐  │
│  │ OpenAI-Compatible   │  │   │  │ Ollama API             │  │
│  │ API                 │  │   │  │ - /api/generate        │  │
│  │ - /v1/audio/        │  │   │  │ - /api/chat            │  │
│  │   transcriptions    │  │   │  └────────────────────────┘  │
│  │ - /v1/audio/speech  │  │   │  ┌────────────────────────┐  │
│  └─────────────────────┘  │   │  │ Model Storage          │  │
│  ┌─────────────────────┐  │   │  │ - Llama 3.2 (3B/1B)    │  │
│  │ Model Storage       │  │   │  └────────────────────────┘  │
│  │ - STT Models        │  │   └──────────────────────────────┘
│  │ - TTS Models        │  │
│  └─────────────────────┘  │
└───────────────────────────┘
```

### Component Interaction Flow

1. **User initiates conversation**:
   - User opens web interface in browser
   - JavaScript establishes WebRTC connection
   - Sends offer to `/api/offer` endpoint

2. **Connection establishment**:
   - FastAPI server receives offer
   - SmallWebRTCRequestHandler processes offer
   - Creates WebRTC connection
   - Spawns new Pipecat agent session
   - Returns SDP answer to browser

3. **Audio processing pipeline**:
   - Browser captures microphone audio → WebRTC → Pipecat Transport
   - VAD detects speech activity
   - Audio sent to Speaches STT endpoint
   - Text transcription returned
   - LLM Context Aggregator adds to conversation context
   - Text sent to Ollama LLM endpoint (Llama 3.2)
   - LLM generates response
   - Response text sent to Speaches TTS endpoint
   - Synthesized audio returned
   - Audio streamed back through WebRTC → Browser speakers

## Components and Interfaces

### 1. Pipecat Agent Application

**File**: `pipecat-agent/bot.py`

**Responsibilities**:
- Initialize and configure Pipecat pipeline
- Manage conversation context
- Integrate with Speaches for STT/TTS
- Integrate with Ollama
- Handle WebRTC connection lifecycle

**Key Classes/Functions**:

```python
async def run_bot(webrtc_connection):
    """
    Main bot entry point that sets up the Pipecat pipeline.
    
    Args:
        webrtc_connection: WebRTC connection from SmallWebRTCTransport
    """
    # Initialize transport with VAD
    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
            audio_out_10ms_chunks=2
        )
    )
    
    # Initialize LLM service (Pipecat's native Ollama support)
    llm = OllamaLLMService(
        base_url=OLLAMA_URL,
        model=OLLAMA_MODEL  # e.g., "llama3.2:3b" or "llama3.2:1b"
    )
    
    # Initialize STT/TTS with Speaches using OpenAI services
    stt = OpenAISTTService(
        api_key="not-needed",
        base_url=f"{SPEACHES_URL}/v1",
        model=STT_MODEL
    )
    
    tts = OpenAITTSService(
        api_key="not-needed",
        base_url=f"{SPEACHES_URL}/v1",
        model=TTS_MODEL,
        voice=TTS_VOICE
    )
    
    # Create context and aggregator
    context = LLMContext(
        [
            {
                "role": "user",
                "content": "Start by greeting the user warmly and introducing yourself."
            }
        ]
    )
    context_aggregator = LLMContextAggregatorPair(context)
    
    # Create pipeline
    pipeline = Pipeline([
        transport.input(),
        stt,
        context_aggregator.user(),
        llm,
        tts,
        transport.output(),
        context_aggregator.assistant()
    ])
    
    # Create task
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True
        )
    )
    
    # Event handlers
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")
        # Kick off the conversation with initial greeting
        await task.queue_frames([LLMRunFrame()])
    
    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await task.cancel()
    
    # Run pipeline
    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)
```

**Configuration**:
- `SPEACHES_BASE_URL`: Speaches service endpoint (default: `http://speaches:8000`)
- `OLLAMA_BASE_URL`: Ollama service endpoint (default: `http://ollama:11434`)
- `OLLAMA_MODEL`: Ollama model to use (default: `llama3.2:3b`)
- `SYSTEM_INSTRUCTION`: System prompt for the agent

### 2. FastAPI Server

**File**: `pipecat-agent/server.py`

**Responsibilities**:
- Handle WebRTC signaling
- Serve web interface
- Manage agent sessions
- Handle ICE candidate exchange

**Endpoints**:

```python
@app.post("/api/offer")
async def offer(request: SmallWebRTCRequest, background_tasks: BackgroundTasks):
    """
    Handle WebRTC offer and create agent session.
    
    Returns SDP answer for WebRTC connection.
    """
    async def webrtc_connection_callback(connection):
        background_tasks.add_task(run_bot, connection)
    
    answer = await small_webrtc_handler.handle_web_request(
        request=request,
        webrtc_connection_callback=webrtc_connection_callback
    )
    return answer

@app.patch("/api/offer")
async def ice_candidate(request: SmallWebRTCPatchRequest):
    """
    Handle ICE candidate exchange for WebRTC connection.
    """
    await small_webrtc_handler.handle_patch_request(request)
    return {"status": "success"}

@app.get("/")
async def serve_index():
    """
    Serve the web interface HTML.
    """
    return FileResponse("index.html")
```

### 3. Speaches Integration

Speaches provides an OpenAI-compatible API, so we use Pipecat's built-in `OpenAISTTService` and `OpenAITTSService` with a custom `base_url` pointing to the local Speaches instance.

**STT Service Configuration**:

```python
from pipecat.services.openai import OpenAISTTService

# Initialize STT with Speaches endpoint
stt = OpenAISTTService(
    api_key="not-needed",  # Speaches doesn't require API key
    base_url="http://speaches:8000/v1",
    model="Systran/faster-distil-whisper-small.en"
)
```

**TTS Service Configuration**:

```python
from pipecat.services.openai import OpenAITTSService

# Initialize TTS with Speaches endpoint
tts = OpenAITTSService(
    api_key="not-needed",  # Speaches doesn't require API key
    base_url="http://speaches:8000/v1",
    model="speaches-ai/Kokoro-82M-v1.0-ONNX",
    voice="af_heart"
)
```

**Key Points**:
- Speaches implements the OpenAI `/v1/audio/transcriptions` and `/v1/audio/speech` endpoints
- No custom wrapper classes needed - use Pipecat's native OpenAI services
- Set `base_url` to point to local Speaches instance
- API key can be any non-empty string (Speaches doesn't validate it)
- All OpenAI TTS/STT parameters are supported (model, voice, response_format, etc.)

### 4. Ollama Integration

Pipecat provides native support for Ollama through the `OllamaLLMService`, which inherits from `BaseOpenAILLMService` and provides an OpenAI-compatible interface for locally-run Ollama models.

**LLM Service Configuration**:

```python
from pipecat.services.ollama import OllamaLLMService

# Initialize Ollama LLM
llm = OllamaLLMService(
    base_url="http://ollama:11434",
    model="llama3.2:3b"  # or llama3.2:1b for faster inference
)
```

**Key Points**:
- No API key required - Ollama runs entirely locally
- Compatible with OpenAI's API format for easy integration
- Supports all Ollama models (llama3.2, mistral, phi, gemma, etc.)
- Model must be pulled before use: `ollama pull llama3.2:3b`
- Default port is 11434
- Configurable base_url for Docker networking

**Model Management**:

```python
async def ensure_ollama_model(base_url: str, model: str):
    """
    Ensure Ollama model is pulled and available.
    
    Args:
        base_url: Ollama service URL
        model: Model name (e.g., "llama3.2:3b")
    """
    client = httpx.AsyncClient(base_url=base_url, timeout=300.0)
    
    # Check if model exists
    response = await client.get("/api/tags")
    models = response.json().get("models", [])
    
    if not any(m["name"] == model for m in models):
        # Pull model
        logger.info(f"Pulling Ollama model: {model}")
        await client.post("/api/pull", json={"name": model})
        logger.info(f"Model {model} pulled successfully")
```

### 5. Web Interface

**File**: `pipecat-agent/index.html`

**Responsibilities**:
- Provide UI for starting/stopping conversations
- Handle microphone permissions
- Establish WebRTC connection
- Display connection status
- Play audio responses

**Key Features**:
- Start/Stop conversation button
- Connection status indicator
- Microphone permission handling
- Audio playback
- Error display

**WebRTC Connection Logic**:

```javascript
async function startConversation() {
    // Get microphone access
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    
    // Create peer connection
    const pc = new RTCPeerConnection();
    
    // Add audio track
    stream.getTracks().forEach(track => pc.addTrack(track, stream));
    
    // Create offer
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    
    // Send offer to server
    const response = await fetch('/api/offer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sdp: offer.sdp, type: offer.type })
    });
    
    const answer = await response.json();
    await pc.setRemoteDescription(answer);
    
    // Handle ICE candidates
    pc.onicecandidate = async (event) => {
        if (event.candidate) {
            await fetch('/api/offer', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ candidate: event.candidate })
            });
        }
    };
    
    // Handle incoming audio
    pc.ontrack = (event) => {
        const audio = new Audio();
        audio.srcObject = event.streams[0];
        audio.play();
    };
}
```

## Data Models

### WebRTC Request Models

```python
class SmallWebRTCRequest(BaseModel):
    """WebRTC offer request from client."""
    sdp: str
    type: str  # "offer"

class SmallWebRTCPatchRequest(BaseModel):
    """ICE candidate exchange request."""
    candidate: dict
```

### Conversation Context

```python
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair

# Initialize context with optional initial messages
context = LLMContext(
    [
        {
            "role": "user",
            "content": "Start by greeting the user warmly and introducing yourself."
        }
    ]
)

# Create aggregator pair for managing user and assistant messages
context_aggregator = LLMContextAggregatorPair(context)
```

**Key Points**:
- `LLMContext` is Pipecat's native class for managing conversation history
- Initialize with a list of message dictionaries (role + content)
- `LLMContextAggregatorPair` provides `.user()` and `.assistant()` processors for the pipeline
- Context automatically accumulates messages as conversation progresses

### Configuration Models

```python
class AgentConfig(BaseModel):
    """Configuration for the Pipecat agent."""
    speaches_base_url: str = "http://speaches:8000"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2:3b"  # or llama3.2:1b for faster inference
    stt_model: str = "Systran/faster-distil-whisper-small.en"
    tts_model: str = "speaches-ai/Kokoro-82M-v1.0-ONNX"
    tts_voice: str = "af_heart"
    system_instruction: str = "You are a helpful voice assistant."
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: WebRTC Connection Establishment

*For any* valid WebRTC offer from a client, the server should return a valid SDP answer that enables bidirectional audio streaming.

**Validates: Requirements 3.2**

### Property 2: Agent Session Greeting

*For any* client connection, when the WebRTC connection is established, the agent should initiate the conversation with a greeting message.

**Validates: Requirements 3.4**

### Property 3: Agent Session Cleanup

*For any* client disconnection, the agent session should be gracefully terminated and all associated resources should be cleaned up.

**Validates: Requirements 3.5**

### Property 4: Conversation Context Preservation

*For any* sequence of user messages, the conversation context should accumulate all messages in order and be available to the LLM for generating contextually appropriate responses.

**Validates: Requirements 1.5**

### Property 5: Speaches Service Connectivity

*For any* Docker Compose stack startup with valid configuration, the Pipecat agent should be able to resolve and connect to the Speaches service at the configured endpoint.

**Validates: Requirements 2.2**

### Property 6: OpenAI-Compatible API Format

*For any* STT or TTS request to Speaches, the request should use the OpenAI-compatible API format with proper structure and required fields.

**Validates: Requirements 9.1, 9.2**

### Property 7: Speaches Error Handling

*For any* scenario where the Speaches service is unavailable or returns an error, the Pipecat agent should handle the error gracefully without crashing.

**Validates: Requirements 9.5**

### Property 8: Model Persistence Across Restarts

*For any* STT or TTS model that has been downloaded to the Speaches service, the model should remain available and functional after the service restarts.

**Validates: Requirements 8.6**

### Property 9: Environment Variable Configuration

*For any* environment variable set in the system configuration, the corresponding application setting should use the environment variable value; when not set, the system should use the defined default value.

**Validates: Requirements 7.1, 7.7**

### Property 10: Concurrent Session Isolation

*For any* number of simultaneous client connections (up to system limits), each should have an independent agent session with isolated conversation context that does not interfere with other sessions.

**Validates: Requirements 10.7**

### Property 11: New Agent Session Creation

*For any* valid WebRTC offer received by the server, a new agent session should be created and associated with that connection.

**Validates: Requirements 10.5**

## Error Handling

### WebRTC Connection Errors

**Scenario**: Client fails to establish WebRTC connection

**Handling**:
- Log connection failure details
- Return appropriate HTTP error status
- Display user-friendly error message in web interface
- Provide retry mechanism

### Speaches Service Unavailable

**Scenario**: Speaches service is not reachable

**Handling**:
- Implement retry logic with exponential backoff
- Log service unavailability
- Return graceful error to user
- Consider fallback to alternative STT/TTS provider (optional)

**Implementation**:
```python
async def call_speaches_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func()
        except httpx.ConnectError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### Model Not Downloaded

**Scenario**: Required STT or TTS model not available in Speaches

**Handling**:
- Check model availability on startup
- Provide clear error message indicating missing model
- Include instructions for downloading model
- Optionally auto-download on first use

### LLM API Errors

**Scenario**: LLM service returns error or times out

**Handling**:
- Log error details
- Return fallback response to user
- Maintain conversation context
- Implement timeout handling

### Audio Processing Errors

**Scenario**: Audio data is corrupted or in unsupported format

**Handling**:
- Validate audio format before processing
- Log validation failures
- Skip corrupted frames
- Continue processing subsequent audio

### Resource Exhaustion

**Scenario**: System runs out of memory or CPU

**Handling**:
- Implement connection limits
- Monitor resource usage
- Gracefully reject new connections when at capacity
- Log resource exhaustion events

## Testing Strategy

### Unit Tests

Unit tests will verify specific examples, edge cases, and error conditions for individual components:

**Transport Layer**:
- Test WebRTC offer/answer exchange with valid SDP
- Test ICE candidate handling
- Test connection cleanup on disconnect

**Speaches Integration**:
- Test STT API call with sample audio file
- Test TTS API call with sample text
- Test error handling for invalid API responses
- Test retry logic for connection failures

**Pipeline Components**:
- Test VAD with silent audio
- Test VAD with speech audio
- Test context aggregator with message sequences
- Test pipeline initialization

**Configuration**:
- Test environment variable loading
- Test default value fallback
- Test configuration validation

### Property-Based Tests

Property-based tests will verify universal properties across all inputs using a PBT library (e.g., Hypothesis for Python). Each test will run a minimum of 100 iterations.

**Test Configuration**:
- Library: Hypothesis (Python)
- Minimum iterations: 100 per property
- Tag format: `# Feature: pipecat-voice-agent, Property {N}: {property_text}`

**Property Test Examples**:

```python
from hypothesis import given, strategies as st
import pytest

# Feature: pipecat-voice-agent, Property 1: WebRTC Connection Establishment
@given(st.text(min_size=10))  # Generate random SDP strings
async def test_webrtc_offer_returns_answer(sdp):
    """For any valid WebRTC offer, server returns valid SDP answer."""
    request = SmallWebRTCRequest(sdp=sdp, type="offer")
    response = await offer(request, BackgroundTasks())
    assert response.type == "answer"
    assert len(response.sdp) > 0

# Feature: pipecat-voice-agent, Property 4: Speaches API Communication
@given(st.binary(min_size=100))  # Generate random audio data
async def test_stt_api_format(audio_data):
    """For any audio data, STT request uses OpenAI-compatible format."""
    stt = SpeachesSTTService(base_url="http://speaches:8000")
    # Verify request format matches OpenAI spec
    # This would use a mock to inspect the request
    pass

# Feature: pipecat-voice-agent, Property 5: Conversation Context Preservation
@given(st.lists(st.text(min_size=1), min_size=1, max_size=10))
async def test_context_accumulation(messages):
    """For any sequence of messages, context preserves all in order."""
    context = LLMContext([])
    for msg in messages:
        context.add_user_message(msg)
    
    assert len(context.messages) == len(messages)
    for i, msg in enumerate(messages):
        assert context.messages[i]["content"] == msg
        assert context.messages[i]["role"] == "user"
```

### Integration Tests

Integration tests will verify end-to-end functionality:

**Full Pipeline Test**:
- Start Docker Compose stack
- Establish WebRTC connection
- Send audio through pipeline
- Verify audio response received
- Verify conversation context maintained

**Speaches Integration Test**:
- Verify Pipecat agent can reach Speaches service
- Verify STT transcription works
- Verify TTS synthesis works
- Verify model persistence across restarts

**Multi-Client Test**:
- Establish multiple concurrent connections
- Verify session isolation
- Verify independent conversation contexts

### Manual Testing

Manual testing will verify user experience aspects:

- Web interface usability
- Audio quality
- Response latency
- Error message clarity
- Connection stability

## Security Considerations

### Configuration Management

- Store sensitive configuration in environment variables
- Never commit secrets to version control
- Use Docker secrets for production deployments
- Rotate credentials regularly

### Network Security

- Use HTTPS for production deployments
- Implement rate limiting on API endpoints
- Validate all input data
- Sanitize user messages before LLM processing
- Isolate services using Docker networks

### WebRTC Security

- Implement STUN/TURN servers for NAT traversal
- Use secure WebRTC (HTTPS required)
- Validate SDP offers before processing
- Implement connection timeouts

### Container Security

- Use non-root users in containers
- Scan images for vulnerabilities
- Keep base images updated
- Minimize attack surface
- Limit resource usage per container

### LLM Security

- Implement input validation and sanitization
- Set reasonable token limits
- Monitor for prompt injection attempts
- Implement content filtering if needed

## Monitoring and Observability

### Logging

**Log Levels**:
- DEBUG: Detailed pipeline events
- INFO: Connection events, API calls
- WARNING: Retry attempts, degraded performance
- ERROR: Failures, exceptions

**Log Format**:
```python
logger.info(
    "WebRTC connection established",
    extra={
        "client_id": client_id,
        "timestamp": datetime.utcnow().isoformat()
    }
)
```

### Metrics

**Key Metrics to Track**:
- Active connections count
- Average response latency
- STT/TTS API call duration
- LLM API call duration
- Error rates by type
- Resource usage (CPU, memory, GPU)

### Health Checks

**Endpoints**:
- `/health` - Overall system health
- `/health/speaches` - Speaches service connectivity
- `/health/ollama` - Ollama service connectivity

**Implementation**:
```python
@app.get("/health")
async def health_check():
    checks = {
        "speaches": await check_speaches_health(),
        "ollama": await check_ollama_health()
    }
    status = "healthy" if all(checks.values()) else "degraded"
    return {"status": status, "checks": checks}

async def check_ollama_health():
    """Check if Ollama service is reachable and model is loaded."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return response.status_code == 200
    except:
        return False
```

## Deployment Configuration

### Project Structure

```
pipecat-agent/
├── pyproject.toml          # Python dependencies (uv)
├── Dockerfile              # Container image definition
├── bot.py                  # Main agent logic
├── server.py               # FastAPI server
├── index.html              # Web interface
└── .env.example            # Environment variables template
```

### Python Dependencies

**File**: `pipecat-agent/pyproject.toml`

Using `uv` for modern Python dependency management:

```toml
[project]
name = "pipecat-voice-agent"
version = "0.1.0"
description = "Voice AI agent using Pipecat with Speaches and Ollama"
requires-python = ">=3.10"
dependencies = [
    "pipecat-ai[webrtc,openai,ollama,silero]>=0.0.50",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "python-dotenv>=1.0.1",
    "loguru>=0.7.2",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Key Dependencies**:
- `pipecat-ai[daily,openai,ollama,silero]` - Core Pipecat with plugins:
  - `webrtc`: SmallWebRTC transport support
  - `openai`: OpenAI STT/TTS services (used with Speaches)
  - `ollama`: Ollama LLM service
  - `silero`: Silero VAD analyzer
- `fastapi` - Web framework for server
- `uvicorn[standard]` - ASGI server with WebSocket support
- `python-dotenv` - Environment variable management
- `loguru` - Structured logging

### Dockerfile

**File**: `pipecat-agent/Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy project files
COPY pyproject.toml .
COPY bot.py server.py index.html ./

# Install dependencies using uv
RUN uv pip install --system -r pyproject.toml

# Expose port
EXPOSE 7860

# Run the application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
```

### Docker Compose Configuration

**Main Compose File**: `docker-compose.yml`

```yaml
services:
  pipecat-agent:
    build: ./pipecat-agent
    ports:
      - "7860:7860"
    environment:
      - SPEACHES_BASE_URL=http://speaches:8000
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_MODEL=${OLLAMA_MODEL:-llama3.2:3b}
      - STT_MODEL=${STT_MODEL:-Systran/faster-distil-whisper-small.en}
      - TTS_MODEL=${TTS_MODEL:-speaches-ai/Kokoro-82M-v1.0-ONNX}
      - TTS_VOICE=${TTS_VOICE:-af_heart}
    depends_on:
      - speaches
      - ollama
    networks:
      - voice-agent-network

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama-models:/root/.ollama
    networks:
      - voice-agent-network
    # Uncomment for GPU support
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: all
    #           capabilities: [gpu]

include:
  - path: ./speaches/compose.${SPEACHES_MODE:-cpu}.yaml
    env_file: .env

networks:
  voice-agent-network:
    driver: bridge

volumes:
  speaches-models:
    driver: local
  ollama-models:
    driver: local
```

### Environment Configuration

**File**: `.env.example`

```bash
# Ollama Configuration
OLLAMA_MODEL=llama3.2:3b  # Options: llama3.2:1b (faster), llama3.2:3b (better quality)

# Speaches Configuration
SPEACHES_MODE=cpu  # Options: cpu, cuda, cuda-cdi
STT_MODEL=Systran/faster-distil-whisper-small.en
TTS_MODEL=speaches-ai/Kokoro-82M-v1.0-ONNX
TTS_VOICE=af_heart

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=7860
```

### Speaches Submodule Setup

**Location**: `speaches/` (Git submodule)

**Initialization**:
```bash
git submodule add https://github.com/speaches-ai/speaches.git speaches
git submodule update --init --recursive
```

**Compose Files**:
- `speaches/compose.yaml` - Base configuration
- `speaches/compose.cpu.yaml` - CPU-only mode
- `speaches/compose.cuda.yaml` - CUDA GPU mode
- `speaches/compose.cuda-cdi.yaml` - CUDA with CDI

## Model Management

### Automatic Model Pulling

All models (Ollama LLM, Speaches STT/TTS) are automatically pulled on agent startup if not already available.

### Ollama Model Management

**Automatic Pull on Startup**:

```python
async def ensure_ollama_model(base_url: str, model: str):
    """
    Ensure Ollama model is pulled and available.
    Automatically pulls model if not present.
    """
    import httpx
    
    client = httpx.AsyncClient(base_url=base_url, timeout=300.0)
    
    try:
        response = await client.get("/api/tags")
        models = response.json().get("models", [])
        
        if not any(m["name"] == model for m in models):
            logger.info(f"Pulling Ollama model: {model} (this may take a few minutes)...")
            await client.post("/api/pull", json={"name": model}, timeout=600.0)
            logger.info(f"Model {model} pulled successfully")
        else:
            logger.info(f"Ollama model {model} already available")
    finally:
        await client.aclose()
```

**Available Models**:
- `llama3.2:1b` - Fast (~1GB download, ~1-2GB RAM)
- `llama3.2:3b` - Balanced (~2GB download, ~2-4GB RAM)

### Speaches Model Management

**Automatic Download on First Use**:

Speaches automatically downloads models on first API request. The agent startup can optionally pre-check model availability:

```python
async def ensure_speaches_models(base_url: str, stt_model: str, tts_model: str):
    """
    Check Speaches model availability.
    Models will auto-download on first use.
    """
    import httpx
    
    client = httpx.AsyncClient(base_url=base_url, timeout=600.0)
    
    try:
        response = await client.get("/v1/models")
        models = response.json().get("data", [])
        model_ids = [m["id"] for m in models]
        
        if stt_model not in model_ids:
            logger.info(f"STT model {stt_model} will be downloaded on first use")
        if tts_model not in model_ids:
            logger.info(f"TTS model {tts_model} will be downloaded on first use")
    finally:
        await client.aclose()
```

**Available Models**:
- STT: `Systran/faster-distil-whisper-small.en` (~150MB)
- TTS: `speaches-ai/Kokoro-82M-v1.0-ONNX` (~80MB)

### Model Storage

- Ollama: `/root/.ollama` → `ollama-models` volume
- Speaches: `/home/ubuntu/.cache/huggingface/hub` → `speaches-models` volume
- Both volumes persist across container restarts

## Performance Considerations

### Potential Improvements

1. **Multi-language Support**: Add language detection and multi-language models
2. **Voice Selection**: Allow users to choose from multiple TTS voices
3. **Conversation History**: Persist conversation history to database
4. **Analytics Dashboard**: Web UI for monitoring system metrics
5. **Mobile App**: Native mobile applications for iOS/Android
6. **Advanced VAD**: Implement more sophisticated voice activity detection
7. **Emotion Detection**: Analyze user sentiment and adjust responses
8. **Custom Wake Words**: Add wake word detection for hands-free activation
9. **Multi-modal Input**: Support text input alongside voice
10. **Agent Personalities**: Multiple agent personalities/characters

### Scalability Considerations

For production deployments at scale:

- **Load Balancing**: Distribute connections across multiple agent instances
- **Horizontal Scaling**: Run multiple Pipecat agent containers
- **Speaches Scaling**: Deploy multiple Speaches instances with load balancer
- **State Management**: Use Redis for shared state across instances
- **Message Queue**: Implement queue for handling high request volumes
- **CDN**: Serve static web interface assets from CDN
- **Database**: Add persistent storage for conversation history
- **Monitoring**: Implement comprehensive monitoring and alerting
