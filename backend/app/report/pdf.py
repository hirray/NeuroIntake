"""
Clinical PDF Report Generator (ReportLab with Multilingual Indic Fonts)
========================================================================
Design:
- A4 size, crisp, high-contrast, black-and-white printable
- Prominent "DRAFT – PENDING DOCTOR REVIEW" banner until doctor signs
- Digital "REVIEWED" status stamp with doctor details upon sign-off
- Embedded Noto Sans, Noto Sans Devanagari, and Noto Sans Gujarati fonts
- QR code for clinician portal access
- Complete questionnaire table with original-language transcript and machine translation
"""
import os
import io
import hashlib
import qrcode
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, Image, HRFlowable
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from ..clinical.screening import evaluate_ichd3_screening, ScreeningOutcome, ScreeningResult
from ..clinical.scoring import compute_clinical_summary
from ..dialogue.state import SessionState

FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

# Register TrueType fonts
_FONTS_REGISTERED = False

def register_indic_fonts():
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return

    font_files = {
        "NotoSans": os.path.join(FONTS_DIR, "NotoSans-Regular.ttf"),
        "NotoSans-Bold": os.path.join(FONTS_DIR, "NotoSans-Bold.ttf"),
        "NotoSansDevanagari": os.path.join(FONTS_DIR, "NotoSansDevanagari-Regular.ttf"),
        "NotoSansDevanagari-Bold": os.path.join(FONTS_DIR, "NotoSansDevanagari-Bold.ttf"),
        "NotoSansGujarati": os.path.join(FONTS_DIR, "NotoSansGujarati-Regular.ttf"),
        "NotoSansGujarati-Bold": os.path.join(FONTS_DIR, "NotoSansGujarati-Bold.ttf"),
    }

    for name, path in font_files.items():
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
            except Exception as e:
                print(f"Warning registering font {name}: {e}")

    _FONTS_REGISTERED = True

def get_font_for_lang(lang: str, bold: bool = False) -> str:
    register_indic_fonts()
    if lang == "hi":
        return "NotoSansDevanagari-Bold" if bold else "NotoSansDevanagari"
    elif lang == "gu":
        return "NotoSansGujarati-Bold" if bold else "NotoSansGujarati"
    return "NotoSans-Bold" if bold else "NotoSans"

