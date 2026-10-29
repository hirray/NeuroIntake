"""
Unit and Golden Tests for Clinical Rules & ICHD-3 Screening
===========================================================
Tests all boundary values, golden cases, and non-negotiable safety rules:
1. Red flags preempt any migraine outcome immediately.
2. Motor weakness blocks aura classification and routes to specialist review.
3. Lifetime attacks threshold: 4 attacks fails Criterion A, 5 attacks passes.
4. Untreated duration: <4h fails Criterion B, 4-72h passes Criterion B.
5. Unknown / missing answers route cleanly to INSUFFICIENT_INFORMATION.
6. Kaggle export dictionary strictly contains expected columns.
"""
import pytest
from backend.app.clinical.screening import (
    evaluate_ichd3_screening,
    ScreeningOutcome
)
from backend.app.clinical.redflags import (
    evaluate_red_flags,
    check_immediate_escalation
)
from backend.app.clinical.scoring import (
    compute_clinical_summary,
    export_kaggle_features
)

def test_red_flag_thunderclap_preempts_all():
    """E1 (thunderclap) must immediately return URGENT_RED_FLAG."""
    answers = {
        "E1": "yes",
        "P6": "five_or_more",
        "H1": "4_to_72h",
        "H3": "one_sided",
        "H4": "throbbing_pulsating",
        "H5": "severe",
        "H6": "yes",
        "H7": "yes",
        "H9": "yes",
        "H10": "yes"
    }
    result = evaluate_ichd3_screening(answers)
    assert result.outcome == ScreeningOutcome.URGENT_RED_FLAG
    assert result.is_urgent is True
    assert len(result.red_flags) > 0
    assert "E1" in str(result.red_flags)

def test_emergency_phrase_escalation():
    """Real-time emergency utterance detection across en, hi, gu."""
    is_esc, _ = check_immediate_escalation("I have chest pain and can't breathe")
    assert is_esc is True

    is_esc_hi, _ = check_immediate_escalation("मुझे सांस नहीं आ रही और बहुत तेज असहनीय दर्द है")
    assert is_esc_hi is True

    is_esc_gu, _ = check_immediate_escalation("મને છાતીમાં દુખાવો થાય છે અને શ્વાસ નથી ચડતો")
    assert is_esc_gu is True

    is_safe, _ = check_immediate_escalation("The light really hurts my eyes")
    assert is_safe is False

def test_golden_case_migraine_without_aura():
    """Classic migraine without aura: >=5 attacks, 4-72h, unilateral, throbbing, severe, nausea."""
    answers = {
        "E1": "no", "E2": "no", "E3": "no", "E4": "no",
        "E5": "no", "E6": "no", "E7": "no", "E8": "no",
        "P1": 32, "P2": "female", "P6": "five_or_more",
        "H1": "4_to_72h", "H2": 5,
        "H3": "one_sided",
        "H4": "throbbing_pulsating",
        "H5": "severe",
        "H6": "yes",
        "H7": "yes", "H8": "no",
        "H9": "yes", "H10": "yes",
        "A1": ["none"], "A2": ["none"], "A3": "no", "A4": "no",
        "A5": "no", "A6": "no", "A7": "no", "A8": "no",
        "A9": "no", "A10": "no", "A11": "no", "A12": "no",
        "A13": "no", "A14": "no_aura", "A15": "yes",
        "F1": "yes", "F5": "no"
    }
    result = evaluate_ichd3_screening(answers)
    assert result.outcome == ScreeningOutcome.CRITERIA_MET_MIGRAINE_WITHOUT_AURA
    assert result.is_urgent is False
    assert len(result.specialist_flags) == 0

def test_golden_case_migraine_with_typical_aura():
    """Migraine with typical aura: visual zigzag + spots, spreading, 5-60m, reversible, no motor."""
    answers = {
        "E1": "no", "E2": "no", "E3": "no", "E4": "no",
        "E5": "no", "E6": "no", "E7": "no", "E8": "no",
        "P1": 28, "P2": "female", "P6": "five_or_more",
        "H1": "4_to_72h", "H2": 2,
        "H3": "one_sided", "H4": "throbbing_pulsating", "H5": "moderate", "H6": "yes",
        "H7": "yes", "H8": "no", "H9": "yes", "H10": "yes",
        "A1": ["zigzag_lines", "flashing_lights"],
        "A2": ["none"],
        "A3": "no", "A4": "no", "A5": "no", "A6": "no", "A7": "no", "A8": "no",
        "A9": "no", "A10": "no", "A11": "no", "A12": "no",
        "A13": "no",
        "A14": "5_to_60min",
        "A15": "yes",
        "A16": "yes", # gradual spread
        "A17": "yes", # succession
        "A18": "yes", # unilateral
        "A19": "yes", # headache within 60 min
        "F1": "yes", "F5": "no"
    }
    result = evaluate_ichd3_screening(answers)
    assert result.outcome == ScreeningOutcome.CRITERIA_MET_MIGRAINE_WITH_AURA
    assert result.is_urgent is False

def test_motor_weakness_blocks_aura_and_requires_specialist_review():
    """A13 == yes must NEVER be classified as standard migraine; routes to FEATURES_NEED_SPECIALIST_REVIEW."""
    answers = {
        "E1": "no", "E2": "no", "E3": "no", "E4": "no",
        "E5": "no", "E6": "no", "E7": "no", "E8": "no",
        "P6": "five_or_more", "H1": "4_to_72h", "H3": "one_sided", "H4": "throbbing_pulsating",
        "H5": "severe", "H6": "yes", "H7": "yes", "H9": "yes", "H10": "yes",
        "A1": ["zigzag_lines"], "A2": ["none"], "A3": "no", "A13": "yes", # Motor weakness!
        "A14": "5_to_60min", "A15": "yes", "A16": "yes", "A17": "no", "A18": "yes", "A19": "yes"
    }
    result = evaluate_ichd3_screening(answers)
    assert result.outcome == ScreeningOutcome.FEATURES_NEED_SPECIALIST_REVIEW
    assert any("motor" in f.lower() for f in result.specialist_flags)

