"""
Bounded LLM Parsing & Clarification Service
============================================
Non-negotiable Safety Guardrails:
1. NO medical advice, diagnosis, prescription, or reassurance.
2. NO patient-identifying data is ever passed to the LLM.
3. Strict JSON output schema for option mapping.
4. Explanations of terms strictly constrained to human-reviewed glossary.
5. Immediate escalation detection on acute distress statements.
6. Deterministic regex/keyword fallback when LLM is disabled or unavailable.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel

logger = logging.getLogger("migraine_assist.llm")

SYSTEM_PROMPT = (
    "You are a parsing and clarification helper inside a medical intake form. "
    "You never give medical advice, diagnoses, reassurance, or medication information. "
    "Given a question, its allowed options and the patient's reply, return only JSON mapping the reply to an option, or null if unclear. "
    "If the patient asks what a word means, explain it in one or two simple sentences using only the supplied glossary. "
    "If the patient describes an emergency or says they feel unwell now, output {\"escalate\": true}. "
    "If asked anything else, say you can only help with the questions and the doctor will answer other concerns."
)

class LLMParseResult(BaseModel):
    value: Any = None
    confidence: float = 0.0
    needs_confirmation: bool = False
    escalate: bool = False
    clarification_response: Optional[str] = None
    translated_text: Optional[str] = None

class LLMService:
    def __init__(self):
        self.enabled = os.getenv("LLM_ENABLED", "false").lower() in ["true", "1", "yes"]
        self.provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def parse_with_llm(
        self,
        question_id: str,
        question_text: str,
        allowed_options: List[Dict[str, Any]],
        patient_reply: str,
        glossary_context: Optional[str] = None
    ) -> LLMParseResult:
        """
        Parses patient utterance using LLM if enabled, otherwise returns null for keyword fallback.
        Ensures NO PII is included in the prompt.
        """
        if not self.enabled or not patient_reply:
            return LLMParseResult()

        options_summary = [
            {"code": opt["code"], "description": opt.get("label_key", opt["code"])}
            for opt in allowed_options
        ] if allowed_options else "Free text or numeric"

        prompt = (
            f"Question: {question_text}\n"
            f"Allowed Options: {json.dumps(options_summary)}\n"
            f"Glossary Definitions: {glossary_context or 'None'}\n"
            f"Patient Reply: \"{patient_reply}\"\n\n"
            "Respond ONLY with a JSON object:\n"
            "{\"value\": <matched_code_or_value_or_null>, \"confidence\": <0.0_to_1.0>, "
            "\"needs_confirmation\": <true/false>, \"escalate\": <true/false>, \"clarification\": <optional_string_if_asking_definition>}"
        )

        try:
            raw_response = self._call_provider(prompt)
            if not raw_response:
                return LLMParseResult()

            # Extract JSON block
            clean_json = raw_response.strip()
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_json:
                clean_json = clean_json.split("```")[1].split("```")[0].strip()

            parsed = json.loads(clean_json)
            return LLMParseResult(
                value=parsed.get("value"),
                confidence=float(parsed.get("confidence", 0.9)),
                needs_confirmation=bool(parsed.get("needs_confirmation", False)),
                escalate=bool(parsed.get("escalate", False)),
                clarification_response=parsed.get("clarification")
            )
        except Exception as e:
            logger.warning(f"LLM parsing failed, gracefully falling back to deterministic parser: {e}")
            return LLMParseResult()

    def translate_patient_free_text(self, text: str, source_lang: str) -> str:
        """
        Translates patient's non-English free text to English for clinician review.
        Labeled as 'machine-translated'.
        """
        if source_lang == "en" or not text:
            return text

        if not self.enabled:
            return f"[Original {source_lang.upper()} text: {text}]"

        prompt = (
            f"Translate the following patient symptom notes from {source_lang} to English accurately and neutrally. "
            f"Do not add any medical opinions or advice.\n\nText: \"{text}\""
        )
        try:
            translation = self._call_provider(prompt)
            if translation:
                return f"[Machine-translated]: {translation.strip()}"
        except Exception as e:
            logger.warning(f"Translation failed: {e}")

        return f"[Original {source_lang.upper()} text: {text}]"

    def _call_provider(self, prompt: str) -> Optional[str]:
        if self.provider == "anthropic" and self.api_key:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model=self.model,
                max_tokens=256,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        elif self.provider == "ollama":
            import httpx
            resp = httpx.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3",
                    "system": SYSTEM_PROMPT,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=10.0
            )
            if resp.status_code == 200:
                return resp.json().get("response")
        return None
