# =============================================================================
# clean_cases.py  --  The Cold Case File   (ITSS/OPRE 3312, Midterm)
# =============================================================================
#
# BIG PICTURE
#   ONE command turns the raw file into three output files:
#
#       python clean_cases.py
#
#       midterm_cases_raw.csv  ->  cases_clean.csv   every usable case, cleaned
#                              ->  quarantine.csv    every rejected row + line number + reason
#                              ->  report.txt        the numbers for the briefing
#
#   The cleaning rules for a single row live in case_model.py (Case.from_row).
#   This file is the "pipeline" around them: it reads the file, decides what
#   to do with each row, counts everything, and writes the results.
#
# ARCHITECTURE  (data flows top to bottom - the same flow as briefing slide 13)
#
#   midterm_cases_raw.csv
#            |
#            v
#      load_cases(path)         csv.reader walks the file ONCE. For each row:
#            |                    - blank line or repeated header -> skip it (just count it)
#            |                    - Case.from_row(row) inside try/except:
#            |                        ValueError -> the row goes to quarantine with its reason
#            |                        works      -> is its case_id already in the set?
#            |                                        yes -> duplicate, drop it
#            |                                        no  -> keep it as a clean case
#            v
#      (cases, quarantine, stats)
#            |
#            +--> write_clean(cases, path)            cases_clean.csv, sorted by case_id
#            +--> write_quarantine(quarantine, path)  quarantine.csv, in file order
#            +--> build_report(cases, stats)          the report lines (slide 7, questions 1-6)
#            v
#        main()                  prints the report and saves it to report.txt
#
# THE KEY DATA STRUCTURES (weeks 3 and 4)
#   cases        a LIST of Case objects, one per clean case
#   quarantine   a LIST of tuples: (line number, reason, raw row text)
#   seenIds      a SET of case_ids we have already kept. Checking "x in set"
#                is instant, which is why we use a set and not a list.
#   stats        a DICT of running counts (accumulators), filled during the one pass
#   reasons      a DICT inside stats: reason -> how many rows were quarantined for it
#   decades/beats   DICTS built in build_report to group cases and count them
#
# HOW TO RUN
#   python clean_cases.py       (keep this file next to midterm_cases_raw.csv)
#   pytest                      (runs the tests in test_cases.py)
# =============================================================================

import csv                     # reads and writes CSV files, and understands quoted fields like "Walker, G"
from pathlib import Path       # builds file paths that work on any computer

from case_model import Case    # our class: Case.from_row() cleans a row or raises ValueError


# The columns of cases_clean.csv, in the exact order slide 5 requires.
CLEAN_HEADER = ["case_id", "victim_name", "sex", "age", "incident_date",
                "year", "beat", "status", "callback_phone"]

# The columns of quarantine.csv (slide 5).
QUARANTINE_HEADER = ["line_number", "reason", "raw_row"]


# -----------------------------------------------------------------------------
# 1. LOAD  -  one pass over every row, sorting each one into a pile
# -----------------------------------------------------------------------------

