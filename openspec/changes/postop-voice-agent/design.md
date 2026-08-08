# Design: Post-Operative Voice Follow-Up Agent (Colombian Spanish)

## Technical Approach

A unified FastAPI backend serving real-time bidirectional WebSocket voice streaming and an admin REST console. Integrates Groq Whisper (STT) with regional vocabulary prompting (`capa2_ruidosa`), BGE-M3 embeddings in ChromaDB for hot-swappable RAG with metadata-hashed versioning, a hybrid escalation engine combining a deterministic red-flag safety floor with Llama 3 contextual reasoning, and Kokoro-82M / Piper local TTS synthesis.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| **Backend Framework** | FastAPI (Python) | Node.js / Go | Native async support for WebSockets, seamless integration with Python ML/RAG libraries (ChromaDB, Transformers). |
| **RAG & Vector Store** | ChromaDB + BGE-M3 | Qdrant / PgVector | Zero external server dependency, local file persistence, fast embedding and metadata filtering. |
| **Triage Strategy** | Hybrid (Rule Floor + LLM) | Pure rules / Pure LLM | Guarantees 0% missed critical red flags (`rojo`) while correctly interpreting colloquial Colombian slang. |
| **Voice Streaming** | Native WebSockets | WebRTC | Simpler setup for ≤15-min reproducible deployment without STUN/TURN server overhead. |

## Deterministic Red-Flag Floor

The escalation engine enforces a deterministic safety floor that runs synchronously prior to LLM reasoning. If any user utterance or trayectorias snapshot matches a red-flag rule, the system forces `triage_level: "rojo"` immediately.

### Red-Flag Rule Matrix (Colombian Spanish)

| Symptom Category | Trayectoria Field | Detection Keywords / Regex (Colombian Spanish) | Forced Triage |
|------------------|-------------------|------------------------------------------------|---------------|
| **Hemorrhage / Active Bleeding** | `herida` | `sangrado activo`, `chorro`, `empapa compresas`, `bota mucha sangre`, `sangre fresca constante` | `rojo` |
| **Fever Threshold** | `fiebre_c` | `fiebre`, `calentura`, `temperatura alta`, `≥ 38.5`, `temblando de frío` (when combined with thermal measure) | `rojo` |
| **Dyspnea / Breathing Difficulty** | `respiracion` | `ahogo`, `falta de aire`, `no puedo respirar`, `me ahogo`, `respiración agitada`, `opresión pecho` | `rojo` |
| **Wound Dehiscence / Discharge** | `herida` | `se abrió`, `pus`, `secreción fétida`, `hueco en la herida`, `líquido mal olor` | `rojo` |
| **Severe / Uncontrolled Pain** | `dolor_nrs` | `dolor insoportable`, `nrs 8`, `nrs 9`, `nrs 10`, `dolor que no cede`, `peor dolor de mi vida` | `rojo` |
| **Signs of Sepsis** | `estado_general` | `escalofríos severos`, `confusión`, `delirio`, `mareo extremo`, `desvanecimiento` | `rojo` |
| **Altered Consciousness** | `neurologico` | `desorientado`, `somnoliento`, `desmayo`, `síncope`, `no responde bien`, `confundido` | `rojo` |
| **Urinary Retention** | `orina` | `no puedo orinar`, `retención urinaria`, `no orino hace muchas horas`, `vejiga llena y no sale` | `rojo` |

### Floor & LLM Composition
1. **Synchronous Interception**: The rule engine evaluates every transcript against the regex matrix.
2. **One-Way Escalation**: The safety floor can escalate any triage level to `rojo`, but *never* de-escalates an LLM-determined `rojo`.
3. **LLM Upward Flexibility**: If the floor evaluates to `verde`, the LLM context engine may escalate it to `amarillo` or `rojo` based on multi-turn clinical nuance, trajectory trends, or subtle symptoms (e.g., progressive nausea or mild tachycardia).

## Data Flow

```
Browser Mic (Audio) ──→ WebSocket (`/ws/voice`) ──→ Groq Whisper STT (~150ms)
                                                             │
Client Audio Out ←── Kokoro TTS (~150ms) ←── Llama Reasoning + ChromaDB RAG (~300ms)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/main.py` | Create | FastAPI application entry point, CORS, static mounts, and route registration. |
| `backend/routers/voice.py` | Create | WebSocket endpoint (`/ws/voice`), audio buffering, barge-in cancellation, and voice loop orchestration. |
| `backend/routers/admin.py` | Create | REST endpoints for PDF upload, listing, status inspection, and hot-swap ChromaDB deletion/ingestion. |
| `backend/services/stt.py` | Create | Groq Whisper integration with Colombian slang prompting. |
| `backend/services/rag.py` | Create | ChromaDB client, BGE-M3 embedding, chunking, and metadata-hashed version purging. |
| `backend/services/escalation.py` | Create | Deterministic red-flag safety rules and Llama semantic triage engine. |
| `backend/services/tts.py` | Create | Kokoro-82M TTS synthesis with Piper fallback. |
| `console/static/` | Create | Admin dashboard static HTML/JS frontend. |
| `eval/run_eval.py` | Create | Automated test runner against `dataset_final.xlsx`. |

