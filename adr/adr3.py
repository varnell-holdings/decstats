from collections import defaultdict
import csv
from dataclasses import dataclass
from datetime import datetime
import re

import tkinter as tk
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
# filenames = (
#     askopenfilename()
# )  # show an "Open" dialog box and return the path to the selected file
# print(filenames)
files_list = []


@dataclass
class Ep:
    date: str = ""
    surname: str = ""
    mrn: str = ""
    dob: str = ""
    doc: str = ""
    procedure: str = ""
    ta: str = ""
    sa: str = ""
    tva: str = ""
    malig: str = ""


def date_range(procedure_date, d_range):
    iso_date = procedure_date[4:8] + procedure_date[2:4] + procedure_date[0:2]
    if d_range[0] == 0:
        d_range[0] = iso_date
        d_range[1] = iso_date
    elif iso_date < d_range[0]:
        d_range[0] = iso_date
    elif iso_date > d_range[1]:
        d_range[1] = iso_date
    print(d_range)
    return d_range


def under50(dop, dob):
    """given a date of procedure and date of birth in
    strings of format 'ddmmyyyy' return True if aged < 50
    on date of procedure or false otherwise"""

    # Parse the date strings into datetime objects
    procedure_date = datetime.strptime(dop, "%d%m%Y")
    birth_date = datetime.strptime(dob, "%d%m%Y")

    # Calculate age on the procedure date
    age = procedure_date.year - birth_date.year

    # Adjust for cases where birthday hasn't occurred yet this year
    if (procedure_date.month, procedure_date.day) < (birth_date.month, birth_date.day):
        age -= 1

    return age < 50


def doc_dict_maker():
    """Make key:value pairs from episodes.csv
    Need multiple keys as some data in the PHISCData file is incorrect.
    The values are a tuple of (doctor, mrn)
    """
    doc_dict = dict()
    unknown_doc_dict_1 = dict()
    unknown_doc_dict_2 = dict()
    with open("episodes.csv", "r") as f:
        reader = csv.reader(f)
        next(reader)
        for entry in reader:
            date = entry[0]
            date = date.replace("-", "")

            dob = entry[18]
            dob = dob.replace("/", "")
            if len(dob) == 7:
                dob = "0" + dob
            name = entry[17].lower()
            key = date + dob + name
            second_key = date + dob
            third_key = date + name
            dob_for_csv = entry[18].replace("/", "")
            if len(dob_for_csv) == 7:
                dob_for_csv = "0" + dob_for_csv
            doc = (entry[5].lower(), entry[1], dob_for_csv)
            doc_dict[key] = doc
            unknown_doc_dict_1[second_key] = doc
            unknown_doc_dict_2[third_key] = doc
    return doc_dict, unknown_doc_dict_1, unknown_doc_dict_2


def iter_over_files(doc_dict, unknown_doc_dict_1, unknown_doc_dict_2):
    for num, file in enumerate(files_list):
        parser(file, num, doc_dict, unknown_doc_dict_1, unknown_doc_dict_2)


