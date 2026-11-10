# tests/test_intake.py - proof the renovated package still works (week 6/8)
import pytest

from src.intake import clean_age, clean_case_id, clean_date, clean_sex, clean_status
from src.models import Case


def _good_row():
    """A known-good 9-field row every test can start from and then break in one spot."""
    return ["CC-10003", " ramirez, k ", "M", "24", "1992-06-14",
            "412 Larkmoor Ln", "451", "CLOSED", "cb 214-555-0193"]


def test_case_from_row_builds_case():
    case = Case.from_row(_good_row())
    assert case.case_id == "CC-10003"
    assert case.victim_name == "Ramirez, K"
    assert case.year == 1992
    assert case.callback_phone == "214-555-0193"


def test_clean_case_id_rejects_bad_value():          # failure path
    with pytest.raises(ValueError):
        clean_case_id("not-a-case-id")


def test_clean_status_rejects_unknown():              # failure path
    with pytest.raises(ValueError):
        clean_status("PENDING")


def test_clean_date_rejects_missing_date():           # failure path
    with pytest.raises(ValueError):
        clean_date("unknown")


def test_clean_date_rejects_future_date():            # failure path
    with pytest.raises(ValueError):
        clean_date("2030-01-01")


def test_clean_age_out_of_range_is_blank():
    assert clean_age("999") == ""
    assert clean_age("-1") == ""
    assert clean_age("36") == 36


def test_clean_sex_defaults_to_u():
    assert clean_sex("unk") == "U"
    assert clean_sex("Male") == "M"
    assert clean_sex("female") == "F"


def test_is_stale_property():
    row = _good_row()
    row[7] = "OPEN"
    row[4] = "2015-01-01"               # more than 5 years before TODAY (2026-10-07)
    case = Case.from_row(row)
    assert case.is_stale is True
