"""test_intake.py - pytest suite proving intake_safe.py actually works (slide 8).

WHY TESTS (slide 8): "it worked when I ran it" is a vibe, not proof. Each
test below locks in one specific promise the parser makes, so a future
change that breaks that promise fails loudly here instead of quietly in
the field.

RUN WITH:  pytest test_intake.py
"""

import pytest  # provides pytest.raises(...) for asserting that bad input raises the right error

from intake_safe import parse_row, load_cases  # the two functions this suite holds accountable


def test_good_row_parses():
    """A clean, well-formed row should parse without raising and produce correct values."""
    row = ["CC-1", " carter, d ", "m", "36", "2018-03-22", "412 larkmoor", "352", "open"]
    case = parse_row(row)              # the happy path - this call must NOT raise
    assert case["age"] == 36           # "36" (string) correctly converted to 36 (int)
    assert case["name"] == "Carter, D"  # " carter, d " correctly stripped + title-cased
    assert case["status"] == "OPEN"    # "open" correctly uppercased


def test_bad_age_rejected():
    """A row with a non-numeric age ('unknown') must raise ValueError, not crash the caller."""
    row = ["CC-2", "Doe, J", "M", "unknown", "2018-03-22", "1 Main St", "100", "OPEN"]
    with pytest.raises(ValueError):   # int("unknown") is exactly where this fails
        parse_row(row)


def test_missing_date_rejected():
    """A row with a blank date field must raise ValueError with a clear, specific reason."""
    row = ["CC-3", "Doe, J", "M", "40", "", "1 Main St", "100", "OPEN"]
    with pytest.raises(ValueError, match="missing date"):  # our own custom message, not int()'s
        parse_row(row)


def test_truncated_row_rejected():
    """A row missing trailing fields (beat/status dropped) must raise ValueError, not IndexError."""
    row = ["CC-4", "Doe, J", "M", "40", "2018-03-22", "1 Main St"]  # only 6 of the required 8 fields
    with pytest.raises(ValueError, match="expected 8 fields"):
        parse_row(row)


def test_load_cases_matches_required_totals():
    """End-to-end check against the real lab file: the totals must match slide 13 exactly."""
    good, quarantine = load_cases("wk06_data_raw_cases_100.csv")
    assert len(good) == 89        # the required "Rows loaded cleanly" count
    assert len(quarantine) == 11  # the required "Rows quarantined" count


def test_blank_line_is_skipped_quietly(tmp_path):
    """Stretch (slide 14): a genuinely blank line must be skipped, not crash and not get logged."""
    mini_csv = tmp_path / "mini.csv"  # pytest's tmp_path fixture - a throwaway folder just for this test
    mini_csv.write_text(
        "case_id,victim_name,sex,age,date,address,beat,status\n"
        "CC-1,Doe J,M,40,2018-03-22,1 Main St,100,OPEN\n"
        "\n"
        "CC-2,Roe A,F,30,2019-01-01,2 Oak St,101,CLOSED\n",
        encoding="utf-8",
    )
    good, quarantine = load_cases(str(mini_csv))
    assert len(good) == 2        # both real rows loaded despite the blank line between them
    assert len(quarantine) == 0  # the blank line produced no crash AND no quarantine entry
