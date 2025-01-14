import csv
from collections import defaultdict
import os


def stringify(m):
    if m < 10:
        m = "0" + str(m)
    else:
        m = str(m)
    return m


def dates_finder(month):
    z = month - 3
    a = month - 2
    b = month - 1
    c = month
    flip_flag = False
    if c == 3:
        z = 12
        flip_flag = True

    return {stringify(a), stringify(b), stringify(c)}, stringify(z), flip_flag


def find_repeats(year, month):
    month_set, z, flip_flag = dates_finder(month)
    procedures = defaultdict(list)
    admissions = 0
    repeat_patients = 0
    with open("day_surgery.csv") as fh:
        reader = csv.reader(fh)
        for episode in reader:
            if (episode[0][6:10] == year and episode[0][3:5] in month_set) or (
                flip_flag
                and episode[0][6:10] == str(int(year) - 1)
                and episode[0][3:5] == "12"
            ):
                mrn = episode[1]
                data = (episode[1], episode[0], episode[7], episode[8])
                if mrn not in procedures:
                    procedures[mrn].append(data)
                else:
                    flat_info = [item for tup in procedures[mrn] for item in tup]
                    if data[1] not in flat_info:
                        procedures[mrn].append(data)
                admissions += 1

        # print(procedures)
        with open("repeats.txt", "a") as f:
            for key, value in procedures.items():
                if len(value) > 1:
                    for admission in value:
                        print(
                            f"{admission[0].ljust(15)} {admission[1].ljust(15)} {admission[2].ljust(15)} {admission[3].ljust(15)}"
                        )
                    print()
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
        month = int(
            input("Enter the month to finish survey as a number, 3, 6, 9, 12: ")
        )
        if month in {3, 6, 9, 12}:
            break

    return year, month


if __name__ == "__main__":
    if os.path.exists("repeats.txt"):
        os.remove("repeats.txt")
    year, month = intro()
    find_repeats(year, month)
