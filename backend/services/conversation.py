import re
import logging
from typing import List, Dict, Any, Optional
from backend.services.escalation import EscalationEngine, TriageDecisionPayload, generate_call_summary

logger = logging.getLogger(__name__)

class ConversationManager:
    DOMAINS = ["dolor", "fiebre", "movilidad", "herida", "apetito", "sueno"]
    
    AMBIGUOUS_PATTERNS = [
        r"por ahí", r"un poquito", r"más o menos", r"raro", r"como que sí",
        r"ahí vamos", r"regular", r"ahí"
    ]

    def __init__(
        self,
        caso_id: str,
        paciente_id: str,
        dia_postop: int,
        trayectoria_snapshot: Dict[str, Any],
        escalation_engine: Optional[EscalationEngine] = None,
        max_clarification_rounds: int = 2
    ):
        self.dialogo_id = f"diag_{caso_id}_{dia_postop}"
        self.caso_id = caso_id
        self.paciente_id = paciente_id
        self.dia_postop = dia_postop
        self.trayectoria_snapshot = trayectoria_snapshot
        self.escalation_engine = escalation_engine or EscalationEngine()
        self.max_clarification_rounds = max_clarification_rounds
        
        self.covered_domains: List[str] = []
        self.current_domain: Optional[str] = self.DOMAINS[0] if self.DOMAINS else None
        self.ambiguity_count = 0
        self.turns = 0
        self.history: List[Dict[str, str]] = []
        self.final_triage = "verde"
        self.is_completed = False

    def get_initial_prompt(self) -> str:
        procedimiento = self.trayectoria_snapshot.get("procedimiento", "cirugía")
        return (
            f"Hola, hablemos de su recuperación al día {self.dia_postop} de su {procedimiento}. "
            f"¿Cómo ha sentido el dolor hoy? (Por favor califíquelo de 0 a 10)."
        )

    def is_ambiguous(self, utterance: str) -> bool:
        text = utterance.lower().strip()
        # If utterance is extremely short or matches vague patterns without numbers/details
        if len(text.split()) < 3 and not any(char.isdigit() for char in text):
            return True
        for pat in self.AMBIGUOUS_PATTERNS:
            if re.search(pat, text):
                return True
        return False

    def process_turn(self, user_utterance: str) -> Dict[str, Any]:
        if self.is_completed:
            return {
                "response": "La conversación ya ha finalizado. Gracias por su reporte.",
                "next_domain": None,
                "triage_level": self.final_triage,
                "needs_clarification": False,
                "escalated": False,
                "summary": self._build_summary("Conversación finalizada previamente.")
            }

        self.turns += 1
        self.history.append({"role": "user", "content": user_utterance})

        # 1. Evaluate Escalation / Red-Flags
        triage_res = self.escalation_engine.evaluate(user_utterance, self.trayectoria_snapshot)
        self.final_triage = triage_res.triage_level

        if self.final_triage == "rojo":
            self.is_completed = True
            response_text = (
                f"ALERTA CLÍNICA: He detectado una señal de alerta importante ({triage_res.justification}). "
                "Por favor comuníquese con su equipo médico de urgencias o acuda al centro asistencial inmediatamente."
            )
            self.history.append({"role": "assistant", "content": response_text})
            return {
                "response": response_text,
                "next_domain": None,
                "triage_level": "rojo",
                "needs_clarification": False,
                "escalated": True,
                "summary": self._build_summary(f"Escalado a ROJO: {triage_res.justification}")
            }

        # 2. Check Ambiguity (Capa 2 handling / Clarification Loop)
        if self.is_ambiguous(user_utterance):
            self.ambiguity_count += 1
            if self.ambiguity_count >= self.max_clarification_rounds:
                # Escalation handoff on repeated ambiguity
                self.final_triage = "amarillo"
                self.is_completed = True
                response_text = (
                    "Notamos varias respuestas poco claras sobre su evolución. "
                    "Para mayor seguridad, hemos derivado su caso para una revisión prioritaria con enfermería."
                )
                self.history.append({"role": "assistant", "content": response_text})
                return {
                    "response": response_text,
                    "next_domain": None,
                    "triage_level": "amarillo",
                    "needs_clarification": False,
                    "escalated": True,
                    "summary": self._build_summary("Derivado a amarillo por ambigüedad persistente.")
                }
            else:
                domain_name = self.current_domain or "su evolución"
                response_text = (
                    f"Entiendo. Para poder ayudarle mejor con {domain_name}, "
                    f"¿podría ser más específico? Indíquenos exactamente dónde le molesta y califíquelo de 0 a 10."
                )
                self.history.append({"role": "assistant", "content": response_text})
                return {
                    "response": response_text,
                    "next_domain": self.current_domain,
                    "triage_level": self.final_triage,
                    "needs_clarification": True,
                    "escalated": False,
                    "summary": None
                }

        # Reset ambiguity count on valid specific input
        self.ambiguity_count = 0

        # 3. Advance Domains
        if self.current_domain and self.current_domain not in self.covered_domains:
            self.covered_domains.append(self.current_domain)

        # Find next uncovered domain
        next_dom = None
        for dom in self.DOMAINS:
            if dom not in self.covered_domains:
                next_dom = dom
                break
        
        self.current_domain = next_dom

        if not self.current_domain:
            # All domains covered! Complete session
            self.is_completed = True
            response_text = (
                "Hemos completado todas las preguntas de su seguimiento post-operatorio. "
                "Sus respuestas han sido registradas exitosamente. ¡Que tenga una excelente recuperación!"
            )
            self.history.append({"role": "assistant", "content": response_text})
            return {
                "response": response_text,
                "next_domain": None,
                "triage_level": self.final_triage,
                "needs_clarification": False,
                "escalated": False,
                "summary": self._build_summary("Seguimiento post-operatorio completado exitosamente.")
            }

        # Generate adaptive question for next domain
        response_text = self._generate_domain_question(self.current_domain)
        self.history.append({"role": "assistant", "content": response_text})
        return {
            "response": response_text,
            "next_domain": self.current_domain,
            "triage_level": self.final_triage,
            "needs_clarification": False,
            "escalated": False,
            "summary": None
        }

    def _generate_domain_question(self, domain: str) -> str:
        questions = {
            "dolor": "¿Cómo ha manejado el dolor hoy y en qué escala del 0 al 10 lo ubica?",
            "fiebre": "¿Ha presentado sensación de fiebre, calentura o tomado la temperatura recientemente?",
            "movilidad": "¿Cómo ha estado su movilidad y capacidad para caminar o levantarse?",
            "herida": "¿Cómo observa su herida quirúrgica? ¿Nota enrojecimiento, inflamación o secreción?",
            "apetito": "¿Cómo ha estado su apetito y tolerancia a líquidos y alimentos?",
            "sueno": "¿Cómo ha estado durmiendo y descansando durante la noche?"
        }
        return questions.get(domain, f"¿Cómo ha evolucionado en cuanto a {domain}?")

    def _build_summary(self, notes: str) -> Any:
        return generate_call_summary(
            dialogo_id=self.dialogo_id,
            caso_id=self.caso_id,
            paciente_id=self.paciente_id,
            dia_postop=self.dia_postop,
            turns=self.turns,
            final_triage=self.final_triage,
            trayectoria_snapshot=self.trayectoria_snapshot,
            clinical_notes=notes
        )