def load_cases(path):
    """Read the raw CSV once and return (clean cases, quarantined rows, counts)."""
    cases = []                 # clean Case objects go here
    quarantine = []            # rejected rows go here as (line number, reason, raw row text)
    seenIds = set()            # every case_id we have kept so far, to catch duplicates

    # Accumulators: every number the report needs is counted during this ONE
    # pass, instead of looping over the file again later.
    stats = {
        "dataRows": 0,         # rows that hold data (not blank, not a header)
        "blankLines": 0,       # empty or spaces-only lines that were skipped
        "headerRows": 0,       # header rows that were skipped (the real one + repeats from merged exports)
        "duplicates": 0,       # clean rows whose case_id we had already kept
        "rawClosed": 0,        # raw rows whose status says exactly "CLOSED", for the raw-vs-clean question
        "reasons": {},         # quarantine reason -> count, e.g. {"invalid date": 59, ...}
    }

    # "with" opens the file and closes it for us when the block ends, even if
    # something goes wrong. newline="" lets the csv module handle line endings
    # itself (the csv docs ask for this), and utf-8 reads the text the same way
    # on every computer.
    with open(path, newline="", encoding="utf-8") as rawFile:
        # csv.reader hands us one row at a time as a LIST of strings. Because it
        # understands quotes, "Walker, G" stays ONE field even though it has a
        # comma inside - something a plain .split(",") would get wrong.
        reader = csv.reader(rawFile)

        for row in reader:
            # reader.line_num is the line number in the file (header = line 1),
            # the same number you see in VS Code. We save it so the quarantine
            # file can say exactly WHERE each bad row lives.
            lineNum = reader.line_num

            # SKIP 1 - blank lines. A truly empty line comes back as [], and a
            # line of only spaces comes back as ["   "]. Joining all the fields
            # and stripping the result gives "" in both cases. A blank line holds
            # no data, so it is skipped and counted, NOT quarantined (slide 4).
            if "".join(row).strip() == "":
                stats["blankLines"] += 1
                continue                               # jump to the next row

            # SKIP 2 - header rows. The first line is the header, and merged
            # exports repeated it in the middle of the file. Any row whose
            # first field says "case_id" is a header, not a case.
            if row[0].strip().lower() == "case_id":
                stats["headerRows"] += 1
                continue

            # From here on, this row is a real data row.
            stats["dataRows"] += 1

            # For the "raw vs clean" question: count rows whose status is
            # EXACTLY "CLOSED", with no cleaning at all - the number you would
            # get if you trusted the raw file at face value. Short rows don't
            # have a status column, so we check the length first.
            if len(row) == 9 and row[7] == "CLOSED":
                stats["rawClosed"] += 1

            # THE QUARANTINE PATTERN (week 6). We TRY to build a Case. If any
            # critical field is broken, Case.from_row raises a ValueError, and
            # instead of crashing we log the row and move on to the next one.
            try:
                case = Case.from_row(row)
            except ValueError as err:
                reason = str(err)                      # the message we raised, e.g. "invalid date"
                rawText = ",".join(row)                # the row glued back into one line of text
                quarantine.append((lineNum, reason, rawText))
                # dict.get(reason, 0) means "the current count, or 0 if this
                # reason is new", so the first time we see a reason it starts at 1.
                stats["reasons"][reason] = stats["reasons"].get(reason, 0) + 1
                continue                               # nothing else to do with a bad row

            # DUPLICATES (week 4). We compare case_ids AFTER cleaning, so
            # "cc-19495" and " CC 19495 " count as the same case. The first
            # one we see is kept; any later copy is dropped.
            if case.case_id in seenIds:
                stats["duplicates"] += 1
                continue
            seenIds.add(case.case_id)                  # remember this id for the rest of the file
            cases.append(case)                         # a clean, unique case

    # Return three things at once; the caller unpacks them:
    #   cases, quarantine, stats = load_cases(path)
    return cases, quarantine, stats


# -----------------------------------------------------------------------------
# 2. WRITE  -  save the two CSV deliverables
# -----------------------------------------------------------------------------

def write_clean(cases, path):
    """Write the clean cases to a CSV file, sorted by case_id."""
    # sorted(..., key=...) sorts the list by whatever the key function returns.
    # "lambda case: case.case_id" is a tiny unnamed function that just returns
    # each case's id, so the cases come out in CC-##### order.
    sortedCases = sorted(cases, key=lambda case: case.case_id)
    with open(path, "w", newline="", encoding="utf-8") as outFile:
        # csv.writer automatically puts quotes around any value that contains a
        # comma, so "Ramirez, K" is written correctly and nothing else is quoted.
        writer = csv.writer(outFile)
        writer.writerow(CLEAN_HEADER)                  # first line: the column names
        for case in sortedCases:
            writer.writerow(case.to_row())             # one line per case, in column order


def write_quarantine(quarantine, path):
    """Write every rejected row with its line number and reason."""
    with open(path, "w", newline="", encoding="utf-8") as outFile:
        writer = csv.writer(outFile)
        writer.writerow(QUARANTINE_HEADER)
        # Each item is already a tuple (line number, reason, raw row), which is
        # exactly one CSV row, so writerows can write them all at once.
        writer.writerows(quarantine)


