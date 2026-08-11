import pytest
import os
import pandas as pd
from eval.run_eval import run_evaluation

def test_eval_synthetic_fixture(tmp_path):
    data = {
        "dialogo_id": ["dlg_1", "dlg_2", "dlg_3"],
        "caso_id": ["caso_1", "caso_2", "caso_3"],
        "paciente_id": ["pac_1", "pac_2", "pac_3"],
        "dia_postop": [1, 2, 3],
        "turno_idx": [0, 0, 0],
        "hablante": ["paciente", "paciente", "paciente"],
        "texto": ["tengo dolor leve", "todo normal", "tengo sangrado activo en la herida"],
        "label_ground_truth": ["verde", "verde", "rojo"],
        "estilo_paciente": ["natural", "natural", "natural"],
        "modelo_paciente": ["gpt", "gpt", "gpt"],
        "modelo_agente": ["llama", "llama", "llama"],
        "capa": ["capa1_limpia", "capa1_limpia", "capa1_limpia"],
        "generado_ts": ["2026-07-15", "2026-07-15", "2026-07-15"]
    }
    df = pd.DataFrame(data)
    test_file = tmp_path / "dataset_synthetic.xlsx"
    df.to_excel(test_file, index=False)
    
    report = run_evaluation(str(test_file), offline=True)
    
    assert report["total_cases"] == 3
    assert report["rojo_misses"] == 0
    assert "confusion_matrix" in report
    assert report["confusion_matrix"]["rojo"]["rojo"] == 1
    assert report["status"] == "PASS"
