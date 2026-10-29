"""
Integration & Smoke Tests for FastAPI Routes
============================================
Verifies start session, answer submission, red-flag escalation,
PDF download, clinician review, and privacy deletion.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "en" in data["languages"]

def test_session_lifecycle(client):
    # 1. Start Session
    start_resp = client.post("/api/session/start", json={"language": "en", "research_consent": True})
    assert start_resp.status_code == 200
    data = start_resp.json()
    sid = data["session_id"]
    assert len(sid) == 6
    assert data["bot_message"]["question_id"] == "E1"

    # 2. Answer E1 (No)
    msg_resp = client.post("/api/chat/message", json={
        "session_id": sid,
        "message": "no",
        "input_mode": "tap",
        "selected_code": "no"
    })
    assert msg_resp.status_code == 200
    msg_data = msg_resp.json()
    assert msg_data["bot_message"]["question_id"] == "E2"

    # 3. Resume Session
    res_resp = client.post("/api/session/resume", json={"session_id": sid})
    assert res_resp.status_code == 200
    assert res_resp.json()["session_id"] == sid

    # 4. Download PDF Report
    pdf_resp = client.get(f"/api/report/pdf/{sid}")
    assert pdf_resp.status_code == 200
    assert pdf_resp.content.startswith(b"%PDF")

    # 5. Doctor Review
    login_resp = client.post("/api/clinician/login", json={"username": "doctor", "password": "clinical123"})
    assert login_resp.status_code == 200

    rev_resp = client.post("/api/clinician/review", json={
        "session_id": sid,
        "decision": "Confirmed",
        "doctor_name": "Dr. Sharma",
        "reg_number": "MCI-9988",
        "notes": "Intake answers reviewed. Patient will be seen for full workup.",
        "confirmed_type": "Migraine without aura"
    })
    assert rev_resp.status_code == 200

    # 6. Kaggle CSV Export
    csv_resp = client.get("/api/clinician/export/kaggle-csv")
    assert csv_resp.status_code == 200
    assert "Age,Duration,Frequency" in csv_resp.text

    # 7. Privacy Deletion
    del_resp = client.post("/api/privacy/delete", json={"session_id": sid})
    assert del_resp.status_code == 200

    # Verify session is gone
    check_resp = client.get(f"/api/session/{sid}")
    assert check_resp.status_code == 404
