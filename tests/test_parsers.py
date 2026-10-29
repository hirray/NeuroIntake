"""
Unit Tests for Multilingual Parsers (en, hi, gu)
================================================
Verifies deterministic synonym matching, digit/word conversions,
duration interpretations, and command extractions.
"""
import pytest
from backend.app.dialogue.parsers import (
    parse_yes_no,
    parse_number,
    parse_duration,
    parse_special_command,
    normalize_text
)

def test_yes_no_english():
    assert parse_yes_no("yes")[0] == "yes"
    assert parse_yes_no("Yep, definitely")[0] == "yes"
    assert parse_yes_no("no")[0] == "no"
    assert parse_yes_no("Not at all")[0] == "no"
    assert parse_yes_no("I don't know")[0] == "unknown"

def test_yes_no_hindi():
    # Devanagari
    assert parse_yes_no("हाँ")[0] == "yes"
    assert parse_yes_no("नहीं")[0] == "no"
    assert parse_yes_no("मुझे नहीं पता")[0] == "unknown"
    # Romanized
    assert parse_yes_no("haan ji")[0] == "yes"
    assert parse_yes_no("nahi")[0] == "no"
    assert parse_yes_no("pata nahi")[0] == "unknown"

def test_yes_no_gujarati():
    # Gujarati script
    assert parse_yes_no("હા")[0] == "yes"
    assert parse_yes_no("ના")[0] == "no"
    assert parse_yes_no("મને ખબર નથી")[0] == "unknown"
    # Romanized
    assert parse_yes_no("ha")[0] == "yes"
    assert parse_yes_no("nathi")[0] == "no"
    assert parse_yes_no("khabar nathi")[0] == "unknown"

def test_number_parsing_and_indic_numerals():
    # Standard digits
    assert parse_number("35")[0] == 35.0
    # Devanagari numerals
    assert parse_number("२५")[0] == 25.0
    assert parse_number("४८")[0] == 48.0
    # Gujarati numerals
    assert parse_number("૨૮")[0] == 28.0
    assert parse_number("૫૦")[0] == 50.0
    # Words in Hindi / Gujarati / English
    assert parse_number("teen")[0] == 3.0
    assert parse_number("chaar")[0] == 4.0
    assert parse_number("tran")[0] == 3.0
    assert parse_number("five")[0] == 5.0

def test_duration_parsing():
    # Hours
    assert parse_duration("2 hours")[0] == "less_than_4h"
    assert parse_duration("6 hours")[0] == "4_to_72h"
    assert parse_duration("80 hours")[0] == "more_than_72h"
    # Hindi hours / days
    assert parse_duration("3 ghante")[0] == "less_than_4h"
    assert parse_duration("24 ghante")[0] == "4_to_72h"
    assert parse_duration("2 din")[0] == "4_to_72h"  # 48h
    assert parse_duration("4 din")[0] == "more_than_72h" # 96h
    # Gujarati kalak / diwas
    assert parse_duration("2 kalak")[0] == "less_than_4h"
    assert parse_duration("12 kalak")[0] == "4_to_72h"
    assert parse_duration("ek diwas")[0] == "4_to_72h" # 24h
    # Minutes
    assert parse_duration("45 minutes")[0] == "less_than_4h"

def test_special_commands():
    # Back
    assert parse_special_command("go back", "en") == "go_back"
    assert parse_special_command("peeche", "hi") == "go_back"
    assert parse_special_command("પાછા જાઓ", "gu") == "go_back"
    # Skip
    assert parse_special_command("skip", "en") == "skip"
    assert parse_special_command("छोड़ें", "hi") == "skip"
    # Pause
    assert parse_special_command("pause", "en") == "pause"
    assert parse_special_command("સત્ર અટકાવો", "gu") == "pause"
    # Repeat
    assert parse_special_command("repeat", "en") == "repeat"
    assert parse_special_command("dobara", "hi") == "repeat"
