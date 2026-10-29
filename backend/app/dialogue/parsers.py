"""
Multilingual Keyword, Regex, and Synonym Parser
================================================
Deterministic parser for English, Hindi, and Gujarati (native script and romanized).
Ensures 100% offline functionality without LLM dependency.
"""
import re
from typing import Dict, Any, List, Optional, Tuple

YES_SYNONYMS = {
    "en": {"yes", "y", "yeah", "yep", "sure", "correct", "true", "definitely", "always", "right", "affirmative", "of course"},
    "hi": {"हाँ", "हां", "हाँजी", "हांजी", "सही", "बिल्कुल", "अवश्य", "haan", "ha", "han", "haji", "sahi", "bilkul", "yes", "true"},
    "gu": {"હા", "હાજી", "સાચું", "ચોક્કસ", "ખરેખર", "ha", "haan", "haji", "sachu", "hov", "hoy", "yes", "true"}
}

NO_SYNONYMS = {
    "en": {"no", "n", "nope", "nah", "never", "false", "negative", "not at all", "none"},
    "hi": {"नहीं", "नही", "ना", "नाजी", "कभी नहीं", "बिलकुल नहीं", "nahi", "nahin", "na", "naji", "never", "no", "false"},
    "gu": {"ના", "નાજી", "નથી", "ક્યારેય નહીં", "બિલકુલ નહીં", "na", "naji", "nathi", "nahi", "no", "never"}
}

UNKNOWN_SYNONYMS = {
    "en": {"i don't know", "don't know", "dont know", "not sure", "unsure", "unknown", "can't say", "cannot say", "no idea"},
    "hi": {"मुझे नहीं पता", "नहीं पता", "पता नहीं", "मालूम नहीं", "निश्चित नहीं", "pata nahi", "maloom nahi", "dont know"},
    "gu": {"મને ખબર નથી", "ખબર નથી", "ખ્યાલ નથી", "ચોક્કસ નથી", "khabar nathi", "khyal nathi", "dont know"}
}

COMMAND_SYNONYMS = {
    "go_back": {
        "en": {"back", "go back", "previous", "return"},
        "hi": {"पीछे", "पीछे जाएं", "वापस", "पिछला", "piche", "peeche", "wapas"},
        "gu": {"પાછા", "પાછા જાઓ", "પાછળ", "પહેલાંનું", "pacha", "pachha", "wapas"}
    },
    "skip": {
        "en": {"skip", "pass", "next question"},
        "hi": {"छोड़ें", "छोड़ दो", "आगे बढ़ें", "skip", "chodo"},
        "gu": {"છોડો", "છોડી દો", "આગળ વધો", "skip", "chodi do"}
    },
    "pause": {
        "en": {"pause", "save", "stop for now", "later"},
        "hi": {"रोकें", "सत्र रोकें", "बाद में", "pause", "roko"},
        "gu": {"અટકાવો", "સત્ર અટકાવો", "પછીથી", "pause", "atkavo"}
    },
    "repeat": {
        "en": {"repeat", "say again", "what did you say", "again"},
        "hi": {"दोहराएं", "फिर से बोलें", "दोबारा", "phir se", "dobara"},
        "gu": {"ફરીથી બોલો", "ફરીથી", "બીજી વાર", "farithi", "biji var"}
    }
}

INDIC_DIGIT_MAP = {
    # Devanagari numerals ०-९
    "०": "0", "१": "1", "२": "2", "३": "3", "४": "4", "५": "5", "६": "6", "७": "7", "૮": "8", "९": "9",
    # Gujarati numerals ૦-૯
    "૦": "0", "૧": "1", "૨": "2", "૩": "3", "૪": "4", "૫": "5", "૬": "6", "૭": "7", "૮": "8", "૯": "9"
}

NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
    "ek": 1, "do": 2, "teen": 3, "chaar": 4, "char": 4, "paanch": 5, "panch": 5, "chheh": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10,
    "એક": 1, "બે": 2, "ત્રણ": 3, "ચાર": 4, "પાંચ": 5, "છ": 6, "સાત": 7, "આઠ": 8, "નવ": 9, "દસ": 10,
    "be": 2, "tran": 3, "nav": 9
}

def normalize_text(text: str) -> str:
    if not text:
        return ""
    t = text.strip().lower()
    # Replace indic digits with arabic
    for ind, arab in INDIC_DIGIT_MAP.items():
        t = t.replace(ind, arab)
    return t

def parse_special_command(text: str, lang: str = "en") -> Optional[str]:
    """Detects commands like go_back, skip, pause, repeat."""
    t = normalize_text(text)
    for cmd, lang_map in COMMAND_SYNONYMS.items():
        for l_code in [lang, "en", "hi", "gu"]:
            if l_code in lang_map:
                for syn in lang_map[l_code]:
                    if t == syn or t.startswith(syn):
                        return cmd
    return None

