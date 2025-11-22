# -*- coding: utf-8 -*-
"""
Created on Thu Sep 13 08:36:36 2018
@author: John Tillett
Return whether on weekly target from first_date.
Count entries in master and current csv files.
"""
import csv
import datetime
import math

import pyautogui as pya
import colorama
colorama.init()


def clear():
    print("\033[2J")  # clear screen
    print("\033[1;1H")  # move to top left

DESIRED_WEEKLY = pya.prompt(text="Weekly Target.", title="Halo", default="40")
YEAR = str(datetime.datetime.now().year)
FIRST_DATE = datetime.datetime(int(YEAR), 1, 1)

carry_over = 320
today = datetime.datetime.now()
this_year_number = 0

with open("d:\JOHN TILLET\episode_data\sedation\Tillett_master.csv") as h:
    reader = csv.reader(h)
    for ep in reader:
        if ep[0].split("-")[-1] == YEAR:
            this_year_number += 1
try:
    with open("d:\JOHN TILLET\episode_data\sedation\Tillett.csv") as h:
        reader = csv.reader(h)
        for ep in reader:
            if ep[0].split("-")[-1] == YEAR:
                this_year_number += 1
except FileNotFoundError:
    this_year_number += 0
#    print("Tillett.csv not found. Try again after doing a patient.")
#    input("Press any key to exit")
#    sys.exit(0)


total_plus_carryover = this_year_number + carry_over
a = today - FIRST_DATE
days_diff = a.days
desired_number = int(days_diff * int(DESIRED_WEEKLY) / 7)
excess = this_year_number - desired_number
av_so_far = this_year_number * 7 / days_diff
clear()
print("Patients this year: {}\n".format(this_year_number))
print("Patients this year plus carry over from last year : {}\n".format(total_plus_carryover))
print("Excess for {} - without carry over: {}\n".format(DESIRED_WEEKLY, excess))
print("Average per week - without carry over: ", math.floor(av_so_far))
input()
