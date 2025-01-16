"""
Looks for all  pat_to_procedure that were repeated within  month
where the last one was done in the last 3 month.
Survey to be done end of March, June, September and December.
Actually need to look back 4 months to find all cases.
"""
import csv
from collections import defaultdict
import os
from datetime import datetime
from itertools import chain

headers = [
    "date",
    "mrn",
    "in_theatre",
    "out_theatre",
    "anaesthetist",
    "endoscopist",
    "asa",
    "upper",
    "colon",
    "banding",
    "nurse",
    "clips",
    "glp1",
    "message",
]
# on deployment change "day_surgery.csv" to this
production_file = "D:\\john tillet\\source\\stats\\repeat_pat_to_procedure.py"


def is_within_31_days(date_string_1, date_string_2):
    date_object_1 = datetime.strptime(date_string_1, "%d-%m-%Y")
    date_object_2 = datetime.strptime(date_string_2, "%d-%m-%Y")
    difference = abs((date_object_2 - date_object_1).days)
    return difference < 31


def stringify(month):
    """Change int to a string and add a leading 0 to month"""
    if month < 10:
        month = "0" + str(month)
    else:
        month = str(month)
    return month


def dates_finder(month):
    """March is special case.
    Use a flag to tell main that we need to
    look in final months of previous year.
    """
    z = month - 3
    a = month - 2
    b = month - 1
    c = month
    flip_flag = False
    if c == 3:
        z = 12
        flip_flag = True

    return (
        {
            "a": stringify(a),
            "b": stringify(b),
            "c": stringify(c),
            "z": stringify(z),
        },
        {"a": stringify(a), "b": stringify(b), "c": stringify(c)},
        flip_flag,
    )


def main(year, month):  # year is str, month is int
    """First - check through day_surgery.csv for admissions in the previos 4 months.
    Out of those build a dictionary mapping mrn to a list of admissions
    Second - check through that dictionary to find patients(mrns) that have had
    more than one admission within 31 days. Exclude those whose second admission was
    within the 4th month previous.
    Third - wrie those patient's data to a report file"""
    month_set, reduced_month_set, flip_flag = dates_finder(month)
    mrn_to_episodes = defaultdict(list)
    repeat_patients = 0
    with open("day_surgery.csv") as file:
        reader = csv.DictReader(file, fieldnames=headers)
        for episode in reader:
            if (
                (
                    not flip_flag
                    and episode["date"][6:10] == year
                    and episode["date"][3:5] in month_set.values()
                )
                or (
                    flip_flag
                    and episode["date"][6:10] == str(int(year) - 1)
                    and episode["date"][3:5] == "12"
                )
                or (
                    flip_flag
                    and episode["date"][6:10] == year
                    and episode["date"][3:5] in reduced_month_set.values()
                )
            ):
                mrn = episode["mrn"]
                if episode["upper"]:
                    episode["upper"] = "upper"
                if episode["colon"][0:3] == "320":
                    episode["colon"] = "short colon"
                if episode["colon"][0:3] == "322":
                    episode["colon"] = "long colon"

                data = {
                    "mrn": episode["mrn"],
                    "date": episode["date"],
                    "endoscopist": episode["endoscopist"],
                    "upper": episode["upper"],
                    "colon": episode["colon"],
                }

                if mrn not in mrn_to_episodes:
                    mrn_to_episodes[mrn].append(data)
                else:
                    flat_info = list(
                        chain.from_iterable(d.values() for d in mrn_to_episodes[mrn])
                    )
                    if (
                        data["date"] not in flat_info
                    ):  # the above excludes duplicates that are in day_surgery.csv
                        mrn_to_episodes[mrn].append(data)

        with open("repeats.txt", "a") as file:
            file.write(
                f"""REPORT ON REPEAT PROCEDUES IN THE 3 MONTHS PRIOR TO THE END OF {str(month)}/{year}\n\n"""
            )
            for (
                mrn,
                list_of_admissions,
            ) in mrn_to_episodes.items():
                if (
                    len(list_of_admissions) > 1
                    and list_of_admissions[1]["date"][3:5] != month_set["z"]
                    and (
                        is_within_31_days(
                            list_of_admissions[0]["date"], list_of_admissions[1]["date"]
                        )
                    )
                    and not (
                        (
                            ""
                            in {
                                list_of_admissions[0]["upper"],
                                list_of_admissions[1]["upper"],
                            }
                        )
                        and (
                            ""
                            in {
                                list_of_admissions[0]["colon"],
                                list_of_admissions[1]["colon"],
                            }
                        )
                    )  # this excludes where the repeated admissions was one for upper and one for colon.
                ):
                    for i, admission in enumerate(list_of_admissions):
                        if i == 0:
                            result_string = f"{admission['mrn'].ljust(15)} {admission['date'].ljust(15)} {admission['endoscopist'].ljust(25)} {admission['upper'].ljust(15)} {admission['colon'].ljust(15)}"
                        else:
                            result_string = f"{''.ljust(15)} {admission['date'].ljust(15)} {''.ljust(25)} {admission['upper'].ljust(15)} {admission['colon'].ljust(15)}"

                        print(result_string)
                        file.write(result_string + "\n")
                    print()
                    repeat_patients += 1
                    file.write("\n\n")
            file.write("\n\n\n")
            file.write("\n\n")
            file.write(f"Number of repeats: {repeat_patients}")
    print(f"Number of repeats: {repeat_patients}")
    # os.startfile("repeats.txt")  # uncomment this on deployment on windows


def intro():
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
    main(year, month)
