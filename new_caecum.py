from collections import defaultdict
import csv

month_dict = {3: "JANUARY-MARCH", 6: "APRIL-JUNE", 9: "JULY-SEPTEMBER", 12: "OCTOBER-DECEMBER"}


def suc_fail_template():
    return {"success": 0, "fail": 0, "total": 0, "poor_prep": 0}


results = defaultdict(suc_fail_template)


def log_doc_caecum(doctor, suc_fail, poor_prep=False):
    results[doctor][suc_fail] += 1
    results[doctor]["total"] += 1
    if poor_prep:
        results[doctor]["poor_prep"] += 1


qps_address = "caecum_qps.txt"
tqm_address = "caecum_tqm.txt"


def dates_finder(month):
    """Set varibles to previous 3 month & stringify them."""

    def stringify(month):
        """Change int to a string and add a leading 0 to month"""
        if month < 10:
            month = "0" + str(month)
        else:
            month = str(month)
        return month

    month_set = [stringify(month), stringify(month - 1), stringify(month - 2)]
    return month_set


def main(year, month):
    month_set = dates_finder(month)
    total_colons = 0
    bad_bowel_preps = 0
    failure_reach_caecum = 0  # For QPS defined as total fails except bowel obstructions and including poor preps
    with open("caecum.csv") as file:
        reader = csv.reader(file)
        for line in reader:
            if line[0][0:4] == year and line[0][5:7] in month_set:
                total_colons += 1
                if line[4] == "Poor Prep":
                    log_doc_caecum(line[1], line[3], poor_prep=True)
                    bad_bowel_preps += 1
                else:
                    log_doc_caecum(line[1], line[3])
                if line[3] == "fail" and line[4] != "Obstruction":
                    failure_reach_caecum += 1

    # Printing to terminal for debugging
    print(f"QPS CAECUM DATA FOR THE 3 MONTHS PRIOR TO {month}/{year}")
    print("\n\n")
    print(f"Total colons performed:  {total_colons}")
    print()
    print(f"Total number of bad bowel preps:  {bad_bowel_preps}")
    print()
    print(f"Total failure to reach caecum minus obstruction:  {failure_reach_caecum}")
    print("\n\n")
    print(F"TQM COLONOSCOPY CAECUM DATA  FOR THE 3 MONTHS PRIOR TO {month}/{year}")
    print("\n\n")
    print(" Doctor                            Total    Poor Prep   Other Failures")
    print()
    for key, value in results.items():
        print(f"{key.ljust(20)}:               {str(value["total"]).ljust(8)}   {str(value["poor_prep"]).ljust(8)} {str(value['fail'] - value["poor_prep"]).ljust(8)}")

    # Printing to two files for QPS and TQM
    with open(qps_address, "w") as file:
        file.write(
            f"""QPS AND TQM CAECUM DATA FOR {month_dict[month]} {year}
            

         Total colons performed:  {total_colons}

         Total number of bad bowel preps:  {bad_bowel_preps}

         Total failure to reach caecum minus obstruction:  {failure_reach_caecum}\n\n\n\n"""
        )
    with open(tqm_address, "w") as file:
        file.write(f"TQM COLONOSCOPY CAECUM DATA FOR {month_dict[month]} {year}\n\n\n")
        file.write("Doctor                            Total    Poor Prep   Other Failures\n\n")
        for key, value in results.items():
            file.write(f"{key.ljust(20)}:               {str(value["total"]).ljust(8)}   {str(value["poor_prep"]).ljust(8)} {str(value['fail'] - value["poor_prep"]).ljust(8)}\n")

    # os.startfile(qps_address)
    # os.startfile(tqm_address)
    # uncomment this on deployment on windows


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
    year, month = intro()
    main(year, month)
