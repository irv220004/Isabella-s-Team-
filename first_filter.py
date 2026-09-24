# first_filter.py -- ITSS/OPRE 3312, Week 3: The First Filter
# Author: Mustafa Hasnain MXH240023
# Sweep all 50 records, flag what matters, find the oldest open case.
# Week 2 = 5 copies of the pipeline. Week 3 = 1 copy inside a loop.

stale_years = 5      # slide 14 stretch: try 3, 5, 10 and watch the stale count move
this_year = 2026

# ACCUMULATORS -- set up BEFORE the loop, update INSIDE it, report AFTER (slide 7).
# Put these inside the loop by mistake and they reset on every record.
total_records = 0
open_count = 0
stale_count = 0
juvenile_count = 0
oldest_year = 2026   # start high so the first open case is guaranteed to beat it
oldest_name = ""

print("FLAGGED OPEN CASES")

# "with open(...) as file" closes the file for us when the block ends.
with open("wk03_data_raw_cases_50.txt", "r") as file:

    # This hands us one line at a time. Everything indented below runs 50 times.
    for line in file:

        if not line.strip():
            continue     # blank line -- skip this one, keep looping (slide 8)

        # Same pipeline as week 2: strip -> split -> clean -> convert.
        # Strip EVERY field, because some rows are "NAME | m | 39" and some are "NAME|m|39".
        fields = line.strip().split("|")
        name = fields[0].strip().title()        # "OKAFOR, DARIUS" -> "Okafor, Darius"
        age = int(fields[2].strip())            # "39" the text -> 39 the number
        year = int(fields[3].strip()[0:4])      # "2014-06-11" -> 2014  ([0:4], not [0:5])
        beat = fields[5].strip().title()
        status = fields[6].strip().upper()      # "open"/"Open"/"OPEN" all become "OPEN"

        years_unsolved = this_year - year
        total_records = total_records + 1

        # == asks a question, = makes an assignment (slide 5).
        # We can compare against one spelling only because we .upper()'d above.
        if status == "OPEN":
            open_count = open_count + 1

            # Nested if: this is only asked about OPEN cases, since it sits inside
            # the block above.
            if years_unsolved >= stale_years:
                stale_count = stale_count + 1
                flag = "*** STALE ***"
            else:
                flag = ""     # not stale, so nothing to print

            if age < 18:
                juvenile_count = juvenile_count + 1
                flag = flag + " [JUVENILE]"

            # Min tracker: compare each open case to the current record-holder
            # and swap if this one is older.
            if year < oldest_year:
                oldest_year = year
                oldest_name = name

            # f-string: {curly braces} get swapped for the variable's value.
            # :<22 pads the name to 22 characters so the columns line up.
            print(f"{name:<22} | age {age} | {year} | {beat} | {years_unsolved} yrs unsolved {flag}")

# REPORT -- flush left, so it runs AFTER the loop, once.
# Indent these into the loop and you get 50 reports instead of 1.
print()
print(f"Total records:        {total_records}")
print(f"Open cases:           {open_count}")
print(f"Stale (>= {stale_years} yrs):     {stale_count}")
print(f"Oldest open case:     {oldest_name} ({oldest_year})")
print(f"Juveniles (age < 18): {juvenile_count}")
