# src/intake.py - field cleaners + the quarantine loader (weeks 2, 3, 4, 5, 6)
# Renovated out of midterm.py into the package layout week 8 asks for.
import csv
import io
from collections import Counter
from datetime import date, datetime

from src.patterns import extract_case_id, extract_beat, extract_phone

TODAY = date(2026, 10, 7)          # "today", per the cleaning standard -> future-date cutoff
RAW_COLUMNS = 9                    # case_id, victim_name, sex, age, incident_date,
                                    # address, beat, status, tip_notes

DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y")   # the 3 accepted raw date formats

STATUS_MAP = {                     # every raw spelling collapses to one of two values
    "OPEN": "OPEN", "OPN": "OPEN",
    "CLOSED": "CLOSED", "CLSD": "CLOSED", "CLEARED": "CLOSED",
}


# -----------------------------------------------------------------------------
# Field cleaners - one docstringed function per column
# -----------------------------------------------------------------------------

def clean_case_id(raw):
    """Normalize a raw case id to CC-##### or raise ValueError('bad case_id')."""
    digits = extract_case_id(raw)                # regex work is delegated to patterns.py
    if digits is None:
        raise ValueError("bad case_id")
    return f"CC-{digits}"


def clean_name(raw):
    """Collapse whitespace and title-case a 'Last, Initial' name."""
    return " ".join(raw.strip().split()).title()


def clean_sex(raw):
    """Map a raw sex value to 'M', 'F', or 'U' for anything else."""
    value = raw.strip().upper()
    if value in ("M", "MALE"):
        return "M"
    if value in ("F", "FEMALE"):
        return "F"
    return "U"


def clean_age(raw):
    """Return a whole number 0-110, or '' if the value is missing/garbage."""
    value = raw.strip()
    if not value.isdigit():
        return ""
    age = int(value)
    return age if 0 <= age <= 110 else ""


def clean_date(raw):
    """Parse a raw date into a date object. Raises ValueError for a bad date."""
    value = raw.strip()
    if not value or value.lower() in ("n/a", "unknown"):
        raise ValueError("missing date")
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt).date()
            break
        except ValueError:
            continue
    else:
        raise ValueError("invalid date")
    if parsed > TODAY:
        raise ValueError("future date")
    return parsed


def clean_beat(raw):
    """Extract the 3-digit beat number, or '' if the field has none."""
    digits = extract_beat(raw)
    return digits if digits else ""


def clean_status(raw):
    """Map a raw status string to OPEN/CLOSED. Raises ValueError for anything else."""
    value = raw.strip().upper()
    if value not in STATUS_MAP:
        raise ValueError("unknown status")
    return STATUS_MAP[value]


def extract_callback_phone(raw):
    """Return the first phone number in free text as ###-###-####, or '' if none."""
    phone = extract_phone(raw)
    return phone if phone else ""


def _raw_row_text(row):
    """Rebuild a raw CSV row's exact text (with proper quoting) for quarantine.csv."""
    buf = io.StringIO()
    csv.writer(buf).writerow(row)
    return buf.getvalue().strip("\r\n")


# -----------------------------------------------------------------------------
# load_cases - one pass over every row, a set to dedupe, dicts to count,
# try/except to quarantine (weeks 3, 4, 6)
# -----------------------------------------------------------------------------

def load_cases(path):
    """Read the raw CSV once. Returns (clean_cases, quarantine_rows, stats)."""
    from src.models import Case            # imported here to avoid a circular import

    cases = []
    quarantine_rows = []
    seen_ids = set()
    quarantine_reasons = Counter()
    rows_read = 0
    blank_or_header_skipped = 0
    duplicates = 0

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for line_number, row in enumerate(reader, start=2):
            if not row or row == header:
                blank_or_header_skipped += 1
                continue
            rows_read += 1
            try:
                case = Case.from_row(row)
            except ValueError as err:
                reason = str(err)
                quarantine_reasons[reason] += 1
                quarantine_rows.append([line_number, reason, _raw_row_text(row)])
                continue
            if case.case_id in seen_ids:
                duplicates += 1
                continue
            seen_ids.add(case.case_id)
            cases.append(case)

    stats = {
        "rows_read": rows_read,
        "blank_or_header_skipped": blank_or_header_skipped,
        "quarantined": len(quarantine_rows),
        "quarantine_reasons": quarantine_reasons,
        "duplicates": duplicates,
        "clean_cases": len(cases),
    }
    return cases, quarantine_rows, stats


