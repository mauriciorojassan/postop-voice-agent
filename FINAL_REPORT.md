# Technical Report: Post-Operative Voice Follow-Up Agent

## Executive Summary

This repository implements a FastAPI prototype for post-operative follow-up in Colombian Spanish. Its demonstrated interaction is a browser microphone call: the user records a manual turn, sends `audio.webm` through a WebSocket, receives a transcript and structured response, and hears the answer through browser `speechSynthesis`. It is not telephony and must not replace qualified clinical judgment.

The current validation record contains **57 passing tests**, an HTTP health smoke check returning **200**, a WebSocket audio and ping-pong check, and a **46-second, 1280x720** video evidence recording.

## Architecture

The service exposes four relevant interfaces:

- `/call`: browser call surface using microphone capture and manual turns.
- `/ws/voice`: WebSocket endpoint for audio bytes, `EOT` turn boundaries, structured events, and `ping`/`pong`.
- `/api/documents`: PDF upload, listing, and deletion for the local RAG store.
- `/health`, `/admin`, and `/docs`: health, administration, and interactive API documentation.

The voice path is `audio.webm` -> local Faster-Whisper -> `ConversationManager` -> deterministic `EscalationEngine` -> optional Groq reasoning -> response event. The browser's `speechSynthesis` is the primary audible response in the demo. Optional backend Kokoro/Piper TTS remains available through `TTSService`.

The safety floor evaluates red flags before normal progression. It can force `rojo`; optional LLM reasoning cannot lower that escalation. Ambiguous answers enter clarification and repeated ambiguity can become `amarillo`.

See [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md) for the component and data-flow view.

## Models and Tools

| Area | Implementation | Role |
|---|---|---|
| Web service | FastAPI and Uvicorn | HTTP routes, WebSocket, static surfaces, and health endpoint |
| STT | Faster-Whisper, CPU/int8, local by default | Real Spanish transcription of browser `audio.webm` |
| Optional STT | Groq Whisper | Remote alternative selected explicitly with configuration |
| Triage reasoning | Optional Llama 3 through Groq | Contextual reasoning after the deterministic safety floor |
| Safety floor | Python rules and thresholds | One-way red-flag escalation |
| Retrieval | BGE-M3 and ChromaDB | Local multilingual embeddings and persistent document retrieval |
| PDF extraction | `pypdf` | Included dependency for the RAG ingestion path |
| Demo TTS | Browser `speechSynthesis` | Primary audible response in the browser demo |
| Optional backend TTS | Kokoro ONNX and Piper | Local synthesis or fallback audio when configured |

## Operational Flow

1. The browser opens a WebSocket and requests microphone permission.
2. The user clicks **Grabar**, speaks, and clicks **Enviar**.
3. The browser sends the WebM chunks followed by `EOT`; there is no automatic turn detection or active barge-in flow.
4. The backend transcribes, evaluates safety, advances the conversation state, and sends transcript and agent-response events.
5. The browser speaks the response with `speechSynthesis`; the session can emit a final summary.

## Installation

Supported route: Linux, Python 3.12, and Chrome/Chromium. The first installation and model download are not bounded to 15 minutes; timing depends on network, CPU, disk, packages, and model size.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Set `STT_PROVIDER=local` and `LOCAL_WHISPER_MODEL=tiny` for the first test. Use `small` for better accuracy when the machine can handle the larger download and CPU cost. The RAG path depends on `pypdf`, already pinned in `requirements.txt`.

```bash
.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The browser call is at `http://localhost:8000/call`; API docs are at `http://localhost:8000/docs`.

## Current Validation

Recorded checks for the current build:

```text
./.venv/bin/pytest -q
57 passed, 3 warnings
```

- HTTP smoke: `GET /health` returned `200`.
- WebSocket smoke: audio connection accepted and `ping` returned `pong`.
- Video evidence: 46 seconds, 1280x720, generated from local Chromium captures.
- No automated end-to-end browser test is claimed. The test suite covers application contracts and service behavior, not a full browser-driven call.

## Risks and Boundaries

- This is a prototype and not a medical device or clinical decision substitute.
- Local STT needs `faster-whisper`, model weights, CPU, disk, and a first download.
- Groq paths need a valid `GROQ_API_KEY`, network access, and provider availability.
- The sample voice route uses synthetic case context rather than authenticated patient data.
- Process-local rate limiting does not provide shared protection across workers.
- ChromaDB is local persistent storage, not a multi-user production data platform.
- Optional TTS can return silent mock WAV data if model assets are absent.
- Authentication, authorization, audit retention, encryption, observability, clinical validation, and regulatory work are outside this repository.

## Final Checklist

- [x] README documents the supported setup, exact manual voice flow, limits, and security boundaries.
- [x] Architecture diagram reflects local Faster-Whisper, manual turns, browser `speechSynthesis`, and optional Groq.
- [x] 57-test validation recorded.
- [x] HTTP health smoke returned 200.
- [x] WebSocket audio and ping-pong smoke completed.
- [x] Video evidence generated at 46 seconds and 1280x720.
- [x] No automated browser E2E integration is represented as completed.
- [x] [MIT License](LICENSE) and [.env.example](.env.example) are referenced.
