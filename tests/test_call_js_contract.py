from pathlib import Path


def test_browser_voice_contract_is_present():
    source = (Path(__file__).parents[1] / "console/call/call.js").read_text()
    assert "window.speechSynthesis" in source
    assert "es-co" in source
    assert "data.event === 'error'" in source
    assert "lastSpokenResponse" in source
