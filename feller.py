import csv


old_csv = "day_surgery.csv"

with open(old_csv, "r") as oldcsv, open("new_csv.csv", "w") as new_csv:
    reader = csv.reader(oldcsv)
    writer = csv.writer(new_csv)
    for entry in reader:
        if entry[5] == "Dr R Feller":
            entry[5] = "A/Prof R Feller"
        writer.writerow(entry)
