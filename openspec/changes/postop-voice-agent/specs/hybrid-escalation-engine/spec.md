# Specification: Hybrid Escalation Engine & Call Summaries

## Purpose

Defines the hybrid escalation engine combining a deterministic safety floor for critical red-flag symptoms with LLM semantic reasoning for Colombian colloquialisms, producing structured JSON ratings (`verde`/`amarillo`/`rojo`) with complete justifications, and generating structured per-call summaries.

## Requirements

### Requirement: Deterministic Safety Floor (Red-Flag Rules)

The system MUST enforce a deterministic safety rule floor that immediately classifies critical clinical red flags (e.g., severe hemorrhage, acute chest pain, high fever >38.5°C, unmanaged surgical site dehiscence) as `rojo` regardless of LLM text generation.

#### Scenario: Triggering deterministic red-flag escalation

- GIVEN a patient transcript reports "siento que me ahogo y sangra mucho la herida"
- WHEN evaluated by the escalation engine
- THEN the deterministic safety floor triggers a mandatory `rojo` triage classification instantly, overriding any ambivalent language

### Requirement: LLM Contextual Reasoning for Slang and Ambiguity

The system MUST utilize Llama reasoning with RAG context to evaluate ambiguous or colloquial patient statements against clinical protocols for `verde` and `amarillo` classifications.

#### Scenario: Evaluating ambiguous post-op discomfort

- GIVEN a patient states "tengo un poco flojo el estómago pero sin fiebre"
- WHEN evaluated by the hybrid escalation engine
- THEN the LLM reasons over the statement and clinical guidelines, classifying the case as `amarillo` (monitor hydration, mild gastrointestinal side effect) with clear justification

### Requirement: Structured JSON Triage Output and Justification

The system MUST return a validated Pydantic JSON structure for every patient turn containing `triage_level`, `justification`, `source_citations`, and `confidence`.

#### Scenario: Generating structured triage payload

- GIVEN a processed patient turn and RAG context
- WHEN the escalation engine completes evaluation
- THEN it outputs a JSON object with keys `triage_level` (`verde`/`amarillo`/`rojo`), `justification` (string), `source_citations` (list), and `confidence` (float 0.0-1.0)

### Requirement: Structured Per-Call Summary Generation

The system MUST generate a structured JSON summary at the conclusion of each patient call, capturing total turns, final triage status, symptom progression, and recommended follow-up actions.

#### Scenario: Completing a post-op voice call

- GIVEN a completed voice session with multiple dialogue turns
- WHEN the call session terminates
- THEN the system compiles and persists a structured call summary containing patient ID, session duration, turn count, final triage level, and clinical notes
