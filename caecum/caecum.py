import csv
import os
import platform
import subprocess
from collections import defaultdict
from pathlib import Path

month_dict = {
    3: "JANUARY-MARCH",
    6: "APRIL-JUNE",
    9: "JULY-SEPTEMBER",
    12: "OCTOBER-DECEMBER",
}


def suc_fail_template():
    return {"success": 0, "fail": 0, "total": 0, "poor_prep": 0}


def log_doc_caecum(results, doctor, outcome, poor_prep=False):
    """Record a colonoscopy result for a doctor."""
    results[doctor][outcome] += 1
    results[doctor]["total"] += 1
    if poor_prep:
        results[doctor]["poor_prep"] += 1


if platform.system() == "Windows":
    base = Path("d:/john tillet/source/active/caecum/")
else:
    base = Path(".")
data_file = base / "episodes.csv"
qps_address = base / "caecum_qps.txt"


def dates_finder(month):
    """Return list of month strings (with leading zeros) for the quarter."""
    return [f"{m:02d}" for m in [month, month - 1, month - 2]]


def format_doctor_line(doctor, stats):
    """Format a single line of doctor statistics."""
    total = stats["total"]
    poor_prep = stats["poor_prep"]
    other_fails = stats["fail"] - poor_prep
    return f"{doctor.ljust(20)}:               {str(total).ljust(8)}   {str(poor_prep).ljust(8)} {str(other_fails).ljust(8)}"


def process_csv_data(year, month):
    """Read the CSV file and return statistics for the quarter.

    Returns a dictionary with:
        results: per-doctor statistics
        total_colons: total number of colonoscopies
        bad_bowel_preps: count of poor prep cases
        failure_reach_caecum: failures minus obstructions (for QPS)
        failures: list of individual failure cases
    """
    results = defaultdict(suc_fail_template)
    month_set = dates_finder(month)
    total_colons = 0
    bad_bowel_preps = 0
    failures = []
    failure_reach_caecum = 0

    with open(data_file) as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Skip rows with no caecum data (upper endoscopies only)
            caecum_value = row['caecum'].strip()
            if not caecum_value:
                continue

            # Parse date in DD-MM-YYYY format
            date_str = row['date']
            date_parts = date_str.split('-')
            row_year = date_parts[2]  # Year is at end
            row_month = date_parts[1]  # Month is in middle

            if row_year == year and row_month in month_set:
                total_colons += 1

                # Determine success/fail from caecum column
                if caecum_value == "success":
                    outcome = "success"
                    reason = ""
                else:
                    outcome = "fail"
                    reason = caecum_value

                if reason == "Poor Prep":
                    log_doc_caecum(results, row['endo'], outcome, poor_prep=True)
                    bad_bowel_preps += 1
                else:
                    log_doc_caecum(results, row['endo'], outcome)

                if outcome == "fail" and reason != "Obstruction":
                    failure_reach_caecum += 1

                if outcome == "fail":
                    case = (date_str, row['endo'], row['mrn'], reason)
                    failures.append(case)

    return {
        "results": results,
        "total_colons": total_colons,
        "bad_bowel_preps": bad_bowel_preps,
        "failure_reach_caecum": failure_reach_caecum,
        "failures": failures,
    }


def print_results(year, month, data):
    """Print summary statistics to the terminal."""
    print(f"QPS CAECUM DATA FOR THE 3 MONTHS PRIOR TO {month}/{year}")
    print("\n\n")
    print(f"Total colons performed:  {data['total_colons']}")
    print()
    print(f"Total number of bad bowel preps:  {data['bad_bowel_preps']}")
    print()
    print(f"Total failure to reach caecum minus obstruction:  {data['failure_reach_caecum']}")
    print("\n\n")
    print(f"TQM COLONOSCOPY CAECUM DATA  FOR THE 3 MONTHS PRIOR TO {month}/{year}")
    print("\n\n")
    print(" Doctor                            Total    Poor Prep   Other Failures")
    print()
    for doctor, stats in data['results'].items():
        print(format_doctor_line(doctor, stats))


def write_report(year, month, data):
    """Write the full report to a file."""
    with open(qps_address, "w") as file:
        # QPS section
        file.write(f"""QPS CAECUM DATA FOR {month_dict[month]} {year}


         Total colons performed:  {data['total_colons']}

         Total number of bad bowel preps:  {data['bad_bowel_preps']}

         Total failure to reach caecum minus obstruction:  {data['failure_reach_caecum']}\n\n\n\n""")

        # TQM section
        file.write(f"TQM CAECUM DATA FOR {month_dict[month]} {year}\n\n\n")
        file.write(
            "Doctor                        Total colons    Poor Prep   Other Failures\n\n"
        )
        for doctor, stats in data['results'].items():
            file.write(format_doctor_line(doctor, stats) + "\n")

        # Individual failure cases
        file.write("\n\n")
        for case in data['failures']:
            file.write(
                f"{case[0]}\t{case[1].ljust(20)}\t{case[2].ljust(20)}\t{case[3]}\n"
            )


def open_report():
    """Open the report file with the default application."""
    if platform.system() == "Windows":
        os.startfile(qps_address)
    else:
        subprocess.run(['open', qps_address])


def main(year, month):
    """Process caecum data and generate reports."""
    data = process_csv_data(year, month)
    print_results(year, month, data)
    write_report(year, month, data)
    open_report()


def intro():
    while True:
        year = input("Year as 4 digits:  ")
        if year.isdigit() and len(year) == 4:
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
