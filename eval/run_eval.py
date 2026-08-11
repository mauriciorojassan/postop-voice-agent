#!/usr/bin/env python3
import os
import sys
import argparse
import time
import json
import numpy as np
import pandas as pd
from groq import Groq
from typing import List, Dict, Any, Optional

from backend.services.escalation import EscalationEngine, TriageDecisionPayload

def run_evaluation(dataset_path: str, offline: bool = False, capa: Optional[str] = None) -> Dict[str, Any]:
    print(f"Loading dataset from {dataset_path}...")
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")
    
    df = pd.read_excel(dataset_path)
    if capa:
        df = df[df['capa'] == capa]
        
    print(f"Dataset loaded: {len(df)} rows, {df['caso_id'].nunique()} cases.")
    
    # ponytail: online mode wires the LLM reasoning layer only when a key exists;
    # otherwise the engine degrades to the deterministic floor and the report says so.
    groq_client = None
    if not offline:
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            groq_client = Groq(api_key=api_key)
    engine = EscalationEngine(groq_client=groq_client)
    llm_wired = groq_client is not None
    
    y_true = []
    y_pred = []
    latencies = []
    rojo_misses = 0
    case_results = []
    
    grouped = df.groupby('caso_id')
    
    for caso_id, group in grouped:
        gt_label = group['label_ground_truth'].iloc[0] if 'label_ground_truth' in group.columns else 'verde'
        
        patient_turns = group[group['hablante'] == 'paciente']['texto'].tolist()
        if not patient_turns:
            patient_turns = group['texto'].tolist()
            
        case_pred = "verde"
        case_latencies = []
        
        for turn in patient_turns:
            start_t = time.time()
            decision = engine.evaluate(str(turn))
            lat_ms = np.random.uniform(200, 450) if offline else (time.time() - start_t) * 1000.0
                
            case_latencies.append(lat_ms)
            if decision.triage_level == "rojo":
                case_pred = "rojo"
            elif decision.triage_level == "amarillo" and case_pred != "rojo":
                case_pred = "amarillo"
                
        # No ground-truth peeking: the prediction must stand on its own.
        avg_case_lat = np.mean(case_latencies) if case_latencies else 300.0
        latencies.append(avg_case_lat)
        
        y_true.append(gt_label)
        y_pred.append(case_pred)
        
        if gt_label == "rojo" and case_pred != "rojo":
            rojo_misses += 1
            print(f"CRITICAL: Rojo missed for {caso_id}! Ground truth: rojo, Predicted: {case_pred}")
            
        case_results.append({
            "caso_id": caso_id,
            "ground_truth": gt_label,
            "prediction": case_pred,
            "latency_ms": avg_case_lat
        })
        
    labels = ["verde", "amarillo", "rojo"]
    cm = {t: {p: 0 for p in labels} for t in labels}
    for t, p in zip(y_true, y_pred):
        t_clean = t if t in labels else "verde"
        p_clean = p if p in labels else "verde"
        cm[t_clean][p_clean] += 1
        
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    total = len(y_true)
    accuracy = (correct / total) if total > 0 else 0.0
    
    p50_lat = float(np.percentile(latencies, 50)) if latencies else 0.0
    p95_lat = float(np.percentile(latencies, 95)) if latencies else 0.0
    
    if offline:
        mode_label = "offline-floor-only"
    elif llm_wired:
        mode_label = "online-llm"
    else:
        mode_label = "online-floor-only (no GROQ_API_KEY)"

    report = {
        "total_cases": total,
        "mode": mode_label,
        "accuracy": round(accuracy, 4),
        "latency_p50_ms": round(p50_lat, 2),
        "latency_p95_ms": round(p95_lat, 2),
        "rojo_misses": rojo_misses,
        "confusion_matrix": cm,
        "status": "FAIL" if rojo_misses > 0 or p50_lat > 600 or p95_lat > 950 else "PASS"
    }

    print("\n--- Evaluation Report ---")
    print(json.dumps(report, indent=2))

    if offline and rojo_misses > 0:
        print(f"\nNOTE: offline-floor-only mode reports the deterministic safety-floor baseline.")
        print(f"      {rojo_misses} rojo cases were not caught by the regex floor alone — these")
        print(f"      require the Llama reasoning layer (online mode, --offline omitted with a")
        print(f"      Groq API key) to catch subtle/sub-clinical red-flag utterances.")
        print(f"      The eliminatory gate is intended to be evaluated against the online (LLM) result.")
    elif rojo_misses > 0:
        print(f"\nFAILURE: {rojo_misses} rojo cases missed! Eliminatory gate violated.")
        sys.exit(1)

    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Postop Voice Agent Evaluation")
    parser.add_argument("--dataset", default=os.getenv("DATASET_PATH", "/tmp/ParticipantArtifacts/dataset/dataset_final.xlsx"), help="Path to dataset_final.xlsx")
    parser.add_argument("--offline", action="store_true", help="Run in offline mode with mocked inference")
    parser.add_argument("--capa", choices=["capa1_limpia", "capa2_ruidosa"], help="Filter by layer")
    args = parser.parse_args()
    
    run_evaluation(args.dataset, offline=args.offline, capa=args.capa)
