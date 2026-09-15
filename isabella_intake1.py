record_one = "reyes, miguel|M|32|2018-05-17| 3308 DELAFORD STREET |Beat 347|open"

#stripping the record into fields
fields = record_one.strip().split('|')

#cleaning fields
name = fields[0].title()
sex = fields[1].capitalize()
age = int(fields[2])
date = fields[3]
year = int(date[0:4])
address = fields[4].title()
status = fields[6].capitalize()

#computing years unsolved
yrs_unsolved = 2026 - year

#One-line case summary 
summary = f"CASE: {name} ({sex}, {age}) | {date} | {address} | " \
f"{status} — {yrs_unsolved} years without an arrest"

print(summary)

record_two = "OKAFOR, SAMUEL J | M | 55 | 2018-07-09 | 1519 westhollow avenue | beat 341 | OPEN"

#stripping the record into fields
fields2 = [field.strip() for field in record_two.strip().split('|')]

#cleaning fields
name2 = fields2[0].title()
sex2 = fields2[1].capitalize()
age2 = int(fields2[2])
date2 = fields2[3]
year2 = int(date2[0:4])
address2 = fields2[4].title()
status2 = fields2[6].capitalize()

#computing years unsolved
yrs_unsolved2 = 2026 - year2

#One-line case summary
summary2 = f"CASE: {name2} ({sex2}, {age2}) | {date2} | {address2} | " \
f"{status2} — {yrs_unsolved2} years without an arrest"

print(summary2)

