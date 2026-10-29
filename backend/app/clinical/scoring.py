"""
Clinical Descriptive Scoring & Dataset Mapping
===============================================
Computes descriptive non-diagnostic metrics for the clinician report:
- Frequency classification (episodic vs chronic risk)
- Associated symptoms burden
- Medication overuse indicator (ICHD-3 8.2)
- Direct mapping to public Kaggle migraine dataset schema
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class ClinicalSummary(BaseModel):
    frequency_days_per_month: Optional[int]
    frequency_band: str               # "<4 days (infrequent episodic)", "4-14 days (frequent episodic)", ">=15 days (chronic pattern)"
    intensity_description: str
    duration_band: str
    associated_symptom_count: int
    aura_symptoms_present: List[str]
    medication_overuse_risk: bool
    triggers_reported: List[str]
    lifestyle_summary: Dict[str, Any]

def _val(answers: Dict[str, Any], qid: str) -> str:
    raw = answers.get(qid)
    if raw is None:
        return ""
    if isinstance(raw, dict):
        return str(raw.get("value", "")).strip().lower()
    return str(raw).strip().lower()

def _list(answers: Dict[str, Any], qid: str) -> List[str]:
    raw = answers.get(qid)
    if raw is None:
        return []
    if isinstance(raw, dict):
        v = raw.get("value", [])
        if isinstance(v, list):
            return [str(x).strip().lower() for x in v]
        return [str(v).strip().lower()]
    if isinstance(raw, list):
        return [str(x).strip().lower() for x in raw]
    return [str(raw).strip().lower()]

def compute_clinical_summary(answers: Dict[str, Any]) -> ClinicalSummary:
    # 1. Frequency Band
    freq_str = _val(answers, "H2")
    freq_num: Optional[int] = None
    try:
        freq_num = int(freq_str)
    except (ValueError, TypeError):
        pass

    if freq_num is not None:
        if freq_num >= 15:
            freq_band = f"{freq_num} days/month - Chronic Pattern Risk (>= 15 days)"
        elif freq_num >= 4:
            freq_band = f"{freq_num} days/month - Frequent Episodic (4-14 days)"
        else:
            freq_band = f"{freq_num} days/month - Infrequent Episodic (< 4 days)"
    else:
        freq_band = "Not specified"

    # 2. Intensity
    intensity_val = _val(answers, "H5")
    intensity_desc = intensity_val.capitalize() if intensity_val else "Not specified"

    # 3. Duration
    duration_val = _val(answers, "H1")
    duration_map = {
        "less_than_4h": "< 4 hours",
        "4_to_72h": "4 to 72 hours",
        "more_than_72h": "> 72 hours",
        "unknown": "Unknown"
    }
    duration_band = duration_map.get(duration_val, duration_val or "Not specified")

    # 4. Associated Symptoms Count
    assoc_count = 0
    for q in ["H7", "H8", "H9", "H10"]:
        if _val(answers, q) == "yes":
            assoc_count += 1

    # 5. Aura Symptoms
    aura_list: List[str] = []
    visuals = [x for x in _list(answers, "A1") if x != "none"]
    if visuals:
        aura_list.append(f"Visual disturbances ({len(visuals)} types)")
    sensory = [x for x in _list(answers, "A2") if x != "none"]
    if sensory:
        aura_list.append(f"Sensory changes ({len(sensory)} types)")
    if _val(answers, "A3") == "yes":
        aura_list.append("Dysphasia (word-finding trouble)")
    if _val(answers, "A4") == "yes":
        aura_list.append("Dysarthria (slurred speech)")
    if _val(answers, "A5") == "yes":
        aura_list.append("Vertigo (spinning sensation)")
    if _val(answers, "A6") == "yes":
        aura_list.append("Tinnitus (ear ringing)")
    if _val(answers, "A7") == "yes":
        aura_list.append("Hypoacusis (hearing decrease)")
    if _val(answers, "A8") == "yes":
        aura_list.append("Diplopia (double vision)")
    if _val(answers, "A9") == "yes":
        aura_list.append("Visual field defect (blind spot)")
    if _val(answers, "A10") == "yes":
        aura_list.append("Ataxia (unsteadiness)")
    if _val(answers, "A11") == "yes":
        aura_list.append("Reduced awareness / fainting")
    if _val(answers, "A12") == "yes":
        aura_list.append("Bilateral paresthesia (both sides)")
    if _val(answers, "A13") == "yes":
        aura_list.append("Motor weakness (one side)")

    # 6. Medication Overuse Risk
    med_overuse = (_val(answers, "F5") == "yes")

    # 7. Triggers
    triggers = _list(answers, "F6")

    # 8. Lifestyle
    lifestyle = {
        "sleep_hours": _val(answers, "L1") or "Not answered",
        "stress_level_0_10": _val(answers, "L2") or "Not answered",
        "water_liters": _val(answers, "L3") or "Not answered",
        "caffeine_cups": _val(answers, "L4") or "Not answered",
        "screen_hours": _val(answers, "L5") or "Not answered"
    }

    return ClinicalSummary(
        frequency_days_per_month=freq_num,
        frequency_band=freq_band,
        intensity_description=intensity_desc,
        duration_band=duration_band,
        associated_symptom_count=assoc_count,
        aura_symptoms_present=aura_list,
        medication_overuse_risk=med_overuse,
        triggers_reported=triggers,
        lifestyle_summary=lifestyle
    )

def export_kaggle_features(answers: Dict[str, Any], confirmed_doctor_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Extracts columns conforming strictly to public Kaggle migraine dataset format:
    Age, Duration, Frequency, Location, Character, Intensity, Nausea, Vomit,
    Phonophobia, Photophobia, Visual, Sensory, Dysphasia, Dysarthria, Vertigo,
    Tinnitus, Hypoacusis, Diplopia, Defect, Ataxia, Conscience, Paresthesia, DPF, Type
    """
    def _bool_int(qid: str) -> int:
        return 1 if _val(answers, qid) == "yes" else 0

    # Age
    try:
        age = int(_val(answers, "P1"))
    except (ValueError, TypeError):
        age = 0

    # Duration: code as 1 (<4h), 2 (4-72h), 3 (>72h) or raw hours
    dur_val = _val(answers, "H1")
    if dur_val == "less_than_4h":
        duration_code = 1
    elif dur_val == "4_to_72h":
        duration_code = 2
    elif dur_val == "more_than_72h":
        duration_code = 3
    else:
        duration_code = 0

    # Frequency
    try:
        frequency = int(_val(answers, "H2"))
    except (ValueError, TypeError):
        frequency = 0

    # Location: 1 = one-sided, 0 = both or varies
    location = 1 if _val(answers, "H3") == "one_sided" else 0

    # Character: 1 = throbbing, 0 = other
    character = 1 if _val(answers, "H4") == "throbbing_pulsating" else 0

    # Intensity: 1 = mild, 2 = moderate, 3 = severe
    int_str = _val(answers, "H5")
    int_map = {"mild": 1, "moderate": 2, "severe": 3}
    intensity = int_map.get(int_str, 0)

    # Visual count 0-4
    visuals = [x for x in _list(answers, "A1") if x != "none"]
    visual_count = min(len(visuals), 4)

    # Sensory count 0-2
    sensory = [x for x in _list(answers, "A2") if x != "none"]
    sensory_count = min(len(sensory), 2)

    return {
        "Age": age,
        "Duration": duration_code,
        "Frequency": frequency,
        "Location": location,
        "Character": character,
        "Intensity": intensity,
        "Nausea": _bool_int("H7"),
        "Vomit": _bool_int("H8"),
        "Phonophobia": _bool_int("H9"),
        "Photophobia": _bool_int("H10"),
        "Visual": visual_count,
        "Sensory": sensory_count,
        "Dysphasia": _bool_int("A3"),
        "Dysarthria": _bool_int("A4"),
        "Vertigo": _bool_int("A5"),
        "Tinnitus": _bool_int("A6"),
        "Hypoacusis": _bool_int("A7"),
        "Diplopia": _bool_int("A8"),
        "Defect": _bool_int("A9"),
        "Ataxia": _bool_int("A10"),
        "Conscience": _bool_int("A11"),
        "Paresthesia": _bool_int("A12"),
        "DPF": _bool_int("F1"),
        "Type": confirmed_doctor_type or "Unreviewed"
    }
