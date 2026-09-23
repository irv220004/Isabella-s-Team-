# Where the raw case data lives, relative to this script
DATA_FILE = "wk03_data_raw_cases_50.txt"

# Constants at the top: the "rules" of this audit, easy to find and tweak
CURRENT_YEAR = 2026
STALE_YEARS = 5   # an OPEN case this many years old or older gets flagged

# Accumulators: set up BEFORE the loop, at zero/starting values.
# Each one gets updated a little bit on every pass through the loop below.
total_records = 0        # how many valid records we've processed
open_count = 0            # how many of those are status == "open"
stale_count = 0           # how many open cases are 5+ years old
juvenile_open_count = 0   # how many open cases involve someone under 18
oldest_year = CURRENT_YEAR   # start high (2026); any real case year will be older/smaller
oldest_name = ""             # paired with oldest_year, updated together

# open() gives us a file object; "with" auto-closes the file when the block ends
with open(DATA_FILE) as case_file:
    # for loops over the file one line at a time -- one full record per pass
    for line in case_file:
        line = line.strip()   # remove the trailing newline (and any stray spaces)

        # Guard clause: an empty line (after stripping) has nothing to parse.
        # continue jumps straight back to the top of the loop for the next line,
        # instead of letting the code below crash on a line with no data.
        if line == "":
            continue   # skip blanks, keep looping

        # Break the record into its 7 pipe-separated pieces:
        # name|sex|age|date|address|beat|status
        fields = line.split("|")

        # Pull out only the fields we actually need, cleaning each one
        # individually since the file's spacing/casing is inconsistent:
        #   .strip()  removes leading/trailing spaces around that one field
        #   .title()  capitalizes each word ("reyes, miguel" -> "Reyes, Miguel")
        #   .lower()  normalizes OPEN / Open / open to one consistent value
        name = fields[0].strip().title()
        age = int(fields[2].strip())              # int() converts the text "39" to the number 39
        year = int(fields[3].strip()[0:4])         # [0:4] grabs just the year out of "2014-06-11"
        status = fields[6].strip().lower()

        years_unsolved = CURRENT_YEAR - year
        total_records = total_records + 1   # counts every non-blank line; has to come after the skipping the blank line 

        # Required output for every record, valid or not otherwise skipped above
        print(f"{name}: {years_unsolved} years")

        # Everything below only applies to OPEN cases -- this if is "the filter"
        if status == "open":
            open_count = open_count + 1

            # Nested condition: of the open cases, which are ALSO old enough to flag?
            if years_unsolved >= STALE_YEARS:
                stale_count = stale_count + 1
                print("    *** STALE ***")

            # Separate, independent check: is this open case a juvenile victim?
            if age < 18:
                juvenile_open_count = juvenile_open_count + 1

            # Running "find the minimum" by hand: only overwrite oldest_year/name
            # when we find a case older than anything we've seen so far
            if year < oldest_year:
                oldest_year = year
                oldest_name = name

# Everything below runs once, AFTER the loop has finished all 50 records --
# it just prints the accumulators that were built up one line at a time above
print() # Prints blank line 
print(f"Total records:        {total_records}")
print(f"Open cases:           {open_count}")
print(f"Stale (>= {STALE_YEARS} yrs):     {stale_count}")
print(f"Oldest open case:     {oldest_name} ({oldest_year})")
print(f"Juvenile open cases:  {juvenile_open_count}")
