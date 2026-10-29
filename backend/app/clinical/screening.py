"""
Deterministic ICHD-3 Migraine Screening Engine
===============================================
Clinical Rule Citations:
- Headache Classification Committee of the International Headache Society (IHS).
  The International Classification of Headache Disorders, 3rd edition. Cephalalgia 2018, Vol. 38(1) 1–211.
  * Section 1.1: Migraine without aura
  * Section 1.2: Migraine with aura (1.2.1 Typical aura)
  * Section 8.2: Medication-overuse headache (MOH) screening risk

NON-NEGOTIABLE SAFETY PRINCIPLES:
1. Screening Aid ONLY: Not a diagnosis, prescription, or reassurance.
2. The LLM NEVER computes, changes, softens, or alters any clinical rule output.
3. This function takes strictly parsed coded answers.
"""
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from .redflags import evaluate_red_flags

class ScreeningOutcome(str, Enum):
    CRITERIA_MET_MIGRAINE_WITHOUT_AURA = "CRITERIA_MET_MIGRAINE_WITHOUT_AURA"
    CRITERIA_MET_MIGRAINE_WITH_AURA = "CRITERIA_MET_MIGRAINE_WITH_AURA"
    FEATURES_NEED_SPECIALIST_REVIEW = "FEATURES_NEED_SPECIALIST_REVIEW"
    CRITERIA_NOT_MET = "CRITERIA_NOT_MET"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
    URGENT_RED_FLAG = "URGENT_RED_FLAG"

class CriterionResult(BaseModel):
    criterion: str          # e.g., "ICHD-3 1.1 Criterion A (>= 5 lifetime attacks)"
    code: str               # "A", "B", "C", "D"
    required: str           # Description of threshold
    patient_answer: str     # Raw or coded string
    met: Optional[bool]     # True / False / None (unknown/insufficient)
    questions: List[str]    # Questions supplying this criterion

class ScreeningResult(BaseModel):
    outcome: ScreeningOutcome
    summary_text: str
    doctor_disclaimer: str
    criteria_table: List[CriterionResult]
    specialist_flags: List[str]
    red_flags: List[str]
    missing_items: List[str]
    points_to_clarify: List[str]
    is_urgent: bool

def _get_val(answers: Dict[str, Any], qid: str) -> str:
    """Helper to extract clean normalized string value from answer structure."""
    raw = answers.get(qid)
    if raw is None:
        return ""
    if isinstance(raw, dict):
        return str(raw.get("value", "")).strip().lower()
    return str(raw).strip().lower()

def _get_list(answers: Dict[str, Any], qid: str) -> List[str]:
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

