# first_filter.py
# Squad Lab: Operation First Filter (Week 3, Lecture 3 - Conditionals & Loops)
# Mission: sweep all 50 records in wk03_data_raw_cases_50.txt, flag stale/open
# cases, and report the counts described on slide 13's "Results To Achieve".

from datetime import datetime

stale_years = 5              # threshold (in years) for a case to count as "stale"
current_year = datetime.now().year
datal_file = input("Enter the file name with extension (.txt, .csv, etc.) for filtering: ")

# --- Step 4 setup: accumulators are created BEFORE the loop starts (slide 7) ---
total_records = 0            # counts every valid record we process
open_count = 0                # counts records whose status is OPEN
stale_count = 0                # counts OPEN records that are also stale (5+ yrs)
juvenile_open_count = 0        # counts OPEN records where the victim is under 18
oldest_open_year = current_year   # start high so the first OPEN case always wins
oldest_open_name = ""              # will hold the name tied to oldest_open_year

data_file = open(datal_file, "r", encoding="utf-8")  # open the raw evidence file
lines = data_file.readlines()  # read every line into a list so we can loop over it
data_file.close()              # close the file now that its contents are in memory

# --- Step 2: get the loop walking over every record ---
for raw_line in lines:                 # for loop: same 4-5 lines run once per record
    line = raw_line.strip()            # remove leading/trailing whitespace & newline

    if line == "":                     # slide 8: blank lines must not crash the loop
        continue                       # skip this iteration, move to the next record

    fields = line.split("|")           # split the pipe-delimited record into fields

    if len(fields) != 7:               # a malformed/planted "surprise" record
        continue                       # skip it instead of crashing on bad data

    # unpack + clean every field so mixed case/spacing doesn't break comparisons
    name = fields[0].strip().title()          # "TRAMMELL, monica " -> "Trammell, Monica"
    sex = fields[1].strip().upper()            # normalize m/M/f/F to M or F
    age_text = fields[2].strip()               # raw age string, still needs int()
    date_text = fields[3].strip()              # raw date string, e.g. "2014-06-11"
    address = fields[4].strip().title()        # normalize address capitalization
    beat = fields[5].strip().title()           # normalize "beat 352"/"Beat 352"
    status = fields[6].strip().upper()         # normalize open/OPEN/Closed to OPEN/CLOSED

    if not age_text.isdigit():         # guard against a corrupted age field
        continue                       # skip rather than crash on int() conversion

    age = int(age_text)                # convert the cleaned age string to a number
    year = int(date_text[0:4])         # first 4 characters of the date are the year

    years_unsolved = current_year - year   # slide 4: how long the case has been open

    # --- Step 3: if/elif/else flagging logic (slide 4) ---
    if years_unsolved >= stale_years:      # most specific/important condition first
        flag = "*** STALE ***"             # case is old enough to flag as stale
    elif years_unsolved >= 2:              # only checked if the STALE test was False
        flag = "aging"                     # not stale yet, but not brand new either
    else:                                   # everything left over
        flag = "recent"                    # a fairly new case

    # only cases that are OPEN and stale get the loud "*** STALE ***" flag text
    stale_flag_text = ""                        # default: nothing extra to print
    if status == "OPEN" and years_unsolved >= stale_years:   # slide 4's example check
        stale_flag_text = "  *** STALE ***"      # attach the flag for open+stale cases

    print(f"{name}: {years_unsolved} years unsolved [{status}]{stale_flag_text}")
    # ^ Step 2 requirement: print name + years_unsolved for every one of the 50 records
    # (the "aging"/"recent"/general-stale value from the if/elif/else above is `flag`,
    #  kept as a variable to show the pattern even though it isn't printed here)

    # --- Step 4: update accumulators INSIDE the loop (slide 7's 3-step pattern) ---
    total_records = total_records + 1      # one more record has been processed

    if status == "OPEN":                    # only run the OPEN-specific accumulators
        open_count = open_count + 1              # tally another open case

        if years_unsolved >= stale_years:        # step 3: stale OPEN cases
            stale_count = stale_count + 1            # tally another stale-open case

        if age < 18:                              # step 3: juvenile victims
            juvenile_open_count = juvenile_open_count + 1   # tally another juvenile-open case

        if year < oldest_open_year:               # slide 7: track the minimum year seen
            oldest_open_year = year                   # this case is older, remember its year
            oldest_open_name = name                    # ...and remember whose case it is

# --- Step 5: report AFTER the loop (slide 7's 3rd step) ---
print()                                     # blank line to separate detail from summary
print(f"Juvenile open cases (age < 18):  {juvenile_open_count}")  # extra stat from step 3
print()                                     # another blank line before the final report

# This block matches the exact format required on slide 13's "Results To Achieve"
print(f"Total records:        {total_records}")
print(f"Open cases:           {open_count}")
print(f"Stale (>= {stale_years} yrs):     {stale_count}")
print(f"Oldest open case:     {oldest_open_name} ({oldest_open_year})")