# -----------------------------------------------------------------------------
# 3. REPORT  -  answer the six questions on slide 7
# -----------------------------------------------------------------------------

def percent(part, whole):
    """Return part / whole as a percentage, or 0.0 when whole is 0 (so we never divide by zero)."""
    if whole == 0:
        return 0.0
    return part / whole * 100


def build_report(cases, stats):
    """Return the report as a list of text lines."""
    lines = []                 # every line of the report; main() prints and saves them

    # Two lists we will need several times below.
    closedCases = [case for case in cases if case.status == "CLOSED"]   # list comprehension: keep only closed cases
    openCases = [case for case in cases if case.status == "OPEN"]       # and only open cases
    quarantined = sum(stats["reasons"].values())       # total rows quarantined, across every reason

    # ---- 1. INTAKE ----------------------------------------------------------
    # The funnel on briefing slide 12: data rows - quarantined - duplicates = clean.
    # Format codes:  {x:<28} pads the label to 28 characters so the numbers line
    # up in a column,  {x:>5} right-aligns a number in 5 characters,  and
    # {x:,} would add thousands commas.
    lines.append("THE COLD CASE FILE - CLEANING REPORT")
    lines.append("=" * 50)
    lines.append("")
    lines.append("1. INTAKE")
    lines.append(f"   {'Data rows read:':<28}{stats['dataRows']:>5}")
    lines.append(f"   {'Blank lines skipped:':<28}{stats['blankLines']:>5}")
    lines.append(f"   {'Header rows skipped:':<28}{stats['headerRows']:>5}")
    lines.append(f"   {'Rows quarantined:':<28}{quarantined:>5}")
    # Sort the reasons from most common to least. stats["reasons"].get returns
    # the count for a reason, so sorting by it ranks reasons by their counts.
    for reason in sorted(stats["reasons"], key=stats["reasons"].get, reverse=True):
        lines.append(f"      {reason + ':':<25}{stats['reasons'][reason]:>5}")
    lines.append(f"   {'Duplicates removed:':<28}{stats['duplicates']:>5}")
    lines.append(f"   {'Clean cases:':<28}{len(cases):>5}")
    lines.append(f"   Check: {stats['dataRows']} - {quarantined} - {stats['duplicates']} = "
                 f"{stats['dataRows'] - quarantined - stats['duplicates']}")
    lines.append("")

    # ---- 2. CLEARANCE ---------------------------------------------------------
    # Clearance rate = closed cases / all clean cases.
    # For each decade we need two counts (total and closed), so we use two
    # dicts with the decade as the key. 1987 // 10 * 10 = 1980: integer
    # division chops off the last digit, then * 10 puts the zero back.
    cleanRate = percent(len(closedCases), len(cases))
    decadeTotal = {}
    decadeClosed = {}
    for case in cases:
        decade = case.year // 10 * 10
        decadeTotal[decade] = decadeTotal.get(decade, 0) + 1
        if case.status == "CLOSED":
            decadeClosed[decade] = decadeClosed.get(decade, 0) + 1

    lines.append("2. CLEARANCE")
    lines.append(f"   Overall clearance rate: {cleanRate:.1f}%  ({len(closedCases)} closed / {len(cases)} clean cases)")
    for decade in range(1980, 2030, 10):               # 1980, 1990, 2000, 2010, 2020
        total = decadeTotal.get(decade, 0)
        closed = decadeClosed.get(decade, 0)
        lines.append(f"   {decade}s: {percent(closed, total):5.1f}%  ({closed} / {total})")
    lines.append("")

    # ---- 3. OPEN CASES ----------------------------------------------------------
    # is_stale is a property on the Case class, so we just ask each case.
    staleCount = sum(1 for case in openCases if case.is_stale)   # add 1 for every stale case
    # The 5 oldest open cases: sort open cases by date (oldest first), take the first 5.
    oldestOpen = sorted(openCases, key=lambda case: case.incident_date)[:5]

    lines.append("3. OPEN CASES")
    lines.append(f"   Open cases: {len(openCases)}")
    lines.append(f"   Stale open cases (open 5+ years): {staleCount}")
    lines.append("   The 5 oldest open cases:")
    for case in oldestOpen:
        lines.append(f"      {case.case_id}  {case.incident_date}  "
                     f"{case.years_unsolved} years unsolved  beat {case.beat or 'unknown'}")
    lines.append("")

    # ---- 4. BEATS -----------------------------------------------------------------
    # Three dicts keyed by beat: total cases, closed cases, open cases.
    # Cases with a blank beat are skipped, because "" is not a real beat.
    beatTotal = {}
    beatClosed = {}
    beatOpen = {}
    for case in cases:
        if case.beat == "":
            continue
        beatTotal[case.beat] = beatTotal.get(case.beat, 0) + 1
        if case.status == "CLOSED":
            beatClosed[case.beat] = beatClosed.get(case.beat, 0) + 1
        else:
            beatOpen[case.beat] = beatOpen.get(case.beat, 0) + 1

    # Rank beats by open cases, most first. The key returns a pair: the
    # NEGATIVE open count (so bigger counts sort first) and the beat number
    # (so ties are broken the same way every time, lowest beat first).
    topBeats = sorted(beatOpen, key=lambda beat: (-beatOpen[beat], beat))[:10]

    lines.append("4. BEATS - top 10 by open cases")
    lines.append(f"   {'Beat':<6}{'Open':>6}{'Total':>7}{'Clearance':>11}")
    for beat in topBeats:
        rate = percent(beatClosed.get(beat, 0), beatTotal[beat])
        lines.append(f"   {beat:<6}{beatOpen[beat]:>6}{beatTotal[beat]:>7}{rate:>10.1f}%")
    lines.append("")

    # ---- 5. LEADS -----------------------------------------------------------------
    # An empty string counts as False, so "if case.callback_phone" is True
    # only when a phone number was found in the tip notes.
    withPhone = sum(1 for case in openCases if case.callback_phone)
    lines.append("5. LEADS")
    lines.append(f"   Open cases with a callback phone: {percent(withPhone, len(openCases)):.1f}%  "
                 f"({withPhone} / {len(openCases)})")
    lines.append("")

    # ---- 6. RAW vs CLEAN ----------------------------------------------------------
    # The naive way: count raw rows whose status is exactly "CLOSED" and divide
    # by every raw data row. This misses "Closed", "CLSD" and "CLEARED", and the
    # denominator still includes junk rows and duplicates.
    rawRate = percent(stats["rawClosed"], stats["dataRows"])
    lines.append("6. RAW vs CLEAN")
    lines.append(f"   Raw clearance rate (status exactly 'CLOSED'): {rawRate:.1f}%  "
                 f"({stats['rawClosed']} / {stats['dataRows']} raw data rows)")
    lines.append(f"   Clean clearance rate:                         {cleanRate:.1f}%")
    # abs() gives the size of the gap without a minus sign; the one-line
    # if/else then says which direction the raw number was wrong in.
    direction = "too low" if rawRate < cleanRate else "too high"
    lines.append(f"   The raw number is off by {abs(cleanRate - rawRate):.1f} percentage points ({direction}).")

    return lines


# -----------------------------------------------------------------------------
# 4. PROGRAM ENTRY  -  the one command
# -----------------------------------------------------------------------------

def main():
    """Run the whole pipeline: raw file in, three files out, report printed."""
    # Path(__file__) is where THIS script lives. with_name swaps the script's
    # file name for another file name in the same folder, so the program finds
    # its files no matter which folder you run it from.
    folder = Path(__file__)
    cases, quarantine, stats = load_cases(folder.with_name("midterm_cases_raw.csv"))

    write_clean(cases, folder.with_name("cases_clean.csv"))
    write_quarantine(quarantine, folder.with_name("quarantine.csv"))

    # "\n".join puts a line break between every report line, giving one big string.
    reportText = "\n".join(build_report(cases, stats))
    print(reportText)                                  # show it in the terminal
    folder.with_name("report.txt").write_text(reportText + "\n", encoding="utf-8")  # and save it


# Run main() only when this file is started directly (python clean_cases.py),
# not when another file imports it.
if __name__ == "__main__":
    main()
