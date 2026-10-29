"""
PDF Report Delivery Routes
===========================
Generates and serves clinical PDF reports for doctors and patients.
"""
import json
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import IntakeSessionModel, DoctorReviewModel, AuditLogModel
from ..dialogue.state import SessionState
from ..dialogue.engine import DialogueEngine
from ..report.pdf import build_pdf_report
from ..config import settings

router = APIRouter(prefix="/api/report", tags=["Report"])
engine = DialogueEngine()

@router.get("/pdf/{session_id}")
def download_pdf_report(
    session_id: str,
    for_patient: bool = Query(False),
    db: Session = Depends(get_db)
):
    sid = session_id.strip().upper()
    row = db.query(IntakeSessionModel).filter(IntakeSessionModel.session_id == sid).first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found.")

    state = SessionState(**json.loads(row.state_json))
    review_row = db.query(DoctorReviewModel).filter(DoctorReviewModel.session_id == sid).first()

    doctor_review_dict = None
    if review_row:
        doctor_review_dict = {
            "status": "reviewed",
            "decision": review_row.decision,
            "doctor_name": review_row.doctor_name,
            "reg_number": review_row.reg_number,
            "notes": review_row.notes,
            "confirmed_type": review_row.confirmed_type,
            "timestamp": review_row.timestamp.isoformat()
        }

    # Generate PDF bytes
    pdf_bytes = build_pdf_report(
        session_state=state,
        question_map=engine.question_map,
        doctor_review=doctor_review_dict,
        for_patient_only=for_patient,
        show_screening_to_patient=settings.SHOW_SCREENING_TO_PATIENT
    )

    # Audit log
    audit_action = "patient_report_downloaded" if for_patient else "doctor_report_downloaded"
    audit = AuditLogModel(session_id=sid, action=audit_action, details=f"Size: {len(pdf_bytes)} bytes")
    db.add(audit)
    db.commit()

    filename = f"MigraineAssist_Patient_Summary_{sid}.pdf" if for_patient else f"MigraineAssist_Clinical_Report_{sid}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
    )
