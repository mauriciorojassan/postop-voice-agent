# Proposal: Post-Operative Voice Follow-Up Agent (Colombian Spanish)

## Intent

Deliver a real-time, resilient, and traceable post-operative voice follow-up agent tailored to Colombian Spanish colloquialisms (`capa2_ruidosa`). The agent clears all 5 eliminatory gates (live voice, console knowledge management, ≤15-min setup, declared allowed model stack, and 4 required deliverables) while maximizing the two 20-pt rubric criteria: RAG precision and hybrid escalation accuracy.

## Scope

### In Scope
- Real-time voice conversation loop (Groq Whisper STT + Llama reasoning + Kokoro-82M TTS via WebSocket/REST).
- Admin knowledge console for uploading, indexing (BGE-M3 + ChromaDB), hot-swapping, and deleting clinical source PDFs.
- Hybrid escalation engine (deterministic safety floor for critical red flags + LLM contextual reasoning for Colombian slang) with structured per-decision justification.
- Per-answer source traceability and citation mapping.
- Automated test evaluation suite against the provided dataset (`dataset_final.xlsx`, trayectorias, perfiles).

### Out of Scope
- Real telephony trunking / PSTN integration (WebSockets & browser audio only).
- Direct hospital electronic health record (EHR) / HIS system integration.
- Enterprise multi-tenant authentication, RBAC, and cloud database clusters.
- Full clinical coverage of every surgical procedure (scoped to primary validation procedures / laparoscopic recovery protocols).
- Video generation, physical diagrams, and final PDF report generation (handled as standalone offline artifacts/deliverables, not core runtime services).

## Capabilities

> This section is the CONTRACT between proposal and specs phases.

### New Capabilities
- `voice-conversation-loop`: Real-time audio streaming, Whisper transcription, Llama reasoning, and Kokoro-82M TTS synthesis in Colombian Spanish.
- `hotswap-rag`: ChromaDB vector store with BGE-M3 embeddings, instant chunk-level ingestion, and zero-stale-version deletion hooks.
- `hybrid-escalation-engine`: Combined deterministic safety rules and Llama semantic triage producing structured JSON ratings (`verde`/`amarillo`/`rojo`) with per-decision rationale.
- `admin-knowledge-console`: Web dashboard for document management (PDF upload, indexing status, version verification, and chunk inspection).
- `traceable-citations`: Per-answer source attribution mapping agent responses directly to retrieved clinical PDF chunk IDs.

### Modified Capabilities
- None (Greenfield system).

## Approach

A unified Python + FastAPI backend serving both the admin console REST/static UI and the real-time voice streaming endpoints.
- **Voice Loop**: Client captures audio via MediaRecorder API, streams over WebSockets to FastAPI, which forwards to Groq Whisper Large V3, feeds text through Llama 3 with RAG context, and synthesizes speech via Kokoro-82M (with Piper fallback).
- **RAG & Storage**: ChromaDB local vector store indexed with BGE-M3 embeddings. Document additions and deletions enforce explicit ID filtering to guarantee zero stale contamination.
- **Escalation & Audit**: Every patient turn evaluates rules and model output, returning a structured JSON payload containing `triage_level`, `justification`, `source_citations`, and `confidence`. Logs are persisted per-call for evaluation and audit.

## Affected Areas

| Area | Impact | Description |
|------|------|-------------|
| `backend/` | New | FastAPI application, WebSocket handlers, and routing. |
| `services/` | New | Groq STT/LLM integration, Kokoro TTS, and ChromaDB RAG clients. |
| `console/` | New | Admin knowledge management interface. |
| `eval/` | New | Dataset validation and scoring scripts against `dataset_final.xlsx`. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| STT misinterpreting Colombian colloquial slang (`capa2_ruidosa`) | Med | Add explicit vocabulary prompting and fallback clarification prompts. |
| Latency spikes in local TTS or remote Groq inference | Med | Optimize payload sizes, use async streaming, and set strict WebSocket timeout budgets. |
| RAG hallucination on edge-case clinical queries | Low | Enforce strict citation matching and deterministic safety rule floors. |

## Rollback Plan

If audio streaming or local TTS fails on target hardware, gracefully degrade to text-only chat mode with audio generation fallback or Piper local binary, maintaining full RAG and triage functionality.

## Dependencies

- Python 3.10+, FastAPI, Uvicorn, WebSockets.
- Groq API SDK (Whisper & Llama).
- ChromaDB, HuggingFace Transformers / BGE-M3 embedding library.
- Kokoro-82M / Piper TTS local binaries.
- Dataset files (`dataset_final.xlsx`, PDF `textos/`).

## Success Criteria

- [ ] Complete setup and verification in ≤15 minutes via single setup script / README instructions on an 8-16GB laptop.
- [ ] 100% safety-critical red flag detection (zero false negatives on `rojo` triage items from test dataset).
- [ ] RAG precision score > 85% on retrieval evaluation.
- [ ] Admin console successfully uploads, indexes, and hot-swaps knowledge docs without server restart.
- [ ] All 4 required deliverables and 5 eliminatory gates verified successfully.
