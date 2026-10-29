"""
MigraineAssist Intake — FastAPI Main Application
=================================================
Clinical Intake & Screening Assistant with Multilingual Support.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import engine, Base
from .routes import session, chat, report, clinician, privacy

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MigraineAssist Intake API",
    description="Multilingual Voice-Enabled Clinical Intake Chatbot & ICHD-3 Screening Aid",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(session.router)
app.include_router(chat.router)
app.include_router(report.router)
app.include_router(clinician.router)
app.include_router(privacy.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "llm_enabled": settings.LLM_ENABLED,
        "languages": ["en", "hi", "gu"],
        "emergency_number": settings.EMERGENCY_NUMBER_PRIMARY
    }

# Mount static frontend build if present
FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
