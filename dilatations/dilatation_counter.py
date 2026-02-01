import csv
import platform

if platform.system() == "Windows":
    csv_path = r"D:\John TILLET\episode_data\episodes.csv"
else:
    csv_path = "episodes.csv"

print("Welcome to Dilatation Counter")
print()

year = input("Enter year: ")

print("Select period:")
print("1. January-June")
print("2. July-December")
period_choice = input("Enter 1 or 2: ")

if period_choice == "1":
    period_name = "January-June"
    start_month = 1
    end_month = 6
else:
    period_name = "July-December"
    start_month = 7
    end_month = 12

dilatation_count = 0
upper_endoscopy_count = 0

with open(csv_path, "r") as file:
    reader = csv.DictReader(file)
    for row in reader:
        date_parts = row["date"].split("-")
        entry_day = int(date_parts[0])
        entry_month = int(date_parts[1])
        entry_year = date_parts[2]

        if entry_year == year and start_month <= entry_month <= end_month:
            if row["upper"].strip():
                upper_endoscopy_count += 1
            if row["upper"] == "30475":
                dilatation_count += 1

print()
print(f"The number of upper endoscopies performed in the period {period_name} {year} was {upper_endoscopy_count}.")
print(f"The number of dilatations performed in the period {period_name} {year} was {dilatation_count}.")
