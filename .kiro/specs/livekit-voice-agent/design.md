# Design Document

## Overview

This document describes the design for a voice AI agent built using the LiveKit Agents framework. The system will provide a complete voice conversation experience using Deepgram for speech-to-text, Gemini for language understanding, and ElevenLabs for text-to-speech, all accessed through LiveKit Inference. The implementation follows the same structure and user experience as the existing Pipecat-based agent but leverages LiveKit's architecture for WebRTC communication and agent orchestration.

### Key Design Decisions

1. **LiveKit Agents Framework**: Use LiveKit's high-level AgentSession API for orchestrating the voice pipeline
2. **LiveKit Inference**: Leverage managed AI services (Deepgram STT, Gemini LLM, ElevenLabs TTS) through LiveKit Inference to avoid managing separate API keys
3. **FastAPI Server**: Maintain compatibility with the existing web interface by providing similar HTTP endpoints
4. **Docker Compose**: Package the application for easy deployment and consistency across environments
5. **uv Package Manager**: Use modern Python package management for fast, reliable dependency resolution

## Architecture

The system consists of three main layers:

### 1. Web Interface Layer
- Browser-based UI for user interaction
- WebRTC client for bidirectional audio streaming
- Connection management (connect/disconnect)
- Status display

### 2. HTTP Server Layer (FastAPI)
- Serves the web interface
- Manages LiveKit room connections
- Provides health check endpoints

### 3. Agent Layer (LiveKit Agents)
- AgentSession orchestrates the voice pipeline
- Processes audio input through STT (Deepgram)
- Generates responses through LLM (Gemini)
- Synthesizes speech through TTS (ElevenLabs)
- Manages conversation state and turn-taking


## Components and Interfaces

### 1. Configuration Module (config.py)

**Purpose**: Centralize environment variable management and validation

**Interface**:
```python
class Config:
    # LiveKit connection
    LIVEKIT_URL: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str
    
    # Server configuration
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 7860
    
    # Agent configuration
    SYSTEM_INSTRUCTION: str
    
    @classmethod
    def validate() -> bool:
        """Validate all required configuration values"""
        
    @classmethod
    def log_configuration() -> None:
        """Log current configuration for debugging"""
```

**Responsibilities**:
- Load environment variables with defaults
- Validate required configuration on startup
- Provide typed access to configuration values
- Log configuration for debugging (without exposing secrets)

### 2. Agent Module (agent.py)

**Purpose**: Define the voice AI agent logic using LiveKit Agents framework

**Interface**:
```python
class VoiceAssistant(Agent):
    """Custom agent with specific instructions and behavior"""
    
    def __init__(self, instructions: str):
        super().__init__(instructions=instructions)

async def create_agent_session(ctx: JobContext) -> None:
    """
    Create and start an AgentSession for handling voice conversations.
    
    This function is decorated with @server.rtc_session() to register
    it as the entrypoint for new LiveKit room connections.
    """
```

**Responsibilities**:
- Define agent instructions and personality
- Configure the voice pipeline (STT, LLM, TTS)
- Set up VAD (Voice Activity Detection) for turn detection
- Handle agent lifecycle (initialization, greeting, cleanup)
- Emit events for observability


### 3. HTTP Server Module (server.py)

**Purpose**: Provide HTTP endpoints for the web interface and LiveKit room management

**Interface**:
```python
app = FastAPI()

@app.get("/")
async def serve_index() -> FileResponse:
    """Serve the web interface HTML"""

@app.post("/connect")
async def connect(request: ConnectRequest) -> ConnectResponse:
    """
    Create a LiveKit room and return connection details.
    
    Request: { participant_identity: str }
    Response: { url: str, token: str, room_name: str }
    """

@app.get("/health")
async def health_check() -> dict:
    """Check system health and service availability"""
```

**Responsibilities**:
- Serve static web interface
- Create LiveKit rooms for new connections
- Generate access tokens for participants
- Provide health check endpoint
- Handle errors gracefully with appropriate HTTP status codes

### 4. Web Interface (index.html)

**Purpose**: Provide browser-based UI for voice conversations

**Interface**:
- Connect/Disconnect button
- Status display (Disconnected, Connecting, Connected)
- Audio element for playback
- LiveKit client SDK integration

**Responsibilities**:
- Request microphone permissions
- Establish WebRTC connection to LiveKit room
- Display connection status
- Handle user interactions (connect/disconnect)
- Stream audio bidirectionally
- Match the look and feel of the Pipecat implementation


## Data Models

### ConnectRequest
```python
class ConnectRequest(BaseModel):
    participant_identity: str = "user"
```

### ConnectResponse
```python
class ConnectResponse(BaseModel):
    url: str              # LiveKit server URL
    token: str            # Access token for the participant
    room_name: str        # Name of the created room
```

### HealthCheckResponse
```python
class HealthCheckResponse(BaseModel):
    status: str           # "healthy" or "degraded"
    livekit: bool         # LiveKit server reachability
    timestamp: str        # ISO 8601 timestamp
```

## Error Handling

### Configuration Errors
- **Missing required environment variables**: Log error and exit with code 1
- **Invalid configuration values**: Log specific validation error and exit with code 1

