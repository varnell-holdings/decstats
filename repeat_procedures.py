import csv
from collections import defaultdict
import os
from datetime import datetime


def is_within_91_days(date_string_1, date_string_2):
    date_object_1 = datetime.strptime(date_string_1, "%d-%m-%Y")
    date_object_2 = datetime.strptime(date_string_2, "%d-%m-%Y")
    difference = abs((date_object_2 - date_object_1).days)
    return difference < 91


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

    return (
        {"a": stringify(a), "b": stringify(b), "c": stringify(c), "z": stringify(z)},
        {"a": stringify(a), "b": stringify(b), "c": stringify(c)},
        flip_flag,
    )


def find_repeats(year, month):
    month_set, reduced_month_set, flip_flag = dates_finder(month)
    procedures = defaultdict(list)
    # admissions = 0
    repeat_patients = 0
    with open("day_surgery.csv") as fh:
        reader = csv.reader(fh)
        for episode in reader:
            if (
                (
                    not flip_flag
                    and episode[0][6:10] == year
                    and episode[0][3:5] in month_set.values()
                )
                or (
                    flip_flag
                    and episode[0][6:10] == str(int(year) - 1)
                    and episode[0][3:5] == "12"
                )
                or (
                    flip_flag
                    and episode[0][6:10] == str(int(year))
                    and episode[0][3:5] in reduced_month_set.values()
                )
            ):
                mrn = episode[1]
                if episode[7]:
                    episode[7] = "upper"
                if episode[8][0:3] == "320":
                    episode[8] = "short colon"
                if episode[8][0:3] == "322":
                    episode[8] = "long colon"
                data = (episode[1], episode[0], episode[7], episode[8])
                if mrn not in procedures:
                    procedures[mrn].append(data)
                else:
                    flat_info = [item for tup in procedures[mrn] for item in tup]
                    if (
                        data[1] not in flat_info
                    ):  # don't add duplicates in day_surgery.csv
                        procedures[mrn].append(data)
                # admissions += 1

        # print(procedures)
        with open("repeats.txt", "a") as fh:
            fh.write(
                f"""REPORT ON REPEAT PROCEDURES IN THE 3 MONTHS PRIOR TO THE END OF {str(month)}/{year}\n\n"""
            )
            for key, value in procedures.items():
                if (
                    len(value) > 1
                    and value[1][1][3:5]
                    != month_set["z"]  # exclude repeats in the 4th month ago :
                    and (is_within_91_days(value[0][1], value[1][1]))
                    and not (
                        "" in {value[0][2], value[1][2]}
                        and "" in {value[0][3], value[1][3]}
                    )
                ):
                    for admission in value:
                        result_string = f"{admission[0].ljust(15)} {admission[1].ljust(15)} {admission[2].ljust(15)} {admission[3].ljust(15)}"
                        print(result_string)
                        fh.write(result_string + "\n")
                    print()
                    repeat_patients += 1
                    fh.write("\n\n")
            fh.write("\n\n\n")
            # fh.write(f"Number of admissions: {admissions}")
            fh.write("\n\n")
            fh.write(f"Number of repeats: {repeat_patients}")
    # print(f"Number of admissions in previous 4 months: {admissions}")
    print(f"Number of repeats: {repeat_patients}")
    # os.startfile("repeats.txt")


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