def evaluate_ichd3_screening(answers: Dict[str, Any]) -> ScreeningResult:
    """
    Computes deterministic ICHD-3 screening result from coded answers.
    Takes ONLY coded dictionary, completely independent of any LLM.
    """
    doctor_disclaimer = (
        "Automated screening aid based on ICHD-3 criteria applied to patient-reported answers. "
        "Not a diagnosis. Final clinical diagnosis and treatment plan rest entirely with the treating physician."
    )

    # 1. Step 1: Check Red Flags FIRST
    is_urgent, red_codes, red_reasons = evaluate_red_flags(answers)
    if is_urgent:
        return ScreeningResult(
            outcome=ScreeningOutcome.URGENT_RED_FLAG,
            summary_text="URGENT RED FLAG TRIGGERED: Patient reported acute neurological or systemic red flags requiring immediate medical evaluation.",
            doctor_disclaimer=doctor_disclaimer,
            criteria_table=[],
            specialist_flags=[],
            red_flags=red_reasons,
            missing_items=[],
            points_to_clarify=["Urgent evaluation for secondary headache etiologies indicated (e.g. neuroimaging, lumbar puncture, vascular workup)."],
            is_urgent=True
        )

    specialist_flags: List[str] = []
    points_to_clarify: List[str] = []
    missing_items: List[str] = []
    criteria_table: List[CriterionResult] = []

    # 2. Step 2: Check Specialist Review features (Aura Red Flags & Mimics)
    # A13: Motor weakness on one side
    if _get_val(answers, "A13") == "yes":
        specialist_flags.append("Motor weakness reported during attacks (concern for hemiplegic migraine or transient ischemic attack).")
    # A8: Diplopia (double vision)
    if _get_val(answers, "A8") == "yes":
        specialist_flags.append("Diplopia (double vision) reported during attacks.")
    # A10: Ataxia (unsteadiness)
    if _get_val(answers, "A10") == "yes":
        specialist_flags.append("Ataxia (unsteadiness / balance disturbance) reported during attacks.")
    # A4 + A11: Slurred speech together with reduced consciousness
    if _get_val(answers, "A4") == "yes" and _get_val(answers, "A11") == "yes":
        specialist_flags.append("Combination of dysarthria (slurred speech) and altered awareness / syncope reported.")
    # Brainstem aura pattern: >= 2 of vertigo (A5), tinnitus (A6), hypoacusis (A7)
    brainstem_count = sum(1 for q in ["A5", "A6", "A7"] if _get_val(answers, q) == "yes")
    if brainstem_count >= 2:
        specialist_flags.append("Multiple brainstem symptoms reported (vertigo, tinnitus, hypoacusis) suggesting possible migraine with brainstem aura.")
    # Aura > 60 min or not fully resolving
    if _get_val(answers, "A14") == "more_than_60min":
        specialist_flags.append("Prolonged aura duration (> 60 minutes) reported.")
    if _get_val(answers, "A15") == "no":
        specialist_flags.append("Aura symptoms not fully reversible according to patient report.")

    # 3. Step 3: Evaluate ICHD-3 1.1 (Migraine without aura)
    # Criterion A: At least 5 lifetime attacks (P6)
    p6_val = _get_val(answers, "P6")
    crit_a_met: Optional[bool] = None
    if p6_val == "five_or_more":
        crit_a_met = True
    elif p6_val == "less_than_5":
        crit_a_met = False
    elif p6_val in ["unknown", ""]:
        missing_items.append("P6 (Lifetime attacks count)")

    criteria_table.append(CriterionResult(
        criterion="ICHD-3 1.1 Criterion A",
        code="A",
        required=">= 5 lifetime attacks",
        patient_answer=p6_val or "Unanswered",
        met=crit_a_met,
        questions=["P6"]
    ))

    # Criterion B: Untreated duration 4-72 hours (H1)
    h1_val = _get_val(answers, "H1")
    crit_b_met: Optional[bool] = None
    if h1_val == "4_to_72h":
        crit_b_met = True
    elif h1_val in ["less_than_4h", "more_than_72h"]:
        crit_b_met = False
    elif h1_val in ["unknown", ""]:
        missing_items.append("H1 (Attack duration)")

    criteria_table.append(CriterionResult(
        criterion="ICHD-3 1.1 Criterion B",
        code="B",
        required="Untreated attack duration 4 to 72 hours",
        patient_answer=h1_val or "Unanswered",
        met=crit_b_met,
        questions=["H1"]
    ))

    # Criterion C: At least 2 of 4 headache characteristics:
    # 1. Unilateral (H3 == 'one_sided')
    # 2. Pulsating (H4 == 'throbbing_pulsating')
    # 3. Moderate/severe (H5 in ['moderate', 'severe'])
    # 4. Aggravated by routine physical activity (H6 == 'yes')
    c_features = []
    h3_val = _get_val(answers, "H3")
    h4_val = _get_val(answers, "H4")
    h5_val = _get_val(answers, "H5")
    h6_val = _get_val(answers, "H6")

    if h3_val == "one_sided":
        c_features.append("Unilateral location (H3)")
    if h4_val == "throbbing_pulsating":
        c_features.append("Pulsating quality (H4)")
    if h5_val in ["moderate", "severe"]:
        c_features.append(f"Moderate/Severe intensity (H5: {h5_val})")
    if h6_val == "yes":
        c_features.append("Aggravated by routine physical activity (H6)")

    unknown_c = any(v in ["unknown", ""] for v in [h3_val, h4_val, h5_val, h6_val])
    crit_c_met: Optional[bool] = None
    if len(c_features) >= 2:
        crit_c_met = True
    elif not unknown_c and len(c_features) < 2:
        crit_c_met = False
    else:
        crit_c_met = None
        missing_items.append("H3/H4/H5/H6 (Pain characteristics)")

    criteria_table.append(CriterionResult(
        criterion="ICHD-3 1.1 Criterion C",
        code="C",
        required=">= 2 of: unilateral, pulsating, moderate/severe, aggravated by routine activity",
        patient_answer=f"{len(c_features)}/4 met ({', '.join(c_features) if c_features else 'None'})",
        met=crit_c_met,
        questions=["H3", "H4", "H5", "H6"]
    ))

    # Criterion D: At least 1 of:
    # 1. Nausea and/or vomiting (H7 == 'yes' or H8 == 'yes')
    # 2. Both photophobia AND phonophobia (H9 == 'yes' and H10 == 'yes')
    h7_val = _get_val(answers, "H7")
    h8_val = _get_val(answers, "H8")
    h9_val = _get_val(answers, "H9")
    h10_val = _get_val(answers, "H10")

    nausea_vomiting = (h7_val == "yes" or h8_val == "yes")
    both_photo_phono = (h9_val == "yes" and h10_val == "yes")
    crit_d_met: Optional[bool] = None

    if nausea_vomiting or both_photo_phono:
        crit_d_met = True
    elif (h7_val == "no" and h8_val == "no") and (h9_val == "no" or h10_val == "no"):
        crit_d_met = False
    else:
        crit_d_met = None
        missing_items.append("H7/H8/H9/H10 (Associated symptoms)")

    d_desc = []
    if nausea_vomiting:
        d_desc.append("Nausea/Vomiting present")
    if both_photo_phono:
        d_desc.append("Both Photophobia & Phonophobia present")
    if not d_desc:
        d_desc.append("Neither nausea/vomiting nor dual sensitivity reported")

    criteria_table.append(CriterionResult(
        criterion="ICHD-3 1.1 Criterion D",
        code="D",
        required=">= 1 of: Nausea/vomiting OR both photophobia and phonophobia",
        patient_answer="; ".join(d_desc),
        met=crit_d_met,
        questions=["H7", "H8", "H9", "H10"]
    ))

    # 4. Step 4: Evaluate ICHD-3 1.2 (Migraine with typical aura)
    visual_items = _get_list(answers, "A1")
    has_visual = any(x in ["zigzag_lines", "flashing_lights", "bright_spots", "blurred_patches"] for x in visual_items)
    sensory_items = _get_list(answers, "A2")
    has_sensory = any(x in ["spreading_tingling", "spreading_numbness"] for x in sensory_items)
    has_speech = (_get_val(answers, "A3") == "yes")

    has_any_aura = has_visual or has_sensory or has_speech
    aura_reversible = (_get_val(answers, "A15") == "yes")
    no_motor = (_get_val(answers, "A13") == "no")

    crit_aura_met = False
    if has_any_aura and aura_reversible and no_motor:
        # Check characteristic features (need >= 3 of 6):
        # 1. gradual spread >= 5 min (A16)
        # 2. >= 2 symptoms in succession (A17)
        # 3. duration 5-60 min (A14)
        # 4. unilateral (A18)
        # 5. positive symptom (scintillations or tingling)
        # 6. headache accompanies or follows within 60 min (A19)
        aura_features_count = 0
        if _get_val(answers, "A16") == "yes":
            aura_features_count += 1
        if _get_val(answers, "A17") == "yes":
            aura_features_count += 1
        if _get_val(answers, "A14") == "5_to_60min":
            aura_features_count += 1
        if _get_val(answers, "A18") == "yes":
            aura_features_count += 1
        # Positive symptoms
        pos_symptom = any(x in ["zigzag_lines", "flashing_lights", "bright_spots"] for x in visual_items) or ("spreading_tingling" in sensory_items)
        if pos_symptom:
            aura_features_count += 1
        if _get_val(answers, "A19") == "yes":
            aura_features_count += 1

        if aura_features_count >= 3:
            crit_aura_met = True

    # Check medication overuse risk (F5 == 'yes')
    if _get_val(answers, "F5") == "yes":
        points_to_clarify.append("Medication Overuse Warning: Patient takes acute headache medication >= 10 days/month (evaluate for Medication-Overuse Headache ICHD-3 8.2).")

    # Final Outcome Decision Tree
    if specialist_flags:
        return ScreeningResult(
            outcome=ScreeningOutcome.FEATURES_NEED_SPECIALIST_REVIEW,
            summary_text="FEATURES NEED SPECIALIST REVIEW: Specific atypical neurological or aura symptoms were reported requiring specialist neurological evaluation.",
            doctor_disclaimer=doctor_disclaimer,
            criteria_table=criteria_table,
            specialist_flags=specialist_flags,
            red_flags=[],
            missing_items=missing_items,
            points_to_clarify=points_to_clarify + ["Rule out secondary headache, stroke mimic, or atypical aura before establishing primary headache diagnosis."],
            is_urgent=False
        )

    # If any required criteria had unknown/missing answers preventing certainty
    if crit_a_met is None or crit_b_met is None or crit_c_met is None or crit_d_met is None:
        # Check if aura criteria alone definitively met
        if crit_aura_met:
            return ScreeningResult(
                outcome=ScreeningOutcome.CRITERIA_MET_MIGRAINE_WITH_AURA,
                summary_text="CRITERIA MET: Features align with ICHD-3 1.2 Migraine with typical aura.",
                doctor_disclaimer=doctor_disclaimer,
                criteria_table=criteria_table,
                specialist_flags=[],
                red_flags=[],
                missing_items=missing_items,
                points_to_clarify=points_to_clarify,
                is_urgent=False
            )
        return ScreeningResult(
            outcome=ScreeningOutcome.INSUFFICIENT_INFORMATION,
            summary_text="INSUFFICIENT INFORMATION: Answers to one or more essential diagnostic criteria were incomplete, skipped, or unknown.",
            doctor_disclaimer=doctor_disclaimer,
            criteria_table=criteria_table,
            specialist_flags=[],
            red_flags=[],
            missing_items=missing_items,
            points_to_clarify=points_to_clarify + [f"Clarify missing items during consultation: {', '.join(missing_items)}"],
            is_urgent=False
        )

    # Both without aura and with aura
    if crit_aura_met:
        return ScreeningResult(
            outcome=ScreeningOutcome.CRITERIA_MET_MIGRAINE_WITH_AURA,
            summary_text="CRITERIA MET: Patient-reported symptoms fulfill ICHD-3 1.2 criteria for Migraine with typical aura.",
            doctor_disclaimer=doctor_disclaimer,
            criteria_table=criteria_table,
            specialist_flags=[],
            red_flags=[],
            missing_items=[],
            points_to_clarify=points_to_clarify,
            is_urgent=False
        )

    if crit_a_met and crit_b_met and crit_c_met and crit_d_met:
        return ScreeningResult(
            outcome=ScreeningOutcome.CRITERIA_MET_MIGRAINE_WITHOUT_AURA,
            summary_text="CRITERIA MET: Patient-reported symptoms fulfill ICHD-3 1.1 criteria for Migraine without aura.",
            doctor_disclaimer=doctor_disclaimer,
            criteria_table=criteria_table,
            specialist_flags=[],
            red_flags=[],
            missing_items=[],
            points_to_clarify=points_to_clarify,
            is_urgent=False
        )

    return ScreeningResult(
        outcome=ScreeningOutcome.CRITERIA_NOT_MET,
        summary_text="Reported pattern does not meet the screening criteria for migraine. This does NOT rule out migraine or any other headache disorder. Clinical evaluation recommended.",
        doctor_disclaimer=doctor_disclaimer,
        criteria_table=criteria_table,
        specialist_flags=[],
        red_flags=[],
        missing_items=[],
        points_to_clarify=points_to_clarify + ["Evaluate for tension-type headache, cluster/TACs, or secondary headache disorders."],
        is_urgent=False
    )