### Runtime Errors
- **LiveKit connection failures**: Log error, return 503 Service Unavailable
- **Room creation failures**: Log error, return 500 Internal Server Error
- **Token generation failures**: Log error, return 500 Internal Server Error
- **Agent initialization failures**: Log error, clean up resources, notify user

### Logging Strategy
- Use structured logging with log levels (DEBUG, INFO, WARNING, ERROR)
- Log all important events: connections, disconnections, errors
- Include context in error logs (room name, participant identity, error details)
- Avoid logging sensitive information (API keys, tokens)


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

The following properties define the correctness criteria for the LiveKit voice agent system. Each property references the specific requirements it validates.

### Property 1: Configuration Validation

*For any* set of configuration values, if all required fields (LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) are present and valid, then validation should succeed; otherwise, validation should fail with a clear error message indicating which field is missing or invalid.

**Validates: Requirements 2.1, 2.4, 2.5**

### Property 2: Error Resilience

*For any* non-fatal error (connection timeout, service unavailability, invalid input), the system should log the error with appropriate detail and continue operating without crashing.

**Validates: Requirements 3.5, 8.5, 9.4**

### Property 3: Structured Logging

*For any* important event (connection, disconnection, error), the system should emit a log entry with the appropriate log level (INFO for connections, ERROR for errors) and include relevant context (participant identity, room name, error details).

**Validates: Requirements 9.1, 9.2, 9.3**

### Property 4: Configuration Error Messages

*For any* configuration validation failure, the error message should clearly identify which configuration field is problematic and provide guidance on how to fix it.

**Validates: Requirements 9.5**

### Property 5: Concurrent Connection Handling

*For any* number of concurrent connection requests (within reasonable limits), the system should successfully create separate LiveKit rooms and return valid connection details for each request without interference between connections.

**Validates: Requirements 10.5**


## Testing Strategy

The testing strategy employs both unit tests and property-based tests to ensure comprehensive coverage of the system's behavior.

### Unit Testing

Unit tests will verify specific examples, edge cases, and integration points:

1. **Configuration Module Tests**
   - Test loading valid configuration from environment variables
   - Test validation with missing required fields
   - Test validation with invalid values (empty strings, invalid URLs)
   - Test configuration logging (verify sensitive data is not logged)

2. **Server Module Tests**
   - Test serving the web interface (GET /)
   - Test room creation endpoint (POST /connect)
   - Test health check endpoint (GET /health)
   - Test error responses for invalid requests
   - Test token generation for participants

3. **Agent Module Tests**
   - Test agent initialization with custom instructions
   - Test AgentSession configuration (STT, LLM, TTS models)
   - Test agent greeting behavior on connection
   - Test agent cleanup on disconnection

4. **Integration Tests**
   - Test complete connection flow (HTTP request → LiveKit room creation → token generation)
   - Test agent session lifecycle (start → greeting → conversation → cleanup)
   - Test error handling across module boundaries

### Property-Based Testing

Property-based tests will verify universal properties across many generated inputs using the Hypothesis library for Python. Each property test will run a minimum of 100 iterations to ensure comprehensive coverage.

1. **Property 1: Configuration Validation**
   - Generate random configuration dictionaries with various combinations of present/missing/invalid fields
   - Verify validation succeeds only when all required fields are valid
   - Verify error messages correctly identify problematic fields
   - **Tag**: Feature: livekit-voice-agent, Property 1: Configuration Validation

2. **Property 2: Error Resilience**
   - Generate various non-fatal error scenarios (timeouts, service errors, invalid inputs)
   - Verify system logs errors and continues operating
   - Verify no crashes or unhandled exceptions
   - **Tag**: Feature: livekit-voice-agent, Property 2: Error Resilience

3. **Property 3: Structured Logging**
   - Generate random events (connections, disconnections, errors) with various contexts
   - Verify each event produces a log entry with correct level and context
   - Verify log format is consistent and parseable
   - **Tag**: Feature: livekit-voice-agent, Property 3: Structured Logging

4. **Property 4: Configuration Error Messages**
   - Generate invalid configurations with different types of errors
   - Verify each error message clearly identifies the problem and provides guidance
   - Verify messages are actionable and user-friendly
   - **Tag**: Feature: livekit-voice-agent, Property 4: Configuration Error Messages

5. **Property 5: Concurrent Connection Handling**
   - Generate random numbers of concurrent connection requests (1-20)
   - Verify each request receives unique room details
   - Verify no interference between concurrent requests
   - Verify all connections can be established successfully
   - **Tag**: Feature: livekit-voice-agent, Property 5: Concurrent Connection Handling

### Testing Tools

- **pytest**: Test runner and framework
- **pytest-asyncio**: Support for async test functions
- **hypothesis**: Property-based testing library
- **httpx**: HTTP client for testing FastAPI endpoints
- **pytest-mock**: Mocking support for external dependencies

### Test Organization

Tests will be organized in a `tests/` directory with the following structure:
- `tests/unit/` - Unit tests for individual modules
- `tests/integration/` - Integration tests across modules
- `tests/properties/` - Property-based tests
- `tests/conftest.py` - Shared fixtures and configuration
