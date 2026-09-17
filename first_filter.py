# first_filter.py — Operation: First Filter
# ITSS/OPRE 3312 — Lecture 3: The First Filter
#
# Sweeps every record in data/wk03_data_raw_cases_50.txt, prints each
# case's years-unsolved, flags stale/juvenile open cases, and ends with
# the counts report.

from datetime import datetime

DATA_FILE = "data/wk03_data_raw_cases_50.txt"
STALE_YEARS = 5
CURRENT_YEAR = datetime.now().year

total = 0
open_count = 0
stale_count = 0
juvenile_open_count = 0
oldest_open_year = None
oldest_open_name = None

with open(DATA_FILE, encoding="utf-8") as f:
    for raw_line in f:
        line = raw_line.strip()
        if not line:                       # skip blank/blank-ish planted lines
            continue

        fields = [field.strip() for field in line.split("|")]
        if len(fields) < 7:                # skip anything malformed instead of crashing
            continue

        name = fields[0].title()
        age = int(fields[2])
        year = int(fields[3][0:4])
        status = fields[6].upper()

        years_unsolved = CURRENT_YEAR - year
        total += 1

        flags = ""
        if status == "OPEN":
            open_count += 1

            if age < 18:
                juvenile_open_count += 1
                flags += " *** JUVENILE ***"

            if years_unsolved >= STALE_YEARS:
                stale_count += 1
                flags += " *** STALE ***"

            if oldest_open_year is None or year < oldest_open_year:
                oldest_open_year = year
                oldest_open_name = name

        print(f"{name} - {years_unsolved} years unsolved{flags}")

print()
print(f"Total records:        {total}")
print(f"Open cases:           {open_count}")
print(f"Stale (>= {STALE_YEARS} yrs):     {stale_count}")
print(f"Oldest open case:     {oldest_open_name} ({oldest_open_year})")
print(f"Open juveniles (<18): {juvenile_open_count}")
