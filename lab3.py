# first_filter.py — Operation: First Filter
# ITSS/OPRE 3312 — Lecture 3: The First Filter
#
# Sweeps every record in data/wk03_data_raw_cases_50.txt, prints each
# case's years-unsolved, flags stale/juvenile open cases, and ends with
# the counts report.

from datetime import datetime                # gives us access to today's date/year

DATA_FILE = "data/wk03_data_raw_cases_50.txt"  # path to the raw records, named once
STALE_YEARS = 5                                # threshold for "stale" — change here if the rule changes
CURRENT_YEAR = datetime.now().year             # today's year, computed once up front

total = 0                  # how many valid records we've processed
open_count = 0              # how many records are status OPEN
stale_count = 0              # how many OPEN records are >= STALE_YEARS old
juvenile_open_count = 0      # how many OPEN records have age < 18
oldest_open_year = None      # year of the oldest OPEN case seen so far (None = none yet)
oldest_open_name = None      # name that goes with oldest_open_year

with open(DATA_FILE, encoding="utf-8") as f:   # open the file; auto-closes when the block ends
    for raw_line in f:                          # read the file one line at a time
        line = raw_line.strip()                 # drop leading/trailing whitespace and the newline
        if not line:                       # skip blank/blank-ish planted lines
            continue

        fields = [field.strip() for field in line.split("|")]  # split on "|", trim each field
        if len(fields) < 7:                # skip anything malformed instead of crashing
            continue

        name = fields[0].title()           # "trammell, monica" -> "Trammell, Monica"
        age = int(fields[2])               # age as text -> number, so it can be compared
        year = int(fields[3][0:4])         # "2014-06-11" -> "2014" -> 2014
        status = fields[6].upper()         # normalize "open"/"Open"/"OPEN" to "OPEN"

        years_unsolved = CURRENT_YEAR - year   # how long this case has been sitting
        total += 1                              # row passed all checks, so it counts

        flags = ""                         # per-record flag text, empty unless something applies
        if status == "OPEN":               # everything below only matters for open cases
            open_count += 1

            if age < 18:                                # victim was a juvenile
                juvenile_open_count += 1
                flags += " *** JUVENILE ***"

            if years_unsolved >= STALE_YEARS:           # case is old enough to flag stale
                stale_count += 1
                flags += " *** STALE ***"

            if oldest_open_year is None or year < oldest_open_year:  # new oldest open case?
                oldest_open_year = year
                oldest_open_name = name

        print(f"{name} - {years_unsolved} years unsolved{flags}")  # per-record line, flags if any

print()                                                    # blank line before the summary
print(f"Total records:        {total}")                    # records successfully parsed
print(f"Open cases:           {open_count}")                # how many are OPEN
print(f"Stale (>= {STALE_YEARS} yrs):     {stale_count}")   # how many OPEN are stale
print(f"Oldest open case:     {oldest_open_name} ({oldest_open_year})")  # oldest OPEN case found
print(f"Open juveniles (<18): {juvenile_open_count}")        # OPEN cases with age < 18
