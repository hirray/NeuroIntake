"""
Chat & Dialogue API Routes
===========================
Processes patient user input (text, speech transcript, button tap) and returns bot responses.
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db, encrypt_data
from ..models import IntakeSessionModel, AuditLogModel
from ..schemas import SendMessageRequest
from ..dialogue.state import SessionState
from ..dialogue.engine import DialogueEngine

router = APIRouter(prefix="/api/chat", tags=["Chat"])
engine = DialogueEngine()

@router.post("/message")
def send_message(req: SendMessageRequest, db: Session = Depends(get_db)):
    sid = req.session_id.strip().upper()
    row = db.query(IntakeSessionModel).filter(IntakeSessionModel.session_id == sid).first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found.")

    state_dict = json.loads(row.state_json)
    state = SessionState(**state_dict)

    # Process message through deterministic dialogue engine
    bot_msg = engine.process_message(
        state=state,
        user_input=req.message,
        input_mode=req.input_mode,
        selected_code=req.selected_code
    )

    # Update database
    row.status = state.status
    row.state_json = state.model_dump_json()

    answers_raw = {k: v.model_dump() for k, v in state.answers.items()}
    row.encrypted_answers = encrypt_data(json.dumps(answers_raw))

    # Audit log
    audit_detail = f"InputMode: {req.input_mode}, QID: {bot_msg.question_id}, Status: {state.status}"
    audit = AuditLogModel(session_id=sid, action="answer_recorded", details=audit_detail)
    db.add(audit)
    db.commit()

    return {
        "session_id": sid,
        "status": state.status,
        "bot_message": bot_msg,
        "data_quality": state.data_quality.model_dump()
    }
