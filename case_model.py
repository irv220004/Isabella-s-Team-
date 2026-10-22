"""case_model.py - the Case class plus one small cleaner function per field.

Weeks used: 2 (strings), 5 (functions + regex), 6 (ValueError for bad rows),
7 (classes, properties, classmethod).
"""
import re                       # week 5: regular expressions for ids, dates, beats, phones
from datetime import date       # a real date object lets Python reject Feb 30 / month 13 for us

today = date.today()             #variable for the current date, updates value when the program is run
reference_year = date.today().year # week 7 lecture: years_unsolved = current year
stale_years = 5                    # slide 7: "stale" = open 5+ years; one constant = one place to change it

# Month names -> month numbers, used only for dates like "July 1, 2022".
months = {                      # a dict (week 4) is a lookup table: name in, number out
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}

# Every spelling of status we know, mapped to the two allowed answers (slide 4).
status_map = {
    "OPEN": "OPEN", "OPN": "OPEN",
    "CLOSED": "CLOSED", "CLSD": "CLOSED", "CLEARED": "CLOSED",
}


# ---------------------------------------------------------------------------
# CRITICAL-FIELD CLEANERS: these RAISE ValueError, which quarantines the row.
# The message IS the quarantine reason, so it must match slide 4's wording.
# ---------------------------------------------------------------------------

def clean_case_id(text):
    """Normalize 'cc-19495', 'CC 16288', ' CC-76856 ', 'CC81472' to 'CC-#####'; ValueError if impossible."""
    # ^cc        starts with "cc" (re.IGNORECASE lets "cc" and "CC" both match)
    # [\s-]?     optionally ONE space or dash between the letters and digits
    # (\d{5})$   exactly five digits, then the end of the string (capture group keeps the digits)
    match = re.match(r"^cc[\s-]?(\d{5})$", text.strip(), re.IGNORECASE)
    if match is None:                       # no match = the id can't be rescued
        raise ValueError("bad case_id")
    return "CC-" + match.group(1)           # rebuild it in the one standard shape


def clean_date(text):
    """Turn a date in one of the 3 allowed formats into a date object; ValueError says why it failed."""
    text = text.strip()                                     # week 2: strip stray whitespace first
    if text.lower() in ("", "n/a", "unknown"):              # the three ways a date can be "missing"
        raise ValueError("missing date")

    # Try each of the 3 formats. Each regex only captures the PIECES; the
    # date() constructor below is what actually checks the date is real.
    iso = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", text)              # 2018-03-22
    us = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", text)               # 6/7/2000  (month first)
    named = re.match(r"^([A-Za-z]+) (\d{1,2}), (\d{4})$", text)         # July 1, 2022

    if iso:
        year, month, day = (int(g) for g in iso.groups())   # generator turns the 3 strings into ints
    elif us:
        month, day, year = (int(g) for g in us.groups())    # US order is month/day/year
    elif named and named.group(1).lower() in months:        # the word must be a real month name
        month = months[named.group(1).lower()]              # look the month number up in the dict
        day, year = int(named.group(2)), int(named.group(3))
    else:
        raise ValueError("invalid date")                    # matches none of the 3 formats

    try:
        result = date(year, month, day)                     # raises ValueError for Feb 30 or month 13
    except ValueError:
        raise ValueError("invalid date") from None          # re-raise with OUR reason text instead

    if result > today:                                      # checked last: only real dates can be "future"
        raise ValueError("future date")
    return result


def clean_status(text):
    """Map any known spelling to 'OPEN' or 'CLOSED'; ValueError('unknown status') for anything else."""
    key = text.strip().upper()                              # 'Closed', ' clsd ' -> 'CLOSED', 'CLSD'
    if key not in status_map:                               # dict membership test (week 4)
        raise ValueError("unknown status")
    return status_map[key]


# ---------------------------------------------------------------------------
# NON-CRITICAL CLEANERS: these NEVER raise. A bad value is repaired or blanked
# and the row is kept (slide 4, "repair & keep the row").
# ---------------------------------------------------------------------------

def clean_name(text):
    """'  JORDAN, C ' / 'NAVARRO,  M' -> 'Jordan, C' / 'Navarro, M' (strip, collapse spaces, Title Case)."""
    collapsed = " ".join(text.split())      # split() with no args splits on ANY run of whitespace; join puts back single spaces
    return collapsed.title()                # 'walker, g' -> 'Walker, G'


def clean_sex(text):
    """Return 'M' or 'F'; anything else (blank, 'unk', ...) becomes 'U'."""
    key = text.strip().upper()
    if key in ("M", "MALE"):
        return "M"
    if key in ("F", "FEMALE"):
        return "F"
    return "U"


