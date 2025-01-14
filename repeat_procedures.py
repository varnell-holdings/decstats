import csv
from collections import defaultdict
import os


def stringify(m):
    if m < 10:
        m = "0" + str(m)
    else:
        m = str(m)
    return m


def month_finder(month):
    a = month - 2
    b = month - 1
    c = month

    return {stringify(a), stringify(b), stringify(c)}


def find_repeats(year, month):
    month_set = month_finder(month)
    procedures = defaultdict(int)
    admissions = 0
    repeat_patients = 0
    with open("day_surgery.csv") as fh:
        reader = csv.reader(fh)
        for episode in reader:
            if (episode[0][6:10] == year and episode[0][3:5] in month_set) or (
                episode[0][6:10] == str(int(year) - 1) and episode[0][3:5] == "12"
            ):
                mrn = episode[1]
                procedures[mrn] += 1
                admissions += 1
                # print(episode[0])
        # print(procedures)
        with open("repeats.txt", "a") as f:
            for key, value in procedures.items():
                if value > 1:
                    print(key)
                    repeat_patients += 1
                    f.write(key + "\n")
    print(f"Number of admissions: {admissions}")
    print(f"Number of repeats: {repeat_patients}")


def intro():
    # print(hi)
    while True:
        year = input("Year as 4 digits:  ")
        if year.isdigit() and len(year) == 4:
            year = year
            break

    while True:
        month = int(input("Enter the month to finish survey as a number: "))
        if month < 13:
            break

    return year, month


if __name__ == "__main__":
    if os.path.exists("repeats.txt"):
        os.remove("repeats.txt")
    year, month = intro()
    find_repeats(year, month)
