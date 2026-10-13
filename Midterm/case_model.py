# =============================================================================
# case_model.py  --  The Cold Case File   (ITSS/OPRE 3312, Midterm)
# =============================================================================
#
# BIG PICTURE
#   This file knows how to turn ONE messy row of the raw file into ONE clean
#   Case object. It does not open any files and it does not print anything.
#   That is on purpose: because it only works on data handed to it, every
#   piece of it can be tested on its own in test_cases.py.
#
#   It has two layers:
#
#     1. FIELD CLEANERS  -  one small function per column (the week 5 rule:
#        one function, one job, one docstring). Each one takes the raw text of
#        a single field and hands back the clean value.
#          - Cleaners for CRITICAL fields (case_id, date, status) RAISE a
#            ValueError when the value is broken. That error is the signal that
#            the whole row must be quarantined.
#          - Cleaners for NON-CRITICAL fields (name, sex, age, beat, phone)
#            never raise. They repair what they can and leave a blank for the rest.
#
#     2. THE Case CLASS  -  a blueprint for one clean case (week 7).
#          Case.from_row(row)  runs the checks in the order slide 4 gives and
#                              builds a Case from the cleaned values
#          .year               the 4-digit year of the incident
#          .years_unsolved     how many full years an OPEN case has been open
#          .is_stale           True if the case is OPEN and 5+ years old
#          .to_row()           the case as a list, ready for csv.writer
#
# THE ORDER OF THE CHECKS (from slide 4 - it matters!)
#   A row can be broken in more than one way. We always report the FIRST
#   problem in this order, so every squad gets the same counts:
#       wrong field count -> bad case_id -> missing date -> invalid date
#       -> future date -> unknown status
#
# DESIGN RULES (same as weeks 5 and 6)
#   - Standard library only: re and datetime. No pandas.
#   - We raise and catch ValueError specifically - never a bare "except:".
#   - Variable names are camelCase. Function names are snake_case.
# =============================================================================

import re                              # regular expressions: describe the SHAPE of text and search for it
from datetime import date, datetime    # date = a calendar day; datetime.strptime turns text into a date


# "Today" is fixed by the assignment (slide 4) as October 7, 2026. We do NOT use
# date.today(), because then the numbers would change depending on the day you
# run the program, and they would no longer match the answer key.
TODAY = date(2026, 10, 7)              # the reference date for "future date" and "years unsolved"

# A case counts as stale when it has been open this many years or more.
STALE_YEARS = 5                        # slide 7: "stale (open 5+ years)"


# -----------------------------------------------------------------------------
# 1a. CRITICAL FIELD CLEANERS  -  these raise ValueError when the value is broken
# -----------------------------------------------------------------------------

def clean_case_id(text):
    """Return the case id as CC-#####, or raise ValueError("bad case_id")."""
    # The raw ids look like:  cc-19495   CC 16288   " CC-76856 "   CC81472
    # First we strip the spaces off both ends and make everything uppercase,
    # so "cc-19495" and " CC-19495 " both become "CC-19495".
    text = text.strip().upper()                        # trim spaces, then capitals

    # Now we describe the shape we will accept, as a regex:
    #   CC        the letters C and C
    #   [- ]?     an OPTIONAL dash or space (the ? means "zero or one of these")
    #   (\d{5})   exactly five digits, CAPTURED in a group so we can pull them out
    # re.fullmatch only succeeds if the WHOLE string fits the pattern. So
    # "CC-123" (too short), "CC-123456" (too long) and "XX-12345" are all rejected.
    match = re.fullmatch(r"CC[- ]?(\d{5})", text)      # try to match the whole id
    if match is None:                                  # None means the shape did not fit
        raise ValueError("bad case_id")                # critical field is broken: quarantine the row

    # match.group(1) is the text inside the first ( ), which is the 5 digits.
    # We rebuild the id in the one standard format: CC-#####.
    return f"CC-{match.group(1)}"                      # e.g. "CC-19495"


def clean_date(text):
    """Return the incident date as a date object, or raise ValueError with the reason."""
    # The raw file mixes three date formats:
    #     2018-03-22        6/7/2000        July 1, 2022
    # plus junk like "N/A", "unknown", blanks, "07/27/02x", "Smarch 5, 2010",
    # impossible days like Feb 30, and dates in the future.
    text = text.strip()                                # trim spaces so "  " becomes ""

    # CHECK 1 - missing date. A blank, "N/A" or "unknown" means nobody recorded
    # a date at all. .lower() lets us catch "N/A", "n/a", "Unknown", etc.
    if text.lower() in ("", "n/a", "unknown"):         # is it one of the "no date" values?
        raise ValueError("missing date")               # yes: quarantine with this reason

    # CHECK 2 - which of the 3 allowed formats does it look like?
    # We use a regex to recognize the SHAPE, and pick the matching strptime
    # format code. The format codes mean:
    #   %Y = 4-digit year   %m = month number   %d = day number   %B = month name
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):       # shape: 2018-03-22
        dateFormat = "%Y-%m-%d"
    elif re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", text): # shape: 6/7/2000 or 06/07/2000
        dateFormat = "%m/%d/%Y"
    elif re.fullmatch(r"[A-Za-z]+ \d{1,2}, \d{4}", text):  # shape: July 1, 2022
        dateFormat = "%B %d, %Y"
    else:                                              # none of the three shapes, e.g. "07/27/02x"
        raise ValueError("invalid date")

    # CHECK 3 - is it a real calendar day? The shape can be right while the
    # date is still impossible: "2004-02-30" (Feb 30) or "Smarch 5, 2010" (not
    # a month). datetime.strptime raises its own ValueError in those cases.
    # We catch it and raise a NEW ValueError with our standard reason text,
    # so the quarantine file always says "invalid date" and not Python's
    # long technical message.
    try:
        incidentDate = datetime.strptime(text, dateFormat).date()  # text -> datetime -> just the date part
    except ValueError:
        raise ValueError("invalid date")               # the shape fit, but the day does not exist

    # CHECK 4 - a crime cannot have happened after "today".
    if incidentDate > TODAY:                           # dates can be compared with > like numbers
        raise ValueError("future date")

    return incidentDate                                # a real, past date


