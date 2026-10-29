"""
Privacy, Security & Data Deletion Routes
=========================================
Implements patient data deletion rights ("Right to be Forgotten")
and access to audit trail.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import IntakeSessionModel, DoctorReviewModel, AuditLogModel
from ..schemas import DeleteSessionRequest

router = APIRouter(prefix="/api/privacy", tags=["Privacy"])

@router.post("/delete")
def delete_patient_data(req: DeleteSessionRequest, db: Session = Depends(get_db)):
    """
    Permanently erases all clinical records, answers, and reviews
    associated with the participant session code.
    """
    sid = req.session_id.strip().upper()
    row = db.query(IntakeSessionModel).filter(IntakeSessionModel.session_id == sid).first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Remove reviews
    db.query(DoctorReviewModel).filter(DoctorReviewModel.session_id == sid).delete()
    # Remove sessions
    db.query(IntakeSessionModel).filter(IntakeSessionModel.session_id == sid).delete()

    # Record final deletion in audit log without storing any clinical answers
    audit = AuditLogModel(
        session_id=sid,
        action="session_deleted",
        details="Patient requested complete data deletion. All clinical answers purged."
    )
    db.add(audit)
    db.commit()

    return {
        "status": "success",
        "message": f"All data associated with session code {sid} has been permanently deleted."
    }

@router.get("/audit/{session_id}")
def get_session_audit_log(session_id: str, db: Session = Depends(get_db)):
    """Returns access audit log for compliance inspection."""
    sid = session_id.strip().upper()
    logs = db.query(AuditLogModel).filter(AuditLogModel.session_id == sid).order_by(AuditLogModel.timestamp.asc()).all()
    return {
        "session_id": sid,
        "logs": [
            {
                "action": l.action,
                "timestamp": l.timestamp.isoformat() if l.timestamp else "",
                "details": l.details
            }
            for l in logs
        ]
    }