def test_diplopia_triggers_specialist_review():
    """A8 (diplopia) triggers specialist review."""
    answers = {
        "E1": "no", "E2": "no", "E3": "no", "E4": "no",
        "E5": "no", "E6": "no", "E7": "no", "E8": "no",
        "P6": "five_or_more", "H1": "4_to_72h", "H3": "one_sided", "H4": "throbbing_pulsating",
        "H5": "moderate", "H6": "yes", "H7": "yes", "H9": "yes", "H10": "yes",
        "A8": "yes", "A13": "no", "A15": "yes"
    }
    result = evaluate_ichd3_screening(answers)
    assert result.outcome == ScreeningOutcome.FEATURES_NEED_SPECIALIST_REVIEW
    assert any("diplopia" in f.lower() for f in result.specialist_flags)

def test_boundary_lifetime_attacks():
    """4 lifetime attacks (<5) fails Criterion A; 5 attacks passes."""
    base = {
        "E1": "no", "E2": "no", "E3": "no", "E4": "no",
        "E5": "no", "E6": "no", "E7": "no", "E8": "no",
        "H1": "4_to_72h", "H3": "one_sided", "H4": "throbbing_pulsating",
        "H5": "severe", "H6": "yes", "H7": "yes", "H9": "yes", "H10": "yes",
        "A1": ["none"], "A2": ["none"], "A13": "no", "A15": "yes"
    }
    case_4 = dict(base, P6="less_than_5")
    res_4 = evaluate_ichd3_screening(case_4)
    assert res_4.outcome == ScreeningOutcome.CRITERIA_NOT_MET

    case_5 = dict(base, P6="five_or_more")
    res_5 = evaluate_ichd3_screening(case_5)
    assert res_5.outcome == ScreeningOutcome.CRITERIA_MET_MIGRAINE_WITHOUT_AURA

def test_boundary_duration():
    """Untreated duration <4h or >72h fails Criterion B for migraine without aura."""
    base = {
        "E1": "no", "E2": "no", "E3": "no", "E4": "no",
        "E5": "no", "E6": "no", "E7": "no", "E8": "no",
        "P6": "five_or_more", "H3": "one_sided", "H4": "throbbing_pulsating",
        "H5": "severe", "H6": "yes", "H7": "yes", "H9": "yes", "H10": "yes",
        "A1": ["none"], "A2": ["none"], "A13": "no", "A15": "yes"
    }
    res_under_4 = evaluate_ichd3_screening(dict(base, H1="less_than_4h"))
    assert res_under_4.outcome == ScreeningOutcome.CRITERIA_NOT_MET

    res_over_72 = evaluate_ichd3_screening(dict(base, H1="more_than_72h"))
    assert res_over_72.outcome == ScreeningOutcome.CRITERIA_NOT_MET

    res_4_to_72 = evaluate_ichd3_screening(dict(base, H1="4_to_72h"))
    assert res_4_to_72.outcome == ScreeningOutcome.CRITERIA_MET_MIGRAINE_WITHOUT_AURA

def test_insufficient_information_on_unknown():
    """When key questions are answered 'unknown', return INSUFFICIENT_INFORMATION."""
    answers = {
        "E1": "no", "E2": "no", "E3": "no", "E4": "no",
        "E5": "no", "E6": "no", "E7": "no", "E8": "no",
        "P6": "unknown",
        "H1": "unknown",
        "H3": "unknown",
        "H4": "throbbing_pulsating",
        "H5": "moderate",
        "A13": "no"
    }
    result = evaluate_ichd3_screening(answers)
    assert result.outcome == ScreeningOutcome.INSUFFICIENT_INFORMATION
    assert len(result.missing_items) > 0

def test_kaggle_feature_export_structure():
    """Verifies that export_kaggle_features outputs all required columns exactly."""
    answers = {
        "P1": 35, "H1": "4_to_72h", "H2": 8, "H3": "one_sided", "H4": "throbbing_pulsating",
        "H5": "severe", "H7": "yes", "H8": "no", "H9": "yes", "H10": "yes",
        "A1": ["zigzag_lines", "flashing_lights"], "A2": ["spreading_tingling"],
        "A3": "no", "A4": "no", "A5": "no", "A6": "no", "A7": "no", "A8": "no",
        "A9": "no", "A10": "no", "A11": "no", "A12": "no", "F1": "yes"
    }
    feats = export_kaggle_features(answers, confirmed_doctor_type="Migraine without aura")
    expected_cols = [
        "Age", "Duration", "Frequency", "Location", "Character", "Intensity",
        "Nausea", "Vomit", "Phonophobia", "Photophobia", "Visual", "Sensory",
        "Dysphasia", "Dysarthria", "Vertigo", "Tinnitus", "Hypoacusis",
        "Diplopia", "Defect", "Ataxia", "Conscience", "Paresthesia", "DPF", "Type"
    ]
    for col in expected_cols:
        assert col in feats, f"Missing column {col} in Kaggle export"
    assert feats["Age"] == 35
    assert feats["Location"] == 1
    assert feats["Visual"] == 2
    assert feats["Sensory"] == 1
    assert feats["Type"] == "Migraine without aura"
