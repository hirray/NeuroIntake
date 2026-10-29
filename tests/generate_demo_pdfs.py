"""
Generate Demo PDFs across outcomes and languages
================================================
Generates:
1. demo_reports/migraine_without_aura_draft_en.pdf
2. demo_reports/migraine_with_aura_reviewed_hi.pdf
3. demo_reports/urgent_red_flag_gu.pdf
"""
import os
from backend.app.dialogue.state import SessionState, AnswerRecord
from backend.app.dialogue.engine import DialogueEngine
from backend.app.report.pdf import build_pdf_report

def main():
    out_dir = os.path.join(os.path.dirname(__file__), "..", "demo_reports")
    os.makedirs(out_dir, exist_ok=True)
    engine = DialogueEngine()

    # 1. English - Migraine Without Aura (Draft)
    s1 = SessionState(session_id="DEMO01", language="en")
    for q in ["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"]:
        s1.answers[q] = AnswerRecord(question_id=q, value="no", raw_text="No")
    s1.answers["P1"] = AnswerRecord(question_id="P1", value=34, raw_text="34")
    s1.answers["P2"] = AnswerRecord(question_id="P2", value="female", raw_text="Female")
    s1.answers["P6"] = AnswerRecord(question_id="P6", value="five_or_more", raw_text="5 or more")
    s1.answers["H1"] = AnswerRecord(question_id="H1", value="4_to_72h", raw_text="12 to 24 hours")
    s1.answers["H2"] = AnswerRecord(question_id="H2", value=4, raw_text="4")
    s1.answers["H3"] = AnswerRecord(question_id="H3", value="one_sided", raw_text="One side only")
    s1.answers["H4"] = AnswerRecord(question_id="H4", value="throbbing_pulsating", raw_text="Throbbing")
    s1.answers["H5"] = AnswerRecord(question_id="H5", value="severe", raw_text="Severe")
    s1.answers["H6"] = AnswerRecord(question_id="H6", value="yes", raw_text="Yes")
    s1.answers["H7"] = AnswerRecord(question_id="H7", value="yes", raw_text="Yes")
    s1.answers["H9"] = AnswerRecord(question_id="H9", value="yes", raw_text="Yes")
    s1.answers["H10"] = AnswerRecord(question_id="H10", value="yes", raw_text="Yes")
    s1.answers["A13"] = AnswerRecord(question_id="A13", value="no", raw_text="No")
    s1.answers["A15"] = AnswerRecord(question_id="A15", value="yes", raw_text="Yes")
    s1.answers["F1"] = AnswerRecord(question_id="F1", value="yes", raw_text="Yes, mother")
    s1.answers["F5"] = AnswerRecord(question_id="F5", value="no", raw_text="No")

    pdf1 = build_pdf_report(s1, engine.question_map, doctor_review=None)
    with open(os.path.join(out_dir, "migraine_without_aura_draft_en.pdf"), "wb") as f:
        f.write(pdf1)
    print("Generated demo_reports/migraine_without_aura_draft_en.pdf")

    # 2. Hindi - Migraine with Typical Aura (Doctor Reviewed)
    s2 = SessionState(session_id="DEMO02", language="hi")
    for q in ["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"]:
        s2.answers[q] = AnswerRecord(question_id=q, value="no", raw_text="नहीं")
    s2.answers["P1"] = AnswerRecord(question_id="P1", value=29, raw_text="२९")
    s2.answers["P6"] = AnswerRecord(question_id="P6", value="five_or_more", raw_text="५ से अधिक")
    s2.answers["H1"] = AnswerRecord(question_id="H1", value="4_to_72h", raw_text="८ घंटे")
    s2.answers["H3"] = AnswerRecord(question_id="H3", value="one_sided", raw_text="एक तरफ")
    s2.answers["H4"] = AnswerRecord(question_id="H4", value="throbbing_pulsating", raw_text="धड़कने जैसा")
    s2.answers["H5"] = AnswerRecord(question_id="H5", value="moderate", raw_text="मध्यम")
    s2.answers["H6"] = AnswerRecord(question_id="H6", value="yes", raw_text="हाँ")
    s2.answers["H7"] = AnswerRecord(question_id="H7", value="yes", raw_text="हाँ")
    s2.answers["H9"] = AnswerRecord(question_id="H9", value="yes", raw_text="हाँ")
    s2.answers["H10"] = AnswerRecord(question_id="H10", value="yes", raw_text="हाँ")
    s2.answers["A1"] = AnswerRecord(question_id="A1", value=["zigzag_lines", "flashing_lights"], raw_text="जिग-जैग रेखाएं और रोशनी")
    s2.answers["A2"] = AnswerRecord(question_id="A2", value=["spreading_tingling"], raw_text="झुनझुनी")
    s2.answers["A13"] = AnswerRecord(question_id="A13", value="no", raw_text="नहीं")
    s2.answers["A14"] = AnswerRecord(question_id="A14", value="5_to_60min", raw_text="२० मिनट")
    s2.answers["A15"] = AnswerRecord(question_id="A15", value="yes", raw_text="हाँ")
    s2.answers["A16"] = AnswerRecord(question_id="A16", value="yes", raw_text="हाँ")
    s2.answers["A17"] = AnswerRecord(question_id="A17", value="yes", raw_text="हाँ")
    s2.answers["A18"] = AnswerRecord(question_id="A18", value="yes", raw_text="हाँ")
    s2.answers["A19"] = AnswerRecord(question_id="A19", value="yes", raw_text="हाँ")

    doctor_review = {
        "status": "reviewed",
        "decision": "Confirmed",
        "doctor_name": "Dr. R. Sharma, MD Neurologist",
        "reg_number": "MCI-489201",
        "notes": "Classic visual and sensory typical aura preceding throbbing hemicranial headache. Prescribed acute triptan and sleep hygiene guidance.",
        "confirmed_type": "Migraine with typical aura",
        "timestamp": "2026-10-29T11:45:00"
    }

    pdf2 = build_pdf_report(s2, engine.question_map, doctor_review=doctor_review)
    with open(os.path.join(out_dir, "migraine_with_aura_reviewed_hi.pdf"), "wb") as f:
        f.write(pdf2)
    print("Generated demo_reports/migraine_with_aura_reviewed_hi.pdf")

    # 3. Gujarati - Urgent Red Flag Report
    s3 = SessionState(session_id="DEMO03", language="gu")
    s3.status = "urgent_red_flag"
    s3.answers["E1"] = AnswerRecord(question_id="E1", value="yes", raw_text="હા, ૧ મિનિટમાં ભયંકર દુખાવો")
    s3.red_flag_codes.append("E1")
    s3.red_flag_reasons.append("[E1] Thunderclap headache: peak intensity reached in under 1 minute")

    pdf3 = build_pdf_report(s3, engine.question_map, doctor_review=None)
    with open(os.path.join(out_dir, "urgent_red_flag_gu.pdf"), "wb") as f:
        f.write(pdf3)
    print("Generated demo_reports/urgent_red_flag_gu.pdf")

if __name__ == "__main__":
    main()
