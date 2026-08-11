# Apply Progress: Unit 6 & 7 (Voice Loop, Eval & Final Docs)

**Change**: postop-voice-agent
**Mode**: Standard (all tests passing successfully)

## Completed Tasks
- [x] 6.1 RED: `tests/test_voice.py` — rapid connect attempts rate-limited, idle WS times out
- [x] 6.2 RED: TTS subprocess injection — all args via list/escape, no `shell=True`; Kokoro/Piper args escaped
- [x] 6.3 Implement `backend/services/stt.py`: Groq Whisper v3 with Colombian slang prompt
- [x] 6.4 Implement `backend/services/tts.py`: Kokoro-82M ONNX with Piper fallback
- [x] 6.5 `backend/routers/voice.py`: WS `/ws/voice` audio streaming, barge-in cancellation, per-call JSON summary
- [x] 7.1 `eval/run_eval.py`: dataset evaluation against `dataset_final.xlsx` (accuracy, latency P50<600ms / P95<950ms, triage vs ground truth, zero rojo misses)
- [x] 7.2 Eval offline mode (mocked inference) for CI + unit test fixture
- [x] 7.3 README ≤15-min setup path, declared allowed models & rationale (G3 declaration), rubric map
- [x] 7.4 Full `pytest` (48/48 passed) + `eval/run_eval.py` green; updated tasks.md checkboxes

## Files Changed
| File | Action | What Was Done |
|------|--------|---------------|
| `backend/services/stt.py` | Created | Groq Whisper integration with Colombian Spanish slang prompting. |
| `backend/services/tts.py` | Created | Kokoro-82M ONNX TTS with Piper fallback and safe subprocess list arguments. |
| `backend/routers/voice.py` | Created | WebSocket endpoint (`/ws/voice`) for bidirectional voice streaming, barge-in, and call summary. |
| `eval/run_eval.py` | Created | Automated evaluation runner against `dataset_final.xlsx` measuring accuracy, latency, and confusion matrix. |
| `tests/test_eval.py` | Created | Unit test for evaluation schema and confusion matrix aggregation using synthetic fixture. |
| `README.md` | Modified | Comprehensive final README with ≤15-min bootstrap, G3 model declarations, and rubric map. |
| `backend/services/escalation.py` | Modified | Expanded safety floor regex patterns for robust clinical detection of fever and wound discharge. |
| `openspec/changes/postop-voice-agent/tasks.md` | Modified | Marked Phase 6 and Phase 7 tasks as completed `[x]`. |

## Status
All Units (1 through 7) completed successfully. 48/48 pytest tests passing. Evaluation harness passing with 0 rojo misses and latency within P50/P95 budget. Ready for verification and PR delivery.
