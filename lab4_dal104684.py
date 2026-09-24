# lockers.py (lab4_dal104684.py)
# Squad Lab: Operation Evidence Lockers (Week 4, Lecture 4 - Lists, Sets, Dicts)
# Mission: dedupe the 60-line file, profile victim ages, and rank beats by
# open-case count. Target numbers are on slide 12's "Results To Achieve":
#   Lines in file: 60 | Unique records: 52 | Duplicates removed: 8
#   Youngest 17 / Oldest 70 / Average 39.1 | beat ranking with # bars

data_file = input("Enter the file name with extension (.txt, .csv, etc.) for deduping: ")      #file selection for deduping

# --- Step 1/2: read the file and normalize every line into a list ---
data_file = open(data_file, "r", encoding="utf-8")  # open the raw evidence file
raw_lines = data_file.readlines()   # read every physical line into a list
data_file.close()                   # close the file once its contents are in memory

normalized = []                      # empty LIST locker: ordered evidence (slide 4)
for raw_line in raw_lines:           # walk every line exactly once
    line = raw_line.strip()          # drop leading/trailing whitespace & newline
    if line == "":                   # blank/junk lines must not crash or count
        continue                     # skip this iteration, move to the next line
    clean = line.upper()             # slide 5: normalize case BEFORE dedupe
    normalized.append(clean)         # collect-then-analyze: gather first (slide 4)

lines_in_file = len(normalized)      # step 2 checkpoint: should read 60

# --- Step 3: dedupe with a SET (uniqueness), only after normalizing ---
unique_records = set(normalized)     # a set keeps only one copy of each exact string
unique_count = len(unique_records)   # how many distinct records actually exist
duplicates_removed = lines_in_file - unique_count   # slide 5: 60 - unique = dupes gone

# --- Step 4: loop the UNIQUE records only, collect ages + count open beats ---
ages = []                            # LIST locker: every victim age, unique records only
per_beat = {}                        # DICT locker: beat (key) -> open-case count (value)

for record in unique_records:        # iterate the deduped set, not the raw 60 lines
    fields = record.split("|")       # split the pipe-delimited record into fields
    if len(fields) != 7:             # guard against a malformed/planted record
        continue                     # skip it instead of crashing on bad data

    age_text = fields[2].strip()     # raw age field, still text at this point
    beat = fields[5].strip().title() # normalize "BEAT 352"/"Beat 352" for display
    status = fields[6].strip().upper()   # normalize OPEN/open/Open to OPEN

    if not age_text.isdigit():       # guard against a corrupted age field
        continue                     # skip rather than crash on int() conversion

    age = int(age_text)              # convert the cleaned age string to a number
    ages.append(age)                 # slide 4: .append(x) adds to the end of the list

    if status == "OPEN":             # only rank beats by OPEN cases (slide 6)
        if beat in per_beat:         # have we seen this beat before?
            per_beat[beat] += 1      # yes: increment its existing count
        else:                        # first time seeing this beat
            per_beat[beat] = 1       # create the key, starting its count at 1

# --- Step 5: report the numbers, in the order slide 12 expects ---
youngest = min(ages)                 # slide 4: min() is free once ages is a list
oldest = max(ages)                   # slide 4: max() is free too
average_age = sum(ages) / len(ages)  # slide 4: sum()/len() gives the mean

print(f"Lines in file:      {lines_in_file}")
print(f"Unique records:     {unique_count}")
print(f"Duplicates removed: {duplicates_removed}")
print()                              # blank line to separate dedupe stats from ages
print(f"Youngest {youngest} / Oldest {oldest} / Average {average_age:.1f}")
print()                              # blank line to separate ages from the beat ranking

print("Open cases by beat (most-burdened first):")
# slide 7: sorted(dict, key=dict.get, reverse=True) ranks KEYS by their VALUES, biggest first
for beat in sorted(per_beat, key=per_beat.get, reverse=True):      # key=per_beat.get describes sorting criteria (cases per beat)
    count = per_beat[beat]                                         # look up this beat's open-case count
    bar = "#" * count                                              # zero-library histogram: one # per case
    print(f"{beat:<10}{count:>3}  {bar}")                          # left-align beat name, right-align count, then bar