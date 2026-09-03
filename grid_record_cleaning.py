##IMPORTING TABULATE LIBRARY FOR GRID CREATION##
from tabulate import tabulate                                                       #-m pip install tabulate to install tabulate library if not already installed (requires 0.10.0)


##RECORD CLEANING FUNCTION##
def clean_record(record):                                                           #parameter added to allow arguments to be passed to the function from the file input section
                                                            
    fields = record.strip().split("|")                                              #splits record into fields 

    name = fields[0].title()                                                        #defines name & fixes formatting (Reyes, Miguel)

    sex = fields[1].upper()                                                         #defines sex & fixes formatting ("M") 

    age = int(fields[2])                                                            #defines age & converts variable type to int

    date = fields[3]                                                                #defines date 
  
    date_parts = fields[3].split("-")                                               #splits date into year, month, and day 
    year = int(date_parts[0])                                                           #converts year to int 
    month = int(date_parts[1])                                                          #converts month to int
    day = int(date_parts[2])                                                            #converts day to int                              

    address = fields[4].title()                                                     #defines address & fixes formatting (1234 Main St, Anytown, USA)                              

    status = fields[6].upper()                                                      #defines case status (open, closed, etc.) 

    years_unsolved = 2026 - year                                                    #defines years unsolved     

    row = [name, sex, age, date, status, years_unsolved]                            #places cleaned fields into list 
    return(row)                                                              



##FILE INPUT SECTION##
file_input = input('\nEnter the file name (with extension i.e. .txt, .csv, etc.) containing the records you want to clean: ')     #user input for file name *MAKE SURE THE FILE IS IN THE SAME FOLDER AS THIS PROGRAM*
try: 
    with open(file_input, 'r', encoding='utf-8') as file:                                                                       #with open automatically closes the file after the block of code is executed, r opens in read mode, encoding='utf-8' ensures proper handling of special characters
        print(f'\nContents of {file_input} have been cleaned and placed into a grid: ')                                                 
        records = []                                                                                                            #list created in order to make grid
        headers = ["Name", "Sex", "Age", "Date", "Status", "Years Unsolved"]                                                    #defines headers for grid
        for line in file:                                                                                                       #iterates through each line in the file
            if "|" in line:                                                                                                     #checks for "|", ignoring any blank lines
                records.append(clean_record(line))                                                                              #adds cleaned record to the "records" list created on line 39
    print(tabulate(records, headers = headers, tablefmt = 'grid'))                                                              #tabulate function called to create a grid, records list used as argument for grid data, headers list used as argument for grid headers, tablefmt = 'grid' used to select format for the output

    age = [row[2] for row in records]                                                                                           #age list created by iterating through the records list and selecting the age field (index 2) from each record
    average_age = sum(age) / len(age)                                                                                           #average age calculated by summing values in the list and dividing by list length 
    print(f'Average victim age: {average_age:.2f} years old')   

    years_unsolved_list = [row[5] for row in records]                                                                           #years unsolved list created by iterating through the records list and selecting the years unsolved field (index 5) from each record
    total_years_unsolved = sum(years_unsolved_list)                                                                             #list values summed to calculate total time unsolved
    print(f'Total years unsolved: {total_years_unsolved} years\n')                                                                                  

except FileNotFoundError:                                                                                                       #handles error in which the file is not found
    print(f'Error: The file "{file_input}" could not be found.\n' 
    f'Please check the spelling and ensure the file is in the correct folder, then try again.')

except Exception as e:                                                                                                          #handles any other unexpected errors & prints the error message for the user 
    print(f'An unexpected error occurred: {e}\n' 
    f'Please check the file and try again.') 
