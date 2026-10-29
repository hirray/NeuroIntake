"""
Database Setup & Field-Level Encryption
========================================
Uses SQLite with Fernet encryption for patient symptom answers.
No unencrypted clinical answers stored at rest.
"""
import os
import base64
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from cryptography.fernet import Fernet
from .config import settings

DB_FILE = os.path.join(os.path.dirname(__file__), "migraine_intake.db")
DATABASE_URL = f"sqlite:///{DB_FILE}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_fernet_cipher() -> Fernet:
    """Derives a 32-byte Fernet key safely from settings."""
    raw_key = settings.DATA_ENCRYPTION_KEY.encode("utf-8")
    if len(raw_key) == 44:
        try:
            return Fernet(raw_key)
        except Exception:
            pass
    # Generate stable key from secret
    padded = settings.SECRET_KEY.ljust(32)[:32].encode("utf-8")
    key = base64.urlsafe_b64encode(padded)
    return Fernet(key)

_cipher = get_fernet_cipher()

def encrypt_data(plaintext: str) -> str:
    if not plaintext:
        return ""
    return _cipher.encrypt(plaintext.encode("utf-8")).decode("utf-8")

def decrypt_data(ciphertext: str) -> str:
    if not ciphertext:
        return ""
    try:
        return _cipher.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except Exception:
        return ciphertext

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