def parser(f, num, doc_dict, unknown_doc_dict_1, unknown_doc_dict_2):
    """Input a PHISCData text file
    Output a csv file
    See above dataclass for entries in csv
    See info_data.txt in this directory for an example of a split line from
    the PHISCData file
    The doc and mrn entries are not in the PHISCData file and are retrieved
    from episodes.csv using a key:value generated by doc_dict_maker
    """
    if num == 0:
        mode = "w"
    else:
        mode = "a"

    headers = [
        "date",
        "surname",
        "mrn",
        "dob",
        "doc",
        "procedure",
        "ta",
        "sa",
        "tva",
        "malig" "",
    ]
    with open(f) as file, open("adr.csv", mode) as csvfile:
        writer = csv.writer(csvfile)
        if num == 0:
            writer.writerow(headers)
        file.readline()
        for line in file.readlines():
            ep = Ep()
            entry = line.split()

            procedure_codes = entry[-2]
            if "32090" in procedure_codes or "32093" in procedure_codes:
                if "32090" in procedure_codes:
                    ep.procedure = "32090"
                elif "32093" in procedure_codes:
                    ep.procedure = "32093"

                ep.surname = entry[2].lower()

                # find the entry that is either 04 or starts with 04G
                # this is where the ICD codes start
                # Also dob is 2 entries before that
                # return -1 if not found
                index = next(
                    (
                        i
                        for i, item in enumerate(entry)
                        if (item == "04" or item[:3] == "04G")
                    ),
                    -1,
                )
                if index != -1:
                    ep.date = entry[index - 2][:8]

                    digits_only = re.sub(r"[^0-9]", "", entry[index - 3])
                    ep.dob = digits_only[4:12]

                    if ep.procedure == "32093":  # iterate through icd codes
                        i = index + 1
                        while True:
                            if entry[i] == "2":
                                break
                            elif entry[i] == "2M8211/0":
                                ep.ta = "ta"  # tubular adenoma
                                i += 1
                            elif entry[i] == "2M8213/0":
                                ep.sa = "sa"  # serrated adenoma
                                i += 1
                            elif entry[i] == "2M8263/0":
                                ep.tva = "tva"  # tubulovillous adenoma
                                i += 1
                            elif entry[i][:2] == "2M":
                                if not ep.malig:
                                    ep.malig = ep.malig + entry[i]
                                else:
                                    ep.malig = ep.malig + " " + entry[i]
                                i += 1
                            else:
                                i += 1

                    #  get the doctor and mrn from episodes.csv using dictionaries
                    key_for_doc = ep.date + ep.dob + ep.surname
                    second_key = ep.date + ep.dob
                    third_key = ep.date + ep.surname
                    try:
                        doctor = doc_dict[key_for_doc]
                    except KeyError:
                        try:
                            doctor = unknown_doc_dict_1[second_key]
                        except KeyError:
                            doctor = unknown_doc_dict_2.get(
                                third_key, ("unknown", "?", "?")
                            )
                    ep.doc = doctor[0]
                    ep.mrn = doctor[1]
                    if not ep.dob:
                        ep.dob = doctor[2]
                    try:
                        datetime.strptime(ep.dob, "%d%m%Y")
                    except ValueError as e:
                        ep.dob = doctor[2]
                        print(f"{e}")

                    line_list = []
                    line_list.append(ep.date)
                    line_list.append(ep.surname)
                    line_list.append(ep.mrn)
                    line_list.append(ep.dob)
                    line_list.append(ep.doc)
                    line_list.append(ep.procedure)
                    line_list.append(ep.ta)
                    line_list.append(ep.sa)
                    line_list.append(ep.tva)
                    line_list.append(ep.malig)

                print(line_list)
                writer.writerow(line_list)


