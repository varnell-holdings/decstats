"""caecum.py calculate % failure rate to reach caecum."""


from collections import defaultdict
import csv
import os

# from tabulate import tabulate


def format_fixed_width(rows):
    column_lengths = [max(len(cell) for cell in col) for col in zip(*rows)]
    output = ""
    for row in rows:
        for column, length in zip(row, column_lengths):
            output += column.ljust(length + 2)
        output = output.rstrip() + "\n"
    return output.rstrip()


while True:
    year = input("Enter year as four digits:  ")
    if len(year) != 4:
        print("Year must be 4 digits.")
        continue
    if not year.isdigit():
        print("Year must be 4 digits.")
        continue
    if int(year) < 2019:
        print("Data starts from July 2019.")
        continue
    else:
        break


print()
while True:
    month = input("Enter first month of period as two digits:  ")
    if len(month) != 2:
        print("Month must be 2 digits.")
        continue
    if not month.isdigit():
        print("Month must be 2 digits.")
        continue
    if int(month) < 1 or int(month) > 12:
        print("Enter a number between 1 and 12")
        continue
    else:
        month = int(month)
        break

print()
while True:
    num_months = input("How many months of data do you want?  ")
    if not num_months.isdigit():
        print("Input must be a number.")
        continue
    else:
        num_months = int(num_months)
        break


months = []
for i in range(num_months):
    months.append(month + i)

months = [str(s).zfill(2) for s in months]

longs = defaultdict(int)
failures = defaultdict(int)


doctor_headers = ["Endoscopist", "Colonoscopies", "Failures", "% Failures"]
doctor_table = [doctor_headers]
failure_table = []
failure_headers = ["Date", "Endoscopist", "MRN", "Reason"]

""" csv file cotains the following data
    - date as String
    - Dr Surname
    - mrn as String
    - 'success/fail' flag as String
    - Reason for fail - empty string if success, 'Poor Prep', etc for fail

"""


with open("D:\\john tillet\\source\\caecum\\caecum.csv") as file:
    reader = csv.reader(file)
    for scope in reader:
        name = scope[1]
        if name == "Lee":
            name = "Fenton-Lee"
        elif name == "HAIFER":
            name = "Haifer"
        if scope[0][:4] == year and scope[0][5:7] in months:
            longs[name] += 1
            if scope[3] == "fail":
                failures[name] += 1
                failure_table.append([scope[0], scope[1], scope[2], ""])


for doctor in sorted(longs):
    entry = []
    num_lowers = str(longs[doctor])
    denom = int(num_lowers)
    numerator = int(failures.get(doctor, "0"))
    percentage = str(round((numerator / denom) * 100, 0))
    #    percentage_as_str = "{0:.1f}".format(percentage)
    entry.extend([doctor, num_lowers, str(failures.get(doctor, "0")), percentage])
    doctor_table.append(entry)


# Print results to caecum.txt

target_file = "d:\\john tillet\\source\\caecum\\caecum.txt"
print(
    "CAECAL INTUBATION RATES FOR {} MONTHS FROM 1-{}-{}\n\n".format(
        num_months, month, year
    ),
    file=open(target_file, "w"),
)
# print(tabulate(doctor_table, doctor_headers), file=open(target_file, "a"))

with open(target_file, "a") as file:
    file.write(format_fixed_width(doctor_table))
print("\n\n\n\n", file=open(target_file, "a"))
# print(tabulate(failure_table, failure_headers), file=open(target_file, "a"))

with open(target_file, "a") as file:
    file.write(format_fixed_width(failure_table))
print("Data written to D:\\john tillet\\source\\caecum\\caecum.txt")
input("Press any key to finish")
os.startfile(target_file)
