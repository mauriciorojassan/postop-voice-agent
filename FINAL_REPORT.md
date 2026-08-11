# Post-Operative Voice Follow-Up Agent

## Executive Summary

This repository contains a FastAPI application for post-operative patient follow-up in Colombian Spanish. It combines a bidirectional voice WebSocket, speech-to-text, adaptive conversation state, deterministic clinical red-flag escalation, optional Llama-based triage, local text-to-speech, and an administrative knowledge console backed by ChromaDB.

The verified test result is **48 passed** using the repository virtual environment. This is a prototype and must not replace assessment or instructions from qualified clinical staff.

## Architecture

The application is a single Python/FastAPI service with two primary surfaces:

- `/ws/voice`: accepts audio chunks, transcribes them, processes a conversation turn, returns structured events and synthesized audio, and emits a call summary.
- `/api/documents`: uploads, lists, and deletes PDF knowledge documents. Uploads are validated, extracted, chunked, embedded, and stored in persistent ChromaDB.

The voice path uses `ConversationManager` to progress through pain, fever, mobility, wound, appetite, and sleep domains. `EscalationEngine` evaluates each utterance before normal progression. Its deterministic safety floor can force `rojo`; optional Groq/Llama reasoning can provide contextual triage but cannot lower a safety-floor escalation. Ambiguous replies receive clarification, and repeated ambiguity is handed off as `amarillo`.

See [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md) for the component and data-flow diagram.

## Models and Tools

| Area | Model or tool | Role |
|---|---|---|
| Web service | FastAPI, Uvicorn | HTTP, WebSocket, static console, and health endpoint |
| STT | Groq Whisper Large V3 | Spanish audio transcription with post-operative vocabulary prompting |
| Triage reasoning | Llama 3 through Groq, optional | Contextual triage when a Groq client is configured |
| Safety floor | Python regex and threshold rules | Synchronous red-flag detection and one-way escalation to `rojo` |
| Retrieval | BGE-M3, ChromaDB | Multilingual embeddings and persistent local document retrieval |
| TTS | Kokoro-82M ONNX, Piper fallback | Local Spanish speech synthesis with mock audio fallback for development/tests |
| Validation | Pytest, FastAPI TestClient | Unit and integration coverage for conversation, escalation, RAG, admin, voice, TTS, and health paths |

## Reproducible Setup in 15 Minutes or Less

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install the pinned dependencies:

   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Create local configuration from the checked-in template:

   ```bash
   cp .env.example .env
   ```

   Set `GROQ_API_KEY` only when live Groq STT or reasoning is required. Do not commit `.env` or credentials.

4. Start the service:

   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. Verify the service and interfaces:

   ```bash
   curl -s http://localhost:8000/health
   .venv/bin/pytest -q
   ```

   Expected test result: `48 passed`.

   Available interfaces are `http://localhost:8000/docs`, `http://localhost:8000/admin`, and the call surface at `http://localhost:8000/call`.

## Verified Tests

Command executed from the repository root:

```text
./.venv/bin/pytest -q
48 passed, 15 warnings in 19.23s
```

The warnings are dependency deprecation warnings and did not fail the suite. Running the system `pytest` outside the project virtual environment is not a valid project verification because required packages such as ChromaDB and pandas are unavailable there.

## Limitations and Risks

- The application is a prototype and is not a medical device or a substitute for professional clinical judgment.
- Live Groq behavior requires a valid `GROQ_API_KEY`, network access, and provider availability.
- The default voice route uses a sample trajectory snapshot; production deployment requires authenticated patient and case data handling.
- Rate limiting is process-local and should be replaced with shared protection for multiple workers or public deployment.
- ChromaDB is local persistent storage; it is not configured as a multi-user production data platform.
- TTS may return mock silent WAV data when model files or Piper are unavailable.
- Authentication, authorization, audit retention, encryption policy, and production observability are outside this repository's current scope.
- The test suite verifies behavior but does not establish clinical efficacy or regulatory compliance.

## Delivery Checklist

- [x] Final technical report created.
- [x] Architecture diagram created from the implemented components.
- [x] README links to both delivery artifacts.
- [x] README includes the pending video placeholder without inventing a URL.
- [x] `LICENSE` is present and referenced by the README/report.
- [x] `.env.example` is present and referenced by the setup instructions.
- [x] Test suite verified with 48 passing tests.
- [ ] Upload the video demo to YouTube as **unlisted** before final submission.
- [ ] Replace the video placeholder with the real YouTube unlisted URL before final submission.

## License and Configuration References

The repository is distributed under the [MIT License](LICENSE). Local environment variables must be created from [.env.example](.env.example); secrets belong in `.env`, which must remain uncommitted.
