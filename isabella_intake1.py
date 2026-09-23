# Raw pipe-delimited record: name|sex|age|date|address|beat|status
record_one = "reyes, miguel|M|32|2018-05-17| 3308 DELAFORD STREET |Beat 347|open"

# Split into a list of 7 fields on '|'. record_one has no spaces padding
# the delimiters (except inside the address field), so no per-field
# stripping is needed here.
fields = record_one.strip().split('|')

# Cleaning fields: normalize casing and convert types
name = fields[0].title()
sex = fields[1].capitalize()
age = int(fields[2])
date = fields[3]
year = int(date[0:4])          # first 4 chars of the date string = year
address = fields[4].title()    # .title() capitalizes after every word break,
                               # so it tolerates the leading/trailing spaces baked into this field's raw text                                
status = fields[6].capitalize()


# Computing years unsolved (relative to the current year)
yrs_unsolved = 2026 - year

# One-line case summary (split across two lines with \ for readability)
summary = f"CASE: {name} ({sex}, {age}) | {date} | {address} | " \
f"{status} — {yrs_unsolved} years without an arrest"

print(summary)

# Second raw record, same field order as record_one, but this source has
# a space padding every '|' delimiter.
record_two = "OKAFOR, SAMUEL J | M | 55 | 2018-07-09 | 1519 westhollow avenue | beat 341 | OPEN"

# Split into fields, then strip() each individual piece to remove the
# padding spaces. This matters because .capitalize() only capitalizes the
# very first character of a string — a leading space here would leave the
# real first letter lowercased (e.g. ' M '.capitalize() -> ' m ').
fields2 = [field.strip() for field in record_two.strip().split('|')]

# Cleaning fields: normalize casing and convert types
name2 = fields2[0].title()
sex2 = fields2[1].capitalize()
age2 = int(fields2[2])
date2 = fields2[3]
year2 = int(date2[0:4])        # first 4 chars of the date string = year
address2 = fields2[4].title()
status2 = fields2[6].capitalize()


# Computing years unsolved (relative to the current year)
yrs_unsolved2 = 2026 - year2

# One-line case summary (split across two lines with \ for readability)
summary2 = f"CASE: {name2} ({sex2}, {age2}) | {date2} | {address2} | " \
f"{status2} — {yrs_unsolved2} years without an arrest"

print(summary2)
