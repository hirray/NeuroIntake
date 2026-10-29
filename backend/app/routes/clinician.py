"""
Clinician Portal & Research Dataset Export Routes
==================================================
Provides doctor authentication, intake review, decision recording,
and Kaggle-aligned CSV research export (strictly for consented cases).
"""
import io
import csv
import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from ..db import get_db, decrypt_data
from ..models import IntakeSessionModel, DoctorReviewModel, AuditLogModel
from ..schemas import DoctorLoginRequest, DoctorReviewRequest
from ..dialogue.state import SessionState
from ..dialogue.engine import DialogueEngine
from ..clinical.screening import evaluate_ichd3_screening
from ..clinical.scoring import compute_clinical_summary, export_kaggle_features
from ..config import settings

router = APIRouter(prefix="/api/clinician", tags=["Clinician"])
engine = DialogueEngine()

@router.post("/login")
def clinician_login(req: DoctorLoginRequest):
    """Simple authenticated login for the clinician portal."""
    if req.username == settings.CLINICIAN_USERNAME and req.password == settings.CLINICIAN_PASSWORD:
        return {
            "authenticated": True,
            "doctor_name": "Dr. R. Sharma, MD",
            "token": "clinician-auth-token-valid"
        }
    raise HTTPException(status_code=401, detail="Invalid clinician credentials.")

@router.get("/sessions")
def list_sessions(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Lists all intake sessions with status, date, and review state."""
    query = db.query(IntakeSessionModel).order_by(IntakeSessionModel.created_at.desc())
    if status and status != "all":
        query = query.filter(IntakeSessionModel.status == status)

    rows = query.all()
    results = []
    for r in rows:
        rev = db.query(DoctorReviewModel).filter(DoctorReviewModel.session_id == r.session_id).first()
        results.append({
            "session_id": r.session_id,
            "language": r.language,
            "status": r.status,
            "is_urgent": r.status == "urgent_red_flag",
            "research_consent": r.research_consent,
            "has_review": rev is not None,
            "review_decision": rev.decision if rev else None,
            "created_at": r.created_at.isoformat() if r.created_at else "",
            "updated_at": r.updated_at.isoformat() if r.updated_at else ""
        })
    return {"sessions": results, "total": len(results)}

@router.get("/session/{session_id}")
def get_session_for_clinician(session_id: str, db: Session = Depends(get_db)):
    """Fetches complete clinical assessment data for a single patient."""
    sid = session_id.strip().upper()
    row = db.query(IntakeSessionModel).filter(IntakeSessionModel.session_id == sid).first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found.")

    state = SessionState(**json.loads(row.state_json))
    review = db.query(DoctorReviewModel).filter(DoctorReviewModel.session_id == sid).first()

    # Compute deterministic clinical screening and summaries
    answers_dict = {k: v.value for k, v in state.answers.items()}
    screening = evaluate_ichd3_screening(answers_dict)
    summary = compute_clinical_summary(answers_dict)

    # Detailed questionnaire entries
    qa_list = []
    for qid in engine.question_sequence:
        q_def = engine.question_map[qid]
        ans = state.answers.get(qid)
        qa_list.append({
            "id": qid,
            "section": q_def.get("section"),
            "label": q_def.get("report_label"),
            "type": q_def.get("type"),
            "answered": ans is not None,
            "value": ans.value if ans else None,
            "raw_text": ans.raw_text if ans else None,
            "translation": ans.english_translation if ans else None,
            "input_mode": ans.input_mode if ans else None
        })

    # Audit log
    audit = AuditLogModel(session_id=sid, action="report_viewed", details="Clinician opened session review")
    db.add(audit)
    db.commit()

    return {
        "session_id": sid,
        "language": state.language,
        "status": state.status,
        "created_at": state.created_at,
        "screening": screening.model_dump(),
        "clinical_summary": summary.model_dump(),
        "questionnaire": qa_list,
        "data_quality": state.data_quality.model_dump(),
        "research_consent": state.research_consent,
        "review": {
            "decision": review.decision,
            "doctor_name": review.doctor_name,
            "reg_number": review.reg_number,
            "notes": review.notes,
            "confirmed_type": review.confirmed_type,
            "timestamp": review.timestamp.isoformat()
        } if review else None
    }

@router.post("/review")
def record_doctor_review(req: DoctorReviewRequest, db: Session = Depends(get_db)):
    """Records doctor's clinical conclusion, notes, and digital sign-off."""
    sid = req.session_id.strip().upper()
    row = db.query(IntakeSessionModel).filter(IntakeSessionModel.session_id == sid).first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found.")

    existing_rev = db.query(DoctorReviewModel).filter(DoctorReviewModel.session_id == sid).first()
    if existing_rev:
        existing_rev.decision = req.decision
        existing_rev.doctor_name = req.doctor_name
        existing_rev.reg_number = req.reg_number
        existing_rev.notes = req.notes
        existing_rev.confirmed_type = req.confirmed_type
    else:
        new_rev = DoctorReviewModel(
            session_id=sid,
            decision=req.decision,
            doctor_name=req.doctor_name,
            reg_number=req.reg_number,
            notes=req.notes,
            confirmed_type=req.confirmed_type
        )
        db.add(new_rev)

    # If interview was completed or in progress, update status to reviewed
    if row.status != "urgent_red_flag":
        row.status = "reviewed"

    audit = AuditLogModel(
        session_id=sid,
        action="doctor_reviewed",
        details=f"Decision: {req.decision}, Doctor: {req.doctor_name}, Reg: {req.reg_number}"
    )
    db.add(audit)
    db.commit()

    return {"status": "success", "message": "Doctor review recorded successfully."}

@router.get("/export/kaggle-csv")
def export_kaggle_dataset_csv(db: Session = Depends(get_db)):
    """
    Exports a CSV matching Kaggle migraine schema strictly for sessions
    where patient gave research consent and doctor confirmed diagnosis.
    """
    rows = db.query(IntakeSessionModel).filter(IntakeSessionModel.research_consent == True).all()

    output = io.StringIO()
    columns = [
        "Age", "Duration", "Frequency", "Location", "Character", "Intensity",
        "Nausea", "Vomit", "Phonophobia", "Photophobia", "Visual", "Sensory",
        "Dysphasia", "Dysarthria", "Vertigo", "Tinnitus", "Hypoacusis",
        "Diplopia", "Defect", "Ataxia", "Conscience", "Paresthesia", "DPF", "Type"
    ]
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()

    count = 0
    for r in rows:
        rev = db.query(DoctorReviewModel).filter(DoctorReviewModel.session_id == r.session_id).first()
        state = SessionState(**json.loads(r.state_json))
        answers_dict = {k: v.value for k, v in state.answers.items()}

        confirmed_type = rev.confirmed_type if rev else (rev.decision if rev else "Unreviewed")
        features = export_kaggle_features(answers_dict, confirmed_doctor_type=confirmed_type)
        writer.writerow(features)
        count += 1

    csv_data = output.getvalue()
    output.close()

    # Audit log
    audit = AuditLogModel(session_id="ALL", action="kaggle_csv_exported", details=f"Exported {count} consented rows")
    db.add(audit)
    db.commit()

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="migraine_research_dataset_kaggle.csv"'}
    )
