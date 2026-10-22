"""clean_cases.py - raw file in; cases_clean.csv, quarantine.csv and report.txt out.

Run:  python clean_cases.py                      (reads midterm_cases_raw.csv)
      python clean_cases.py path/to/other_file.csv

Weeks used: 3 (one loop + accumulators), 4 (set + dicts), 6 (csv, try/except), 7 (Case objects).
"""
import csv
import sys

from case_model import Case, today

default_input = "midterm_cases_raw.csv"
clean_header = ["case_id", "victim_name", "sex", "age", "incident_date", "year", "beat", "status", "callback_phone"]


def percentage(part, whole):
    """Format part/whole as a percent string like '41.3%'; 'n/a' if whole is 0 (no ZeroDivisionError)."""
    if whole == 0:
        return "n/a"
    return f"{part / whole * 100:.1f}%"


def is_header(row):
    """True for the header line or a repeated header from a merged export."""
    return row[0].strip().lower() == "case_id"      # a real case id never equals the column name


# ---------------------------------------------------------------------------
# LOADING: one pass over the file (week 3) with the quarantine pattern (week 6)
# ---------------------------------------------------------------------------

def load_cases(path):
    """Read the raw file; return (cases, quarantine, stats). Never crashes on a bad row."""
    cases = []                  # Case objects that survived cleaning
    quarantine = []             # (line_number, reason, raw_row) for every rejected row
    seen_ids = set()            # week 4: a set answers "have we kept this case_id already?" instantly
    reason_counts = {}          # week 4: dict tally of quarantine reasons
    raw_status_fixed = {}       # dict tally: spellings that really mean CLOSED but aren't exactly "CLOSED"
    stats = {"rows_read": 0, "blank_lines": 0, "headers": 0, "duplicates": 0, "raw_exact_closed": 0}

    # utf-8-sig quietly removes the invisible BOM some Excel exports put at the very start of the file.
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            line_number = reader.line_num       # the reader tracks the physical line for us

            if not any(cell.strip() for cell in row):   # [] or only whitespace = a blank line
                stats["blank_lines"] += 1
                continue                                # SKIP, don't quarantine (slide 4)
            if is_header(row):
                stats["headers"] += 1
                continue                                # also a skip

            stats["rows_read"] += 1                     # from here on it counts as a DATA row

            # For question 6 of the report: how many rows say exactly "CLOSED" in the raw file?
            if len(row) == 9 and row[7] == "CLOSED":    # no strip(), no upper(): "exactly" means exactly
                stats["raw_exact_closed"] += 1

            try:
                case = Case.from_row(row)               # the risky call: may raise ValueError
            except ValueError as err:                   # catch the SPECIFIC error, never a bare except
                reason = str(err)
                quarantine.append((line_number, reason, row))
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
                continue                                # keep looping

            if case.case_id in seen_ids:                # duplicate AFTER cleaning (so 'cc-1' and 'CC 1' match)
                stats["duplicates"] += 1
                continue                                # keep the first one, drop this one
            seen_ids.add(case.case_id)
            cases.append(case)

            raw_status = row[7].strip()
            if case.status == "CLOSED" and raw_status != "CLOSED":      # e.g. 'closed', 'CLSD', 'CLEARED'
                raw_status_fixed[raw_status] = raw_status_fixed.get(raw_status, 0) + 1

    cases.sort(key=lambda c: c.case_id)                 # slide 5: clean file sorted by case_id
    stats["reason_counts"] = reason_counts
    stats["raw_status_fixed"] = raw_status_fixed
    return cases, quarantine, stats


# ---------------------------------------------------------------------------
# OUTPUT FILES
# ---------------------------------------------------------------------------

def write_clean_csv(cases, path="cases_clean.csv"):
    """Write cases_clean.csv in the exact slide-5 format."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")     # csv adds quotes only where needed, e.g. "Ramirez, K"
        writer.writerow(clean_header)
        for case in cases:
            writer.writerow(case.to_row())


def write_quarantine_csv(quarantine, path="quarantine.csv"):
    """Write quarantine.csv: line_number, reason, raw_row."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["line_number", "reason", "raw_row"])
        for line_number, reason, row in quarantine:
            writer.writerow([line_number, reason, ",".join(row)])   # rebuild the raw line as one text cell


# ---------------------------------------------------------------------------
# REPORT: answers the 6 questions on slide 7
# ---------------------------------------------------------------------------

