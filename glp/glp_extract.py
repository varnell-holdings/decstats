import csv

with open("day_surgery.csv") as f1, open("glp.csv", "w") as f2:
    reader = csv.reader(f1)
    writer = csv.writer(f2)
    for a in reader:
        if a[12] in {"Yes", "No"}:
            writer.writerow(a)
