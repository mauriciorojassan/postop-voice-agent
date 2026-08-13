from pathlib import Path


def test_browser_voice_contract_is_present():
    root = Path(__file__).parents[1]
    source = (root / "console/call/call.js").read_text()
    html = (root / "console/call/index.html").read_text()
    assert "window.speechSynthesis" in source
    assert "es-co" in source
    assert "data.event === 'error'" in source
    assert "lastSpokenResponse" in source
    assert "startRecording" in source
    assert "sendRecording" in source
    assert "setTimeout" not in source
    assert 'id="record-btn"' in html
    assert 'id="send-btn"' in html
    for state in ("Listo para escuchar", "Grabando...", "Procesando...", "Respuesta recibida"):
        assert state in source