def analyse():
    num_colons = defaultdict(int)
    num_polyps = defaultdict(int)
    adr_dict = defaultdict(float)
    num_ssa = defaultdict(int)
    ssa_dict = defaultdict(float)

    num_colons_under50 = defaultdict(int)
    num_polyps_under50 = defaultdict(int)
    adr_dict_under50 = defaultdict(float)

    num_colons_over50 = defaultdict(int)
    num_polyps_over50 = defaultdict(int)
    adr_dict_over50 = defaultdict(float)
    total_colons_over_50 = 0
    total_polyps_over_50 = 0
    total_ssa_over_50 = 0

    d_range = [0, 0]

    with open("adr.csv", "r") as f:
        reader = csv.DictReader(f)
        for entry in reader:
            print(entry)
            d_range = date_range(entry["date"], d_range)
            if entry["dob"] in {"?", ""}:
                continue
            # all patients

            num_colons[entry["doc"]] += 1
            if entry["sa"]:
                num_ssa[entry["doc"]] += 1
            if entry["ta"] or entry["sa"] or entry["tva"]:
                num_polyps[entry["doc"]] += 1

            # under 50
            if under50(entry["date"], entry["dob"]):
                num_colons_under50[entry["doc"]] += 1
                if entry["ta"] or entry["sa"] or entry["tva"]:
                    num_polyps_under50[entry["doc"]] += 1

            # over 50
            else:
                num_colons_over50[entry["doc"]] += 1
                total_colons_over_50 += 1
                if entry["sa"]:
                    total_ssa_over_50 += 1
                if entry["ta"] or entry["sa"] or entry["tva"]:
                    num_polyps_over50[entry["doc"]] += 1
                    total_polyps_over_50 += 1

    doc_list = sorted([n for n in num_colons.keys()])
    # pprint.pprint(doc_list)
    # pprint.pprint(num_colons)
    # pprint.pprint(num_polyps)

    for doctor in doc_list:
        if num_colons[doctor] == 0:
            adr_dict[doctor] = -1
        else:
            adr_dict[doctor] = round((num_polyps[doctor] / num_colons[doctor]) * 100)

    for doctor in doc_list:
        if num_colons[doctor] == 0:
            ssa_dict[doctor] = -1
        else:
            ssa_dict[doctor] = round((num_ssa[doctor] / num_colons[doctor]) * 100)

    for doctor in doc_list:
        if num_colons_under50[doctor] == 0:
            adr_dict_under50[doctor] = -1
        else:
            adr_dict_under50[doctor] = round(
                (num_polyps_under50[doctor] / num_colons_under50[doctor]) * 100
            )

    for doctor in doc_list:
        if num_colons_over50[doctor] == 0:
            adr_dict_over50[doctor] = -1
        else:
            adr_dict_over50[doctor] = round(
                (num_polyps_over50[doctor] / num_colons_over50[doctor]) * 100
            )
    unit_adr = round((total_polyps_over_50 / total_colons_over_50) * 100)
    unit_ssa = round((total_ssa_over_50 / total_colons_over_50) * 100)
    print(unit_adr)

    start_date = d_range[0]
    start_date = start_date[6:8] + "-" + start_date[4:6] + "-" + start_date[0:4]
    end_date = d_range[1]
    end_date = end_date[6:8] + "-" + end_date[4:6] + "-" + end_date[0:4]
    # pprint.pprint(adr_dict)
    # pprint.pprint(adr_dict_under50)
    # pprint.pprint(adr_dict_over50)
    print(f"ADR Results from {start_date} to {end_date}")
    print()
    print(" " * 20, " NumCols     ADR       ADR<50      ADR>50    SSA(all ages)")
    print()
    for doctor in doc_list:
        print(
            f"{doctor.title().ljust(20)}  {str(num_colons[doctor]).ljust(10)}  {str(adr_dict[doctor]).ljust(10)}  {str(adr_dict_under50[doctor]).ljust(10)} {str(adr_dict_over50[doctor]).ljust(10)} {str(ssa_dict[doctor]).ljust(10)}"
        )
    print("\n")
    print("\n")
    print(
        f"Total colonoscopies done on patients over 50 years:  {total_colons_over_50}"
    )
    print("\n")
    print(f"Unit wide ADR for over 50 years:  {unit_adr}%")
    print("\n")
    print(f"Unit wide SSA for over 50 years:  {unit_ssa}%")

    with open("adr.txt", "w") as file:
        file.write(f"ADR Results from {start_date} to {end_date}\n")
        file.write(" " * 20)
        file.write(" Total Cols     ADR       ADR<50      ADR>50   SSA(all ages)")
        file.write("\n")
        for doctor in doc_list:
            file.write(
                f"{doctor.title().ljust(20)}  {str(num_colons[doctor]).ljust(10)}  {str(adr_dict[doctor]).ljust(10)}  {str(adr_dict_under50[doctor]).ljust(10)} {str(adr_dict_over50[doctor]).ljust(10)} {str(ssa_dict[doctor]).ljust(10)}\n"
            )
        file.write("\n")
        file.write("\n")
        file.write(
            f"Total colonoscopies done on patients over 50 years:  {total_colons_over_50}"
        )
        file.write("\n")
        file.write(f"Unit wide ADR for over 50 years:  {unit_adr}%")
        file.write("\n")
        file.write(f"Unit wide SSA for over 50 years:  {unit_ssa}%")


def collect_files():
    print("Button 1 clicked")
    global files_list
    filename = askopenfilename()
    files_list.append(filename)
    print(files_list)


def button2_click():
    print("Button 2 clicked")
    # Add your function code here
    doc_dict, unknown_doc_dict_1, unknown_doc_dict_2 = doc_dict_maker()
    iter_over_files(doc_dict, unknown_doc_dict_1, unknown_doc_dict_2)


def button3_click():
    print("Button 3 clicked")
    # Add your function code here


def button4_click():
    print("Button 4 clicked")
    # Add your function code here


# Create the main window
root = tk.Tk()
root.title("Four Button Window")
root.geometry("200x300")

# Create and pack the buttons vertically
button1 = tk.Button(root, text="Open Files", command=collect_files, width=15, height=2)
button1.pack(pady=10)

button2 = tk.Button(
    root, text="Create datafile", command=button2_click, width=15, height=2
)
button2.pack(pady=10)

button3 = tk.Button(root, text="Open data", command=button3_click, width=15, height=2)
button3.pack(pady=10)

button4 = tk.Button(root, text="Analyse", command=analyse, width=15, height=2)
button4.pack(pady=10)

# Start the GUI event loop
root.attributes("-topmost", True)
root.mainloop()

# if __name__ == "__main__":
#     doc_dict, unknown_doc_dict_1, unknown_doc_dict_2 = doc_dict_maker()
#     Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
#     filenames = (
#         askopenfilename()
#     )  # show an "Open" dialog box and return the path to the selected file
#     print(filenames)
#     iter_over_files(filenames)
