# Implementation Plan: Pipecat Voice Agent

## Overview

This implementation plan breaks down the development of a Pipecat-based voice AI agent with Speaches (STT/TTS) and Ollama (LLM) integration into discrete, manageable tasks. The agent will run in Docker Compose with a web interface for real-time voice conversations via WebRTC.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create `pipecat-agent/` directory structure
  - Create `pyproject.toml` with all required dependencies
  - Create `.env.example` with configuration templates
  - Create `.gitignore` for Python and Docker artifacts
  - _Requirements: 1.6, 6.1_

- [x] 2. Add Speaches as Git submodule
  - Initialize Speaches submodule in `speaches/` directory
  - Verify submodule compose files are accessible
  - _Requirements: 2.1_

- [x] 3. Implement Docker Compose orchestration
  - [x] 3.1 Create main `docker-compose.yml`
    - Define pipecat-agent service with build configuration
    - Define ollama service with volume mounts
    - Include Speaches compose file using include directive
    - Configure networks and volumes
    - Set up service dependencies
    - _Requirements: 5.1, 5.2, 5.3, 5.6, 5.7, 5.8_
  
  - [x] 3.2 Create Dockerfile for Pipecat agent
    - Base on Python 3.12-slim
    - Install system dependencies (libgl1, libglib2.0-0, curl)
    - Install uv package manager
    - Copy project files and install Python dependencies
    - Expose port 7860
    - Define startup command
    - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 4. Implement model management utilities
  - [x] 4.1 Create Ollama model management function
    - Implement `ensure_ollama_model()` to check and pull models
    - Add logging for model pull progress
    - Handle timeouts and errors gracefully
    - _Requirements: 8.1, 8.5, 8.6_
  
  - [ ]* 4.2 Write unit tests for Ollama model management
    - Test model availability check
    - Test model pull trigger
    - Test error handling
    - _Requirements: 8.1, 8.6_
  
  - [x] 4.3 Create Speaches model management function
    - Implement `ensure_speaches_models()` to check model availability
    - Add logging for model status
    - Handle auto-download on first use
    - _Requirements: 8.2, 8.5, 8.6_
  
  - [ ]* 4.4 Write unit tests for Speaches model management
    - Test model availability check
    - Test first-use download behavior
    - _Requirements: 8.2, 8.6_

- [x] 5. Implement core Pipecat agent (bot.py)
  - [x] 5.1 Create bot.py with imports and configuration
    - Import all required Pipecat modules
    - Import OpenAI and Ollama services
    - Load environment variables
    - Define system instruction
    - _Requirements: 1.1, 7.1_
  
  - [x] 5.2 Implement `run_bot()` function
    - Initialize SmallWebRTCTransport with VAD
    - Initialize OllamaLLMService with configured endpoint
    - Initialize OpenAISTTService pointing to Speaches
    - Initialize OpenAITTSService pointing to Speaches
    - Create LLMContext with initial greeting
    - Create LLMContextAggregatorPair
    - Build pipeline with all components
    - Create PipelineTask with metrics enabled
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 2.3, 2.4, 3.1_
  
  - [x] 5.3 Add event handlers
    - Implement `on_client_connected` handler to queue LLMRunFrame
    - Implement `on_client_disconnected` handler to cancel task
    - _Requirements: 3.4, 3.5_
  
  - [x] 5.4 Add startup model checks
    - Call `ensure_ollama_model()` before starting bot
    - Call `ensure_speaches_models()` before starting bot
    - _Requirements: 8.1, 8.2_
  
  - [ ]* 5.5 Write unit tests for bot initialization
    - Test pipeline creation with all components
    - Test event handler registration
    - _Requirements: 1.2, 1.3, 1.4_

