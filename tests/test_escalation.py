import pytest
from unittest.mock import MagicMock
from backend.services.escalation import EscalationEngine, TriageDecisionPayload, generate_call_summary

@pytest.mark.parametrize("category,utterance", [
    ("hemorrhage", "tengo sangrado activo en la herida"),
    ("hemorrhage", "sale en chorro por la cortada"),
    ("hemorrhage", "se empapa compresas de sangre"),
    ("hemorrhage", "bota mucha sangre cada rato"),
    ("hemorrhage", "sangre fresca constante en la gasa"),
    ("fever", "tengo fiebre alta y escalofríos"),
    ("fever", "siento mucha calentura"),
    ("fever", "temperatura en 38.6 grados"),
    ("fever", "estoy a 38.5 y temblando de frío"),
    ("dyspnea", "siento que me ahogo"),
    ("dyspnea", "falta de aire al caminar"),
    ("dyspnea", "no puedo respirar bien"),
    ("dyspnea", "tengo opresión pecho fuerte"),
    ("dehiscence", "se abrió la herida del abdomen"),
    ("dehiscence", "tiene pus y secreción fétida"),
    ("dehiscence", "hay un hueco en la herida con líquido mal olor"),
    ("severe_pain", "tengo un dolor insoportable"),
    ("severe_pain", "es un nrs 9 que no aguanto"),
    ("severe_pain", "dolor que no cede con nada, peor dolor de mi vida"),
    ("sepsis", "tengo escalofríos severos y confusión"),
    ("sepsis", "siento delirio y mareo extremo"),
    ("sepsis", "desvanecimiento repentino"),
    ("consciousness", "el paciente está desorientado y somnoliento"),
    ("consciousness", "síncope y desmayo hace un momento"),
    ("consciousness", "confundido y no responde bien"),
    ("urinary_retention", "no puedo orinar desde ayer"),
    ("urinary_retention", "retención urinaria total"),
    ("urinary_retention", "no orino hace muchas horas con vejiga llena y no sale")
])
def test_red_flag_floor_categories(category, utterance):
    engine = EscalationEngine()
    result = engine.evaluate(utterance)
    assert result.triage_level == "rojo"
    assert "safety floor" in result.justification.lower() or "red-flag" in result.justification.lower()
    # Validate against Pydantic schema
    assert isinstance(result, TriageDecisionPayload)

def test_trayectoria_snapshot_red_flags():
    engine = EscalationEngine()
    # Test fever snapshot
    res_fever = engine.evaluate("me siento un poco cansado", trayectoria_snapshot={"fiebre_c": 39.0})
    assert res_fever.triage_level == "rojo"

    # Test pain snapshot
    res_pain = engine.evaluate("todo normal", trayectoria_snapshot={"dolor_nrs": 9})
    assert res_pain.triage_level == "rojo"

    # Test wound snapshot
    res_wound = engine.evaluate("todo bien", trayectoria_snapshot={"herida": "sangrado profuso"})
    assert res_wound.triage_level == "rojo"

def test_one_way_floor_and_llm_composition():
    # Mock Groq client returning verde
    mock_groq = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"triage_level": "verde", "justification": "Mild symptoms.", "confidence": 0.9}'
    mock_groq.chat.completions.create.return_value = mock_response

    engine = EscalationEngine(groq_client=mock_groq)

    # Utterance triggers red-flag floor ("sangrado activo") -> floor forces rojo even if LLM said verde
    result = engine.evaluate("tengo sangrado activo")
    assert result.triage_level == "rojo"

    # Utterance does not trigger floor -> LLM decision stands (verde)
    result_verde = engine.evaluate("tengo una molestia leve")
    assert result_verde.triage_level == "verde"

    # Mock Groq returning rojo, floor clear -> LLM rojo stands
    mock_response.choices[0].message.content = '{"triage_level": "rojo", "justification": "Severe complications.", "confidence": 0.95}'
    result_llm_rojo = engine.evaluate("siento algo extraño sin palabras clave")
    assert result_llm_rojo.triage_level == "rojo"

def test_llm_unavailable_degrades_safely():
    # Groq client raises exception
    mock_groq = MagicMock()
    mock_groq.chat.completions.create.side_effect = Exception("API down")

    engine = EscalationEngine(groq_client=mock_groq)

    # Without red flag -> defaults safely to verde
    res_verde = engine.evaluate("hola doctor")
    assert res_verde.triage_level == "verde"

    # With red flag -> safety floor catches it and forces rojo
    res_rojo = engine.evaluate("tengo fiebre alta de 39")
    assert res_rojo.triage_level == "rojo"

def test_call_summary_generation():
    summary = generate_call_summary(
        dialogo_id="diag_101",
        caso_id="caso_202",
        paciente_id="pac_01",
        dia_postop=3,
        turns=5,
        final_triage="amarillo",
        trayectoria_snapshot={"dolor_nrs": 4, "fiebre_c": 37.2},
        clinical_notes="Patient reported moderate pain controlled with analgesics."
    )
    assert summary.dialogo_id == "diag_101"
    assert summary.final_triage == "amarillo"
    assert summary.turns == 5
    assert summary.trayectoria_snapshot["dolor_nrs"] == 4
