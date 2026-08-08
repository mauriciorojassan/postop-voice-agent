import pytest
from backend.services.conversation import ConversationManager
from backend.services.escalation import EscalationEngine

def test_ambiguous_input_clarification_loop():
    trayectoria = {"procedimiento": "laparoscopia", "dia_postop": 2}
    manager = ConversationManager(
        caso_id="caso_101",
        paciente_id="pac_01",
        dia_postop=2,
        trayectoria_snapshot=trayectoria
    )
    
    initial = manager.get_initial_prompt()
    assert "dolor" in initial.lower()
    
    # Send ambiguous input ("me duele un poquito por ahí")
    res = manager.process_turn("me duele un poquito por ahí")
    
    assert res["needs_clarification"] is True
    assert res["escalated"] is False
    assert "específico" in res["response"].lower() or "exactamente" in res["response"].lower()
    assert res["next_domain"] == "dolor" # did not advance domain prematurely

def test_red_flag_escalation_handoff():
    trayectoria = {"procedimiento": "apendicectomía", "dia_postop": 1}
    manager = ConversationManager(
        caso_id="caso_102",
        paciente_id="pac_02",
        dia_postop=1,
        trayectoria_snapshot=trayectoria
    )
    
    res = manager.process_turn("tengo sangrado activo en la herida")
    
    assert res["triage_level"] == "rojo"
    assert res["escalated"] is True
    assert res["summary"] is not None
    assert res["summary"].final_triage == "rojo"
    assert "sangrado" in res["summary"].clinical_notes.lower() or "rojo" in res["summary"].clinical_notes.lower()

def test_adaptive_flow_covers_domains():
    trayectoria = {"procedimiento": "colecistectomía", "dia_postop": 3}
    manager = ConversationManager(
        caso_id="caso_103",
        paciente_id="pac_03",
        dia_postop=3,
        trayectoria_snapshot=trayectoria
    )
    
    # Turn 1: Dolor specific answer
    r1 = manager.process_turn("me duele un poco, nrs 3")
    assert r1["needs_clarification"] is False
    assert r1["next_domain"] == "fiebre"
    
    # Turn 2: Fiebre answer
    r2 = manager.process_turn("no tengo fiebre, 36.5 grados")
    assert r2["next_domain"] == "movilidad"
    
    # Turn 3: Movilidad answer
    r3 = manager.process_turn("camino despacio pero bien")
    assert r3["next_domain"] == "herida"
    
    # Turn 4: Herida answer
    r4 = manager.process_turn("herida seca y limpia")
    assert r4["next_domain"] == "apetito"
    
    # Turn 5: Apetito answer
    r5 = manager.process_turn("estoy comiendo bien")
    assert r5["next_domain"] == "sueno"
    
    # Turn 6: Sueno answer (final domain)
    r6 = manager.process_turn("duermo bien por las noches")
    assert r6["next_domain"] is None
    assert r6["summary"] is not None
    assert r6["summary"].final_triage == "verde"
    assert r6["summary"].turns == 6

def test_repeated_ambiguity_escalation():
    trayectoria = {"procedimiento": "hernia", "dia_postop": 2}
    manager = ConversationManager(
        caso_id="caso_104",
        paciente_id="pac_04",
        dia_postop=2,
        trayectoria_snapshot=trayectoria,
        max_clarification_rounds=2
    )
    
    # 1st ambiguous turn
    r1 = manager.process_turn("más o menos")
    assert r1["needs_clarification"] is True
    assert r1["escalated"] is False
    
    # 2nd ambiguous turn (hits max rounds -> escalation handoff)
    r2 = manager.process_turn("por ahí")
    assert r2["needs_clarification"] is False
    assert r2["escalated"] is True
    assert r2["triage_level"] == "amarillo"
    assert r2["summary"] is not None
    assert "ambigüedad" in r2["summary"].clinical_notes.lower()
