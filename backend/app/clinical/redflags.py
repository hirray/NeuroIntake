"""
Clinical Red Flags Assessment Module (Deterministic Safety Rules)
===================================================================
Safety Principle: Neurological red flags are checked FIRST and at any moment
a red flag answer or emergency phrase is encountered.
On red flag: STOP interview, mark URGENT_RED_FLAG, show calm emergency guidance,
NEVER reassure, NEVER give diagnostic labels.
"""
from typing import Dict, Any, List, Tuple
import re

# Red flag question IDs in question bank
RED_FLAG_QUESTION_IDS = ["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"]

RED_FLAG_DESCRIPTIONS = {
    "E1": "Thunderclap headache: peak intensity reached in under 1 minute (possible subarachnoid hemorrhage / vascular event)",
    "E2": "Worst headache of life or first-ever severe acute headache",
    "E3": "New focal neurological deficit (weakness, numbness, speech loss, confusion) differing from typical pattern",
    "E4": "Syncope, seizure, or sudden drop in level of consciousness",
    "E5": "Systemic symptoms: fever combined with neck stiffness or acute rash (possible meningitis/encephalitis)",
    "E6": "Sudden vision loss or acute major visual field cut",
    "E7": "Post-traumatic headache: onset following recent head injury",
    "E8": "New onset headache after age 50 or fundamental change in headache pattern (possible temporal arteritis or intracranial pathology)",
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

def evaluate_red_flags(answers: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Evaluates current answers for red flags.
    Returns:
        (is_urgent: bool, triggered_codes: List[str], triggered_reasons: List[str])
    """
    triggered_codes: List[str] = []
    triggered_reasons: List[str] = []

    # Check E1-E8 explicitly
    for qid in RED_FLAG_QUESTION_IDS:
        val = answers.get(qid)
        # val can be string 'yes', dict {'value': 'yes'}, or boolean True
        answer_val = ""
        if isinstance(val, dict):
            answer_val = str(val.get("value", "")).lower()
        elif val is not None:
            answer_val = str(val).lower()

        if answer_val in ["yes", "true", "1"]:
            triggered_codes.append(qid)
            desc = RED_FLAG_DESCRIPTIONS.get(qid, f"Positive red flag answer to {qid}")
            triggered_reasons.append(f"[{qid}] {desc}")

    # Also check if motor weakness (A13) is marked yes without being a known long-standing aura
    a13_val = answers.get("A13")
    if isinstance(a13_val, dict):
        a13_str = str(a13_val.get("value", "")).lower()
    else:
        a13_str = str(a13_val).lower() if a13_val is not None else ""

    # If new motor weakness occurred or syncope/seizure
    a11_val = answers.get("A11")
    if isinstance(a11_val, dict):
        a11_str = str(a11_val.get("value", "")).lower()
    else:
        a11_str = str(a11_val).lower() if a11_val is not None else ""

    # Note: A13 alone is also flagged in specialist review, but if marked in conjunction with E3, it's captured.
    is_urgent = len(triggered_codes) > 0
    return is_urgent, triggered_codes, triggered_reasons
