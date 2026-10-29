"""
Application Settings & Safety Configurations
============================================
"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "MigraineAssist Intake"
    HOST: str = "127.0.0.1"
    PORT: int = 8005
    DEBUG: bool = False
    SECRET_KEY: str = "clinical-intake-secret-key-32-bytes-secure"
    DATA_ENCRYPTION_KEY: str = "dGhpcy1pcy1hLXRlc3QtZmVybmV0LWtleS0zMmJ5dGVzPT0="

    # Clinical Emergency Numbers
    EMERGENCY_NUMBER_PRIMARY: str = "112"
    EMERGENCY_NUMBER_AMBULANCE: str = "108"

    # Clinical Safety Flags
    SHOW_SCREENING_TO_PATIENT: bool = False
    DATA_RETENTION_DAYS: int = 90

    # LLM Settings
    LLM_ENABLED: bool = False
    LLM_PROVIDER: str = "anthropic"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Clinician Authentication (Default doctor credentials for demo/viva)
    CLINICIAN_USERNAME: str = "doctor"
    CLINICIAN_PASSWORD: str = "clinical123"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
