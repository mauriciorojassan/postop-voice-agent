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
            r"sangrado activo", r"\bchorro\b", r"empapa\s+(?:las\s+)?compresas",
            r"bota mucha sangre", r"sangre fresca", r"sangra y no para"
        ],
        "fever": [
            r"\bfiebre\b(?!\s+(?:no|ni))", r"\bcalentura\b(?!\s+(?:no|ni))",
            r"temperatura\s+(?:de\s+)?(?:3[8-9]|4[0-2])", r"temblando de frío",
            r"\bafiebrad[ao]\b", r"escalofríos?\s+(?:fuerte|severo|mucho)"
        ],
        "dyspnea": [
            r"\bahog[ao]\b", r"falta de aire", r"no puedo respirar",
            r"respiración agitada", r"opresión(?:\s+en\s+el)?\s+pecho", r"me cuesta respirar"
        ],
        "dehiscence": [
            r"se\s+(?:me\s+)?abri[óo]\s+(?:la\s+)?herida", r"\bpus\b",
            r"secreción\s+(?:con\s+pus|mal\s+olor|fétida)", r"líquido\s+(?:amarillo|con\s+pus|mal\s+olor)",
            r"hueco en la herida", r"herida\s+(?:abierta|dehiscencia|se\s+abrió)",
            r"\blíquido[, ]+amarill[oa]\b", r"se\s+ve\s+(?:como\s+)?líquido"
        ],
        "severe_pain": [
            r"dolor\s+(?:insoportable|insoporble|insportable)", r"nrs\s*(?:[89]|10)\b",
            r"dolor que no cede", r"peor dolor de mi vida", r"\bnrs\s*10\b"
        ],
        "sepsis": [
            r"escalofríos?\s+severos", r"\bdelirio\b", r"\bconfusión\b(?:\s+(?:y|con|acompañada))?",
            r"mareo extremo", r"desvanecimiento(?:\s+(?:repetido|constante|repentino))?"
        ],
        "consciousness": [
            r"\bdesorientad[ao]\b", r"\bsomnolent[ao]\b", r"\bdesmay[oeo]\b",
            r"\bsíncope\b", r"no responde bien", r"\bconfundid[ao]\b"
        ],
        "urinary_retention": [
            r"no puedo orinar", r"retención urinaria",
            r"no orino hace (?:varias\s+horas|muchas\s+horas|más\s+de)", r"vejiga llena y no sale"
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
            if isinstance(fiebre_c, (int, float)) and fiebre_c >= 38.5:
                return "rojo"
            dolor_nrs = trayectoria_snapshot.get("dolor_nrs")
            if isinstance(dolor_nrs, (int, float)) and dolor_nrs >= 8:
                return "rojo"
            herida_status = str(trayectoria_snapshot.get("herida", "")).lower()
            if any(term in herida_status for term in ["sangrado", "pus", "abierta", "dehiscencia"]):
                return "rojo"

        # Ponytail: explicit measured temperature governs fever. If the utterance
        # reports a numeric reading, that single number decides fever — keyword
        # mentions like "¿eso ya es fiebre?" must NOT override a real thermometer.
        temp_matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:°c|grados?|ºc|c)\b", text)
        max_temp = 0.0
        has_temp_reading = False
        for t_str in temp_matches:
            try:
                val = float(t_str)
                # Valid body-temperature range only; ignore 100, 200, etc (ages, IDs).
                if 30.0 <= val <= 45.0:
                    has_temp_reading = True
                    if val > max_temp:
                        max_temp = val
            except ValueError:
                pass
        if has_temp_reading and max_temp >= 38.5:
            return "rojo"

        # Numeric NRS pain score >=8 (with explicit "nrs" or "dolor de N")
        nrs_matches = re.findall(r"(?:nrs|dolor)\s*(?:de\s+)?(\d{1,2})\b", text)
        for n_str in nrs_matches:
            try:
                if int(n_str) >= 8:
                    return "rojo"
            except ValueError:
                pass

        # If a thermometer reading exists and is sub-febrile (<38.5), fever
        # keywords lose their force — the patient has the actual number.
        fever_keywords = ["fiebre", "calentura", "calientica", "afiebrada", "afiebrado"]
        fever_in_utterance = any(k in text for k in fever_keywords)
        if has_temp_reading and fever_in_utterance:
            # 37.x°C plus a "¿es fiebre?" question is NOT a red flag.
            fever_in_utterance = False

        # Check regex patterns across categories (whole-utterance negation check).
        NEGATIONS = ("no ", "sin ", "nunca ", "nada de ", "ningún", "ningun",
                     "cero ", "negativo", "niego", "no he", "no me", "no tengo")
        for category, patterns in self.RED_FLAG_PATTERNS.items():
            # Skip fever category if an explicit sub-febrile reading overrides it.
            if category == "fever" and has_temp_reading and not fever_in_utterance:
                continue
            for pat in patterns:
                match = re.search(pat, text)
                if not match:
                    continue
                start = match.start()
                lookback = re.split(r"[.!?,;:]", text[:start])[-1]
                if any(neg in lookback for neg in NEGATIONS):
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
