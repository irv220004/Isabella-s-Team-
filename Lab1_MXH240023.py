record = " BOOKER, TERRENCE | M | 41 | 2018-11-08 | 907 n. calloway drive | Beat 442 | OPEN "

fields = record.strip().split('|')

#clean the fields
name = fields[0].title()
sex = fields[1].title()
age = int(fields[2])
date = fields[3]
year = int(date[0:5])
addr = fields[4].title()
status = fields[6].title()

case_age = 2026 - year

print(f"Name: {name}, Sex: {sex}, Age: {age}, Year: {year}, Address: {addr}, Status: {status}, Case Age: {case_age}" )






