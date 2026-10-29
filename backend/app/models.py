"""
SQLAlchemy Database Models
===========================
"""
import datetime
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base

class IntakeSessionModel(Base):
    __tablename__ = "intake_sessions"

    session_id = Column(String(10), primary_key=True, index=True)
    language = Column(String(5), default="en", nullable=False)
    status = Column(String(25), default="in_progress", nullable=False) # in_progress, urgent_red_flag, completed, paused
    encrypted_answers = Column(Text, nullable=True)                    # Field-level encrypted JSON
    state_json = Column(Text, nullable=False)                          # Serialized SessionState
    research_consent = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    review = relationship("DoctorReviewModel", back_populates="session", uselist=False, cascade="all, delete-orphan")

class DoctorReviewModel(Base):
    __tablename__ = "doctor_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(10), ForeignKey("intake_sessions.session_id", ondelete="CASCADE"), unique=True, nullable=False)
    decision = Column(String(30), nullable=False)                     # Confirmed, Modified, Not agreed
    doctor_name = Column(String(100), nullable=False)
    reg_number = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)
    confirmed_type = Column(String(100), nullable=True)                # Diagnosis type for research dataset
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    session = relationship("IntakeSessionModel", back_populates="review")

class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(10), index=True, nullable=True)
    action = Column(String(50), nullable=False)                       # session_created, answer_saved, report_viewed, doctor_reviewed, session_deleted
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
