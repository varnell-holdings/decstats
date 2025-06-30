import csv
from collections import defaultdict
from datetime import datetime
import pprint


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


num_colons = defaultdict(int)
num_polyps = defaultdict(int)
adr_dict = defaultdict(float)

num_colons_under50 = defaultdict(int)
num_polyps_under50 = defaultdict(int)
adr_dict_under50 = defaultdict(float)

num_colons_over50 = defaultdict(int)
num_polyps_over50 = defaultdict(int)
adr_dict_over50 = defaultdict(float)


with open("adr.csv", "r") as f:
    reader = csv.DictReader(f)
    for entry in reader:
        # all patients
        num_colons[entry["doc"]] += 1
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
            if entry["ta"] or entry["sa"] or entry["tva"]:
                num_polyps_over50[entry["doc"]] += 1


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

# pprint.pprint(adr_dict)
# pprint.pprint(adr_dict_under50)
# pprint.pprint(adr_dict_over50)
print(" " * 20, " NumCols     ADR       ADR<50      ADR>50")
print()
for doctor in doc_list:
    print(
        f"{doctor.title().ljust(20)}  {str(num_colons[doctor]).ljust(10)}  {str(adr_dict[doctor]).ljust(10)}  {str(adr_dict_under50[doctor]).ljust(10)} {str(adr_dict_over50[doctor]).ljust(10)}"
    )

with open("adr.txt", "w") as file:
    file.write(" " * 20)
    file.write(" NumCols     ADR       ADR<50      ADR>50")
    file.write("\n")
    for doctor in doc_list:
        file.write(
            f"{doctor.title().ljust(20)}  {str(num_colons[doctor]).ljust(10)}  {str(adr_dict[doctor]).ljust(10)}  {str(adr_dict_under50[doctor]).ljust(10)} {str(adr_dict_over50[doctor]).ljust(10)}\n"
        )

if __name__ == "__main__":
    print("\n")
