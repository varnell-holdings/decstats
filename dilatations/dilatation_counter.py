import csv

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

count = 0

with open("episodes.csv", "r") as file:
    reader = csv.DictReader(file)
    for row in reader:
        date_parts = row["date"].split("-")
        entry_day = int(date_parts[0])
        entry_month = int(date_parts[1])
        entry_year = date_parts[2]

        if entry_year == year and start_month <= entry_month <= end_month:
            if row["upper"] == "30475":
                count += 1

print()
print(f"The number of dilatations performed in the period {period_name} {year} was {count}.")
