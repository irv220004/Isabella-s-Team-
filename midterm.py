# midterm.py - ITSS 3312 Midterm Project: The Cold Case File
# Deliverable 1 (clean data) + Deliverable 2 (code: Case class, cleaners, report)
# all live in this one file. Deliverable 3 is the 5-slide briefing itself (not
# code) - it gets built from the numbers that report.txt prints below.
#
# Usage:  python midterm.py [path_to_raw_csv]
# Produces: cases_clean.csv, quarantine.csv, report.txt
import csv                                   # reads/writes comma-separated files, handles quoted commas
import io                                    # lets us build a string in memory (used to re-quote a raw row)
import re                                    # regular expressions, for pulling patterns out of messy text
import sys                                   # lets us read the raw-file path off the command line
from collections import Counter              # a dict that counts things for us (reasons, beats, decades)
from datetime import date, datetime          # date = a calendar day; datetime = date + time, used for parsing

TODAY = date(2026, 10, 7)          # "today", per the assignment -> anything after this is a "future date"
RAW_COLUMNS = 9                    # the raw file must have exactly 9 fields per row:
                                    # case_id, victim_name, sex, age, incident_date,
                                    # address, beat, status, tip_notes

DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y")   # the 3 accepted raw date formats, tried in order

STATUS_MAP = {                     # lookup table: every raw spelling -> one of two clean values
    "OPEN": "OPEN", "OPN": "OPEN",             # both of these become "OPEN"
    "CLOSED": "CLOSED", "CLSD": "CLOSED", "CLEARED": "CLOSED",   # all three become "CLOSED"
}

CASE_ID_RE = re.compile(r"^CC[-\s]?(\d{5})$", re.IGNORECASE)   # "CC" then optional - or space, then 5 digits
BEAT_RE = re.compile(r"(\d{3})")                                # grabs the first run of exactly 3 digits
PHONE_RE = re.compile(r"\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})")  # area code, 3 digits, 4 digits,
                                                                       # with optional parens/dash/dot/space


# ---------------------------------------------------------------------------
# Week 5: one docstringed function per field cleaner, regex where it earns its keep
# ---------------------------------------------------------------------------

def clean_case_id(raw):
    """Normalize a raw case id to CC-##### or raise ValueError('bad case_id')."""
    match = CASE_ID_RE.match(raw.strip())        # strip outer spaces, then test against the pattern
    if not match:                                # match is None when the pattern didn't fit at all
        raise ValueError("bad case_id")          # tell the caller exactly why this row is unusable
    return f"CC-{match.group(1)}"                # group(1) is just the 5 digits; rebuild as CC-#####


def clean_name(raw):
    """Collapse whitespace and title-case a 'Last, Initial' name."""
    collapsed = " ".join(raw.strip().split())   # strip() removes outer spaces, split() breaks on any
                                                  # run of whitespace, " ".join() glues it back with 1 space
    return collapsed.title()                     # title() capitalizes the first letter of each word


def clean_sex(raw):
    """Map a raw sex value to 'M', 'F', or 'U' for anything else."""
    value = raw.strip().upper()                  # strip spaces, then upper() so "m"/"Male"/"MALE" all match
    if value in ("M", "MALE"):                    # covers every raw spelling that means "male"
        return "M"
    if value in ("F", "FEMALE"):                  # covers every raw spelling that means "female"
        return "F"
    return "U"                                    # anything else (blank, "unk", typos, ...) -> Unknown


def clean_age(raw):
    """Return a whole number 0-110, or '' if the value is missing/garbage."""
    value = raw.strip()                          # remove outer spaces first, e.g. " 37 " -> "37"
    if not value.isdigit():                       # isdigit() is False for "unknown", "N/A", "-1", "", etc.
        return ""                                 # anything non-numeric just gets left blank, not rejected
    age = int(value)                              # safe to convert now, we know it's all digits
    return age if 0 <= age <= 110 else ""         # keep only realistic ages; sentinel junk like 999 -> blank


def clean_date(raw):
    """Parse a raw date into a date object. Raises ValueError for a bad date."""
    value = raw.strip()                          # remove outer spaces before checking anything
    if not value or value.lower() in ("n/a", "unknown"):   # catches truly missing dates
        raise ValueError("missing date")
    for fmt in DATE_FORMATS:                      # try each accepted format in turn
        try:
            parsed = datetime.strptime(value, fmt).date()  # strptime parses text -> datetime; .date() drops the time
            break                                  # it worked, stop trying other formats
        except ValueError:
            continue                               # this format didn't match (or date was impossible), try next
    else:                                           # this "else" belongs to the for-loop: runs only if no break
        raise ValueError("invalid date")           # none of the 3 formats worked, so the date is unusable
    if parsed > TODAY:                              # a date later than "today" can't be real
        raise ValueError("future date")
    return parsed                                   # a valid, non-future date object


