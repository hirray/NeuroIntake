"""
Unit Tests for Dialogue Engine & State Machine
==============================================
Verifies state progression, skips, back commands, unknown inputs,
red-flag immediate stop flow, echo confirmation, and language switching.
"""
import pytest
from backend.app.dialogue.engine import DialogueEngine
from backend.app.dialogue.state import SessionState

@pytest.fixture
def engine():
    return DialogueEngine()

def test_initial_prompt(engine):
    state = SessionState(session_id="TEST01", language="en")
    msg = engine.build_question_prompt(state, include_ack=False)
    assert msg.question_id == "E1"
    assert "thunderclap" in msg.text.lower() or "suddenly" in msg.text.lower()
    assert len(msg.options) == 3 # Yes, No, I don't know

def test_red_flag_positive_stops_interview(engine):
    state = SessionState(session_id="TEST02", language="en")
    # Patient answers yes to E1
    msg = engine.process_message(state, user_input="yes", input_mode="tap", selected_code="yes")
    assert msg.is_red_flag_alert is True
    assert state.status == "urgent_red_flag"
    assert "E1" in state.red_flag_codes
    assert "URGENT MEDICAL ATTENTION" in msg.text

def test_normal_advancement_and_history(engine):
    state = SessionState(session_id="TEST03", language="en")
    # Answer E1 with "no"
    msg1 = engine.process_message(state, user_input="no", selected_code="no")
    assert state.current_question_id == "E2"
    assert "E1" in state.question_history
    assert state.answers["E1"].value == "no"

    # Answer E2 with "no"
    msg2 = engine.process_message(state, user_input="no", selected_code="no")
    assert state.current_question_id == "E3"
    assert "E2" in state.question_history

def test_go_back_command(engine):
    state = SessionState(session_id="TEST04", language="en")
    engine.process_message(state, user_input="no", selected_code="no") # Answers E1
    assert state.current_question_id == "E2"

    # Now patient says "go back"
    msg_back = engine.process_message(state, user_input="go back", input_mode="type")
    assert state.current_question_id == "E1"
    assert "E1" not in state.answers # removed to re-answer
    assert state.data_quality.corrections_count == 1

def test_unknown_answer_handling(engine):
    state = SessionState(session_id="TEST05", language="en")
    msg = engine.process_message(state, user_input="I don't know", input_mode="type")
    assert state.current_question_id == "E2"
    assert state.answers["E1"].value == "unknown"
    assert state.data_quality.unknown_count == 1

def test_voice_input_triggers_echo_confirmation(engine):
    state = SessionState(session_id="TEST06", language="en")
    # Voice input for E1: "No"
    msg = engine.process_message(state, user_input="no", input_mode="voice")
    assert msg.needs_confirmation is True
    assert state.pending_confirmation is not None
    assert "I understood" in msg.text

    # User confirms with "yes"
    msg_confirmed = engine.process_message(state, user_input="yes", input_mode="tap", selected_code="yes")
    assert state.pending_confirmation is None
    assert state.current_question_id == "E2"
    assert state.answers["E1"].value == "no"

def test_skip_logic_for_male_gender(engine):
    """P2=male should skip F7 (menstrual related)."""
    state = SessionState(session_id="TEST07", language="en")
    # Set P2 answer as male
    state.current_question_id = "F6"
    from backend.app.dialogue.state import AnswerRecord
    state.answers["P2"] = AnswerRecord(question_id="P2", value="male", raw_text="Male")

    # When F6 is answered, next question should be F8, skipping F7
    engine.process_message(state, user_input="stress", selected_code=["stress"])
    assert state.current_question_id == "F8"
