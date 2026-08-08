# Tasks: Post-Operative Voice Follow-Up Agent (Colombian Spanish)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1100–1500 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | 6 chained PRs (work units below) |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending (user must choose) |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units (batch = all tasks of a unit in one apply run; never merge units)

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Bootstrap: pinned deps, `.env`, uvicorn boots | PR 1 | `bash scripts/setup.sh && curl -s :8000/health` | the ≤12-min setup path itself (gate) | revert PR 1; nothing else landed |
| 2 | RAG hot-swap service, zero contamination | PR 2 | `pytest tests/test_rag.py` | N/A — library-only, unit tests suffice | remove `services/rag.py` + Chroma dir, UUID dedupe |
| 3 | Escalation matrix + JSON payload | PR 3 | `pytest tests/test_escalation.py` | real Groq inference for one hand scenario | revert `services/escalation.py` only |
| 4 | Admin console REST + dashboard | PR 4 | `pytest tests/test_admin.py` | live: upload PDF at `:8000/admin` → `Processed and Available` | revert admin router + console; voice untouched |
| 5 | Conversation flow + voice loop | PR 5 | `pytest tests/test_voice.py` | needs real mic + Groq + Kokoro; manual smoke `uvicorn` | revert voice router/stt/tts; console intact |
| 6 | Eval suite + final README | PR 6 | `python eval/run_eval.py` (offline, mocked) | `dataset_final.xlsx` full run | revert eval/ + README only |

Dependency rule: phases order strictly; PR N waits on PR N−1 merge.

## Phase 1: Scaffold & Reproducible Bootstrap

- [x] 1.1 Create `requirements.txt` pinned (fastapi==0.110.0, uvicorn==0.28.0, chromadb==0.4.24, groq==0.4.2, sentence-transformers==2.5.1, numpy==1.26.4, python-dotenv==1.0.1, pydantic==2.6.4, kokoro-onnx==0.1.2, soundfile>=0.13.0, pytest==8.1.0, httpx==0.27.2)
- [x] 1.2 Create `scripts/setup.sh`: venv + install + copy `.env.example`→`.env` + boot `uvicorn backend.main:app --port 8000` (≤12 min total)
- [x] 1.3 Create `backend/main.py`: FastAPI app, CORS, `/health`, static mounts `/admin`; verify `curl :8000/health` → ok
- [x] 1.4 RED security test: Groq key loaded only from `.env` via python-dotenv, never logged/committed
- [x] 1.5 `.env.example` (GROQ_API_KEY only) + `.gitignore` (venv/, .env, .pdf)

## Phase 2: RAG Service (hot-swap)

- [x] 2.1 RED: `tests/test_rag.py` — ingest v1, replace same doc_id with v2, assert zero old `version_hash` chunks retrievable
- [x] 2.2 RED: chunking 512/64 boundaries + overlap assertions
- [x] 2.3 Implement `backend/services/rag.py`: ChromaDB, BGE-M3 (sentence-transformers), chunker (512/64), upsert-purge by `version_hash`, retrieval + `source_citations`
- [x] 2.4 `scripts/ingest.py`: CLI ingest `textos/*.pdf` → index + stats (setup path)

## Phase 3: Escalation Engine (+ Summary shape)

- [x] 3.1 RED: `tests/test_escalation.py` — parametrized 8-category red-flag matrix (hemorrhage, fever≥38.5, dyspnea, dehiscence, severe pain NRS≥8, sepsis, altered consciousness, urinary retention) → forced `"rojo"`
- [x] 3.2 RED: one-way floor — LLM `rojo` never de-escalated; floor may escalate infra
- [x] 3.3 Implement `backend/services/escalation.py`: regex floor (Colombian Spanish), Groq Llama triage, Pydantic decision record `{triage_level, justification,source_citations,confidence}`
- [x] 3.4 Implement trayectoria snapshot binding (`dolor_n`/`fiebre_c`/`herida`/`respiracion`...) for floor + LLM input

## Phase 4: Admin Console

- [x] 4.1 RED: `tests/test_admin.py` — `../` path traversal + wrong MIME rejected; filename via basename
- [x] 4.2 `backend/routers/admin.py`: `POST|GET|DELETE /api/documents` with status badges (Processing/Processed and Available/Error), delete purges file + Chroma chunks
- [x] 4.3 `console/index.html` + `console/admin.js`: upload form, doc table (chunks, status), delete button

## Phase 5: Conversation Manager

- [x] 5.1 RED: ambiguous input ("me duele un poquito por ahí") → clarification prompt (location + NRS), no premature answer
- [x] 5.2 Implement `backend/conversation.py`: adaptive flow per trayectoria state, max clarification rounds, escalation handoff on repeated ambiguity

## Phase 6: Voice Loop

- [x] 6.1 RED: `tests/test_voice.py` — rapid connect attempts rate-limited, idle WS times out
- [x] 6.2 RED: TTS subprocess injection — all args via list/escape, no `shell=True`; Kokoro/Piper args escaped
- [x] 6.3 Implement `backend/services/stt.py`: Groq Whisper v3 with Colombian slang prompt (calentura, chuzo, "ta' hinchao")
- [x] 6.4 Implement `backend/services/tts.py`: Kokoro-82M ONNX (load >5s → Piper fallback)
- [x] 6.5 `backend/routers/voice.py`: WS `/ws/voice` — buffer audio, no STT→conversation→TTS stream; barge-in cancels TTS stream; close → JSON per-call summary

## Phase 7: Eval + Final Docs

- [x] 7.1 `eval/run_eval.py`: reads `dataset_final.xlsx` → accuracy, latency (P50<600ms / P95<950ms), triage vs `label_ground_truth`; fail on any `rojo` miss
- [x] 7.2 Eval offline mode (mocked Groq/Kokoro) for no-key CI
- [x] 7.3 README ≤15-min path (mirrors setup.sh), declared allowed models + rationale, rubric map (eliminatory gates + deliverables)
- [x] 7.4 Full `pytest` + `eval/run_eval.py` green; update tasks.md checkboxes

## Threat Matrix → Task Traceability

WebSocket DoS → 6.1 · Subprocess injection → 6.2 · API key exposure → 1.4 · Path traversal → 4.1 (all RED-first)