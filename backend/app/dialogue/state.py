"""
Dialogue Session State & Data Quality Tracking
===============================================
Tracks interview progression, history for 'go back', data quality statistics,
and pending echo-confirmations.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import datetime

class AnswerRecord(BaseModel):
    question_id: str
    value: Any                          # Coded representation (e.g. "yes", "4_to_72h", 25, ["zigzag_lines"])
    raw_text: str                       # Raw user typed or spoken transcript
    english_translation: Optional[str] = None # For free text in non-English
    input_mode: str = "tap"             # "tap", "voice", "type"
    confidence: float = 1.0
    confirmed: bool = True
    language: str = "en"
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

class PendingConfirmation(BaseModel):
    question_id: str
    tentative_value: Any
    display_value: str
    raw_text: str
    input_mode: str
    confidence: float

class DataQuality(BaseModel):
    corrections_count: int = 0
    unknown_count: int = 0
    voice_count: int = 0
    typed_count: int = 0
    tap_count: int = 0

class SessionState(BaseModel):
    session_id: str
    language: str = "en"
    current_question_id: str = "E1"
    question_index: int = 0
    total_applicable_questions: int = 35
    status: str = "in_progress"         # "in_progress", "urgent_red_flag", "completed", "paused"
    answers: Dict[str, AnswerRecord] = Field(default_factory=dict)
    question_history: List[str] = Field(default_factory=list)
    pending_confirmation: Optional[PendingConfirmation] = None
    research_consent: bool = False
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    data_quality: DataQuality = Field(default_factory=DataQuality)
    red_flag_codes: List[str] = Field(default_factory=list)
    red_flag_reasons: List[str] = Field(default_factory=list)