def clean_age(text):
    """Return a whole-number age 0-110 as an int, or None (blank) if it is anything else."""
    text = text.strip()
    if not re.match(r"^\d+$", text):        # only plain digits pass: 'unknown', 'N/A', '-1' all fail here
        return None
    age = int(text)                         # safe now: we know it is all digits
    if age > 110:                           # 999 and other impossible ages
        return None
    return age                              # (can't be < 0: a minus sign already failed the regex)


def clean_beat(text):
    """Pull the 3-digit beat out of '157', 'beat 631', 'Beat 418', 'B-150'; '' if there isn't one."""
    # (?<!\d) and (?!\d) mean "not touching another digit", so a 4-digit
    # number can't sneak a 3-digit beat out of its middle.
    match = re.search(r"(?<!\d)(\d{3})(?!\d)", text)
    return match.group(1) if match else ""  # beat stays a string so leading zeros (if any) survive


def extract_callback_phone(text):
    """Return the FIRST phone in the tip notes as '214-555-1234', or '' if there is none."""
    # (?<!\d)       not preceded by a digit        \(?(\d{3})\)?   area code, optional parens
    # [ .-]?        optional space/dot/dash        (\d{3})         exchange
    # [ .-]?        optional space/dot/dash        (\d{4})(?!\d)   line number, not followed by a digit
    match = re.search(r"(?<!\d)\(?(\d{3})\)?[ .-]?(\d{3})[ .-]?(\d{4})(?!\d)", text)
    if match is None:
        return ""
    return "-".join(match.groups())         # write all three groups in the standard dashed form


# ---------------------------------------------------------------------------
# THE CASE CLASS (week 7): data + the questions you ask of it
# ---------------------------------------------------------------------------

class Case:
    """One cleaned case. Build it with Case.from_row(); never trust a raw row directly."""

    def __init__(self, case_id, victim_name, sex, age, incident_date, beat, status, callback_phone):
        self.case_id = case_id                  # 'CC-10003'
        self.victim_name = victim_name          # 'Ramirez, K'
        self.sex = sex                          # 'M' / 'F' / 'U'
        self.age = age                          # int, or None when unusable
        self.incident_date = incident_date      # a datetime.date object
        self.beat = beat                        # '451' or '' when unknown
        self.status = status                    # 'OPEN' / 'CLOSED'
        self.callback_phone = callback_phone    # '214-555-0193' or ''

    @classmethod
    def from_row(cls, row):
        """Clean one raw CSV row (a list of 9 strings) into a Case; raises ValueError with the quarantine reason."""
        if len(row) != 9:                       # rule 1: the field count is checked before anything else
            raise ValueError("wrong field count")

        # Unpack the 9 raw fields into named variables (address is read but dropped, per slide 3).
        raw_id, raw_name, raw_sex, raw_age, raw_date, _address, raw_beat, raw_status, raw_tips = row

        # Critical fields first, in the exact order slide 4 lists them. The
        # FIRST one that raises decides the quarantine reason.
        case_id = clean_case_id(raw_id)
        incident_date = clean_date(raw_date)
        status = clean_status(raw_status)

        # Non-critical fields can't raise, so they come after the checks.
        return cls(
            case_id,
            clean_name(raw_name),
            clean_sex(raw_sex),
            clean_age(raw_age),
            incident_date,
            clean_beat(raw_beat),
            status,
            extract_callback_phone(raw_tips),
        )

    @property
    def year(self):
        """The 4-digit incident year."""
        return self.incident_date.year

    @property
    def decade(self):
        """1992 -> 1990 (integer division drops the last digit, then we put a zero back)."""
        return self.year // 10 * 10

    @property
    def years_unsolved(self):
        """Years between the incident and the reference year."""
        return reference_year - self.year

    @property
    def is_stale(self):
        """True for an OPEN case that has been open STALE_YEARS or more."""
        return self.status == "OPEN" and self.years_unsolved >= stale_years

    def to_row(self):
        """The 9 output columns for cases_clean.csv, in the exact slide-5 order."""
        return [
            self.case_id,
            self.victim_name,
            self.sex,
            "" if self.age is None else self.age,       # None -> blank cell
            self.incident_date.isoformat(),             # date object -> 'YYYY-MM-DD'
            self.year,
            self.beat,
            self.status,
            self.callback_phone,
        ]

    def summary(self):
        """One readable line, handy for the 'oldest open cases' list."""
        return f"{self.case_id}  {self.incident_date.isoformat()}  {self.victim_name}  (beat {self.beat or '?'})"