- [ ] 6. Implement FastAPI server (server.py)
  - [ ] 6.1 Create server.py with FastAPI app
    - Initialize FastAPI application
    - Initialize SmallWebRTCRequestHandler
    - Load environment variables
    - _Requirements: 10.1_
  
  - [ ] 6.2 Implement WebRTC offer endpoint
    - Create POST `/api/offer` endpoint
    - Handle SmallWebRTCRequest
    - Create webrtc_connection_callback
    - Spawn bot in background task
    - Return SDP answer
    - _Requirements: 10.2, 10.5, 10.7_
  
  - [ ] 6.3 Implement ICE candidate endpoint
    - Create PATCH `/api/offer` endpoint
    - Handle SmallWebRTCPatchRequest
    - Process ICE candidates
    - _Requirements: 10.3, 3.6_
  
  - [ ] 6.4 Implement web interface endpoint
    - Create GET `/` endpoint
    - Serve index.html file
    - _Requirements: 10.4, 4.1_
  
  - [ ] 6.5 Add health check endpoints
    - Create GET `/health` endpoint
    - Implement `check_ollama_health()`
    - Implement `check_speaches_health()`
    - Return overall system status
    - _Requirements: 9.3, 9.4_
  
  - [ ]* 6.6 Write unit tests for server endpoints
    - Test offer endpoint with valid SDP
    - Test ICE candidate handling
    - Test health check responses
    - _Requirements: 10.2, 10.3_

- [ ] 7. Create web interface (index.html)
  - [ ] 7.1 Create HTML structure
    - Add page title and meta tags
    - Create container for UI elements
    - Add start/stop conversation button
    - Add connection status indicator
    - Add error message display area
    - _Requirements: 4.1, 4.2, 4.4_
  
  - [ ] 7.2 Implement WebRTC connection logic
    - Request microphone permissions
    - Create RTCPeerConnection
    - Add audio tracks to connection
    - Create and send offer to server
    - Handle SDP answer from server
    - Implement ICE candidate exchange
    - Handle incoming audio tracks
    - _Requirements: 4.3, 4.5, 4.6, 3.2, 3.3_
  
  - [ ] 7.3 Add UI interaction handlers
    - Implement start conversation button handler
    - Implement stop conversation button handler
    - Update connection status display
    - Show/hide error messages
    - _Requirements: 4.2, 4.4_
  
  - [ ]* 7.4 Write integration tests for web interface
    - Test microphone permission flow
    - Test WebRTC connection establishment
    - Test UI state updates
    - _Requirements: 4.2, 4.3, 4.5_

- [ ] 8. Implement configuration management
  - [ ] 8.1 Create configuration loading
    - Load SPEACHES_BASE_URL from environment
    - Load OLLAMA_BASE_URL from environment
    - Load OLLAMA_MODEL from environment with default
    - Load STT_MODEL from environment with default
    - Load TTS_MODEL from environment with default
    - Load TTS_VOICE from environment with default
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [ ]* 8.2 Write property test for configuration
    - **Property 9: Environment Variable Configuration**
    - **Validates: Requirements 7.1, 7.7**
    - Test that any set environment variable is used
    - Test that unset variables use defaults
    - _Requirements: 7.1, 7.7_

- [ ] 9. Implement error handling
  - [ ] 9.1 Add WebRTC connection error handling
    - Catch connection failures
    - Log error details
    - Return appropriate HTTP status
    - Display user-friendly error in UI
    - _Requirements: 3.2_
  
  - [ ] 9.2 Add Speaches service error handling
    - Implement retry logic with exponential backoff
    - Log service unavailability
    - Handle gracefully without crashing
    - _Requirements: 9.5, 2.2_
  
  - [ ] 9.3 Add Ollama service error handling
    - Handle model not available errors
    - Handle timeout errors
    - Log error details
    - _Requirements: 2.2_
  
  - [ ]* 9.4 Write property test for error handling
    - **Property 7: Speaches Error Handling**
    - **Validates: Requirements 9.5**
    - Test graceful handling when Speaches unavailable
    - Test retry logic
    - _Requirements: 9.5_

