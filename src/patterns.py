# src/patterns.py - regex extractors (week 5)
# Pure pattern matching: given raw text, pull out the piece that matches, or
# return None if it isn't there. No business rules live here (no raising, no
# repairing) - that judgment belongs to the callers in intake.py.
import re

CASE_ID_RE = re.compile(r"^CC[-\s]?(\d{5})$", re.IGNORECASE)   # CC-12345, CC 12345, cc12345...
BEAT_RE = re.compile(r"(\d{3})")                                # first run of 3 digits anywhere
PHONE_RE = re.compile(r"\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})")  # dash/dot/space/paren variants


def extract_case_id(text):
    """Return the 5 digits of a CC-##### case id, or None if the shape doesn't fit."""
    match = CASE_ID_RE.match(text.strip())
    return match.group(1) if match else None


def extract_beat(text):
    """Return the first 3-digit beat number found, or None if there isn't one."""
    match = BEAT_RE.search(text)
    return match.group(1) if match else None


def extract_phone(text):
    """Return the first phone number in free text as 214-555-1234, or None if there isn't one."""
    match = PHONE_RE.search(text)
    return "-".join(match.groups()) if match else None
