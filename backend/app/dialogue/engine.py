"""
Deterministic Dialogue Engine
==============================
Strict deterministic state machine walking the question bank.
Safety Rules:
- The engine, NOT the LLM, decides the question flow.
- Red flags checked on every input and spontaneous utterance.
- Parallel input methods: buttons, typing, voice.
- Echo-style confirmation for voice and low-confidence inputs.
- Non-diagnostic neutral patient tone.
"""
import os
import yaml
import random
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel

from .state import SessionState, AnswerRecord, PendingConfirmation
from .parsers import (
    parse_special_command,
    parse_yes_no,
    parse_number,
    parse_duration,
    match_choice_option,
    normalize_text
)
from ..clinical.redflags import (
    evaluate_red_flags,
    check_immediate_escalation,
    RED_FLAG_DESCRIPTIONS
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

class LocalizedOption(BaseModel):
    code: Any
    label: str

class BotMessage(BaseModel):
    text: str
    speech_text: Optional[str] = None
    question_id: Optional[str] = None
    question_type: Optional[str] = None
    options: List[LocalizedOption] = []
    is_red_flag_alert: bool = False
    is_completed: bool = False
    progress_percentage: int = 0
    needs_confirmation: bool = False
    confirmation_value: Optional[str] = None
    acknowledgement: Optional[str] = None
    review_status_warning: Optional[str] = None

class DialogueEngine:
    def __init__(self):
        # Load Question Bank
        qb_path = os.path.join(CURRENT_DIR, "question_bank.yaml")
        with open(qb_path, "r", encoding="utf-8") as f:
            qb_data = yaml.safe_load(f)
            self.questions = qb_data["questions"]
            self.question_map = {q["id"]: q for q in self.questions}
            self.question_sequence = [q["id"] for q in self.questions]

        # Load Glossary
        gl_path = os.path.join(CURRENT_DIR, "glossary.yaml")
        with open(gl_path, "r", encoding="utf-8") as f:
            self.glossary = yaml.safe_load(f).get("terms", {})

        # Load i18n
        self.i18n: Dict[str, Dict[str, Any]] = {}
        for lang in ["en", "hi", "gu"]:
            lang_path = os.path.join(BACKEND_DIR, "i18n", f"{lang}.yaml")
            if os.path.exists(lang_path):
                with open(lang_path, "r", encoding="utf-8") as f:
                    self.i18n[lang] = yaml.safe_load(f)

    def get_i18n(self, lang: str) -> Dict[str, Any]:
        return self.i18n.get(lang, self.i18n.get("en", {}))

    def get_next_question_id(self, state: SessionState) -> Optional[str]:
        """Finds next applicable question based on skip_if conditions."""
        current_id = state.current_question_id
        if current_id not in self.question_sequence:
            return self.question_sequence[0]

        curr_idx = self.question_sequence.index(current_id)
        for next_id in self.question_sequence[curr_idx + 1:]:
            q_def = self.question_map[next_id]
            # Check skip_if condition
            skip_rule = q_def.get("skip_if")
            if skip_rule:
                field = skip_rule.get("field")
                target_val = skip_rule.get("equals")
                if field and target_val:
                    ans_record = state.answers.get(field)
                    if ans_record:
                        ans_val = str(ans_record.value).lower()
                        if ans_val == str(target_val).lower():
                            continue # Skip this question
            return next_id
        return None # All questions completed

    def check_glossary_query(self, text: str, lang: str) -> Optional[str]:
        """Checks if patient is asking about the meaning of a clinical term."""
        t = normalize_text(text)
        if any(w in t for w in ["what is", "what does", "meaning", "mean", "samjha nahi", "kya hai", "matlab", "શું છે", "મતલબ", "સમજાયું નહીં"]):
            for term, trans in self.glossary.items():
                term_clean = term.replace("_", " ")
                if term_clean in t or term in t:
                    return trans.get(lang, trans.get("en", ""))
        return None

    def build_question_prompt(self, state: SessionState, include_ack: bool = True) -> BotMessage:
        lang = state.language
        i18n = self.get_i18n(lang)
        qid = state.current_question_id
        q_def = self.question_map.get(qid)

        if not q_def:
            return self.build_completion_prompt(state)

        # Acknowledgement prefix
        ack_text = None
        if include_ack and state.answers:
            acks = i18n.get("acknowledgements", ["Thank you."])
            ack_text = random.choice(acks)

        # Localized question text
        q_text = i18n.get("questions", {}).get(qid, q_def.get("report_label", ""))

        # Localized options
        localized_options: List[LocalizedOption] = []
        q_type = q_def.get("type")

        if q_type == "yes_no":
            localized_options = [
                LocalizedOption(code="yes", label=i18n.get("options", {}).get("yes", "Yes")),
                LocalizedOption(code="no", label=i18n.get("options", {}).get("no", "No")),
                LocalizedOption(code="unknown", label=i18n.get("options", {}).get("unknown", "I don't know"))
            ]
        elif q_type in ["single_choice", "multi_choice"]:
            for opt in q_def.get("options", []):
                code = opt["code"]
                label_key = opt.get("label_key", "").split(".")[-1]
                label_str = i18n.get("options", {}).get(label_key, code.replace("_", " ").capitalize())
                localized_options.append(LocalizedOption(code=code, label=label_str))
        elif q_type == "duration":
            for code in ["less_than_4h", "4_to_72h", "more_than_72h", "unknown"]:
                label_key = f"duration_{code}" if code != "unknown" else "unknown"
                label_str = i18n.get("options", {}).get(label_key, code)
                localized_options.append(LocalizedOption(code=code, label=label_str))

        # Progress calculation
        curr_idx = self.question_sequence.index(qid) if qid in self.question_sequence else 0
        total = len(self.question_sequence)
        progress = int((curr_idx / total) * 100)

        # Translation review notice
        review_warning = i18n.get("ui", {}).get("unreviewed_translation_warning", "") if i18n.get("review_status") != "reviewed" else ""

        full_display_text = f"{ack_text} {q_text}" if ack_text else q_text

        return BotMessage(
            text=full_display_text,
            speech_text=q_text,
            question_id=qid,
            question_type=q_type,
            options=localized_options,
            is_red_flag_alert=False,
            is_completed=False,
            progress_percentage=progress,
            acknowledgement=ack_text,
            review_status_warning=review_warning
        )

    def build_red_flag_prompt(self, state: SessionState, reason: str) -> BotMessage:
        lang = state.language
        i18n = self.get_i18n(lang)
        alert_info = i18n.get("red_flag_alert", {})
        title = alert_info.get("title", "URGENT MEDICAL ATTENTION RECOMMENDED")
        message = alert_info.get("message", "Please contact a doctor or go to the nearest emergency room right away.")
        full_text = f"⚠️ **{title}**\n\n{message}\n\n**Reason noted:** {reason}"

        return BotMessage(
            text=full_text,
            speech_text=message,
            question_id=state.current_question_id,
            is_red_flag_alert=True,
            is_completed=False,
            progress_percentage=100
        )

    def build_completion_prompt(self, state: SessionState) -> BotMessage:
        lang = state.language
        i18n = self.get_i18n(lang)
        comp = i18n.get("completion", {})
        thank_you = comp.get("thank_you", "Thank you. Your answers have been safely recorded and prepared for your doctor to review.")
        notice = comp.get("status_notice", "Status: Ready for clinician review.")

        full_text = f"{thank_you}\n\n{notice}"
        return BotMessage(
            text=full_text,
            speech_text=thank_you,
            is_red_flag_alert=False,
            is_completed=True,
            progress_percentage=100
        )

    def process_message(
        self,
        state: SessionState,
        user_input: str = "",
        input_mode: str = "tap",
        selected_code: Optional[Any] = None
    ) -> BotMessage:
        lang = state.language
        i18n = self.get_i18n(lang)

        # 0. Safety Enforcement: If interview was stopped due to an urgent red flag, it cannot be resumed or bypassed
        if state.status == "urgent_red_flag":
            reason = state.red_flag_reasons[0] if state.red_flag_reasons else "Urgent neurological or systemic symptom recorded."
            return self.build_red_flag_prompt(state, reason)

        # 1. Update data quality tracking
        if input_mode == "voice":
            state.data_quality.voice_count += 1
        elif input_mode == "type":
            state.data_quality.typed_count += 1
        else:
            state.data_quality.tap_count += 1

        # 2. Check for real-time spontaneous emergency utterance
        if user_input:
            is_esc, esc_reason = check_immediate_escalation(user_input)
            if is_esc:
                state.status = "urgent_red_flag"
                state.red_flag_codes.append("EMERGENCY_UTTERANCE")
                state.red_flag_reasons.append(esc_reason)
                return self.build_red_flag_prompt(state, esc_reason)

        # 3. Check for glossary questions ("what does photophobia mean?")
        if user_input:
            glossary_ans = self.check_glossary_query(user_input, lang)
            if glossary_ans:
                # Answer the term question politely, then re-prompt current question
                current_prompt = self.build_question_prompt(state, include_ack=False)
                current_prompt.text = f"💡 {glossary_ans}\n\n{current_prompt.text}"
                return current_prompt

        # 4. Handle Pending Confirmation (Echo-check)
        if state.pending_confirmation:
            cmd = parse_special_command(user_input, lang)
            yes_no_val, _ = parse_yes_no(user_input, lang)

            # If user confirms or selected 'yes'
            if selected_code in ["yes", "confirm"] or yes_no_val == "yes":
                pending = state.pending_confirmation
                state.answers[pending.question_id] = AnswerRecord(
                    question_id=pending.question_id,
                    value=pending.tentative_value,
                    raw_text=pending.raw_text,
                    input_mode=pending.input_mode,
                    confidence=pending.confidence,
                    confirmed=True,
                    language=lang
                )
                state.pending_confirmation = None

                # Check if this answered question was a red flag
                q_def = self.question_map.get(pending.question_id, {})
                if q_def.get("is_red_flag") and pending.tentative_value == "yes":
                    state.status = "urgent_red_flag"
                    state.red_flag_codes.append(pending.question_id)
                    reason = RED_FLAG_DESCRIPTIONS.get(pending.question_id, "Reported red flag symptom")
                    state.red_flag_reasons.append(f"[{pending.question_id}] {reason}")
                    return self.build_red_flag_prompt(state, reason)

                # Move to next question
                state.question_history.append(pending.question_id)
                next_qid = self.get_next_question_id(state)
                if not next_qid:
                    state.status = "completed"
                    return self.build_completion_prompt(state)

                state.current_question_id = next_qid
                return self.build_question_prompt(state, include_ack=True)
            else:
                # User says no / wants to change
                state.data_quality.corrections_count += 1
                state.pending_confirmation = None
                retry_prompt = self.build_question_prompt(state, include_ack=False)
                retry_msg = i18n.get("ui", {}).get("retry", "Please select or state your answer again:")
                retry_prompt.text = f"{retry_msg}\n\n{retry_prompt.text}"
                return retry_prompt

        # 5. Check Special Commands
        cmd = parse_special_command(user_input, lang)
        if cmd == "go_back":
            if state.question_history:
                state.data_quality.corrections_count += 1
                prev_qid = state.question_history.pop()
                state.current_question_id = prev_qid
                # Remove prior answer to re-ask cleanly
                state.answers.pop(prev_qid, None)
                back_prompt = self.build_question_prompt(state, include_ack=False)
                back_prompt.text = f"↩️ Re-visiting previous question:\n\n{back_prompt.text}"
                return back_prompt
            else:
                current_prompt = self.build_question_prompt(state, include_ack=False)
                current_prompt.text = f"You are at the first question.\n\n{current_prompt.text}"
                return current_prompt

        if cmd == "skip":
            q_def = self.question_map.get(state.current_question_id, {})
            if not q_def.get("required", True):
                state.answers[state.current_question_id] = AnswerRecord(
                    question_id=state.current_question_id,
                    value="skipped",
                    raw_text="[Skipped]",
                    input_mode=input_mode,
                    confidence=1.0,
                    language=lang
                )
                state.question_history.append(state.current_question_id)
                next_qid = self.get_next_question_id(state)
                if not next_qid:
                    state.status = "completed"
                    return self.build_completion_prompt(state)
                state.current_question_id = next_qid
                return self.build_question_prompt(state, include_ack=True)
            else:
                current_prompt = self.build_question_prompt(state, include_ack=False)
                current_prompt.text = f"This question is required for clinical safety and cannot be skipped.\n\n{current_prompt.text}"
                return current_prompt

        if cmd == "pause":
            state.status = "paused"
            pause_msg = f"Session paused. You can resume at any time using your code: **{state.session_id}**."
            return BotMessage(
                text=pause_msg,
                question_id=state.current_question_id,
                is_completed=False,
                progress_percentage=int((self.question_sequence.index(state.current_question_id) / len(self.question_sequence)) * 100)
            )

        if cmd == "repeat":
            return self.build_question_prompt(state, include_ack=False)

        # 6. Parse Answer to Current Question
        qid = state.current_question_id
        q_def = self.question_map.get(qid)
        if not q_def:
            state.status = "completed"
            return self.build_completion_prompt(state)

        q_type = q_def.get("type")
        parsed_val: Any = None
        confidence: float = 1.0

        # Direct button tap
        if selected_code is not None:
            parsed_val = selected_code
            confidence = 1.0
        else:
            # Parse text input
            raw_text = user_input.strip()
            if q_type == "yes_no":
                yn_val, conf = parse_yes_no(raw_text, lang)
                parsed_val = yn_val
                confidence = conf
            elif q_type in ["number", "scale_0_10"]:
                num_val, conf = parse_number(raw_text)
                if num_val is not None:
                    # Validate ranges
                    val_spec = q_def.get("validation", {})
                    min_v = val_spec.get("min", 0)
                    max_v = val_spec.get("max", 1000)
                    if min_v <= num_val <= max_v:
                        parsed_val = int(num_val) if num_val.is_integer() else num_val
                        confidence = conf
                    else:
                        parsed_val = None
            elif q_type == "duration":
                dur_val, conf = parse_duration(raw_text)
                parsed_val = dur_val
                confidence = conf
            elif q_type in ["single_choice", "multi_choice"]:
                matched_code, conf = match_choice_option(
                    raw_text,
                    q_def.get("options", []),
                    i18n.get("options", {})
                )
                if matched_code:
                    parsed_val = [matched_code] if q_type == "multi_choice" else matched_code
                    confidence = conf
            elif q_type == "free_text":
                parsed_val = raw_text
                confidence = 1.0

        # Check unknown
        if parsed_val == "unknown":
            state.data_quality.unknown_count += 1

        # If parsing failed or unclear
        if parsed_val is None:
            retry_prompt = self.build_question_prompt(state, include_ack=False)
            unclear_msg = "I didn't quite catch that. Please select an option or state your answer:"
            retry_prompt.text = f"{unclear_msg}\n\n{retry_prompt.text}"
            return retry_prompt

        # 7. Echo-confirmation check (voice input or confidence < 0.85)
        if (input_mode == "voice" or confidence < 0.85) and parsed_val != "unknown":
            display_val = str(parsed_val)
            # Find localized label if code
            for opt in q_def.get("options", []):
                if opt["code"] == parsed_val:
                    label_key = opt.get("label_key", "").split(".")[-1]
                    display_val = i18n.get("options", {}).get(label_key, str(parsed_val))
                    break

            echo_template = i18n.get("confirmation", {}).get("voice_echo", "I understood: \"{value}\". Is this correct?")
            echo_msg = echo_template.format(value=display_val)

            state.pending_confirmation = PendingConfirmation(
                question_id=qid,
                tentative_value=parsed_val,
                display_value=display_val,
                raw_text=user_input,
                input_mode=input_mode,
                confidence=confidence
            )

            return BotMessage(
                text=echo_msg,
                speech_text=echo_msg,
                question_id=qid,
                options=[
                    LocalizedOption(code="yes", label=i18n.get("confirmation", {}).get("buttons", {}).get("yes", "Yes, that's right")),
                    LocalizedOption(code="no", label=i18n.get("confirmation", {}).get("buttons", {}).get("no", "No, let me change"))
                ],
                needs_confirmation=True,
                confirmation_value=display_val,
                progress_percentage=int((self.question_sequence.index(qid) / len(self.question_sequence)) * 100)
            )

        # 8. Record answer
        state.answers[qid] = AnswerRecord(
            question_id=qid,
            value=parsed_val,
            raw_text=user_input or str(selected_code),
            input_mode=input_mode,
            confidence=confidence,
            confirmed=True,
            language=lang
        )

        # 9. Safety Check on answered question
        if q_def.get("is_red_flag") and parsed_val == "yes":
            state.status = "urgent_red_flag"
            state.red_flag_codes.append(qid)
            reason = RED_FLAG_DESCRIPTIONS.get(qid, "Reported red flag symptom")
            state.red_flag_reasons.append(f"[{qid}] {reason}")
            return self.build_red_flag_prompt(state, reason)

        # 10. Advance to next question
        state.question_history.append(qid)
        next_qid = self.get_next_question_id(state)
        if not next_qid:
            state.status = "completed"
            return self.build_completion_prompt(state)

        state.current_question_id = next_qid
        return self.build_question_prompt(state, include_ack=True)
