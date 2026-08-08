# Specification: Voice Conversation Loop

## Purpose

Defines the real-time voice streaming, transcription, reasoning, and speech synthesis pipeline in Colombian Spanish, including handling of colloquial slang (`capa2_ruidosa`), adaptive clarification loops, real-time interruption (barge-in), and latency budgets.

## Requirements

### Requirement: Real-Time Audio WebSocket Streaming

The system MUST establish a bi-directional WebSocket connection for streaming patient audio chunks and receiving synthesized agent audio responses.

#### Scenario: Successful audio stream connection and bi-directional exchange

- GIVEN a client establishes a WebSocket connection at `/ws/voice`
- WHEN the client streams recorded audio binary chunks (PCM/WAV)
- THEN the backend receives, buffers, and processes the audio stream without connection drops
- AND returns synthesized audio stream chunks in real-time

### Requirement: Groq Whisper STT with Colombian Slang Tuning

The system MUST transcribe incoming patient speech using Groq Whisper Large V3 with vocabulary prompts tuned for Colombian post-operative regionalisms (`capa2_ruidosa`, e.g., "calentura", "chuzo", "ta' hinchao").

#### Scenario: Transcribing colloquial patient input

- GIVEN a patient audio recording containing Colombian colloquialisms ("Doctor, me duele harto el chuzo y tengo calentura")
- WHEN transcribed by the Whisper STT service with regional vocabulary prompting
- THEN the resulting text accurately captures the semantic intent ("Doctor, me duele mucho la herida quirúrgica y tengo fiebre")

### Requirement: Adaptive Clarification Loops for Ambiguous Input

The system MUST trigger active clarification prompts when patient input is ambiguous, incomplete, or contains conflicting symptom descriptions.

#### Scenario: Clarifying ambiguous pain description

- GIVEN a patient states "Me duele un poquito por ahí" without specifying location or intensity
- WHEN the Llama reasoning model evaluates the input against post-op protocols
- THEN the agent initiates a targeted clarification prompt ("¿Te refieres a la herida quirúrgica o al abdomen? Y del 1 al 10, ¿qué tan fuerte es el dolor?")

### Requirement: Real-Time Interruption Handling (Barge-In)

The system MUST immediately cancel ongoing audio generation and playback when new patient speech input is detected during agent speech output.

#### Scenario: Patient interrupts agent speech

- GIVEN the agent is actively streaming audio response chunks to the client
- WHEN the client sends new audio input packets (barge-in signal)
- THEN the backend immediately halts TTS generation, drops remaining audio buffers, and processes the new patient input

### Requirement: End-to-End Latency Budget

The system MUST maintain an end-to-end P50 latency under 600ms and P95 latency under 950ms from audio chunk completion to first synthesized audio response chunk.

#### Scenario: Measuring voice loop latency

- GIVEN a complete patient voice utterance sent via WebSocket
- WHEN processed through STT, RAG/Llama reasoning, and TTS synthesis
- THEN the time to first audio output chunk (TTFB) is measured under 600ms (P50) across standard test runs
