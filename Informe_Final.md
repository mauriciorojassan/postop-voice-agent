# Technical Report: Post-Operative Voice Follow-Up Agent

## Executive Summary

This repository implements a FastAPI prototype for post-operative follow-up in Colombian Spanish. The demonstrated interaction is a browser microphone call: the user records a manual turn, sends `audio.webm` through a WebSocket, receives a transcript and structured response, and hears the answer through browser `speechSynthesis`. It is not telephony and does not replace qualified clinical judgment.

The current validation record includes 57 passing tests, installation and syntax checks, HTTP route smoke checks, a WebSocket audio and ping/pong check, and a 46-second 1280x720 video recording.

## Architecture

The implemented voice path is `audio.webm` -> local Faster-Whisper -> `ConversationManager` -> deterministic `EscalationEngine` -> structured response. The browser's `speechSynthesis` is the primary audible response in the demo. Groq STT/reasoning and Kokoro/Piper backend TTS are optional configuration-dependent paths, not prerequisites for the local-first flow.

The safety floor evaluates red flags before ambiguity and domain progression. It can force `rojo`; optional reasoning cannot lower that result. Ambiguous answers enter clarification, and repeated ambiguity can become `amarillo` with a priority handoff.

See [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md) for the component map, clinical decision flow, event contracts, and boundaries.

## Development Process Evidence

The implementation process focused on a small set of verifiable engineering concerns:

- Architecture exploration mapped the browser, WebSocket, conversation, safety, retrieval, and voice paths before documentation changes.
- The safety floor was designed as a deterministic first gate with one-way red-flag escalation.
- Data and RAG behavior was reviewed around PDF extraction, chunking, versioned document ingestion, embeddings, and local persistence.
- Boundary cases for red flags, repeated ambiguity, insufficient audio, WebM filenames, disconnects, and provider responses were exercised.
- Installation and voice behavior were validated through local startup, HTTP checks, WebSocket audio, ping/pong, and manual browser turns.
- WebM handling, VAD/turn-boundary behavior, and manual turn correction were reviewed to keep `EOT` as the authoritative submission boundary.

## Prompt Strategy (High-Level)

The development prompts were used as focused work themes rather than as application runtime logic:

- Explore the existing architecture and trace the voice-to-decision path.
- Design and verify the deterministic safety floor and its escalation precedence.
- Review data ingestion and RAG behavior, including PDF failure modes and source boundaries.
- Run focused boundary cases for red flags and repeated ambiguous answers.
- Validate installation, local voice operation, WebM handling, VAD/turn boundaries, and manual turn recovery.

No internal prompt text, credentials, or secrets are part of this report.

## Configuration Evidence

| Item | Verified configuration or repository evidence |
|---|---|
| Runtime | Python 3.12 on Linux; browser flow targets Chrome/Chromium |
| Default STT | `STT_PROVIDER=local` with Faster-Whisper |
| Model choices | `LOCAL_WHISPER_MODEL=tiny` for first run; `small` when higher accuracy and CPU/model cost are acceptable |
| Inference | CPU/int8 local path |
| Optional provider | Groq is available only when explicitly configured with network access and a valid key |
| Environment | `.env.example` documents the setup without secrets; local `.env` is not part of the public artifact |
| Dependencies | `requirements.txt` includes Faster-Whisper and `pypdf` alongside the application dependencies |
| Turn control | Manual **Grabar** -> speak -> **Enviar** flow; browser sends WebM chunks followed by `EOT` |

Minimal installation:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

## Validation Evidence

| Check | Command or observation | Result |
|---|---|---|
| Automated tests | `./.venv/bin/pytest -q` | `57 passed, 3 warnings` |
| Dependency consistency | `./.venv/bin/pip check` | No broken requirements reported |
| Python syntax | `./.venv/bin/python -m compileall backend tests` | Completed successfully |
| JavaScript syntax | `node --check console/call/call.js` | Completed successfully |
| HTTP smoke | `GET /health`, `/call`, `/admin`, `/docs` | HTTP `200` on all four routes |
| WebSocket contract | Initial server audio and `ping`/`pong` | Initial audio payload: `44144` bytes; ping returned `pong` |
| Video artifact | `ffprobe` on `demo/postop-voice-agent-demo.mp4` | `46s`, `1280x720` |
| Browser E2E | Not automated | Manual video evidence exists; no automated browser E2E is claimed |

The checks validate application contracts and service behavior. They do not constitute clinical validation or a full browser-driven integration suite.

## Key Engineering Decisions

- **Deterministic safety floor:** red flags are evaluated first, and optional reasoning cannot downgrade `rojo`.
- **No fake transcript:** the demonstrated path uses real local Faster-Whisper transcription; a mock transcript is not presented as voice capability.
- **Local-first STT:** Faster-Whisper with CPU/int8 keeps the default path usable without a remote provider.
- **Explicit turns:** browser `EOT` boundaries are preferred over brittle automatic segmentation; this keeps turn ownership visible and recoverable.
- **Fail-closed PDF extraction:** missing `pypdf` or a PDF without a text layer raises an explicit error instead of ingesting empty content.
- **Browser demo audio:** `speechSynthesis` is the primary demo output, while backend Kokoro/Piper remains optional.

## Known Boundaries

- This is a prototype, not a medical device or clinical decision substitute.
- The sample voice route uses synthetic case context rather than authenticated patient data.
- Local STT requires model weights, CPU, disk, and a first download. `small` costs more time and resources than `tiny`.
- Groq paths require a valid `GROQ_API_KEY`, network access, and provider availability.
- Automatic VAD/segmentation, telephony, and a production barge-in experience are outside the demonstrated flow.
- Process-local rate limiting does not provide shared protection across workers.
- ChromaDB is local persistent storage, not a multi-user production data platform.
- Authentication, authorization, audit retention, encryption, observability, clinical validation, and regulatory work remain outside this repository.

## Public Artifact Checklist

- [x] **Repository:** implementation, setup documentation, limits, and security boundaries are present.
- [x] **Diagram:** component architecture, clinical decision flow, contracts, evidence status, and limits are documented in [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md).
- [x] **Report:** development evidence, configuration, validation, decisions, and known boundaries are summarized here.
- [x] **Video:** `demo/postop-voice-agent-demo.mp4` exists and is 46 seconds at 1280x720; it demonstrates the manual browser flow but is not automated E2E proof or clinical validation.

Additional repository terms are defined in [LICENSE](LICENSE), and setup variables are described in [.env.example](.env.example).