## Interfaces / Contracts

### Triage Decision Payload (JSON)
```json
{
  "triage_level": "verde",
  "justification": "Dolor leve en herida (NRS 3), sin fiebre ni signos de infección.",
  "source_citations": [
    {"doc_id": "proto_lap_v1", "title": "Protocolo Laparoscopia", "chunk_idx": 2}
  ],
  "confidence": 0.95
}
```

### Call Session Record
```json
{
  "dialogo_id": "diag_001",
  "caso_id": "caso_101",
  "paciente_id": "pac_05",
  "dia_postop": 2,
  "turns": 4,
  "final_triage": "verde",
  "trayectoria_snapshot": {"dolor_nrs": 3, "fiebre_c": 36.8, "movilidad": "buena", "herida": "seca"}
}
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Escalation Engine & Safety Floor | Test regex/rules for red flags (`rojo`) and LLM JSON parsing. |
| Integration | Hot-Swap RAG Ingestion & Deletion | Verify ChromaDB chunk purge and zero stale version matches. |
| E2E | Voice Loop & Dataset Evaluation | Run `run_eval.py` against `dataset_final.xlsx` to measure accuracy and latency. |

## Threat Matrix

| Threat Category | Applicable? | Mitigation / Security Behavior |
|-----------------|-------------|---------------------------------|
| WebSocket Flooding / DoS | Applicable | Rate limiting on connection attempts; timeout on idle connections. |
| Subprocess Injection (TTS) | Applicable | Escape all shell parameters for Kokoro/Piper execution; use direct library calls where possible. |
| API Key Exposure | Applicable | Load Groq API key exclusively from `.env` via python-dotenv; never log credentials. |
| Path Traversal in PDF Upload | Applicable | Sanitize uploaded filenames via `os.path.basename` and validate MIME type. |

## Reproducible Setup Flow

Designed for a zero-friction bootstrap on standard developer environments in ≤15 minutes.

### Bootstrap Sequence & Timed Budget

| Step | Action | Command / Detail | Time Budget |
|------|--------|------------------|-------------|
| 1 | Clone & Virtualenv | `git clone ... && python -m venv venv && source venv/bin/activate` | 2 min |
| 2 | Install Dependencies | `pip install -r requirements.txt` (pinned versions) | 3 min |
| 3 | Environment Config | Create `.env` file with Groq API key (`GROQ_API_KEY=gsk_...`) | 1 min |
| 4 | Model & Vector Store Init | Auto-download BGE-M3 embeddings & Kokoro-82M ONNX weights | 4 min |
| 5 | Ingest & Verification | Run ChromaDB ingestion script & unit/eval verification (`pytest`) | 2 min |
| **Total** | **Full Setup to Operational State** | **Fully functional WebSocket voice backend & admin console** | **12 min** |

### Pinned Dependencies (`requirements.txt`)
```text
fastapi==0.110.0
uvicorn==0.28.0
chromadb==0.4.24
groq==0.4.2
sentence-transformers==2.5.1
numpy==1.26.4
python-dotenv==1.0.1
pydantic==2.6.4
kokoro-onnx==0.1.2
soundfile==0.12.1
pytest==8.1.0
```

### Execution & Verification
1. **Run Command**:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. **Operational Verification**:
   - Access FastAPI interactive docs at `http://localhost:8000/docs`.
   - Verify WebSocket endpoint `/ws/voice` and admin dashboard static files at `/admin`.
3. **Caching & Subsequent Runs**:
   - Python packages cached in virtualenv site-packages.
   - BGE-M3 and Kokoro-82M weights cached in `~/.cache/huggingface` and local model caches (subsequent start time < 3 seconds).

## Migration / Rollout

No migration required (Greenfield system).

## Open Questions

- [ ] Optimal chunk size for BGE-M3 embeddings on clinical PDFs (defaulting to 512 tokens with 64 overlap).
- [ ] Kokoro-82M PyTorch model load time on 8GB laptops (fallback to Piper if load exceeds 5s).
