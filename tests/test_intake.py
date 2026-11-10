# tests/test_intake.py - proof the renovated package still works (week 6/8)
import pytest                                 # gives us pytest.raises() to check for exceptions

from src.intake import clean_age, clean_case_id, clean_date, clean_sex, clean_status
from src.models import Case


def _good_row():
    """A known-good 9-field row every test can start from and then break in one spot."""
    return ["CC-10003", " ramirez, k ", "M", "24", "1992-06-14",
            "412 Larkmoor Ln", "451", "CLOSED", "cb 214-555-0193"]
    # not named test_*, so pytest treats this as a helper function, not a test to run


def test_case_from_row_builds_case():
    case = Case.from_row(_good_row())             # should succeed and return a real Case object
    assert case.case_id == "CC-10003"             # case_id passed through unchanged (already clean)
    assert case.victim_name == "Ramirez, K"       # name was cleaned: stripped + title-cased
    assert case.year == 1992                      # year was pulled from the incident_date
    assert case.callback_phone == "214-555-0193"  # phone was found in tip_notes and reformatted


def test_clean_case_id_rejects_bad_value():          # failure path
    with pytest.raises(ValueError):                   # the indented block below MUST raise ValueError
        clean_case_id("not-a-case-id")                # doesn't match the CC-##### pattern at all


def test_clean_status_rejects_unknown():              # failure path
    with pytest.raises(ValueError):
        clean_status("PENDING")                       # not in STATUS_MAP, so this must raise


def test_clean_date_rejects_missing_date():           # failure path
    with pytest.raises(ValueError):
        clean_date("unknown")                         # blank-equivalent text must raise "missing date"


def test_clean_date_rejects_future_date():            # failure path
    with pytest.raises(ValueError):
        clean_date("2030-01-01")                      # later than TODAY (2026-10-07), must raise


def test_clean_age_out_of_range_is_blank():
    assert clean_age("999") == ""                     # sentinel junk value -> blank, not kept as-is
    assert clean_age("-1") == ""                      # not a digit string (minus sign) -> blank
    assert clean_age("36") == 36                       # a normal age -> kept as an int


def test_clean_sex_defaults_to_u():
    assert clean_sex("unk") == "U"                    # unrecognized value -> Unknown
    assert clean_sex("Male") == "M"                    # any spelling of male -> M
    assert clean_sex("female") == "F"                  # any spelling of female -> F


def test_is_stale_property():
    row = _good_row()                                  # start from the known-good row
    row[7] = "OPEN"                                     # corrupt just the status field to OPEN
    row[4] = "2015-01-01"               # more than 5 years before TODAY (2026-10-07)
    case = Case.from_row(row)
    assert case.is_stale is True                       # OPEN + 11 years old must count as stale