class NumberedCanvas(canvas.Canvas):
    """Adds running headers, footers, page numbers and draft banners to all pages."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.is_reviewed = False
        self.report_hash = ""
        self.session_id = ""

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4b5563"))

        # Running Top Header
        self.drawString(40, 810, "MigraineAssist Intake — Clinical Decision Support & Screening Report")
        self.drawRightString(555, 810, f"Participant Code: {self.session_id}")
        self.setStrokeColor(colors.HexColor("#d1d5db"))
        self.setLineWidth(0.5)
        self.line(40, 804, 555, 804)

        # Draft Banner (if not reviewed by doctor)
        if not self.is_reviewed:
            self.saveState()
            self.setFont("Helvetica-Bold", 36)
            self.setFillColor(colors.HexColor("#e5e7eb"), alpha=0.35)
            self.translate(300, 420)
            self.rotate(45)
            self.drawCentredString(0, 0, "DRAFT — PENDING DOCTOR REVIEW")
            self.restoreState()

        # Running Bottom Footer
        self.line(40, 40, 555, 40)
        privacy_note = "CONFIDENTIAL MEDICAL RECORD — Generated for Treating Physician Review Only"
        self.drawString(40, 28, privacy_note)
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(555, 28, page_str)

        # Hash and verification line
        if self.report_hash:
            self.setFont("Helvetica", 6)
            self.drawString(40, 18, f"Audit Hash: {self.report_hash[:24]}... | Not a clinical diagnosis")

        self.restoreState()

def generate_qr_image(data_url: str) -> io.BytesIO:
    qr = qrcode.QRCode(
        version=1,
        box_size=3,
        border=1,
    )
    qr.add_data(data_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def build_pdf_report(
    session_state: SessionState,
    question_map: Dict[str, Any],
    doctor_review: Optional[Dict[str, Any]] = None,
    clinician_url_base: str = "http://localhost:8000/clinician/review",
    for_patient_only: bool = False,
    show_screening_to_patient: bool = False
) -> bytes:
    """
    Builds the complete printable A4 PDF report with criteria tables,
    full questionnaire transcript, doctor review block, and audit hash.
    """
    register_indic_fonts()
    buffer = io.BytesIO()

    # Answers map
    answers_dict = {qid: record.value for qid, record in session_state.answers.items()}
    screening = evaluate_ichd3_screening(answers_dict)
    clinical_summary = compute_clinical_summary(answers_dict)

    # Document setup
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=50
    )

    is_reviewed = doctor_review is not None and doctor_review.get("status") == "reviewed"

    # Compute deterministic report hash
    raw_hash_material = f"{session_state.session_id}_{session_state.created_at}_{is_reviewed}_{answers_dict}"
    report_hash = hashlib.sha256(raw_hash_material.encode("utf-8")).hexdigest()

    # Styles
    base_font = get_font_for_lang("en")
    bold_font = get_font_for_lang("en", bold=True)
    content_font = get_font_for_lang(session_state.language)

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        fontName=bold_font,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#111827"),
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        fontName=base_font,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#4b5563")
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        fontName=bold_font,
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=10,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        "ReportBody",
        fontName=base_font,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1f2937")
    )

    indic_body_style = ParagraphStyle(
        "IndicReportBody",
        fontName=content_font,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1f2937")
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        fontName=bold_font,
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    story = []

    # 1. HEADER & QR CODE
    portal_link = f"{clinician_url_base}/{session_state.session_id}"
    qr_buf = generate_qr_image(portal_link)
    qr_img = Image(qr_buf, width=1.8*cm, height=1.8*cm)

    header_text = [
        Paragraph("MIGRAINEASSIST INTAKE & SCREENING REPORT", title_style),
        Paragraph(
            f"<b>Participant Code:</b> {session_state.session_id} &nbsp;|&nbsp; "
            f"<b>Date/Time:</b> {session_state.created_at[:16].replace('T', ' ')} UTC &nbsp;|&nbsp; "
            f"<b>Language:</b> {session_state.language.upper()} &nbsp;|&nbsp; "
            f"<b>Interviewer:</b> MigraineAssist Intake (automated)",
            subtitle_style
        )
    ]

    header_table = Table([[header_text, qr_img]], colWidths=[435, 80])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))

    # REVIEW STATUS BANNER
    if is_reviewed:
        rev_box = [
            Paragraph(
                f"<b>CLINICIAN REVIEWED:</b> Confirmed by Dr. {doctor_review.get('doctor_name', 'Treating Physician')} "
                f"(Reg No: {doctor_review.get('reg_number', 'N/A')}) on {doctor_review.get('timestamp', '')[:10]}. "
                f"<b>Decision:</b> {doctor_review.get('decision', 'Confirmed')}",
                body_style
            )
        ]
        rev_table = Table([rev_box], colWidths=[515])
        rev_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#dcfce7")),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#166534")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#86efac")),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(rev_table)
    else:
        draft_box = [
            Paragraph(
                "<b>DRAFT — PENDING DOCTOR REVIEW</b><br/>"
                "This report is an automated pre-consultation intake aid. It has NOT yet been verified by a licensed doctor. "
                "Final clinical evaluation and diagnosis rest with the treating physician.",
                body_style
            )
        ]
        draft_table = Table([draft_box], colWidths=[515])
        draft_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fef3c7")),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#92400e")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#fcd34d")),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(draft_table)

    story.append(Spacer(1, 8))

    # 2. URGENT RED FLAG BANNER (if applicable)
    if screening.is_urgent:
        urgent_lines = ["<b>⚠️ URGENT MEDICAL ATTENTION RECOMMENDED</b><br/>"]
        urgent_lines.append("Patient reported acute neurological or systemic red flags requiring prompt emergency evaluation:<br/>")
        for flag in screening.red_flags:
            urgent_lines.append(f"• {flag}<br/>")
        urgent_lines.append("<b>Emergency numbers:</b> National Emergency: 112 | Ambulance: 108")
        urgent_p = Paragraph("".join(urgent_lines), body_style)
        urgent_table = Table([[urgent_p]], colWidths=[515])
        urgent_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fee2e2")),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#991b1b")),
            ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor("#ef4444")),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(urgent_table)
        story.append(Spacer(1, 8))

    # 3. SCREENING RESULT BOX (Clinician View or Patient if enabled)
    if not for_patient_only or show_screening_to_patient:
        story.append(Paragraph("1. Automated ICHD-3 Screening Result (Clinician Aid)", section_heading))

        outcome_colors = {
            ScreeningOutcome.CRITERIA_MET_MIGRAINE_WITHOUT_AURA: ("#eff6ff", "#1d4ed8", "#3b82f6"),
            ScreeningOutcome.CRITERIA_MET_MIGRAINE_WITH_AURA: ("#f5f3ff", "#6d28d9", "#8b5cf6"),
            ScreeningOutcome.FEATURES_NEED_SPECIALIST_REVIEW: ("#fff7ed", "#c2410c", "#f97316"),
            ScreeningOutcome.CRITERIA_NOT_MET: ("#f3f4f6", "#374151", "#9ca3af"),
            ScreeningOutcome.INSUFFICIENT_INFORMATION: ("#fef9c3", "#854d0e", "#eab308"),
            ScreeningOutcome.URGENT_RED_FLAG: ("#fee2e2", "#991b1b", "#ef4444"),
        }
        bg_col, text_col, border_col = outcome_colors.get(screening.outcome, ("#f3f4f6", "#111827", "#d1d5db"))

        result_content = [
            Paragraph(f"<b>Outcome:</b> {screening.outcome.value.replace('_', ' ')}", ParagraphStyle("Outcome", fontName=bold_font, fontSize=11, leading=14, textColor=colors.HexColor(text_col))),
            Paragraph(f"<b>Summary:</b> {screening.summary_text}", body_style),
            Spacer(1, 3),
            Paragraph(f"<i>{screening.doctor_disclaimer}</i>", ParagraphStyle("Disc", fontName=base_font, fontSize=7.5, leading=10, textColor=colors.HexColor("#4b5563")))
        ]

        res_table = Table([[result_content]], colWidths=[515])
        res_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_col)),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor(border_col)),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(res_table)
        story.append(Spacer(1, 8))

        # 4. CRITERIA TABLE
        if screening.criteria_table:
            story.append(Paragraph("2. ICHD-3 Criteria Assessment Table", section_heading))
            crit_rows = [
                [Paragraph("Criterion", table_header_style), Paragraph("Required Threshold", table_header_style), Paragraph("Patient Reported", table_header_style), Paragraph("Status", table_header_style)]
            ]
            for c in screening.criteria_table:
                status_str = "MET" if c.met is True else ("NOT MET" if c.met is False else "UNKNOWN")
                crit_rows.append([
                    Paragraph(f"<b>{c.criterion}</b>", body_style),
                    Paragraph(c.required, body_style),
                    Paragraph(c.patient_answer, body_style),
                    Paragraph(f"<b>{status_str}</b>", body_style)
                ])

            crit_table = Table(crit_rows, colWidths=[130, 160, 155, 70])
            crit_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e3a8a")),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#d1d5db")),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f9fafb")]),
                ('PADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(crit_table)
            story.append(Spacer(1, 8))

    # 5. COMPLETE QUESTIONNAIRE TABLE
    story.append(Paragraph("3. Complete Intake Questionnaire & Patient Responses", section_heading))
    q_rows = [
        [Paragraph("#", table_header_style), Paragraph("Question (English)", table_header_style),
         Paragraph("Patient Answer", table_header_style), Paragraph("Original Transcript / Translation", table_header_style)]
    ]

    def humanise_answer(val) -> str:
        """Convert coded answer values to clean human-readable display strings."""
        if val is None:
            return "—"
        if isinstance(val, list):
            clean = [str(v).replace("_", " ").capitalize() for v in val if str(v).lower() not in ("none", "none_of_the_above")]
            return ", ".join(clean) if clean else "None reported"
        s = str(val)
        if s.lower() in ("skipped", "unknown", "i don't know"):
            return "Not provided"
        return s.replace("_", " ").capitalize()

    for qid, q_def in question_map.items():
        ans_record = session_state.answers.get(qid)
        required = q_def.get("required", True)

        # Skip optional unanswered questions from the table to keep it clean
        if ans_record is None and not required:
            continue

        raw_val = ans_record.value if ans_record else None
        ans_display = humanise_answer(raw_val)

        # Skip rows where the patient explicitly skipped an optional question
        raw_text_val = ans_record.raw_text if ans_record else ""
        if raw_text_val in ("[Skipped]", "") and not required:
            continue

        # Display transcript cleanly
        if not ans_record:
            transcript_str = "Not answered"
        elif raw_text_val in ("[Skipped]",):
            transcript_str = "Question not applicable / skipped"
        else:
            transcript_str = raw_text_val or ans_display

        trans_line = f"<br/><i>EN: {ans_record.english_translation}</i>" if ans_record and ans_record.english_translation else ""

        q_rows.append([
            Paragraph(f"<b>{qid}</b>", body_style),
            Paragraph(q_def.get("report_label", qid), body_style),
            Paragraph(ans_display, body_style),
            Paragraph(f"{transcript_str}{trans_line}", indic_body_style)
        ])

    q_table = Table(q_rows, colWidths=[25, 200, 130, 160])
    q_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e3a8a")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#d1d5db")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f9fafb")]),
        ('PADDING', (0,0), (-1,-1), 3.5),
    ]))
    story.append(q_table)
    story.append(Spacer(1, 8))

    # 6. CLINICAL SUMMARY & LIFESTYLE — professional phrasing
    story.append(Paragraph("4. Clinical Pattern & Lifestyle Summary", section_heading))

    freq_band = clinical_summary.frequency_band if clinical_summary.frequency_band else "Not specified"
    dur_band = clinical_summary.duration_band if clinical_summary.duration_band else "Not specified"
    intensity_desc = clinical_summary.intensity_description if clinical_summary.intensity_description else "Not specified"
    assoc_count = clinical_summary.associated_symptom_count
    aura_list = clinical_summary.aura_symptoms_present
    med_overuse = clinical_summary.medication_overuse_risk
    triggers = clinical_summary.triggers_reported
    ls = clinical_summary.lifestyle_summary

    def ls_val(key, unit=""):
        v = ls.get(key)
        if v is None or str(v) in ("", "None", "0"):
            return "Not provided"
        return f"{v}{unit}"

    summary_text = [
        f"<b>Monthly Headache Frequency:</b> {freq_band}<br/>",
        f"<b>Typical Attack Duration:</b> {dur_band} &nbsp;|&nbsp; <b>Pain Intensity at Peak:</b> {intensity_desc}<br/>",
        f"<b>Associated Symptoms Reported:</b> {assoc_count} of 4 checked (Nausea, Vomiting, Photophobia, Phonophobia)<br/>",
        f"<b>Aura / Neurological Warning Symptoms:</b> {', '.join(aura_list) if aura_list else 'None reported by patient'}<br/>",
        f"<b>Medication Overuse Risk:</b> {'<b>YES</b> — acute medication used on ≥ 10 days/month; MOH should be considered' if med_overuse else 'No overuse pattern detected'}<br/>",
        f"<b>Reported Attack Triggers:</b> {', '.join(triggers) if triggers else 'None identified'}<br/>",
        f"<b>Lifestyle Factors (self-reported):</b> Sleep: {ls_val('sleep_hours', 'h/night')} | Stress: {ls_val('stress_level_0_10', '/10')} | Water: {ls_val('water_liters', ' L/day')} | Caffeine: {ls_val('caffeine_cups', ' cups/day')} | Screen time: {ls_val('screen_hours', 'h/day')}"
    ]
    summary_p = Paragraph("".join(summary_text), body_style)
    summary_table = Table([[summary_p]], colWidths=[515])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 8))

    # 7. DATA QUALITY NOTES
    dq = session_state.data_quality
    dq_text = (
        f"<b>Data Quality Metrics:</b> Answer corrections: {dq.corrections_count} | "
        f"'I don't know' responses: {dq.unknown_count} | "
        f"Input breakdown: {dq.tap_count} button taps, {dq.typed_count} typed, {dq.voice_count} voice utterances."
    )
    story.append(Paragraph(dq_text, subtitle_style))
    story.append(Spacer(1, 8))

    # 8. DOCTOR REVIEW BLOCK (Only in Clinician Report)
    if not for_patient_only:
        story.append(Paragraph("5. Physician Review & Final Clinical Decision", section_heading))
        if is_reviewed:
            dec = doctor_review.get("decision", "Confirmed")
            notes = doctor_review.get("notes", "No additional notes provided.")
            doc_name = doctor_review.get("doctor_name", "Treating Physician")
            reg = doctor_review.get("reg_number", "N/A")
            sign_time = doctor_review.get("timestamp", "")[:19].replace("T", " ")

            doc_block = [
                Paragraph(f"<b>Clinical Decision:</b> [X] {dec.upper()}", body_style),
                Paragraph(f"<b>Physician Impression & Treatment Plan:</b><br/>{notes}", body_style),
                Spacer(1, 4),
                Paragraph(f"<b>Treating Doctor:</b> Dr. {doc_name} &nbsp;|&nbsp; <b>Reg No:</b> {reg} &nbsp;|&nbsp; <b>Signed:</b> {sign_time} UTC (Digital Sign-off)", body_style)
            ]
        else:
            doc_block = [
                Paragraph("<b>Physician Decision:</b> &nbsp;&nbsp; [ &nbsp; ] Confirmed &nbsp;&nbsp;&nbsp;&nbsp; [ &nbsp; ] Modified &nbsp;&nbsp;&nbsp;&nbsp; [ &nbsp; ] Not Agreed", body_style),
                Spacer(1, 4),
                Paragraph("<b>Final Clinical Impression / Differential:</b> ____________________________________________________________________________", body_style),
                Spacer(1, 4),
                Paragraph("<b>Treatment Plan / Investigation:</b> ________________________________________________________________________________", body_style),
                Spacer(1, 6),
                Paragraph("<b>Doctor's Name:</b> _________________________ &nbsp;&nbsp;&nbsp;&nbsp; <b>Reg No:</b> _________________ &nbsp;&nbsp;&nbsp;&nbsp; <b>Signature:</b> _________________ &nbsp;&nbsp;&nbsp;&nbsp; <b>Date:</b> _________", body_style)
            ]

        doc_table = Table([[doc_block]], colWidths=[515])
        doc_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f3f4f6")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#9ca3af")),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(doc_table)

    # Build document
    canvas_maker = lambda *args, **kwargs: NumberedCanvas(*args, is_reviewed=is_reviewed, report_hash=report_hash, session_id=session_state.session_id, **kwargs)
    doc.build(story, canvasmaker=canvas_maker)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
