# Specification: Reproducibility & 15-Minute Setup

## Purpose

Defines the README-driven setup process, dependency declarations, and reproducibility standards ensuring the system boots and verifies successfully in ≤15 minutes on an 8-16GB laptop, meeting the elimination gates and scoring criteria.

## Requirements

### Requirement: README-Driven Setup in ≤15 Minutes

The repository MUST provide clear instructions and a setup script (`setup.sh` or `Makefile`) enabling complete environment initialization, dependency installation, and service startup in 15 minutes or less on standard hardware (8-16GB laptop).

#### Scenario: Executing fresh repository setup

- GIVEN a fresh clone of the repository on a clean developer machine with Python 3.10+
- WHEN the user runs the documented setup command (`bash scripts/setup.sh`)
- THEN all Python dependencies, vector store indices, and local models are installed and configured successfully within 15 minutes

### Requirement: Declared Model Stack and Environment Configuration

The system MUST declare all required environment variables and dependencies in `pyproject.toml` or `requirements.txt` and `.env.example`, restricting models to the allowed stack (Groq Whisper / Llama, Kokoro-82M / Piper TTS, BGE-M3).

#### Scenario: Configuring API keys and runtime parameters

- GIVEN the `.env.example` file is copied to `.env`
- WHEN the user supplies valid Groq API keys and optional local model paths
- THEN the backend successfully initializes all client connections without missing dependency errors

### Requirement: End-to-End Evaluation and Demo Reproducibility

The repository MUST include evaluation scripts to run test cases against `dataset_final.xlsx` and verify 100% safety-critical red flag detection and RAG precision.

#### Scenario: Running evaluation test suite

- GIVEN the dataset files and evaluation script (`python eval/run_eval.py`)
- WHEN executed by the user or grading harness
- THEN it runs test scenarios across the dataset and outputs a summary report confirming score metrics and elimination gate compliance