def build_report(cases, quarantine, stats):
    """Return the whole report as one string (so we can both print it and save it)."""
    total = len(cases)

    # ONE pass over the clean cases collects every accumulator we need (week 3).
    closed = 0
    stale = 0
    open_cases = []
    open_with_phone = 0
    decade_total = {}           # {1980: how many cases}
    decade_closed = {}          # {1980: how many closed}
    beat_open = {}              # {'451': open cases}
    beat_total = {}             # {'451': all cases}
    beat_closed = {}            # {'451': closed cases}
    for c in cases:
        decade_total[c.decade] = decade_total.get(c.decade, 0) + 1
        if c.status == "CLOSED":
            closed += 1
            decade_closed[c.decade] = decade_closed.get(c.decade, 0) + 1
        else:
            open_cases.append(c)
            if c.is_stale:
                stale += 1
            if c.callback_phone:
                open_with_phone += 1
        if c.beat:                                      # blank beats can't be ranked
            beat_total[c.beat] = beat_total.get(c.beat, 0) + 1
            if c.status == "CLOSED":
                beat_closed[c.beat] = beat_closed.get(c.beat, 0) + 1
            else:
                beat_open[c.beat] = beat_open.get(c.beat, 0) + 1

    L = []                                              # L collects the report lines
    L.append("COLD CASE FILE - REPORT")
    L.append(f"Reference date: {today.isoformat()}")

    # 1. INTAKE ---------------------------------------------------------
    quarantined = len(quarantine)
    L.append("")
    L.append("1. INTAKE")
    L.append(f"  Data rows read:          {stats['rows_read']}")
    L.append(f"  Blank lines skipped:     {stats['blank_lines']}")
    L.append(f"  Header rows skipped:     {stats['headers']}")
    L.append(f"  Rows quarantined:        {quarantined}")
    for reason, count in sorted(stats["reason_counts"].items(), key=lambda kv: -kv[1]):
        L.append(f"      {reason}: {count}")
    L.append(f"  Duplicates removed:      {stats['duplicates']}")
    L.append(f"  Clean cases:             {total}")
    L.append(f"  Funnel check: {stats['rows_read']} - {quarantined} - {stats['duplicates']} = "
             f"{stats['rows_read'] - quarantined - stats['duplicates']}")

    # 2. CLEARANCE ------------------------------------------------------
    L.append("")
    L.append("2. CLEARANCE")
    L.append(f"  Overall clearance rate:  {percentage(closed, total)}  ({closed} closed of {total})")
    for decade in sorted(decade_total):
        d_closed = decade_closed.get(decade, 0)         # .get(..., 0): a decade may have no closed cases
        L.append(f"  {decade}s: {percentage(d_closed, decade_total[decade]):>6}  ({d_closed}/{decade_total[decade]})")

    # 3. OPEN CASES -----------------------------------------------------
    L.append("")
    L.append("3. OPEN CASES")
    L.append(f"  Open cases:              {len(open_cases)}")
    L.append(f"  Stale (open 5+ years):   {stale}")
    L.append("  5 oldest open cases:")
    oldest = sorted(open_cases, key=lambda c: (c.incident_date, c.case_id))[:5]    # tuple key = tie-breaker
    for c in oldest:
        L.append(f"    {c.summary()}  - {c.years_unsolved} yrs")

    # 4. BEATS ----------------------------------------------------------
    L.append("")
    L.append("4. TOP 10 BEATS BY OPEN CASES")
    ranked = sorted(beat_open, key=lambda b: (-beat_open[b], b))[:10]    # most open first, beat number breaks ties
    for rank, beat in enumerate(ranked, start=1):
        b_closed = beat_closed.get(beat, 0)
        L.append(f"  {rank:>2}. beat {beat}: {beat_open[beat]} open, "
                 f"clearance {percentage(b_closed, beat_total[beat])} ({b_closed}/{beat_total[beat]})")

    # 5. LEADS ----------------------------------------------------------
    L.append("")
    L.append("5. LEADS")
    L.append(f"  Open cases with a callback phone: {percentage(open_with_phone, len(open_cases))}  "
             f"({open_with_phone} of {len(open_cases)})")

    # 6. RAW VS CLEAN ---------------------------------------------------
    raw_rate = percentage(stats["raw_exact_closed"], stats["rows_read"])
    L.append("")
    L.append("6. RAW VS CLEAN")
    L.append(f"  Raw clearance (status exactly 'CLOSED' / all data rows): {raw_rate}  "
             f"({stats['raw_exact_closed']}/{stats['rows_read']})")
    L.append(f"  Clean clearance:                                       {percentage(closed, total)}  ({closed}/{total})")
    if stats["rows_read"] and total:
        gap = (closed / total - stats["raw_exact_closed"] / stats["rows_read"]) * 100
        L.append(f"  Difference: {gap:+.1f} percentage points")
    L.append("  Clean cases that mean CLOSED but are not spelled exactly 'CLOSED' (missed by the raw count):")
    for spelling, count in sorted(stats["raw_status_fixed"].items(), key=lambda kv: -kv[1]):
        label = spelling if spelling else "(blank)"
        L.append(f"    '{label}': {count}")

    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
# MAIN: one command does everything
# ---------------------------------------------------------------------------

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else default_input      # optional file name from the command line
    try:
        cases, quarantine, stats = load_cases(path)
    except FileNotFoundError:
        print(f"Could not find '{path}'. Put it in this folder or pass its path as an argument.")
        sys.exit(1)

    write_clean_csv(cases)
    write_quarantine_csv(quarantine)

    report = build_report(cases, quarantine, stats)
    print(report)                                                   # show it on screen...
    with open("report.txt", "w", encoding="utf-8") as f:            # ...and save the same text
        f.write(report)


if __name__ == "__main__":
    main()