def clean_beat(raw):
    """Extract the 3-digit beat number, or '' if the field has none."""
    match = BEAT_RE.search(raw)                   # search() looks anywhere in the string, not just the start
    return match.group(1) if match else ""         # group(1) is the captured 3 digits; else leave it blank


def clean_status(raw):
    """Map a raw status string to OPEN/CLOSED. Raises ValueError for anything else."""
    value = raw.strip().upper()                   # normalize case/spacing before the lookup
    if value not in STATUS_MAP:                     # anything not in our lookup table is unrecognized
        raise ValueError("unknown status")
    return STATUS_MAP[value]                        # translate the raw spelling to OPEN or CLOSED


def extract_callback_phone(raw):
    """Return the first phone number in free text as ###-###-####, or '' if none."""
    match = PHONE_RE.search(raw)                   # search the whole tip_notes string for a phone pattern
    return "-".join(match.groups()) if match else ""   # groups() = (area, exchange, number); re-join with dashes


# ---------------------------------------------------------------------------
# Week 7: the Case class - from_row() is the parser, is_stale is the detective's question
# ---------------------------------------------------------------------------

class Case:
    """One cold case, built from a cleaned row of the raw CSV."""

    def __init__(self, case_id, victim_name, sex, age, incident_date, beat, status, callback_phone):
        self.case_id = case_id                      # e.g. "CC-10003"
        self.victim_name = victim_name               # e.g. "Ramirez, K"
        self.sex = sex                                # "M", "F", or "U"
        self.age = age                                # an int, or "" if unknown
        self.incident_date = incident_date            # a real date object, not a string
        self.beat = beat                              # 3-digit beat string, or ""
        self.status = status                          # "OPEN" or "CLOSED"
        self.callback_phone = callback_phone          # "214-555-1234", or ""

    @classmethod
    def from_row(cls, row):
        """Build a Case from one raw 9-field row, or raise ValueError with a reason."""
        if len(row) != RAW_COLUMNS:                  # a truncated or extra-field row can't be trusted
            raise ValueError("wrong field count")
        return cls(                                   # cls(...) calls Case(...) and returns the new object
            case_id=clean_case_id(row[0]),            # row[0] = case_id column
            victim_name=clean_name(row[1]),           # row[1] = victim_name column
            sex=clean_sex(row[2]),                    # row[2] = sex column
            age=clean_age(row[3]),                    # row[3] = age column
            incident_date=clean_date(row[4]),         # row[4] = incident_date column; row[5] (address) is dropped
            beat=clean_beat(row[6]),                  # row[6] = beat column
            status=clean_status(row[7]),              # row[7] = status column
            callback_phone=extract_callback_phone(row[8]),  # row[8] = tip_notes column
        )

    @property
    def year(self):
        return self.incident_date.year               # pull the 4-digit year out of the date object

    @property
    def years_unsolved(self):
        return TODAY.year - self.incident_date.year   # how many years between the incident and "today"

    @property
    def is_stale(self):
        """True if this case is still OPEN after 5+ years."""
        return self.status == "OPEN" and self.years_unsolved >= 5   # both conditions must hold

    def to_row(self):
        """This case's fields in cases_clean.csv column order."""
        return [self.case_id, self.victim_name, self.sex, self.age,       # first 4 clean columns
                self.incident_date.isoformat(), self.year, self.beat,     # date as text, year, beat
                self.status, self.callback_phone]                         # last 2 clean columns


def _raw_row_text(row):
    """Rebuild a raw CSV row's exact text (with proper quoting) for quarantine.csv."""
    buf = io.StringIO()                              # an in-memory text buffer, acts like a file
    csv.writer(buf).writerow(row)                     # writes the row as proper CSV text (re-quotes commas)
    return buf.getvalue().strip("\r\n")                # read the buffer back out, drop the trailing newline


# ---------------------------------------------------------------------------
# Week 3/4/6: one pass over the file, a set to dedupe, dicts to count, try/except to quarantine
# ---------------------------------------------------------------------------

