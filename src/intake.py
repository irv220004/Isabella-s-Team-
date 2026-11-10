# src/intake.py - field cleaners + the quarantine loader (weeks 2, 3, 4, 5, 6)
# Renovated out of midterm.py into the package layout week 8 asks for.
import csv                                   # reads/writes comma-separated files, handles quoted commas
import io                                    # lets us build a string in memory (used to re-quote a raw row)
from collections import Counter              # a dict that counts things for us (reasons, beats, decades)
from datetime import date, datetime          # date = a calendar day; datetime = date + time, used for parsing

from src.patterns import extract_case_id, extract_beat, extract_phone   # the regex work lives there now

TODAY = date(2026, 10, 7)          # "today", per the cleaning standard -> future-date cutoff
RAW_COLUMNS = 9                    # the raw file must have exactly 9 fields per row:
                                    # case_id, victim_name, sex, age, incident_date,
                                    # address, beat, status, tip_notes

DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y")   # the 3 accepted raw date formats, tried in order

STATUS_MAP = {                     # lookup table: every raw spelling -> one of two clean values
    "OPEN": "OPEN", "OPN": "OPEN",             # both of these become "OPEN"
    "CLOSED": "CLOSED", "CLSD": "CLOSED", "CLEARED": "CLOSED",   # all three become "CLOSED"
}


# -----------------------------------------------------------------------------
# Field cleaners - one docstringed function per column
# -----------------------------------------------------------------------------

def clean_case_id(raw):
    """Normalize a raw case id to CC-##### or raise ValueError('bad case_id')."""
    digits = extract_case_id(raw)                # regex work is delegated to patterns.py
    if digits is None:                           # None means the shape didn't fit at all
        raise ValueError("bad case_id")          # tell the caller exactly why this row is unusable
    return f"CC-{digits}"                        # rebuild the id in the one standard format


def clean_name(raw):
    """Collapse whitespace and title-case a 'Last, Initial' name."""
    stripped = raw.strip()                        # remove the outer spaces, e.g. "  JORDAN,  C " -> "JORDAN,  C"
    words = stripped.split()                       # split on ANY run of whitespace, dropping empty pieces
    collapsed = " ".join(words)                     # glue the words back with exactly one space between them
    return collapsed.title()                        # capitalize the first letter of each word: "Jordan, C"


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
    digits = extract_beat(raw)                    # delegate the regex search to patterns.py
    return digits if digits else ""               # None (nothing found) becomes "" instead


def clean_status(raw):
    """Map a raw status string to OPEN/CLOSED. Raises ValueError for anything else."""
    value = raw.strip().upper()                   # normalize case/spacing before the lookup
    if value not in STATUS_MAP:                     # anything not in our lookup table is unrecognized
        raise ValueError("unknown status")
    return STATUS_MAP[value]                        # translate the raw spelling to OPEN or CLOSED


def extract_callback_phone(raw):
    """Return the first phone number in free text as ###-###-####, or '' if none."""
    phone = extract_phone(raw)                     # delegate the regex search to patterns.py
    return phone if phone else ""                  # None (nothing found) becomes "" instead


def _raw_row_text(row):
    """Rebuild a raw CSV row's exact text (with proper quoting) for quarantine.csv."""
    buf = io.StringIO()                              # an in-memory text buffer, acts like a file
    csv.writer(buf).writerow(row)                     # writes the row as proper CSV text (re-quotes commas)
    return buf.getvalue().strip("\r\n")                # read the buffer back out, drop the trailing newline


# -----------------------------------------------------------------------------
# load_cases - one pass over every row, a set to dedupe, dicts to count,
# try/except to quarantine (weeks 3, 4, 6)
# -----------------------------------------------------------------------------

