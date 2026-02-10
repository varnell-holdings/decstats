import csv
from collections import Counter

chosen_year = input("Enter year (e.g. 2025): ").strip()

counts = Counter()

with open("episodes.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        date = row["date"]
        year = date.split("-")[2]
        if year == chosen_year:
            anaes = row["anaes"].strip()
            if anaes:
                counts[anaes] += 1

if not counts:
    print(f"No procedures found for {chosen_year}.")
else:
    with open("anaes_count.txt", "w") as out:
        out.write(f"Anaesthetist procedure counts for {chosen_year}:\n")
        out.write("-" * 35 + "\n")
        for name, count in counts.most_common():
            out.write(f"{name:<20} {count}\n")
        out.write("-" * 35 + "\n")
        out.write(f"{'Total':<20} {sum(counts.values())}\n")

    print(f"Results for {chosen_year} written to anaes_count.txt")
