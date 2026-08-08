import os
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "postop-voice-agent"}

def test_groq_key_loading():
    # ponytail: verify env-based loading without exposure
    with open("backend/main.py", "r") as f:
        content = f.read()
        assert "gsk_" not in content