def clean_status(text):
    """Return OPEN or CLOSED, or raise ValueError("unknown status")."""
    # The raw file spells status many ways: OPEN open OPN CLOSED Closed CLSD CLEARED.
    # Stripping and uppercasing first means we only have to list each spelling once.
    text = text.strip().upper()                        # " open " -> "OPEN"

    if text in ("OPEN", "OPN"):                        # both spellings mean the case is still open
        return "OPEN"
    if text in ("CLOSED", "CLSD", "CLEARED"):          # all three mean the case was solved/closed
        return "CLOSED"

    # Anything else ("PENDING?", "??", "UNK", blank) cannot be trusted, and
    # status is the most important field for the analysis, so the row goes
    # to quarantine.
    raise ValueError("unknown status")


# -----------------------------------------------------------------------------
# 1b. NON-CRITICAL FIELD CLEANERS  -  these repair the value and never raise
# -----------------------------------------------------------------------------

def clean_name(text):
    """Strip and collapse spaces, then Title Case the name: '  JORDAN,  C ' -> 'Jordan, C'."""
    # text.split() with no argument splits on ANY run of spaces and throws the
    # empty pieces away, so "  JORDAN,  C " becomes ["JORDAN,", "C"].
    # " ".join(...) glues the pieces back together with exactly ONE space.
    # That one line does both the "strip" and the "collapse spaces" steps.
    # .title() then capitalizes the first letter of each word: "Jordan, C".
    return " ".join(text.split()).title()


def clean_sex(text):
    """Return M or F; anything else (unk, blank, ...) becomes U for unknown."""
    text = text.strip().upper()                        # "female" -> "FEMALE", " M" -> "M"
    if text in ("M", "MALE"):
        return "M"
    if text in ("F", "FEMALE"):
        return "F"
    return "U"                                         # we keep the row, we just don't know the sex


def clean_age(text):
    """Return the age as a whole number from 0 to 110, or None (blank) if it isn't one."""
    # int() turns text into a whole number, and it ignores spaces, so " 37 "
    # becomes 37. If the text is not a number at all ("unknown", "N/A", "?")
    # int() raises a ValueError. Age is NOT a critical field, so we catch that
    # error right here and just return None instead of rejecting the row.
    try:
        age = int(text)                                # "36" -> 36, "unknown" -> ValueError
    except ValueError:
        return None                                    # not a number: leave the age blank

    # A number can still be impossible: -1 and 999 are "filler" values that
    # someone typed when they didn't know the age.
    if 0 <= age <= 110:                                # a believable human age?
        return age
    return None                                        # out of range: leave it blank


def clean_beat(text):
    """Return the 3-digit beat ('beat 631', 'B-150', ' 157 ' -> '631', '150', '157'), or '' if none."""
    # The regex, piece by piece:
    #   (?:beat\s*|b-)?   an OPTIONAL prefix: the word "beat" plus any spaces, OR "b-".
    #                     (?: ) groups the choices without capturing them, and the
    #                     final ? makes the whole prefix optional.
    #   (\d{3})           exactly three digits, captured so we can pull them out
    # re.IGNORECASE lets one pattern match "beat", "Beat" and "BEAT".
    match = re.fullmatch(r"(?:beat\s*|b-)?(\d{3})", text.strip(), re.IGNORECASE)
    if match is None:                                  # blank or some other junk
        return ""                                      # leave the beat blank, keep the row
    return match.group(1)                              # just the three digits, as text (keeps leading zeros)


def extract_phone(text):
    """Return the first phone number in the tip notes as 214-555-1234, or '' if there isn't one."""
    # Tip notes contain phones in three styles:
    #     214-555-3072     (214) 555-4240     214.555.3072
    # The regex, piece by piece:
    #   \(?       an optional "("   (the backslash means a REAL parenthesis, not a regex group)
    #   (\d{3})   the 3-digit area code, captured as group 1
    #   \)?       an optional ")"
    #   [ .-]?    an optional separator: a space, a dot or a dash
    #   (\d{3})   the next 3 digits, group 2
    #   [.-]      a dot or a dash
    #   (\d{4})   the last 4 digits, group 3
    # re.search looks ANYWHERE in the text and stops at the FIRST match, which is
    # exactly what slide 5 asks for ("first phone number in tip_notes").
    # Case refs like "CC-12345" never match, because they don't have 3-3-4 digits.
    match = re.search(r"\(?(\d{3})\)?[ .-]?(\d{3})[.-](\d{4})", text)
    if match is None:                                  # no phone number in this tip
        return ""
    # Rebuild the number in the one standard style, using the 3 captured groups.
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"


