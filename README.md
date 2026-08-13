# Post-Operative Voice Follow-Up Agent

Web-based voice follow-up for post-operative patients in Colombian Spanish. The application combines a FastAPI backend, local speech recognition, a deterministic clinical safety floor, optional retrieval and reasoning, and a browser call surface that runs with a microphone.

This is a portfolio prototype, not a telephone system, medical device, or replacement for qualified clinical judgment.

## What It Does

- Conducts a structured post-operative follow-up across pain, fever, mobility, wound, appetite, and sleep.
- Transcribes real microphone audio locally with Faster-Whisper by default.
- Applies deterministic red-flag rules before optional LLM reasoning; a safety escalation cannot be downgraded by the LLM.
- Supports local PDF ingestion, chunking, embeddings, metadata filtering, and persistent ChromaDB retrieval.
- Exposes an admin console, API documentation, health endpoint, and browser call surface.
- Returns structured transcript, response, triage, escalation, and session-summary events.

## Limitations

- The voice experience is a web call over microphone and WebSocket, not PSTN or SIP telephony.
- Turns are manual: the user clicks **Grabar**, speaks, clicks **Enviar**, and waits for the response.
- The primary demo TTS path is the browser's `speechSynthesis`. Kokoro/Piper backend TTS is optional and may fall back to silent mock WAV data for development.
- The default voice route uses a sample trajectory snapshot. It is not connected to authenticated patient records.
- No clinical efficacy, regulatory compliance, or production readiness is claimed.

## Requirements

- Linux
- Python 3.12
- Chrome or Chromium with microphone permission
- Network access, CPU, and disk space for dependency and model downloads

The first setup can exceed 15 minutes. Its duration depends on network speed, CPU, available disk, package installation, and the selected model download. The RAG backend requires `pypdf`; it is already included in `requirements.txt`.

## Quick Start

```bash
git clone https://github.com/mauriciorojassan/postop-voice-agent.git
cd postop-voice-agent
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

For the first local voice test, use the small download and faster startup profile:

```dotenv
STT_PROVIDER=local
LOCAL_WHISPER_MODEL=tiny
```

Use `LOCAL_WHISPER_MODEL=small` when better transcription accuracy matters more than download size and CPU time. The default code setting is `small`; setting `tiny` explicitly is recommended for the first trial.

Start the service:

```bash
.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open these URLs in Chrome/Chromium:

| Surface | URL | Purpose |
|---|---|---|
| Call | `http://localhost:8000/call` | Microphone/WebSocket conversation |
| Admin | `http://localhost:8000/admin` | Document management console |
| API docs | `http://localhost:8000/docs` | Interactive HTTP API documentation |
| Health | `http://localhost:8000/health` | Service health check |

## Exact Call Flow

1. Open `/call`, click **Iniciar llamada**, and allow microphone access.
2. Click **Grabar** and speak one patient turn.
3. Click **Enviar**. The browser sends the recorded `audio.webm` and then the `EOT` turn boundary through `/ws/voice`.
4. Faster-Whisper transcribes the audio, the conversation and triage services process it, and the browser speaks the response with `speechSynthesis`.
5. Repeat the manual turn until the follow-up ends, then click **Finalizar llamada**.

## Configuration

Start from [.env.example](.env.example). Keep secrets in `.env`; never commit that file.

| Variable | Local default or use |
|---|---|
| `STT_PROVIDER` | `local`; use `groq` only when a real remote provider is intentionally configured |
| `LOCAL_WHISPER_MODEL` | `small` in the application; `tiny` is recommended for the first test |
| `GROQ_API_KEY` | Required only for optional Groq STT/reasoning paths |
| `KOKORO_MODEL_PATH` / `KOKORO_VOICES_PATH` | Optional local Kokoro assets; install its package separately only if this backend path is enabled |
| `PIPER_BINARY` / `PIPER_MODEL` | Optional Piper fallback |

## Verification and Evaluation

Run the repository tests from the activated environment:

```bash
.venv/bin/pytest -q
```

The current validation result is **57 passed**. Additional smoke checks recorded for the current build are HTTP `/health` returning `200` and a WebSocket connection handling audio plus ping-pong (`ping` -> `pong`).

Run the evaluation harness when a compatible dataset is available:

```bash
.venv/bin/python eval/run_eval.py --dataset /path/to/dataset_final.xlsx --offline
```

The harness reports triage metrics, latency, and a confusion matrix, including the zero-missed-red-flag safety gate configured by the evaluation code.

## Repository Map

```text
backend/                 FastAPI app, routers, conversation, STT, TTS, RAG, escalation
console/                 Browser call and admin interfaces
demo/                    Video evidence and regeneration script
eval/                    Dataset evaluation runner
tests/                   Unit and integration tests
textos/                  Local document registry and knowledge assets
README.md               Project entry point
FINAL_REPORT.md         Technical report and validation record
ARCHITECTURE_DIAGRAM.md System diagram and flow explanation
```

## Security and Secrets

- Do not commit `.env`, API keys, patient data, or uploaded clinical documents.
- The application validates uploaded document names and uses safe subprocess argument lists for optional Piper execution.
- The current rate limiter is process-local and is not sufficient protection for a public multi-worker deployment.
- Authentication, authorization, audit retention, encryption policy, and production observability remain deployment responsibilities.

## Project Artifacts

- [Technical report](FINAL_REPORT.md)
- [Architecture diagram](ARCHITECTURE_DIAGRAM.md)
- [Demo instructions and scope](demo/README.md)
- [Local demo video](demo/postop-voice-agent-demo.mp4)
- [Unlisted video](https://youtu.be/RGncO51IokA)
- [MIT License](LICENSE)
