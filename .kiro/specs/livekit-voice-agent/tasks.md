# Implementation Plan: LiveKit Voice Agent

## Overview

This implementation plan guides the creation of a voice AI agent using the LiveKit Agents framework. The agent will use Deepgram for STT, Gemini for LLM, and ElevenLabs for TTS through LiveKit Inference. The implementation follows the same structure and user experience as the existing Pipecat agent but leverages LiveKit's architecture.

## Tasks

- [x] 1. Set up project structure and configuration
  - Create `livekit-agent/` directory in the workspace root
  - Create `config.py` module for environment variable management
  - Create `pyproject.toml` with LiveKit Agents SDK and dependencies
  - Create `.env.example` file with all required environment variables
  - Create `.gitignore` file for Python projects
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 1.1 Write property test for configuration validation
  - **Property 1: Configuration Validation**
  - **Validates: Requirements 2.1, 2.4, 2.5**

- [x] 2. Implement agent module with LiveKit Agents framework
  - [x] 2.1 Create `agent.py` module with VoiceAssistant class
    - Define agent with system instructions
    - Configure voice pipeline (STT, LLM, TTS) using LiveKit Inference
    - Set up VAD for turn detection
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 2.2 Implement agent session creation function
    - Create `create_agent_session()` function decorated with `@server.rtc_session()`
    - Initialize AgentSession with configured pipeline
    - Handle agent greeting on connection
    - Handle cleanup on disconnection
    - _Requirements: 1.1, 3.1, 3.3, 3.4, 3.5_

  - [ ]* 2.3 Write unit tests for agent initialization
    - Test agent creation with custom instructions
    - Test pipeline configuration
    - _Requirements: 1.1, 8.1, 8.2, 8.3_

- [x] 3. Implement HTTP server with FastAPI
  - [x] 3.1 Create `server.py` module with FastAPI application
    - Initialize FastAPI app with CORS middleware
    - Configure server to bind to host and port from config
    - _Requirements: 10.1, 10.6_

  - [x] 3.2 Implement web interface serving endpoint
    - Create GET `/` endpoint to serve `index.html`
    - _Requirements: 10.2, 4.1_

  - [x] 3.3 Implement LiveKit room connection endpoint
    - Create POST `/connect` endpoint
    - Generate LiveKit room and access token
    - Return connection details (URL, token, room name)
    - _Requirements: 3.1, 3.2, 10.3_

  - [x] 3.4 Implement health check endpoint
    - Create GET `/health` endpoint
    - Check LiveKit server reachability
    - Return health status with timestamp
    - _Requirements: 9.1, 9.2, 9.3_

  - [ ]* 3.5 Write unit tests for server endpoints
    - Test web interface serving
    - Test room creation and token generation
    - Test health check responses
    - Test error handling for invalid requests
    - _Requirements: 10.2, 10.3, 10.4_

- [ ]* 3.6 Write property test for concurrent connection handling
  - **Property 5: Concurrent Connection Handling**
  - **Validates: Requirements 10.5**

- [x] 4. Create web interface matching Pipecat design
  - [x] 4.1 Create `index.html` with matching UI design
    - Implement gradient background and card layout
    - Add microphone icon and title
    - Add connection status indicator with animations
    - Add connect/disconnect button
    - Add error message display area
    - _Requirements: 4.1, 4.2, 4.3, 4.6_

  - [x] 4.2 Implement LiveKit client integration
    - Add LiveKit client SDK script
    - Implement room connection logic
    - Handle microphone permissions
    - Establish WebRTC connection to LiveKit room
    - Stream audio bidirectionally
    - _Requirements: 4.3, 4.4, 4.5_

  - [x] 4.3 Implement connection state management
    - Update UI based on connection state (disconnected, connecting, connected)
    - Handle connection errors with user-friendly messages
    - Implement connect/disconnect button logic
    - _Requirements: 4.2, 4.3, 4.4_

- [x] 5. Implement error handling and logging
  - [x] 5.1 Add structured logging throughout the application
    - Configure logging in config module
    - Add log statements for connections, disconnections, errors
    - Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 5.2 Implement error handling for configuration
    - Validate required environment variables on startup
    - Log clear error messages for missing/invalid config
    - Exit gracefully with appropriate exit codes
    - _Requirements: 2.4, 2.5, 9.5_

  - [x] 5.3 Implement error handling for runtime errors
    - Handle LiveKit connection failures
    - Handle room creation failures
    - Handle agent initialization failures
    - Continue operating after non-fatal errors
    - _Requirements: 3.5, 8.5, 9.4_

- [ ]* 5.4 Write property test for error resilience
  - **Property 2: Error Resilience**
  - **Validates: Requirements 3.5, 8.5, 9.4**

- [ ]* 5.5 Write property test for structured logging
  - **Property 3: Structured Logging**
  - **Validates: Requirements 9.1, 9.2, 9.3**

- [ ]* 5.6 Write property test for configuration error messages
  - **Property 4: Configuration Error Messages**
  - **Validates: Requirements 9.5**

- [x] 6. Create Docker deployment configuration
  - [x] 6.1 Create Dockerfile for the agent
    - Use Python base image
    - Install uv package manager
    - Copy project files
    - Install dependencies using uv
    - Set up entrypoint to run server
    - _Requirements: 5.1, 5.5, 6.1_

  - [x] 6.2 Create docker-compose.yml
    - Define agent service with environment variables
    - Expose web server port
    - Configure service dependencies if needed
    - _Requirements: 5.2, 5.3, 5.4_

  - [x] 6.3 Create environment variable documentation
    - Document all required environment variables in `.env.example`
    - Include LiveKit connection details (URL, API key, API secret)
    - Include system instruction configuration
    - _Requirements: 2.1, 2.2, 2.3_

- [ ] 7. Integration and testing
  - [ ] 7.1 Test complete connection flow
    - Start the server
    - Open web interface in browser
    - Test microphone permissions
    - Test WebRTC connection establishment
    - Test bidirectional audio streaming
    - _Requirements: 1.1, 3.1, 3.2, 3.3, 4.3, 4.4, 4.5_

  - [ ] 7.2 Test agent conversation functionality
    - Verify STT transcription works correctly
    - Verify LLM generates appropriate responses
    - Verify TTS synthesizes speech correctly
    - Verify agent greeting on connection
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 3.4_

  - [ ] 7.3 Test error scenarios
    - Test behavior with invalid configuration
    - Test behavior with connection failures
    - Test behavior with service unavailability
    - Verify error messages are clear and actionable
    - _Requirements: 2.5, 3.5, 8.5, 9.3, 9.4, 9.5_

  - [ ] 7.4 Test Docker deployment
    - Build Docker image
    - Run container with docker-compose
    - Verify all services start correctly
    - Test agent functionality in containerized environment
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- The implementation follows the same structure as the existing Pipecat agent
- LiveKit Inference is used for all AI services (STT, LLM, TTS) to avoid managing separate API keys
- The web interface matches the look and feel of the Pipecat implementation
- Property tests validate universal correctness properties across many inputs
- Unit tests validate specific examples and edge cases
