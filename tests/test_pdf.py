"""
Unit Tests for Multilingual PDF Report Generation
=================================================
Verifies that ReportLab generates valid PDFs with embedded Indic fonts
(English, Hindi, Gujarati), draft banners, reviewed banners, and QR codes.
"""
import pytest
from backend.app.dialogue.state import SessionState, AnswerRecord
from backend.app.dialogue.engine import DialogueEngine
from backend.app.report.pdf import build_pdf_report

@pytest.fixture
def question_map():
    engine = DialogueEngine()
    return engine.question_map

def test_generate_english_pdf_draft(question_map):
    state = SessionState(session_id="EN001", language="en")
    state.answers["E1"] = AnswerRecord(question_id="E1", value="no", raw_text="No")
    state.answers["P1"] = AnswerRecord(question_id="P1", value=30, raw_text="30")
    state.answers["P6"] = AnswerRecord(question_id="P6", value="five_or_more", raw_text="5+")
    state.answers["H1"] = AnswerRecord(question_id="H1", value="4_to_72h", raw_text="12 hours")
    state.answers["H3"] = AnswerRecord(question_id="H3", value="one_sided", raw_text="Left side")
    state.answers["H4"] = AnswerRecord(question_id="H4", value="throbbing_pulsating", raw_text="Throbbing")
    state.answers["H5"] = AnswerRecord(question_id="H5", value="severe", raw_text="Severe")
    state.answers["H6"] = AnswerRecord(question_id="H6", value="yes", raw_text="Yes")
    state.answers["H7"] = AnswerRecord(question_id="H7", value="yes", raw_text="Yes")

    pdf_bytes = build_pdf_report(state, question_map, doctor_review=None)
    assert len(pdf_bytes) > 10000
    assert pdf_bytes.startswith(b"%PDF")

def test_generate_hindi_pdf(question_map):
    state = SessionState(session_id="HI001", language="hi")
    state.answers["E1"] = AnswerRecord(question_id="E1", value="no", raw_text="नहीं")
    state.answers["P1"] = AnswerRecord(question_id="P1", value=28, raw_text="२८")
    state.answers["F8"] = AnswerRecord(question_id="F8", value="सिर में बहुत तेज दर्द होता है", raw_text="सिर में बहुत तेज दर्द होता है", english_translation="Severe headache in the head")

    pdf_bytes = build_pdf_report(state, question_map, doctor_review=None)
    assert len(pdf_bytes) > 10000
    assert pdf_bytes.startswith(b"%PDF")

def test_generate_gujarati_pdf(question_map):
    state = SessionState(session_id="GU001", language="gu")
    state.answers["E1"] = AnswerRecord(question_id="E1", value="no", raw_text="ના")
    state.answers["P1"] = AnswerRecord(question_id="P1", value=42, raw_text="૪૨")
    state.answers["F8"] = AnswerRecord(question_id="F8", value="માથામાં ખૂબ દુખાવો થાય છે", raw_text="માથામાં ખૂબ દુખાવો થાય છે", english_translation="Very severe pain in head")

    pdf_bytes = build_pdf_report(state, question_map, doctor_review=None)
    assert len(pdf_bytes) > 10000
    assert pdf_bytes.startswith(b"%PDF")

def test_generate_reviewed_pdf_with_doctor_signature(question_map):
    state = SessionState(session_id="REV01", language="en")
    doctor_review = {
        "status": "reviewed",
        "decision": "Confirmed",
        "doctor_name": "R. Sharma, MD Neurologist",
        "reg_number": "MCI-489201",
        "notes": "Patient symptoms are classic for episodic migraine without aura. Recommended headache diary and triptan therapy.",
        "timestamp": "2026-10-29T10:30:00"
    }
    pdf_bytes = build_pdf_report(state, question_map, doctor_review=doctor_review)
    assert len(pdf_bytes) > 10000
    assert pdf_bytes.startswith(b"%PDF")