# -----------------------------------------------------------------------------
# 2. THE Case CLASS  -  one object = one clean case
# -----------------------------------------------------------------------------

class Case:
    """One cleaned cold case built from a row of the raw file."""

    def __init__(self, caseId, victimName, sex, age, incidentDate, beat, status, callbackPhone):
        """Store the already-clean values on the new Case object."""
        # __init__ runs automatically every time a Case is created.
        # "self" is the object being built; self.something = value saves a
        # value ON that object, so every Case carries its own data around.
        self.case_id = caseId                  # "CC-19495"
        self.victim_name = victimName          # "Walker, G"
        self.sex = sex                         # "M", "F" or "U"
        self.age = age                         # a whole number, or None if unknown
        self.incident_date = incidentDate      # a date object, e.g. date(2000, 6, 7)
        self.beat = beat                       # "157", or "" if unknown
        self.status = status                   # "OPEN" or "CLOSED"
        self.callback_phone = callbackPhone    # "214-555-0202", or "" if none

    @classmethod
    def from_row(cls, row):
        """Build a Case from one raw CSV row (a list of 9 strings), or raise ValueError with the reason."""
        # @classmethod means we call this on the CLASS itself, not on an
        # existing object:   case = Case.from_row(row)
        # "cls" is the Case class, so cls(...) at the bottom is the same as Case(...).
        # This is called a "factory": it does the checking and cleaning, and
        # only hands back an object if the row is usable.

        # CHECK 1 - field count. A healthy row has exactly 9 fields. Truncated
        # rows (cut off part way) have fewer, and we cannot trust them.
        if len(row) != 9:
            raise ValueError("wrong field count")

        # Unpack the 9 fields into named variables so the code below is
        # readable. Python counts from 0, so row[0] is case_id, row[1] is
        # victim_name, and so on. "address" is unpacked but never used, because
        # slide 3 says to drop it from the clean file.
        rawId, rawName, rawSex, rawAge, rawDate, address, rawBeat, rawStatus, tipNotes = row

        # CHECKS 2 to 6 - the critical fields, in the order slide 4 requires.
        # If any of these raise a ValueError, this function stops right here and
        # the error travels up to the loader's try/except, which quarantines the row.
        caseId = clean_case_id(rawId)                  # may raise "bad case_id"
        incidentDate = clean_date(rawDate)             # may raise "missing date", "invalid date" or "future date"
        status = clean_status(rawStatus)               # may raise "unknown status"

        # The row survived every critical check, so now we repair the
        # non-critical fields and build the object.
        return cls(
            caseId,
            clean_name(rawName),
            clean_sex(rawSex),
            clean_age(rawAge),
            incidentDate,
            clean_beat(rawBeat),
            status,
            extract_phone(tipNotes),
        )

    # @property lets us call a method WITHOUT parentheses, as if it were a
    # stored value:  case.year  instead of  case.year().  It is calculated
    # fresh from incident_date every time, so it can never get out of sync.

    @property
    def year(self):
        """The 4-digit year of the incident, e.g. 1992."""
        return self.incident_date.year                 # date objects already know their year

    @property
    def years_unsolved(self):
        """Full years an OPEN case has been open as of TODAY; 0 for a CLOSED case."""
        if self.status == "CLOSED":                    # a closed case is not unsolved
            return 0
        # Count whole years the same way you count someone's age: subtract the
        # years, then take one away if this year's "anniversary" hasn't come yet.
        # (TODAY.month, TODAY.day) < (month, day) compares the two pairs month first.
        # In Python True counts as 1 and False as 0, so this subtracts 1 or 0.
        years = TODAY.year - self.incident_date.year
        notYetAnniversary = (TODAY.month, TODAY.day) < (self.incident_date.month, self.incident_date.day)
        return years - notYetAnniversary

    @property
    def is_stale(self):
        """True if the case is OPEN and has been unsolved for 5 or more years."""
        # A closed case always has years_unsolved == 0, so it can never be stale.
        return self.years_unsolved >= STALE_YEARS

    def to_row(self):
        """Return the case as a list in the exact column order of cases_clean.csv."""
        # Blank values: an unknown age is None, and we write it as "" so the
        # CSV shows an empty cell instead of the word "None".
        # .isoformat() writes a date as YYYY-MM-DD, the format slide 5 requires.
        return [
            self.case_id,
            self.victim_name,
            self.sex,
            "" if self.age is None else self.age,      # a one-line if/else: blank when unknown
            self.incident_date.isoformat(),
            self.year,
            self.beat,
            self.status,
            self.callback_phone,
        ]