def parse_yes_no(text: str, lang: str = "en") -> Tuple[Optional[str], float]:
    """Parses yes/no/unknown from text across languages."""
    t = normalize_text(text)
    # Check Unknown
    for l_code in [lang, "en", "hi", "gu"]:
        if any(u in t for u in UNKNOWN_SYNONYMS.get(l_code, set())):
            return "unknown", 1.0

    # Check Yes
    for l_code in [lang, "en", "hi", "gu"]:
        for y in YES_SYNONYMS.get(l_code, set()):
            # exact match or word boundary
            pattern = rf"(^|\b|\s){re.escape(y)}(\b|\s|$)"
            if re.search(pattern, t):
                return "yes", 1.0

    # Check No
    for l_code in [lang, "en", "hi", "gu"]:
        for n in NO_SYNONYMS.get(l_code, set()):
            pattern = rf"(^|\b|\s){re.escape(n)}(\b|\s|$)"
            if re.search(pattern, t):
                return "no", 1.0

    return None, 0.0

def parse_number(text: str) -> Tuple[Optional[float], float]:
    """Extracts numeric values from digit strings or number words."""
    t = normalize_text(text)
    # Check for digit numbers
    match = re.search(r"(\d+(\.\d+)?)", t)
    if match:
        try:
            val = float(match.group(1))
            return val, 1.0
        except ValueError:
            pass

    # Check number words
    for word, num in NUMBER_WORDS.items():
        if re.search(rf"\b{re.escape(word)}\b", t):
            return float(num), 0.95

    return None, 0.0

def parse_duration(text: str) -> Tuple[Optional[str], float]:
    """
    Parses duration utterances into '<4h', '4_to_72h', '>72h'.
    Examples: '2 hours', '3 ghante', '24 kalak', '3 days', 'ek diwas', '50 min'.
    """
    t = normalize_text(text)
    if any(u in t for u in ["pata nahi", "don't know", "unknown", "khabar nathi"]):
        return "unknown", 1.0

    # Look for number (either digit or number word)
    num_val, _ = parse_number(t)

    # Check for day keywords
    day_keywords = ["day", "days", "din", "diwas", "દિવાસ", "દિવાસો", "दिन"]
    if any(k in t for k in day_keywords):
        if num_val is not None:
            hours = num_val * 24.0
            if hours < 4.0:
                return "less_than_4h", 1.0
            elif 4.0 <= hours <= 72.0:
                return "4_to_72h", 1.0
            else:
                return "more_than_72h", 1.0

    # Check for hour keywords
    hour_keywords = ["hour", "hours", "hr", "hrs", "ghante", "ghanta", "kalak", "घंटे", "घंटा", "કલાક"]
    if any(k in t for k in hour_keywords):
        if num_val is not None:
            if num_val < 4.0:
                return "less_than_4h", 1.0
            elif 4.0 <= num_val <= 72.0:
                return "4_to_72h", 1.0
            else:
                return "more_than_72h", 1.0

    # Check for minute keywords
    min_keywords = ["min", "minute", "minutes", "मिनट", "મિનિટ"]
    if any(k in t for k in min_keywords):
        if num_val is not None:
            hours = num_val / 60.0
            if hours < 4.0:
                return "less_than_4h", 1.0
            elif 4.0 <= hours <= 72.0:
                return "4_to_72h", 1.0
            else:
                return "more_than_72h", 1.0

    # Direct number fallback
    if num_val is not None:
        if num_val < 4.0:
            return "less_than_4h", 0.8
        elif 4.0 <= num_val <= 72.0:
            return "4_to_72h", 0.8
        else:
            return "more_than_72h", 0.8

    return None, 0.0

def match_choice_option(text: str, allowed_options: List[Dict[str, str]], i18n_options: Dict[str, str]) -> Tuple[Optional[str], float]:
    """Matches text against allowed options for single_choice or multi_choice."""
    t = normalize_text(text)
    if any(u in t for u in ["pata nahi", "don't know", "unknown", "khabar nathi"]):
        return "unknown", 1.0

    best_code: Optional[str] = None
    best_conf = 0.0

    for opt in allowed_options:
        code = opt["code"]
        label_key = opt.get("label_key", "")
        opt_label = i18n_options.get(label_key.split(".")[-1], "").lower()

        # Exact code match
        if t == code.lower() or t == code.replace("_", " ").lower():
            return code, 1.0

        # Exact label match
        if opt_label and (t == opt_label or opt_label in t):
            return code, 0.95

        # Substring / keyword overlap
        code_words = set(code.lower().replace("_", " ").split())
        t_words = set(t.split())
        overlap = code_words.intersection(t_words)
        if len(overlap) >= 1:
            conf = len(overlap) / max(len(code_words), 1) * 0.9
            if conf > best_conf:
                best_conf = conf
                best_code = code

    if best_conf >= 0.7:
        return best_code, best_conf

    return None, 0.0