def load_cases(path):
    """Read the raw CSV once. Returns (clean_cases, quarantine_rows, stats)."""
    cases = []                        # list of good Case objects, built as we go
    quarantine_rows = []              # list of [line_number, reason, raw_row] for rejected rows
    seen_ids = set()                  # a set only remembers "have I seen this before?" - perfect for dedup
    quarantine_reasons = Counter()    # a dict-like counter: quarantine_reasons["bad case_id"] += 1, etc.
    rows_read = 0                     # running total of real data rows seen (not blanks/headers)
    blank_or_header_skipped = 0       # running total of blank lines + repeated header rows
    duplicates = 0                    # running total of rows dropped for a repeated case_id

    with open(path, newline="", encoding="utf-8") as f:   # newline="" is required so csv handles line endings itself
        reader = csv.reader(f)                              # reader yields each line as a list of field strings
        header = next(reader)                               # pull off line 1 (the header) before the loop starts
        for line_number, row in enumerate(reader, start=2):  # start=2 because line 1 was already consumed above
            if not row or row == header:       # an empty list (blank line) or an exact repeat of the header
                blank_or_header_skipped += 1    # these don't count as data and aren't quarantined either
                continue                        # skip straight to the next row
            rows_read += 1                      # only real data rows reach this line
            try:
                case = Case.from_row(row)        # attempt to build a clean Case from this row
            except ValueError as err:            # any cleaner above can raise ValueError with a reason
                reason = str(err)                 # turn the exception into its plain-text message
                quarantine_reasons[reason] += 1    # bump the count for this specific reason
                quarantine_rows.append([line_number, reason, _raw_row_text(row)])   # log it for quarantine.csv
                continue                           # move on to the next row, this one is done
            if case.case_id in seen_ids:         # we've already kept a case with this exact id
                duplicates += 1                   # count it, but...
                continue                          # ...don't add it again - keep only the first occurrence
            seen_ids.add(case.case_id)           # remember this id so later duplicates get caught
            cases.append(case)                   # this case is clean and unique - keep it

    stats = {                                      # bundle all the running totals into one dict to return
        "rows_read": rows_read,
        "blank_or_header_skipped": blank_or_header_skipped,
        "quarantined": len(quarantine_rows),
        "quarantine_reasons": quarantine_reasons,
        "duplicates": duplicates,
        "clean_cases": len(cases),
    }
    return cases, quarantine_rows, stats            # hand all three results back to the caller


def write_clean_csv(cases, path="cases_clean.csv"):
    """Deliverable 1: every usable case, cleaned, sorted by case_id."""
    with open(path, "w", newline="", encoding="utf-8") as f:   # "w" = overwrite the file fresh each run
        writer = csv.writer(f)                                  # writer turns lists into proper CSV lines
        writer.writerow(["case_id", "victim_name", "sex", "age", "incident_date",   # the exact required header
                          "year", "beat", "status", "callback_phone"])
        for case in sorted(cases, key=lambda c: c.case_id):      # sort so case_id is in ascending order
            writer.writerow(case.to_row())                       # write that one case's clean fields


def write_quarantine_csv(quarantine_rows, path="quarantine.csv"):
    """Deliverable 1: every rejected row, with its line number and reason."""
    with open(path, "w", newline="", encoding="utf-8") as f:   # overwrite fresh each run, like above
        writer = csv.writer(f)
        writer.writerow(["line_number", "reason", "raw_row"])   # the exact required header
        writer.writerows(quarantine_rows)                        # writerows() writes many rows in one call


def raw_closed_rate(path):
    """The naive clearance rate: raw rows where status is exactly 'CLOSED', no cleaning at all."""
    total = closed = 0                             # two counters, both starting at 0
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)                        # skip the header line again, same as load_cases
        for row in reader:
            if not row or row == header:              # skip blanks and repeated headers here too
                continue
            total += 1                                # count every real raw row, cleaned or not
            if len(row) == RAW_COLUMNS and row[7].strip() == "CLOSED":   # row[7] = raw status column
                closed += 1                            # only counts the EXACT string "CLOSED", no normalizing
    return closed / total if total else 0.0            # guard against dividing by zero on an empty file


# ---------------------------------------------------------------------------
# report.txt: the numbers the briefing is built from
# ---------------------------------------------------------------------------

