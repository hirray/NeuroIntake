"""
Clinical Red Flags Assessment Module (Deterministic Safety Rules)
===================================================================
Safety Principle: Neurological red flags are checked FIRST and at any moment
a red flag answer or emergency phrase is encountered.
On red flag: STOP interview, mark URGENT_RED_FLAG, show calm emergency guidance,
NEVER reassure, NEVER give diagnostic labels.

v2 — Updated for composite multi_choice E1/E2 questions.
Any choice other than 'none' in E1 or E2 triggers immediate escalation.
"""
from typing import Dict, Any, List, Tuple
import re

# Red flag question IDs in question bank (now composite multi-choice)
RED_FLAG_QUESTION_IDS = ["E1", "E2"]

# Per-code descriptions for each red-flag sub-option
RED_FLAG_DESCRIPTIONS = {
    # E1 codes
    "thunderclap": "Thunderclap headache: peak intensity reached in under 1 minute (possible subarachnoid hemorrhage / vascular event)",
    "worst_headache": "Worst headache of life or first-ever severe acute headache",
    "neuro_deficit": "New focal neurological deficit (weakness, numbness, speech loss, confusion) differing from typical pattern",
    "syncope_seizure": "Syncope, seizure, or sudden drop in level of consciousness",
    # E2 codes
    "fever_neck": "Systemic symptoms: fever combined with neck stiffness or acute rash (possible meningitis/encephalitis)",
    "vision_loss": "Sudden vision loss or acute major visual field cut",
    "post_trauma": "Post-traumatic headache: onset following recent head injury",
    "late_onset": "New onset headache after age 50 or fundamental change in headache pattern (possible temporal arteritis or intracranial pathology)",
    # Legacy single-question codes kept for backward compat
    "E1": "Thunderclap headache: peak intensity reached in under 1 minute",
    "E2": "Worst headache of life or first-ever severe headache",
    "E3": "New focal neurological deficit",
    "E4": "Syncope, seizure, or sudden drop in alertness",
    "E5": "Fever with neck stiffness or rash",
    "E6": "Sudden vision loss or acute visual change",
    "E7": "Post-traumatic headache",
    "E8": "New onset headache after age 50 or pattern change",
}

# Real-time spontaneous escalation keywords / phrases across EN, HI, GU
EMERGENCY_TRIGGER_PATTERNS = [
    # English
    r"\b(can'?t breathe|cannot breathe|chest pain|dying|feel like dying|worst pain ever|passed out|collaps(?:ed|ing)|unbearable pain now|can'?t move my (arm|leg|face|side)|cannot speak|stroke)\b",
    # Hindi (romanized and devanagari)
    r"(मर जाऊंगा|मर जाऊँगी|सांस नहीं आ रही|छाती में दर्द|असहनीय दर्द|शरीर काम नहीं कर रहा|बोल नहीं पा रहा|बेहोश हो गया|लकवा|चक्कर खाकर गिर)",
    r"\b(saans nahi|seene me dard|behosh|lakwa|bol nahi pa raha|mar jaunga|mar jaungi|asahaniya dard)\b",
    # Gujarati (romanized and gujarati)
    r"(મરી જઈશ|શ્વાસ નથી ચડતો|છાતીમાં દુખાવો|અસહ્ય દુખાવો|બેભાન થઈ ગયો|લકવો|બોલી નથી શકાતું|હાથ પગ કામ નથી કરતા)",
    r"\b(shwas nathi|chhatima dukhavo|asahy dard|lakvo|marijais|behban)\b"
]

_COMPILED_EMERGENCY_REGEX = [re.compile(p, re.IGNORECASE) for p in EMERGENCY_TRIGGER_PATTERNS]

def check_immediate_escalation(text: str) -> Tuple[bool, str]:
    """
    Checks if a free-text or spoken utterance indicates an immediate medical crisis.
    """
    if not text:
        return False, ""
    cleaned = text.strip()
    for pattern in _COMPILED_EMERGENCY_REGEX:
        if pattern.search(cleaned):
            return True, "Spontaneous statement describing severe acute distress or sudden neurological deficit"
    return False, ""

def _get_answer_value(val: Any):
    """Normalises an answer value to a comparable form."""
    if isinstance(val, dict):
        return val.get("value")
    return val

def evaluate_red_flags(answers: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Evaluates current answers for red flags.
    Supports both the new composite multi_choice E1/E2 and legacy individual E1-E8 questions.
    Returns:
        (is_urgent: bool, triggered_codes: List[str], triggered_reasons: List[str])
    """
    triggered_codes: List[str] = []
    triggered_reasons: List[str] = []

    # --- New composite question handling (E1, E2 as multi_choice) ---
    for qid in ["E1", "E2"]:
        val = _get_answer_value(answers.get(qid))
        if val is None:
            continue
        # val is either a list (multi_choice) or a scalar
        selected = val if isinstance(val, list) else [str(val)]
        for code in selected:
            code_str = str(code).lower().strip()
            if code_str in ("none", "none_of_the_above", ""):
                continue
            # Any non-none selection is a red flag
            desc = RED_FLAG_DESCRIPTIONS.get(code_str, f"Red flag reported: {code_str}")
            triggered_codes.append(f"{qid}:{code_str}")
            triggered_reasons.append(f"[{qid}] {desc}")

    # --- Legacy individual question handling (E3-E8) for backward compatibility ---
    for qid in ["E3", "E4", "E5", "E6", "E7", "E8"]:
        val = _get_answer_value(answers.get(qid))
        if val is None:
            continue
        answer_val = str(val).lower()
        if answer_val in ["yes", "true", "1"]:
            triggered_codes.append(qid)
            desc = RED_FLAG_DESCRIPTIONS.get(qid, f"Positive red flag answer to {qid}")
            triggered_reasons.append(f"[{qid}] {desc}")

    # Also flag if A2 contains muscle_weakness_one_side (new consolidated aura question)
    a2_val = _get_answer_value(answers.get("A2"))
    if a2_val is not None:
        a2_list = a2_val if isinstance(a2_val, list) else [str(a2_val)]
        if "muscle_weakness_one_side" in [str(x).lower() for x in a2_list]:
            triggered_codes.append("A2:muscle_weakness_one_side")
            triggered_reasons.append("[A2] Reported unilateral motor weakness during attack — requires specialist evaluation")

    is_urgent = len(triggered_codes) > 0
    return is_urgent, triggered_codes, triggered_reasons
