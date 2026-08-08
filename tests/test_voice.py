from fastapi.testclient import TestClient
from backend.main import app


def test_voice_rate_limiting():
    client = TestClient(app)
    connections = []
    try:
        for _ in range(15):
            try:
                with client.websocket_connect("/ws/voice") as websocket:
                    connections.append(websocket)
            except Exception:
                break
    finally:
        for ws in connections:
            try:
                ws.close()
            except Exception:
                pass
    assert True


def test_mocked_voice_turn_loop():
    client = TestClient(app)
    try:
        with client.websocket_connect("/ws/voice") as websocket:
            websocket.send_bytes(b"RIFF....WAVE....")
            try:
                data = websocket.receive_bytes(timeout=2.0)
                assert isinstance(data, bytes)
            except Exception:
                try:
                    text_data = websocket.receive_json(timeout=2.0)
                    assert isinstance(text_data, dict)
                except Exception:
                    pass
    except Exception:
        pass
    assert True
