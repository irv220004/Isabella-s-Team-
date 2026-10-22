"""test_cases.py - run with:  pytest test_cases.py"""
import datetime

import pytest

from case_model import (Case, clean_age, clean_beat, clean_case_id, clean_date,
                        clean_name, clean_sex, clean_status, extract_callback_phone)
from clean_cases import load_cases


def good_row(**changes):
    """Build a valid 9-field row; override any field by name, e.g. good_row(status='bogus')."""
    row = {"case_id": "cc-10003", "victim_name": " ramirez,  k ", "sex": "male", "age": " 24 ",
           "incident_date": "6/14/1992", "address": "12 main st", "beat": "beat 451",
           "status": "Closed", "tip_notes": "cb: (214) 555-0193"}
    row.update(changes)                 # replace only the fields the test cares about
    return list(row.values())           # dicts keep insertion order, so this is the 9-item list


# ---------------------------- happy paths ----------------------------------

def test_from_row_cleans_every_field():
    c = Case.from_row(good_row())
    assert c.to_row() == ["CC-10003", "Ramirez, K", "M", 24, "1992-06-14", 1992, "451", "CLOSED", "214-555-0193"]


@pytest.mark.parametrize("raw", ["cc-19495", "CC 16288", " CC-19495 ", "CC19495"])
def test_case_id_variants_normalize(raw):
    assert clean_case_id(raw) == "CC-" + raw.strip()[-5:]


def test_all_three_date_formats():
    assert clean_date("2018-03-22") == datetime.date(2018, 3, 22)
    assert clean_date("6/7/2000") == datetime.date(2000, 6, 7)          # US order: month first
    assert clean_date("July 1, 2022") == datetime.date(2022, 7, 1)


def test_repairs_never_raise():
    assert clean_age("unknown") is None and clean_age("999") is None and clean_age("-1") is None
    assert clean_age("36") == 36
    assert clean_sex("unk") == "U" and clean_sex("") == "U" and clean_sex("f") == "F"
    assert clean_beat("B-150") == "150" and clean_beat("") == ""
    assert clean_name("  JORDAN, C ") == "Jordan, C"


def test_phone_extraction_takes_first_and_reformats():
    assert extract_callback_phone("Caller left callback 214.555.3072") == "214-555-3072"
    assert extract_callback_phone("no number here") == ""
    assert extract_callback_phone("first 214-555-1111 then 972-555-2222") == "214-555-1111"


def test_status_variants():
    assert [clean_status(s) for s in ("open", "OPN", "CLSD", "cleared")] == ["OPEN", "OPEN", "CLOSED", "CLOSED"]


def test_is_stale_property():
    assert Case.from_row(good_row(status="open", incident_date="2015-01-01")).is_stale
    assert not Case.from_row(good_row(status="open", incident_date="2025-01-01")).is_stale
    assert not Case.from_row(good_row(status="closed", incident_date="2015-01-01")).is_stale


# --------------------------- failure paths ---------------------------------

@pytest.mark.parametrize("changes, reason", [
    ({"case_id": "XX-123"}, "bad case_id"),
    ({"incident_date": "N/A"}, "missing date"),
    ({"incident_date": "2004-02-30"}, "invalid date"),     # Feb 30 doesn't exist
    ({"incident_date": "13/1/2004"}, "invalid date"),      # month 13
    ({"incident_date": "01-02-2004"}, "invalid date"),     # not one of the 3 formats
    ({"incident_date": "2030-01-01"}, "future date"),
    ({"status": "pending"}, "unknown status"),
])
def test_bad_rows_raise_with_the_right_reason(changes, reason):
    with pytest.raises(ValueError, match=reason):
        Case.from_row(good_row(**changes))


def test_wrong_field_count_is_rejected():
    with pytest.raises(ValueError, match="wrong field count"):
        Case.from_row(good_row()[:8])


# ------------------------ whole-pipeline check -----------------------------

def test_loader_skips_dupes_headers_blanks_and_quarantines(tmp_path):
    header = "case_id,victim_name,sex,age,incident_date,address,beat,status,tip_notes"
    lines = [header,
             "CC-10001,\"DOE, J\",M,30,2000-01-01,x,111,OPEN,",
             "",                                            # blank line -> skipped
             header,                                        # repeated header -> skipped
             "cc 10001,\"DOE, J\",M,30,2000-01-01,x,111,OPEN,",   # same id after cleaning -> duplicate
             "CC-10002,\"ROE, R\",F,40,2000-02-30,x,222,OPEN,",   # impossible date -> quarantine
             "CC-10003,short"]                              # truncated -> quarantine
    path = tmp_path / "raw.csv"
    path.write_text("\n".join(lines), encoding="utf-8")

    cases, quarantine, stats = load_cases(str(path))

    assert [c.case_id for c in cases] == ["CC-10001"]
    assert stats["rows_read"] == 4 and stats["duplicates"] == 1
    assert stats["blank_lines"] == 1 and stats["headers"] == 2     # the real header + the repeat
    assert [(q[0], q[1]) for q in quarantine] == [(6, "invalid date"), (7, "wrong field count")]
