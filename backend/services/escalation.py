import re
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SourceCitation(BaseModel):
    doc_id: str
    title: str
    chunk_idx: int

class TriageDecisionPayload(BaseModel):
    triage_level: str = Field(..., pattern="^(verde|amarillo|rojo)$")
    justification: str
    source_citations: List[SourceCitation] = []
    confidence: float = Field(..., ge=0.0, le=1.0)

class CallSummary(BaseModel):
    dialogo_id: str
    caso_id: str
    paciente_id: str
    dia_postop: int
    turns: int
    final_triage: str
    trayectoria_snapshot: Dict[str, Any]
    clinical_notes: str

class EscalationEngine:
    RED_FLAG_PATTERNS = {
        "hemorrhage": [
            r"sangrado activo", r"chorro", r"empapa compresas",
            r"bota mucha sangre", r"sangre fresca constante"
        ],
        "fever": [
            r"fiebre", r"calentura", r"temperatura alta",
            r"3[8-9]\b", r"38\.[0-9]", r"39(?:\.\d+)?", r"4[0-2](?:\.\d+)?",
            r"temblando de frío", r"calientica", r"afiebrada", r"cuerpo caliente"
        ],
        "dyspnea": [
            r"ahogo", r"falta de aire", r"no puedo respirar",
            r"me ahogo", r"respiración agitada", r"opresión pecho"
        ],
        "dehiscence": [
            r"se abrió", r"pus", r"secreción", r"líquido",
            r"amarill[oi]", r"fétida", r"hueco en la herida",
            r"líquido mal olor"
        ],
        "severe_pain": [
            r"dolor insoportable", r"nrs\s*(?:[8-9]|10)",
            r"dolor que no cede", r"peor dolor de mi vida"
        ],
        "sepsis": [
            r"escalofríos severos", r"confusión", r"delirio",
            r"mareo extremo", r"desvanecimiento"
        ],
        "consciousness": [
            r"desorientado", r"somnoliento", r"desmayo",
            r"síncope", r"no responde bien", r"confundido"
        ],
        "urinary_retention": [
            r"no puedo orinar", r"retención urinaria",
            r"no orino hace muchas horas", r"vejiga llena y no sale"
        ]
    }

    def __init__(self, groq_client: Optional[Any] = None, model: str = "llama-3-70b-versatile"):
        self.groq_client = groq_client
        self.model = model

    def evaluate_floor(self, transcript: str, trayectoria_snapshot: Optional[Dict[str, Any]] = None) -> Optional[str]:
        text = transcript.lower()
        
        # Check trayectorias snapshot fields if provided
        if trayectoria_snapshot:
            fiebre_c = trayectoria_snapshot.get("fiebre_c")
            if fiebre_c is not None and isinstance(fiebre_c, (int, float)) and fiebre_c >= 38.5:
                return "rojo"
            dolor_nrs = trayectoria_snapshot.get("dolor_nrs")
            if dolor_nrs is not None and isinstance(dolor_nrs, (int, float)) and dolor_nrs >= 8:
                return "rojo"
            herida_status = str(trayectoria_snapshot.get("herida", "")).lower()
            if any(term in herida_status for term in ["sangrado", "pus", "abierta", "dehiscencia"]):
                return "rojo"

        # Numeric safety checks for temperature >= 38.0
        temp_matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:grados|°c|c)?", text)
        for t_str in temp_matches:
            try:
                val = float(t_str)
                if 38.0 <= val < 45.0:
                    return "rojo"
            except ValueError:
                pass

        # Numeric safety checks for NRS pain score >= 8
        nrs_matches = re.findall(r"(?:nrs|dolor)\s*(?:de)?\s*(\d+)", text)
        for n_str in nrs_matches:
            try:
                val = int(n_str)
                if val >= 8:
                    return "rojo"
            except ValueError:
                pass

        # Check regex patterns across categories (with negation check)
        for category, patterns in self.RED_FLAG_PATTERNS.items():
            for pat in patterns:
                for match in re.finditer(pat, text):
                    start = match.start()
                    prefix = text[max(0, start - 25):start]
                    negations = ["no ", "sin ", "ningun", "cero ", "nada de ", "negativo "]
                    if any(neg in prefix for neg in negations):
                        continue
                    return "rojo"
        
        return None

    def evaluate(
        self,
        transcript: str,
        rag_context: List[Dict[str, Any]] = None,
        trayectoria_snapshot: Optional[Dict[str, Any]] = None
    ) -> TriageDecisionPayload:
        rag_context = rag_context or []
        floor_result = self.evaluate_floor(transcript, trayectoria_snapshot)
        
        llm_decision: Optional[TriageDecisionPayload] = None
        
        if self.groq_client:
            try:
                citations = [
                    SourceCitation(
                        doc_id=c.get("doc_id", "doc_1"),
                        title=c.get("title", "Clinical Guide"),
                        chunk_idx=c.get("chunk_idx", 0)
                    )
                    for c in rag_context
                ]
                prompt = f"""Evaluate the following post-operative patient utterance and trajectory snapshot against clinical protocols.
Utterance: "{transcript}"
Trajectory: {json.dumps(trayectoria_snapshot or {})}
RAG Context: {json.dumps(rag_context)}

Output JSON matching schema:
{{
  "triage_level": "verde" | "amarillo" | "rojo",
  "justification": "...",
  "source_citations": [...],
  "confidence": 0.95
}}"""
                response = self.groq_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content
                data = json.loads(content)
                llm_decision = TriageDecisionPayload(
                    triage_level=data.get("triage_level", "verde"),
                    justification=data.get("justification", "Evaluated by Llama RAG reasoning."),
                    source_citations=citations if citations else [SourceCitation(doc_id="protocol_default", title="Post-op Guide", chunk_idx=0)],
                    confidence=float(data.get("confidence", 0.9))
                )
            except Exception:
                llm_decision = None

        # Composition & One-way escalation rule
        if floor_result == "rojo":
            justification = "Escalated to ROJO by deterministic safety floor red-flag detection."
            if llm_decision and llm_decision.justification:
                justification = f"{justification} LLM Context: {llm_decision.justification}"
            citations = llm_decision.source_citations if llm_decision else [SourceCitation(doc_id="safety_floor", title="Safety Floor Rules", chunk_idx=0)]
            return TriageDecisionPayload(
                triage_level="rojo",
                justification=justification,
                source_citations=citations,
                confidence=1.0
            )
        
        if llm_decision:
            return llm_decision
        
        citations = [SourceCitation(doc_id="safety_floor", title="Safety Floor Rules", chunk_idx=0)]
        return TriageDecisionPayload(
            triage_level="verde",
            justification="Evaluated by safety floor (no red flags triggered).",
            source_citations=citations,
            confidence=1.0
        )

def generate_call_summary(
    dialogo_id: str,
    caso_id: str,
    paciente_id: str,
    dia_postop: int,
    turns: int,
    final_triage: str,
    trayectoria_snapshot: Dict[str, Any],
    clinical_notes: str
) -> CallSummary:
    return CallSummary(
        dialogo_id=dialogo_id,
        caso_id=caso_id,
        paciente_id=paciente_id,
        dia_postop=dia_postop,
        turns=turns,
        final_triage=final_triage,
        trayectoria_snapshot=trayectoria_snapshot,
        clinical_notes=clinical_notes
    )