def build_report(cases, stats, raw_path):
    closed_cases = [c for c in cases if c.status == "CLOSED"]   # list comprehension: every closed clean case
    open_cases = [c for c in cases if c.status == "OPEN"]        # every open clean case
    overall_rate = len(closed_cases) / len(cases) if cases else 0.0   # closed / total, guarded against 0 cases

    lines = ["=" * 60, "COLD CASE FILE - CLEANING REPORT", "=" * 60]   # build the report as a list of text lines

    lines.append("\n1. INTAKE")                                   # \n adds a blank line before this section
    lines.append(f"  Raw data rows read:         {stats['rows_read']}")
    lines.append(f"  Blank/header rows skipped:  {stats['blank_or_header_skipped']}")
    lines.append(f"  Rows quarantined:           {stats['quarantined']}")
    for reason, count in stats["quarantine_reasons"].most_common():   # most_common() sorts biggest count first
        lines.append(f"      - {reason}: {count}")
    lines.append(f"  Duplicate case_ids removed: {stats['duplicates']}")
    lines.append(f"  Clean cases:                {stats['clean_cases']}")

    lines.append("\n2. CLEARANCE")
    lines.append(f"  Overall clearance rate: {overall_rate:.1%}")     # :.1% formats 0.622 as "62.2%"
    by_decade = {}                                                     # dict: decade -> [closed_count, total_count]
    for c in cases:                                                    # one pass over every clean case
        decade = (c.year // 10) * 10                                  # e.g. 1994 -> 1990 (integer division trick)
        closed_n, total_n = by_decade.setdefault(decade, [0, 0])      # setdefault creates [0, 0] the first time
        by_decade[decade][1] += 1                                      # bump that decade's total count
        if c.status == "CLOSED":
            by_decade[decade][0] += 1                                  # bump that decade's closed count too
    for decade in sorted(by_decade):                                   # sorted() so decades print oldest-first
        closed_n, total_n = by_decade[decade]
        rate = closed_n / total_n if total_n else 0.0
        lines.append(f"      {decade}s: {rate:.1%} ({closed_n}/{total_n})")

    lines.append("\n3. OPEN CASES")
    stale = [c for c in open_cases if c.is_stale]                      # every open case that's 5+ years old
    lines.append(f"  Stale open cases (5+ years): {len(stale)}")
    lines.append("  5 oldest open cases:")
    for c in sorted(open_cases, key=lambda c: c.incident_date)[:5]:    # sort oldest-first, keep only the first 5
        lines.append(f"      {c.case_id}  {c.victim_name}  {c.incident_date.isoformat()}"
                      f"  ({c.years_unsolved} yrs unsolved)")

    lines.append("\n4. BEATS")
    open_beat_counts = Counter(c.beat for c in open_cases if c.beat)   # counts open cases per beat, skips blank beats
    lines.append("  Top 10 beats by open-case count:")
    for beat, open_count in open_beat_counts.most_common(10):          # the 10 beats with the most open cases
        beat_cases = [c for c in cases if c.beat == beat]               # every clean case (open or closed) in this beat
        beat_closed = [c for c in beat_cases if c.status == "CLOSED"]
        beat_rate = len(beat_closed) / len(beat_cases) if beat_cases else 0.0
        lines.append(f"      Beat {beat}: {open_count} open, clearance rate {beat_rate:.1%}")

    lines.append("\n5. LEADS")
    with_phone = [c for c in open_cases if c.callback_phone]           # open cases where a phone was extracted
    leads_pct = len(with_phone) / len(open_cases) if open_cases else 0.0
    lines.append(f"  Open cases with a callback phone in tip notes: {leads_pct:.1%}")

    lines.append("\n6. RAW VS CLEAN")
    raw_rate = raw_closed_rate(raw_path)                                # re-scan the raw file with no cleaning
    lines.append(f"  Raw status==CLOSED rate (no cleaning): {raw_rate:.1%}")
    lines.append(f"  Cleaned clearance rate:                {overall_rate:.1%}")
    lines.append(f"  Difference:                            {overall_rate - raw_rate:+.1%}")   # +.1% shows the sign

    return "\n".join(lines)                                             # glue every line together with newlines


# ---------------------------------------------------------------------------
# One command: raw file in, three files out
# ---------------------------------------------------------------------------

def main(raw_path="midterm_cases_raw.csv"):
    cases, quarantine_rows, stats = load_cases(raw_path)   # step 1: read and clean the raw file
    write_clean_csv(cases)                                  # step 2: write cases_clean.csv
    write_quarantine_csv(quarantine_rows)                   # step 3: write quarantine.csv
    report = build_report(cases, stats, raw_path)           # step 4: build the report text
    print(report)                                           # show it on screen
    with open("report.txt", "w", encoding="utf-8") as f:    # step 5: also save it to report.txt
        f.write(report + "\n")                               # trailing \n so the file ends cleanly


if __name__ == "__main__":                                  # only runs when this file is executed directly,
    main(sys.argv[1] if len(sys.argv) > 1 else "midterm_cases_raw.csv")   # not when pytest imports it for tests
    # sys.argv[1] is the first command-line argument (the raw file path), if the user gave one


# ---------------------------------------------------------------------------
# Week 6: pytest tests - 5+ tests, at least 2 failure paths (run: pytest midterm.py)
# ---------------------------------------------------------------------------
try:
    import pytest                  # gives us pytest.raises() to check for exceptions
except ModuleNotFoundError:
    pytest = None                  # pytest isn't installed in this interpreter -
                                    # fine for "python midterm.py", just means the
                                    # tests below can't run (install pytest to run them)


def _good_row():
    """A known-good 9-field row every test can start from and then break in one spot."""
    return ["CC-10003", " ramirez, k ", "M", "24", "1992-06-14",   # a row that should clean up without errors
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