def load_cases(path):
    """Read the raw CSV once. Returns (clean_cases, quarantine_rows, stats)."""
    from src.models import Case            # imported here to avoid a circular import
    # (models.py imports clean_* functions FROM this file, so this file can't
    # import Case back at the top - doing it inside the function breaks the cycle)

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
    """Every usable case, cleaned, sorted by case_id."""
    with open(path, "w", newline="", encoding="utf-8") as f:   # "w" = overwrite the file fresh each run
        writer = csv.writer(f)                                  # writer turns lists into proper CSV lines
        writer.writerow(["case_id", "victim_name", "sex", "age", "incident_date",   # the exact required header
                          "year", "beat", "status", "callback_phone"])
        for case in sorted(cases, key=lambda c: c.case_id):      # sort so case_id is in ascending order
            writer.writerow(case.to_row())                       # write that one case's clean fields


def write_quarantine_csv(quarantine_rows, path="quarantine.csv"):
    """Every rejected row, with its line number and reason."""
    with open(path, "w", newline="", encoding="utf-8") as f:   # overwrite fresh each run, like above
        writer = csv.writer(f)
        writer.writerow(["line_number", "reason", "raw_row"])   # the exact required header
        writer.writerows(quarantine_rows)                        # writerows() writes many rows in one call


def raw_closed_rate(path):
    """The naive clearance rate: raw rows where status is exactly 'CLOSED', no cleaning at all."""
    total = closed = 0                             # two counters, both starting at 0
    with open(path, newline="", encoding="utf-8") as f:   # open the raw file for a second, separate pass
        reader = csv.reader(f)                        # same csv.reader as load_cases uses
        header = next(reader)                        # skip the header line again, same as load_cases
        for row in reader:                            # walk every remaining row
            if not row or row == header:              # skip blanks and repeated headers here too
                continue
            total += 1                                # count every real raw row, cleaned or not
            if len(row) == RAW_COLUMNS and row[7].strip() == "CLOSED":   # row[7] = raw status column
                closed += 1                            # only counts the EXACT string "CLOSED", no normalizing
    return closed / total if total else 0.0            # guard against dividing by zero on an empty file