- [ ] 10. Checkpoint - Verify basic functionality
  - Start Docker Compose stack
  - Verify all services start successfully
  - Check Ollama model is pulled
  - Check Speaches models are available
  - Test web interface loads
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Write property-based tests
  - [ ]* 11.1 Write property test for WebRTC connection
    - **Property 1: WebRTC Connection Establishment**
    - **Validates: Requirements 3.2**
    - Test that any valid offer returns valid answer
    - _Requirements: 3.2_
  
  - [ ]* 11.2 Write property test for agent session greeting
    - **Property 2: Agent Session Greeting**
    - **Validates: Requirements 3.4**
    - Test that any connection triggers greeting
    - _Requirements: 3.4_
  
  - [ ]* 11.3 Write property test for session cleanup
    - **Property 3: Agent Session Cleanup**
    - **Validates: Requirements 3.5**
    - Test that any disconnection cleans up resources
    - _Requirements: 3.5_
  
  - [ ]* 11.4 Write property test for context preservation
    - **Property 4: Conversation Context Preservation**
    - **Validates: Requirements 1.5**
    - Test that any message sequence is preserved in order
    - _Requirements: 1.5_
  
  - [ ]* 11.5 Write property test for service connectivity
    - **Property 5: Speaches Service Connectivity**
    - **Validates: Requirements 2.2**
    - Test that agent can connect to Speaches on startup
    - _Requirements: 2.2_
  
  - [ ]* 11.6 Write property test for API format
    - **Property 6: OpenAI-Compatible API Format**
    - **Validates: Requirements 9.1, 9.2**
    - Test that any STT/TTS request uses correct format
    - _Requirements: 9.1, 9.2_
  
  - [ ]* 11.7 Write property test for model persistence
    - **Property 8: Model Persistence Across Restarts**
    - **Validates: Requirements 8.6**
    - Test that any downloaded model persists after restart
    - _Requirements: 8.6_
  
  - [ ]* 11.8 Write property test for concurrent sessions
    - **Property 10: Concurrent Session Isolation**
    - **Validates: Requirements 10.7**
    - Test that any number of sessions remain isolated
    - _Requirements: 10.7_
  
  - [ ]* 11.9 Write property test for session creation
    - **Property 11: New Agent Session Creation**
    - **Validates: Requirements 10.5**
    - Test that any valid offer creates new session
    - _Requirements: 10.5_

- [ ] 12. Integration testing
  - [ ]* 12.1 Test full voice conversation flow
    - Start Docker Compose stack
    - Establish WebRTC connection from browser
    - Send test audio through pipeline
    - Verify audio response received
    - Verify conversation context maintained
    - _Requirements: 1.2, 1.5, 2.3, 2.4, 3.2, 3.3_
  
  - [ ]* 12.2 Test multi-client scenario
    - Establish multiple concurrent connections
    - Verify session isolation
    - Verify independent conversation contexts
    - _Requirements: 10.7_
  
  - [ ]* 12.3 Test service restart resilience
    - Restart Speaches service
    - Verify models persist
    - Verify agent reconnects
    - _Requirements: 8.6, 2.2_

- [ ] 13. Documentation and deployment preparation
  - [ ] 13.1 Create README.md
    - Add project overview
    - Add prerequisites (Docker, uv)
    - Add installation instructions
    - Add usage instructions
    - Add configuration options
    - Add troubleshooting guide
    - _Requirements: 8.3, 8.4_
  
  - [ ] 13.2 Document model management
    - Document how to list available models
    - Document how to change models
    - Document model download process
    - _Requirements: 8.3, 8.4_
  
  - [ ] 13.3 Add GPU support documentation
    - Document how to enable GPU for Ollama
    - Document how to enable GPU for Speaches
    - Document CUDA requirements
    - _Requirements: 2.5, 2.6, 2.7_

- [ ] 14. Final checkpoint - End-to-end validation
  - Deploy complete stack with docker-compose up
  - Verify automatic model pulling works
  - Test voice conversation end-to-end
  - Verify all health checks pass
  - Test GPU mode (if available)
  - Verify all configuration options work
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property-based tests should run minimum 100 iterations
- All tests should be tagged with feature name and property number
- Model pulling happens automatically on first startup
- GPU support is optional and configurable via environment variables
