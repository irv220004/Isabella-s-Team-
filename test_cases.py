# =============================================================================
# test_cases.py  --  automated proof that the parser works
# =============================================================================
#
# BIG PICTURE
#   "It worked when I ran it" is not the same as "it works." Each test below
#   feeds the cleaners or Case.from_row() a row WE control and checks the
#   answer. If someone breaks a cleaner later, a test turns red right away.
#
# THE TESTS  (4 happy paths, 4 failure paths)
#   Happy paths - messy input is repaired correctly:
#     1. test_good_row_becomes_case     a messy but valid row becomes a clean Case
#     2. test_three_date_formats        all 3 date formats give the same date
#     3. test_repairs_non_critical      status, sex, age and beat spellings are fixed
#     4. test_phone_formats             all 3 phone styles become 214-555-1234
#   Failure paths - broken rows are rejected with the RIGHT reason:
#     5. test_truncated_row_rejected    fewer than 9 fields -> "wrong field count"
#     6. test_bad_case_id_rejected      CC-123 -> "bad case_id"
#     7. test_impossible_date_rejected  Feb 30 -> "invalid date"
#     8. test_future_date_rejected      a date in 2031 -> "future date"
#
# HOW PYTEST WORKS
#   - pytest finds files named test_*.py and runs every function named test_*.
#   - A test PASSES if its function finishes without an error.
#   - assert <condition>   fails the test if the condition is False.
#   - pytest.raises(ValueError, match="...")   passes ONLY if the code inside
#     the "with" block raises a ValueError whose message matches the text.
#
# HOW TO RUN  (in a terminal opened in this folder)
#   pytest                 expected result:  8 passed
# =============================================================================

from datetime import date

import pytest

from case_model import Case, clean_age, clean_beat, clean_date, clean_sex, clean_status, extract_phone


def make_row():
    """Return a fresh, messy-but-valid 9-field raw row (a new list on every call)."""
    # This is a helper, not a test (its name does not start with test_), so
    # pytest does not run it by itself. Each test calls it to get its OWN copy,
    # so a test that breaks one field can never affect another test.
    return [" cc-76856 ", "  walker,  g ", "Male", " 41 ", "6/7/2000",
            "7840 Webb Chapel Rd", "beat 157", "OPN", "cb: (214) 555-0202"]


# -----------------------------------------------------------------------------
# HAPPY PATHS
# -----------------------------------------------------------------------------

def test_good_row_becomes_case():
    """A messy but valid row is cleaned into a correct Case object."""
    case = Case.from_row(make_row())
    assert case.case_id == "CC-76856"          # spaces stripped, uppercased, dash in place
    assert case.victim_name == "Walker, G"     # spaces collapsed, Title Case
    assert case.sex == "M"                     # "Male" -> "M"
    assert case.age == 41                      # " 41 " -> 41 (a number, not text)
    assert case.incident_date == date(2000, 6, 7)
    assert case.year == 2000
    assert case.beat == "157"                  # "beat 157" -> "157"
    assert case.status == "OPEN"               # "OPN" -> "OPEN"
    assert case.callback_phone == "214-555-0202"
    assert case.is_stale                       # open since 2000, so far more than 5 years


def test_three_date_formats():
    """All three allowed date formats are read as the same calendar day."""
    assert clean_date("2000-06-07") == date(2000, 6, 7)
    assert clean_date("6/7/2000") == date(2000, 6, 7)
    assert clean_date("June 7, 2000") == date(2000, 6, 7)


def test_repairs_non_critical():
    """Different spellings of status, sex, age and beat are repaired, not rejected."""
    assert clean_status(" CLEARED ") == "CLOSED"
    assert clean_status("CLSD") == "CLOSED"
    assert clean_sex("unk") == "U"             # anything that isn't M or F -> U
    assert clean_age("999") is None            # impossible age -> blank
    assert clean_age("unknown") is None        # not a number -> blank
    assert clean_beat("B-150") == "150"
    assert clean_beat("") == ""                # no beat -> blank, row is still kept


def test_phone_formats():
    """All three phone styles come out as 214-555-1234, and no phone gives ''."""
    assert extract_phone("Caller left callback 214.555.1234") == "214-555-1234"
    assert extract_phone("cb: (214) 555-1234") == "214-555-1234"
    assert extract_phone("Witness can be reached at 214-555-1234") == "214-555-1234"
    assert extract_phone("possibly linked to CC-12345") == ""   # a case number is not a phone


# -----------------------------------------------------------------------------
# FAILURE PATHS  -  each one must raise ValueError with the right reason
# -----------------------------------------------------------------------------

def test_truncated_row_rejected():
    """A row cut off part way (fewer than 9 fields) is quarantined."""
    row = make_row()[:5]                       # keep only the first 5 of 9 fields
    with pytest.raises(ValueError, match="wrong field count"):
        Case.from_row(row)


def test_bad_case_id_rejected():
    """A case_id that can't be turned into CC- + 5 digits is quarantined."""
    row = make_row()
    row[0] = "CC-123"                          # only 3 digits
    with pytest.raises(ValueError, match="bad case_id"):
        Case.from_row(row)


def test_impossible_date_rejected():
    """A date with the right shape but an impossible day (Feb 30) is quarantined."""
    row = make_row()
    row[4] = "2004-02-30"
    with pytest.raises(ValueError, match="invalid date"):
        Case.from_row(row)


def test_future_date_rejected():
    """A date after 10/07/2026 is quarantined."""
    row = make_row()
    row[4] = "03/24/2031"
    with pytest.raises(ValueError, match="future date"):
        Case.from_row(row)