def build_report(cases, stats, raw_path):
    """The intake/clearance/open-cases/beats/leads/raw-vs-clean report, as one text block."""
    closed_cases = [c for c in cases if c.status == "CLOSED"]   # list comprehension: every closed clean case
    open_cases = [c for c in cases if c.status == "OPEN"]        # every open clean case
    overall_rate = len(closed_cases) / len(cases) if cases else 0.0   # closed / total, guarded against 0 cases

    lines = ["=" * 60, "COLD CASE FILE - CLEANING REPORT", "=" * 60]   # build the report as a list of text lines

    lines.append("\n1. INTAKE")                                   # \n adds a blank line before this section
    lines.append(f"  Raw data rows read:         {stats['rows_read']}")              # how many real data rows existed
    lines.append(f"  Blank/header rows skipped:  {stats['blank_or_header_skipped']}")  # blanks + repeated headers
    lines.append(f"  Rows quarantined:           {stats['quarantined']}")            # total rejected rows
    for reason, count in stats["quarantine_reasons"].most_common():   # most_common() sorts biggest count first
        lines.append(f"      - {reason}: {count}")                     # one line per distinct rejection reason
    lines.append(f"  Duplicate case_ids removed: {stats['duplicates']}")  # rows dropped as repeats
    lines.append(f"  Clean cases:                {stats['clean_cases']}")  # how many cases actually survived

    lines.append("\n2. CLEARANCE")                                      # start the clearance section
    lines.append(f"  Overall clearance rate: {overall_rate:.1%}")     # :.1% formats 0.622 as "62.2%"
    by_decade = {}                                                     # dict: decade -> [closed_count, total_count]
    for c in cases:                                                    # one pass over every clean case
        decade = (c.year // 10) * 10                                  # e.g. 1994 -> 1990 (integer division trick)
        by_decade.setdefault(decade, [0, 0])                          # setdefault creates [0, 0] the first time
        by_decade[decade][1] += 1                                      # bump that decade's total count
        if c.status == "CLOSED":                                       # only count closed cases toward "closed"
            by_decade[decade][0] += 1                                  # bump that decade's closed count too
    for decade in sorted(by_decade):                                   # sorted() so decades print oldest-first
        closed_n, total_n = by_decade[decade]                           # unpack this decade's [closed, total] pair
        rate = closed_n / total_n if total_n else 0.0                   # that decade's own clearance rate
        lines.append(f"      {decade}s: {rate:.1%} ({closed_n}/{total_n})")  # print the decade's line

    lines.append("\n3. OPEN CASES")                                     # start the open-cases section
    stale = [c for c in open_cases if c.is_stale]                      # every open case that's 5+ years old
    lines.append(f"  Stale open cases (5+ years): {len(stale)}")       # how many open cases are stale
    lines.append("  5 oldest open cases:")                              # header line for the list below
    for c in sorted(open_cases, key=lambda c: c.incident_date)[:5]:    # sort oldest-first, keep only the first 5
        lines.append(f"      {c.case_id}  {c.victim_name}  {c.incident_date.isoformat()}"  # id, name, date
                      f"  ({c.years_unsolved} yrs unsolved)")            # how long it's been open

    lines.append("\n4. BEATS")                                          # start the beats section
    open_beat_counts = Counter(c.beat for c in open_cases if c.beat)   # counts open cases per beat, skips blank beats
    lines.append("  Top 10 beats by open-case count:")                  # header line for the table below
    for beat, open_count in open_beat_counts.most_common(10):          # the 10 beats with the most open cases
        beat_cases = [c for c in cases if c.beat == beat]               # every clean case (open or closed) in this beat
        beat_closed = [c for c in beat_cases if c.status == "CLOSED"]   # just the closed ones in this beat
        beat_rate = len(beat_closed) / len(beat_cases) if beat_cases else 0.0  # this beat's own clearance rate
        lines.append(f"      Beat {beat}: {open_count} open, clearance rate {beat_rate:.1%}")  # print the beat's line

    lines.append("\n5. LEADS")                                          # start the leads section
    with_phone = [c for c in open_cases if c.callback_phone]           # open cases where a phone was extracted
    leads_pct = len(with_phone) / len(open_cases) if open_cases else 0.0  # % of open cases with a usable lead
    lines.append(f"  Open cases with a callback phone in tip notes: {leads_pct:.1%}")  # print that percentage

    lines.append("\n6. RAW VS CLEAN")                                   # start the raw-vs-clean section
    raw_rate = raw_closed_rate(raw_path)                                # re-scan the raw file with no cleaning
    lines.append(f"  Raw status==CLOSED rate (no cleaning): {raw_rate:.1%}")  # the naive, uncleaned rate
    lines.append(f"  Cleaned clearance rate:                {overall_rate:.1%}")  # the real, cleaned rate
    lines.append(f"  Difference:                            {overall_rate - raw_rate:+.1%}")   # +.1% shows the sign

    return "\n".join(lines)                                             # glue every line together with newlines


def main(raw_path="data/midterm_cases_raw.csv"):
    cases, quarantine_rows, stats = load_cases(raw_path)   # step 1: read and clean the raw file
    write_clean_csv(cases, "reports/cases_clean.csv")       # step 2: write the clean cases out
    write_quarantine_csv(quarantine_rows, "reports/quarantine.csv")   # step 3: write the rejects out
    report = build_report(cases, stats, raw_path)           # step 4: build the report text
    print(report)                                           # show it on screen
    with open("reports/report.txt", "w", encoding="utf-8") as f:    # step 5: also save it to a file
        f.write(report + "\n")                               # trailing \n so the file ends cleanly


if __name__ == "__main__":                                  # only runs when this file is executed directly,
    main()                                                    # e.g. `python -m src.intake` - not when imported
