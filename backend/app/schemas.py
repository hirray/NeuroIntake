"""
Pydantic API Schemas
====================
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from .dialogue.engine import BotMessage, LocalizedOption

class StartSessionRequest(BaseModel):
    language: str = "en"
    research_consent: bool = False

class ResumeSessionRequest(BaseModel):
    session_id: str

class SendMessageRequest(BaseModel):
    session_id: str
    message: str = ""
    input_mode: str = "tap"     # tap, voice, type
    selected_code: Optional[Any] = None

class ChangeLanguageRequest(BaseModel):
    session_id: str
    language: str               # en, hi, gu

class DoctorLoginRequest(BaseModel):
    username: str
    password: str

class DoctorReviewRequest(BaseModel):
    session_id: str
    decision: str               # Confirmed, Modified, Not agreed
    doctor_name: str
    reg_number: str
    notes: str
    confirmed_type: Optional[str] = None

class DeleteSessionRequest(BaseModel):
    session_id: str

class SessionDetailResponse(BaseModel):
    session_id: str
    language: str
    status: str
    current_question_id: str
    progress_percentage: int
    research_consent: bool
    created_at: str
    updated_at: str
    is_urgent: bool
    has_review: bool
    review_details: Optional[Dict[str, Any]] = None
    answers: Dict[str, Any]
    last_bot_message: Optional[BotMessage] = None
