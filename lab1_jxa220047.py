# intake.py — turn one raw record into a clean summary
record = " CARTER, DEMARCUS | m | 36 | 2018-03-22 | 412 larkmoor lane | beat 352 | OPEN "
# Step 1: strip the blob, split into fields
fields = record.strip().split("|")
# Step 2: clean each field
name = fields[0].title() # "Carter, Demarcus"
sex = fields[1].upper() # "M"
age = int(fields[2]) # 36 (now a number)
date = fields[3]
year = int(date[0:4]) # 2018
addr = fields[4].title() # "412 Larkmoor Lane"
status = fields[6]
print(name, sex, age, year, addr, status)