def write_clean_csv(cases, path="cases_clean.csv"):
    """Every usable case, cleaned, sorted by case_id."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "victim_name", "sex", "age", "incident_date",
                          "year", "beat", "status", "callback_phone"])
        for case in sorted(cases, key=lambda c: c.case_id):
            writer.writerow(case.to_row())


def write_quarantine_csv(quarantine_rows, path="quarantine.csv"):
    """Every rejected row, with its line number and reason."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["line_number", "reason", "raw_row"])
        writer.writerows(quarantine_rows)


def raw_closed_rate(path):
    """The naive clearance rate: raw rows where status is exactly 'CLOSED', no cleaning at all."""
    total = closed = 0
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if not row or row == header:
                continue
            total += 1
            if len(row) == RAW_COLUMNS and row[7].strip() == "CLOSED":
                closed += 1
    return closed / total if total else 0.0


def build_report(cases, stats, raw_path):
    """The intake/clearance/open-cases/beats/leads/raw-vs-clean report, as one text block."""
    closed_cases = [c for c in cases if c.status == "CLOSED"]
    open_cases = [c for c in cases if c.status == "OPEN"]
    overall_rate = len(closed_cases) / len(cases) if cases else 0.0

    lines = ["=" * 60, "COLD CASE FILE - CLEANING REPORT", "=" * 60]

    lines.append("\n1. INTAKE")
    lines.append(f"  Raw data rows read:         {stats['rows_read']}")
    lines.append(f"  Blank/header rows skipped:  {stats['blank_or_header_skipped']}")
    lines.append(f"  Rows quarantined:           {stats['quarantined']}")
    for reason, count in stats["quarantine_reasons"].most_common():
        lines.append(f"      - {reason}: {count}")
    lines.append(f"  Duplicate case_ids removed: {stats['duplicates']}")
    lines.append(f"  Clean cases:                {stats['clean_cases']}")

    lines.append("\n2. CLEARANCE")
    lines.append(f"  Overall clearance rate: {overall_rate:.1%}")
    by_decade = {}
    for c in cases:
        decade = (c.year // 10) * 10
        by_decade.setdefault(decade, [0, 0])
        by_decade[decade][1] += 1
        if c.status == "CLOSED":
            by_decade[decade][0] += 1
    for decade in sorted(by_decade):
        closed_n, total_n = by_decade[decade]
        rate = closed_n / total_n if total_n else 0.0
        lines.append(f"      {decade}s: {rate:.1%} ({closed_n}/{total_n})")

    lines.append("\n3. OPEN CASES")
    stale = [c for c in open_cases if c.is_stale]
    lines.append(f"  Stale open cases (5+ years): {len(stale)}")
    lines.append("  5 oldest open cases:")
    for c in sorted(open_cases, key=lambda c: c.incident_date)[:5]:
        lines.append(f"      {c.case_id}  {c.victim_name}  {c.incident_date.isoformat()}"
                      f"  ({c.years_unsolved} yrs unsolved)")

    lines.append("\n4. BEATS")
    open_beat_counts = Counter(c.beat for c in open_cases if c.beat)
    lines.append("  Top 10 beats by open-case count:")
    for beat, open_count in open_beat_counts.most_common(10):
        beat_cases = [c for c in cases if c.beat == beat]
        beat_closed = [c for c in beat_cases if c.status == "CLOSED"]
        beat_rate = len(beat_closed) / len(beat_cases) if beat_cases else 0.0
        lines.append(f"      Beat {beat}: {open_count} open, clearance rate {beat_rate:.1%}")

    lines.append("\n5. LEADS")
    with_phone = [c for c in open_cases if c.callback_phone]
    leads_pct = len(with_phone) / len(open_cases) if open_cases else 0.0
    lines.append(f"  Open cases with a callback phone in tip notes: {leads_pct:.1%}")

    lines.append("\n6. RAW VS CLEAN")
    raw_rate = raw_closed_rate(raw_path)
    lines.append(f"  Raw status==CLOSED rate (no cleaning): {raw_rate:.1%}")
    lines.append(f"  Cleaned clearance rate:                {overall_rate:.1%}")
    lines.append(f"  Difference:                            {overall_rate - raw_rate:+.1%}")

    return "\n".join(lines)


def main(raw_path="data/midterm_cases_raw.csv"):
    cases, quarantine_rows, stats = load_cases(raw_path)
    write_clean_csv(cases, "reports/cases_clean.csv")
    write_quarantine_csv(quarantine_rows, "reports/quarantine.csv")
    report = build_report(cases, stats, raw_path)
    print(report)
    with open("reports/report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")


if __name__ == "__main__":
    main()
