import csv  # handles real CSV parsing, including commas INSIDE quoted names


def parse_row(row):
    """Validate one raw CSV row and convert it into a clean case dict; raises ValueError on bad data."""
    if len(row) != 8:
        raise ValueError(f"expected 8 fields, got {len(row)}")  # catches the planted truncated rows

    case_id, name, sex, age_text, date_text, address, beat_text, status = row  # unpack the 8 raw strings

    age = int(age_text.strip())  # raises ValueError on its own for text like "unknown" - no custom message needed

    if date_text.strip() == "":
        raise ValueError("missing date")  # int() can't catch an empty string for us, so we check it by hand

    return {
        "case_id": case_id.strip(),           # e.g. "CC-20000" - no cleanup needed beyond whitespace
        "name": name.strip().title(),         # " carter, d " -> "Carter, D" (matches slide 8's pytest example)
        "sex": sex.strip().upper(),           # normalize m/M/f/F to M or F
        "age": age,                           # already converted to int above
        "date": date_text.strip(),            # kept as the ISO string, e.g. "2018-03-22"
        "address": address.strip().title(),   # normalize capitalization
        "beat": int(beat_text.strip()),       # safe to convert - beat is only ever absent on truncated rows,
        "status": status.strip().upper(),     # which already raised ValueError above and never reach this line
    }


def load_cases(path):
    """Read every row in the CSV at path; return (good_cases, quarantine_log)."""
    good = []        # every row that parsed cleanly, as a dict from parse_row()
    quarantine = []  # every rejected row, as (line_number, reason, raw_row)

    with open(path, newline="", encoding="utf-8") as f:  # 'with' closes the file even if parsing explodes
        reader = csv.reader(f)  # csv.reader splits on commas correctly, even inside quoted names like "Kirkland, Monica, Jr, III"
        next(reader)            # eat the header row so the loop below only ever sees data rows

        for line_num, row in enumerate(reader, start=2):  # start=2: physical line 1 was the header we just ate
            if not row:           # a genuinely blank physical line (csv.reader hands back [] for one) - e.g. row 37
                continue          # nothing to validate or log here - it isn't one of "the 100" at all, just skip it

            try:
                good.append(parse_row(row))                   # the risky thing - may raise ValueError
            except ValueError as err:                          # catch the SPECIFIC error, never a bare except
                quarantine.append((line_num, str(err), row))  # log line number + reason + the raw row, then...
            # ...the loop just continues on its own - no extra code needed to "keep looping" (slide 6)

    return good, quarantine


def report(good, quarantine):
    """Print the slide-13 summary: loaded/quarantined counts, then the full quarantine log."""
    print(f"Rows loaded cleanly:   {len(good)}")        # required exact label + count (slide 13)
    print(f"Rows quarantined:      {len(quarantine)}")  # required exact label + count (slide 13)

    if quarantine:                                       # skip the log header entirely if nothing was rejected
        print()
        print("QUARANTINE LOG - every rejected row, with the reason:")
        for line_num, reason, row in quarantine:
            preview = ",".join(row)                      # rebuild a short, readable one-line preview of the row
            print(f"  line {line_num:>3}: {reason}  | {preview}")



def count_reasons(quarantine):
    """Return {reason: how many times it happened}, so repeat failure types stand out."""
    counts = {}                                   # a plain dict used as a tally board
    for _line_num, reason, _row in quarantine:    # the line number and raw row aren't needed for this count
        counts[reason] = counts.get(reason, 0) + 1  # +1 if we've seen this exact reason before, else start at 1
    return counts


def write_quarantine_csv(quarantine, path="quarantine.csv"):
    """Write the quarantine log to its own CSV file (slide 14) instead of only printing it."""
    with open(path, "w", newline="", encoding="utf-8") as f:  # 'with' again guarantees the file closes cleanly
        writer = csv.writer(f)
        writer.writerow(["line_number", "reason", "raw_row"])  # header row for the output file
        for line_num, reason, row in quarantine:
            writer.writerow([line_num, reason, ",".join(row)])
    return path


def main():
    path = input(
        "Enter the case file name with extension (default wk06_data_raw_cases_100.csv): "
    ).strip()
    if path == "":                              # Enter alone picks the default lab file
        path = "wk06_data_raw_cases_100.csv"

    good, quarantine = load_cases(path)  # the whole read-validate-quarantine pipeline in one call
    report(good, quarantine)             # print the required slide-13 summary + full quarantine log


if __name__ == "__main__":
    main()
