"""
Session Management Routes
==========================
Handles anonymous session creation, state resumption, and language switching.
"""
import random
import string
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db, encrypt_data, decrypt_data
from ..models import IntakeSessionModel, AuditLogModel, DoctorReviewModel
from ..schemas import (
    StartSessionRequest, ResumeSessionRequest,
    ChangeLanguageRequest, SessionDetailResponse
)
from ..dialogue.state import SessionState
from ..dialogue.engine import DialogueEngine, BotMessage

router = APIRouter(prefix="/api/session", tags=["Session"])
engine = DialogueEngine()

def generate_session_id(length: int = 6) -> str:
    """Generates user-friendly uppercase alphanumeric participant code (e.g. 'MIG782')."""
    chars = string.ascii_uppercase + string.digits
    # Exclude ambiguous chars like 0, O, 1, I
    clean_chars = [c for c in chars if c not in "0O1I"]
    return "".join(random.choices(clean_chars, k=length))

@router.post("/start")
def start_session(req: StartSessionRequest, db: Session = Depends(get_db)):
    # Generate unique session ID
    for _ in range(10):
        sid = generate_session_id()
        existing = db.query(IntakeSessionModel).filter(IntakeSessionModel.session_id == sid).first()
        if not existing:
            break
    else:
        sid = f"M{random.randint(10000, 99999)}"

    # Create fresh state
    state = SessionState(
        session_id=sid,
        language=req.language,
        research_consent=req.research_consent
    )

    # First question prompt (E1)
    prompt = engine.build_question_prompt(state, include_ack=False)

    # Persist in DB with field-level encryption
    state_json = state.model_dump_json()
    encrypted_ans = encrypt_data(json.dumps({}))

    session_row = IntakeSessionModel(
        session_id=sid,
        language=req.language,
        status="in_progress",
        encrypted_answers=encrypted_ans,
        state_json=state_json,
        research_consent=req.research_consent
    )
    db.add(session_row)

    # Audit log
    audit = AuditLogModel(
        session_id=sid,
        action="session_created",
        details=f"Language: {req.language}, ResearchConsent: {req.research_consent}"
    )
    db.add(audit)
    db.commit()

    return {
        "session_id": sid,
        "language": req.language,
        "status": state.status,
        "bot_message": prompt
    }

@router.post("/resume")
def resume_session(req: ResumeSessionRequest, db: Session = Depends(get_db)):
    sid = req.session_id.strip().upper()
    row = db.query(IntakeSessionModel).filter(IntakeSessionModel.session_id == sid).first()
    if not row:
        raise HTTPException(status_code=404, detail="Session code not found. Please check and try again.")

    state_dict = json.loads(row.state_json)
    state = SessionState(**state_dict)

    if state.status == "urgent_red_flag":
        prompt = engine.build_red_flag_prompt(state, "Previous urgent symptom flagged.")
    elif state.status == "completed":
        prompt = engine.build_completion_prompt(state)
    else:
        state.status = "in_progress"
        prompt = engine.build_question_prompt(state, include_ack=False)

    # Audit log
    audit = AuditLogModel(session_id=sid, action="session_resumed", details=f"Resumed at question {state.current_question_id}")
    db.add(audit)
    db.commit()

    return {
        "session_id": sid,
        "language": state.language,
        "status": state.status,
        "bot_message": prompt,
        "answers": {k: v.value for k, v in state.answers.items()}
    }

@router.post("/language")
def change_language(req: ChangeLanguageRequest, db: Session = Depends(get_db)):
    sid = req.session_id.strip().upper()
    row = db.query(IntakeSessionModel).filter(IntakeSessionModel.session_id == sid).first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found.")

    state_dict = json.loads(row.state_json)
    state = SessionState(**state_dict)
    state.language = req.language
    row.language = req.language

    # Re-render prompt in new language
    if state.status == "urgent_red_flag":
        prompt = engine.build_red_flag_prompt(state, "Urgent safety flag.")
    elif state.status == "completed":
        prompt = engine.build_completion_prompt(state)
    else:
        prompt = engine.build_question_prompt(state, include_ack=False)

    row.state_json = state.model_dump_json()
    db.commit()

    return {
        "session_id": sid,
        "language": state.language,
        "status": state.status,
        "bot_message": prompt
    }

@router.get("/{session_id}")
def get_session_detail(session_id: str, db: Session = Depends(get_db)):
    sid = session_id.strip().upper()
    row = db.query(IntakeSessionModel).filter(IntakeSessionModel.session_id == sid).first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found.")

    state = SessionState(**json.loads(row.state_json))
    review = db.query(DoctorReviewModel).filter(DoctorReviewModel.session_id == sid).first()

    review_info = None
    if review:
        review_info = {
            "decision": review.decision,
            "doctor_name": review.doctor_name,
            "reg_number": review.reg_number,
            "notes": review.notes,
            "confirmed_type": review.confirmed_type,
            "timestamp": review.timestamp.isoformat()
        }

    curr_idx = engine.question_sequence.index(state.current_question_id) if state.current_question_id in engine.question_sequence else len(engine.question_sequence)
    progress = int((curr_idx / len(engine.question_sequence)) * 100)

    return {
        "session_id": sid,
        "language": state.language,
        "status": state.status,
        "current_question_id": state.current_question_id,
        "progress_percentage": progress,
        "research_consent": state.research_consent,
        "created_at": state.created_at,
        "updated_at": state.updated_at,
        "is_urgent": state.status == "urgent_red_flag",
        "has_review": review is not None,
        "review_details": review_info,
        "answers": {k: v.value for k, v in state.answers.items()}
    }
