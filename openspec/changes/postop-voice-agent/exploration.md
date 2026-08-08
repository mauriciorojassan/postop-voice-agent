## Exploration: postop-voice-agent

### Current State
Greenfield project implementing a real-time post-operative voice agent in Colombian Spanish. Locked stack: Groq (Whisper Large V3 + Llama), Kokoro-82M / Piper TTS, ChromaDB + BGE-M3 RAG, Python + FastAPI backend. Target runtime ≤15 min from README on an 8-16GB laptop, $0 cost.

### Dataset Structure & Join Paths
- **Files**:
  - `dataset_final.xlsx`: 3,991 dialogue turns across 40 patients, 160 cases, 4 post-op days, 16 turn indices. Columns: `dialogo_id`, `caso_id`, `paciente_id`, `dia_postop`, `turno_idx`, `hablante`, `texto`, `label_ground_truth` (verde: 3067, amarillo: 623, rojo: 301), `estilo_paciente`, `modelo_paciente`, `modelo_agente`, `capa`, `generado_ts`.
  - `trayectorias_postop_silver.xlsx`: 160 cases. Clinical state per case (`dolor_nrs`, `fiebre_c`, `movilidad`, `herida`). Joins via `caso_id` / `trayectoria_id`.
  - `perfiles_pacientes_co.xlsx`: 40 patients. Demographics, location, EPS. Joins via `paciente_id`.
  - `perfiles_clinicos_pacientes_silver_contest.xlsx`: 40 patients. Surgical bundle, procedure, date, age, gender. Joins via `paciente_id`.
  - `textos/`: 107 clinical PDFs across 5 folders.
- **Two-Layer Noise Model (`capa` column)**:
  - `capa1_limpia`: Clean, formal clinical Spanish dialogues.
  - `capa2_ruidosa`: Noisy, colloquial Colombian Spanish dialogues (slang, disfluencies, regionalisms, imperfect grammar). Represents realistic patient voice interactions.

### Architecture Approaches
1. **Real-Time Voice Loop Latency Budget**:
   - Audio input (WebSocket) → Groq Whisper Large V3 STT (~150ms) → Groq Llama Reasoning + RAG (~300ms) → Kokoro-82M / Piper local TTS (~150ms) → Audio output. Total P50 latency ~600ms, P95 ~950ms.
2. **Hot-Swap RAG (Zero Stale Version Contamination)**:
   - ChromaDB collection partitioned with metadata (`doc_id`, `version_hash`).
   - On upload: Chunk PDF, embed with BGE-M3, insert with unique `doc_id`.
   - On delete: Execute `collection.delete(where={"doc_id": doc_id})` before ingestion or deletion, ensuring instant removal with zero stale context contamination.
3. **Escalation Decision Logic**:
   - Structured JSON output / Pydantic parsing returning `triage_level` (`verde`/`amarillo`/`rojo`), `justification`, `source_citations`, and `recommended_action`.
4. **Per-Answer Source Traceability**:
   - RAG retrieval injects document title and chunk ID into prompt context; Llama is prompted to output inline citations `[Doc: title]`, validated in response payload.

### Comparison of Escalation Approaches
| Approach | Pros | Cons | Tradeoffs / Verdict |
|----------|------|------|---------------------|
| **1. Rule-Based Triage** | Deterministic, zero cost, instant | Fails on regional slang, idioms, and ambiguous phrasing | High false negatives on safety-critical red flags in Colombian Spanish. |
| **2. Zero-Shot LLM Classifier** | Handles natural language and colloquialisms well | Prone to drift, hallucination, and class imbalance bias | Unreliable for asymmetric clinical risk (false negatives on red flags). |
| **3. Hybrid (Deterministic Floor + LLM Reasoning)** | Combines rigid safety floor for critical vitals/symptoms with LLM contextual reasoning for ambiguous slang | Requires careful prompt engineering and validation | **Recommended**: Ensures 0% missed red flags while correctly interpreting regional patient descriptions. |

### Implications of the Noisy Layer (Capa2)
- STT will occasionally misinterpret colloquialisms ("calentura", "chuzo", "me duele la jeta").
- Conversation design must incorporate active listening, clarification prompts ("¿Te refieres a un dolor punzante o sordo del 1 al 10?"), and robust error handling for distorted audio inputs.

### Ready for Proposal
Yes. All dataset structures, architectural components, and decision trade-offs are fully analyzed.
