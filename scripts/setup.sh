#!/usr/bin/env bash
set -e

echo "==> Setting up Post-Op Voice Agent..."
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
    cp .env.example .env
    echo "==> Created .env from .env.example. Local mode requires no credentials; Groq is optional."
fi

echo "==> Setup complete! Run uvicorn backend.main:app --reload --port 8000"
