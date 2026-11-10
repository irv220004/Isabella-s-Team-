# src/patterns.py - regex extractors (week 5)
# Pure pattern matching: given raw text, pull out the piece that matches, or
# return None if it isn't there. No business rules live here (no raising, no
# repairing) - that judgment belongs to the callers in intake.py.
import re                                      # the module that understands regex patterns

CASE_ID_RE = re.compile(r"^CC[-\s]?(\d{5})$", re.IGNORECASE)   # CC-12345, CC 12345, cc12345...
# ^CC          the string must START with the letters C and C
# [-\s]?       then an OPTIONAL dash or whitespace character (zero or one)
# (\d{5})      then exactly 5 digits, CAPTURED in a group so we can pull them out later
# $            the string must END right there - nothing extra allowed
# re.IGNORECASE lets this match "cc", "Cc", "CC", etc. all the same way

BEAT_RE = re.compile(r"(\d{3})")                                # first run of 3 digits anywhere
# (\d{3})      exactly 3 digits in a row, captured. No anchors, so it can match
#              anywhere in the string: "beat 157" or "B-150" or just "157"

PHONE_RE = re.compile(r"\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})")  # dash/dot/space/paren variants
# \(?          an optional literal "(" - the backslash means a REAL parenthesis
# (\d{3})      the 3-digit area code, captured as group 1
# \)?          an optional literal ")"
# [-.\s]?      an optional single separator: a dash, a dot, or whitespace
# (\d{3})      the next 3 digits, group 2
# [-.\s]?      another optional separator
# (\d{4})      the last 4 digits, group 3


def extract_case_id(text):
    """Return the 5 digits of a CC-##### case id, or None if the shape doesn't fit."""
    match = CASE_ID_RE.match(text.strip())      # strip outer spaces, then test against the pattern
    return match.group(1) if match else None    # group(1) is just the captured 5 digits


def extract_beat(text):
    """Return the first 3-digit beat number found, or None if there isn't one."""
    match = BEAT_RE.search(text)                # search() looks anywhere in the string, not just the start
    return match.group(1) if match else None    # the captured 3 digits, or None if nothing matched


def extract_phone(text):
    """Return the first phone number in free text as 214-555-1234, or None if there isn't one."""
    match = PHONE_RE.search(text)                # scan the whole string for the first phone-shaped match
    return "-".join(match.groups()) if match else None   # groups() = (area, exchange, number); rejoin with dashes
