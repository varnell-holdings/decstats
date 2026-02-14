import configparser
import csv
import os
import platform
import subprocess
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import ttk

# ========== CONFIGURATION ==========
# File paths — Windows uses production paths, Mac uses current directory
if platform.system() == "Windows":
    data_base = Path("d:/john tillet/episode_data/")
    code_base = Path("d:/john tillet/source/active/follow_up/")
else:
    data_base = Path(".")
    code_base = Path(".")

# Read start date from config.ini (DD-MM-YYYY format)
config = configparser.ConfigParser()
config.read(code_base / "config.ini")
START_DATE = config["settings"]["start_date"]

EPISODES_FILE = data_base / "episodes.csv"
FOLLOWUP_FILE = code_base / "follow_up.csv"
# ====================================


def load_episodes(filename):
    """Read all rows from the CSV file and return as a list of dictionaries."""
    rows = []
    with open(filename, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def parse_date(date_string):
    """Convert a DD-MM-YYYY string into a datetime object."""
    return datetime.strptime(date_string, "%d-%m-%Y")


def get_outstanding_patients(all_rows):
    """Return patients from START_DATE to yesterday that haven't been called yet.

    - Filters all_rows to only dates from START_DATE up to yesterday (excludes today)
    - Reads follow_up.csv to find already-done patients (matched by date + mrn)
    - Removes already-done patients
    - Sorts by date, oldest first
    """
    start = parse_date(START_DATE)
    yesterday = datetime.now() - timedelta(days=1)

    # Keep only rows in the date range
    in_range = []
    for row in all_rows:
        row_date = parse_date(row["date"])
        if start <= row_date <= yesterday:
            in_range.append(row)

    # Build a set of already-done (date, mrn) pairs from follow_up.csv
    done = set()
    if os.path.exists(FOLLOWUP_FILE) and os.path.getsize(FOLLOWUP_FILE) > 0:
        with open(FOLLOWUP_FILE, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                done.add((row["date"], row["mrn"]))

    # Remove already-done patients
    outstanding = []
    for row in in_range:
        if (row["date"], row["mrn"]) not in done:
            outstanding.append(row)

    # Sort by date, oldest first
    outstanding.sort(key=lambda row: parse_date(row["date"]))

    return outstanding


def display_patient(patient, labels):
    """Update the label widgets with data from one patient row."""
    name = f"{patient['title']} {patient['firstname']} {patient['surname']}"

    labels["date"].config(text=patient["date"])
    labels["name"].config(text=name)
    labels["endo"].config(text=patient["endo"])
    labels["anaes"].config(text=patient["anaes"])
    labels["nurse"].config(text=patient["nurse"])
    labels["upper"].config(text=patient["upper"])
    labels["colon"].config(text=patient["colon"])
    labels["anal"].config(text=patient["anal"])
    labels["polyp"].config(text=patient["polyp"])
    # Format phone as "dddd ddd ddd" for readability
    phone = patient["phone"]
    if len(phone) == 10:
        phone = f"{phone[:4]} {phone[4:7]} {phone[7:]}"
    labels["phone"].config(text=phone)


def clear_display(labels, counter_label):
    """Blank out all the patient data labels."""
    for label in labels.values():
        label.config(text="")
    counter_label.config(text="")


def write_result(patient, answered, issue, issue_text):
    """Append one row to follow_up.csv with original patient data plus follow-up fields."""
    # Get the column names from the patient dict (original CSV columns)
    original_columns = list(patient.keys())
    all_columns = original_columns + ["answered", "issue", "issue_text"]

    # Check if we need to write a header (file doesn't exist or is empty)
    write_header = (
        not os.path.exists(FOLLOWUP_FILE) or os.path.getsize(FOLLOWUP_FILE) == 0
    )

    with open(FOLLOWUP_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_columns)

        if write_header:
            writer.writeheader()

        # Build the row: start with all original patient data, add our 3 new fields
        row = dict(patient)
        row["answered"] = answered
        row["issue"] = issue
        row["issue_text"] = issue_text
        writer.writerow(row)


def update_followup_row(date, mrn, issue, issue_text):
    """Find a row in follow_up.csv by date+mrn and update its follow-up fields.

    Sets answered to "yes", updates issue, and appends new issue_text
    to any existing text (separated by ' | ') so previous notes are preserved.
    Returns True if the row was found and updated, False otherwise.
    """
    rows = []
    found = False

    with open(FOLLOWUP_FILE, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row["date"] == date and row["mrn"] == mrn:
                row["answered"] = "yes"
                row["issue"] = issue
                # Append new details to existing text instead of replacing
                existing = row.get("issue_text", "").strip()
                new_text = issue_text.strip()
                if existing and new_text:
                    row["issue_text"] = f"{existing} | {new_text}"
                elif new_text:
                    row["issue_text"] = new_text
                found = True
            rows.append(row)

    if found:
        with open(FOLLOWUP_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    return found


def main():
    # Load all episodes once at startup
    all_rows = load_episodes(EPISODES_FILE)

    # These variables track the current filtered list and position.
    # We use a list so the nested functions can modify the values.
    filtered = [[]]
    index = [0]
    called = [0]

    # --- Build the window ---
    root = tk.Tk()
    root.title("Follow-Up")

    # --- Menu bar ---
    def open_config():
        config_path = code_base / "config.ini"
        if platform.system() == "Windows":
            subprocess.Popen(["notepad", str(config_path)])
        else:
            subprocess.Popen(["open", str(config_path)])

    def open_callback_dialog():
        """Open a popup to find a patient in follow_up.csv and update their record."""
        dialog = tk.Toplevel(root)
        dialog.title("Patient Callback")
        dialog.resizable(False, False)
        pad = {"padx": 10, "pady": 5}

        # Row 0: Date field
        ttk.Label(dialog, text="Date (DD-MM-YYYY):").grid(row=0, column=0, sticky="w", **pad)
        date_entry = ttk.Entry(dialog, width=15)
        date_entry.grid(row=0, column=1, sticky="w", **pad)

        # Row 1: MRN field
        ttk.Label(dialog, text="MRN:").grid(row=1, column=0, sticky="w", **pad)
        mrn_entry = ttk.Entry(dialog, width=15)
        mrn_entry.grid(row=1, column=1, sticky="w", **pad)

        # Row 3: Patient name (hidden until search succeeds)
        name_label = ttk.Label(dialog, text="", font=("TkDefaultFont", 11, "bold"))
        name_label.grid(row=3, column=0, columnspan=2, sticky="w", **pad)
        name_label.grid_remove()

        # Row 4: Problem? radio buttons
        cb_issue_var = tk.StringVar(value="no")
        ttk.Label(dialog, text="Problem?").grid(row=4, column=0, sticky="w", **pad)
        issue_frame = ttk.Frame(dialog)
        issue_frame.grid(row=4, column=1, sticky="w", **pad)
        cb_issue_yes = ttk.Radiobutton(
            issue_frame, text="Yes", variable=cb_issue_var, value="yes",
            command=lambda: cb_details_entry.config(state="normal"),
        )
        cb_issue_no = ttk.Radiobutton(
            issue_frame, text="No", variable=cb_issue_var, value="no",
            command=lambda: (cb_details_entry.config(state="normal"),
                             cb_details_entry.delete(0, "end"),
                             cb_details_entry.config(state="disabled")),
        )
        cb_issue_yes.pack(side="left", padx=(0, 10))
        cb_issue_no.pack(side="left")
        cb_issue_yes.config(state="disabled")
        cb_issue_no.config(state="disabled")

        # Row 5: Details entry
        ttk.Label(dialog, text="Details:").grid(row=5, column=0, sticky="w", **pad)
        cb_details_entry = ttk.Entry(dialog, width=30, state="disabled")
        cb_details_entry.grid(row=5, column=1, sticky="w", **pad)

        # Row 6: Message label + Save button
        msg_label = ttk.Label(dialog, text="", foreground="red")
        msg_label.grid(row=6, column=0, columnspan=2, sticky="w", **pad)

        # We store the matched row data so Save knows what to update
        matched = [None]

        def do_search():
            """Look up the patient in follow_up.csv by date + mrn."""
            search_date = date_entry.get().strip()
            search_mrn = mrn_entry.get().strip()
            msg_label.config(text="", foreground="red")
            name_label.grid_remove()
            matched[0] = None

            if not search_date or not search_mrn:
                msg_label.config(text="Please enter both date and MRN.")
                return

            if not os.path.exists(FOLLOWUP_FILE) or os.path.getsize(FOLLOWUP_FILE) == 0:
                msg_label.config(text="No follow-up data found.")
                return

            with open(FOLLOWUP_FILE, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["date"] == search_date and row["mrn"] == search_mrn:
                        matched[0] = row
                        break

            if matched[0]:
                patient_name = (f"{matched[0].get('title', '')} "
                                f"{matched[0].get('firstname', '')} "
                                f"{matched[0].get('surname', '')}").strip()
                name_label.config(text=patient_name)
                name_label.grid()
                cb_issue_var.set("no")
                cb_issue_yes.config(state="normal")
                cb_issue_no.config(state="normal")
                cb_details_entry.config(state="normal")
                cb_details_entry.delete(0, "end")
                cb_details_entry.config(state="disabled")
                save_button.config(state="normal")
                msg_label.config(text="Patient found. Update details below.",
                                 foreground="green")
            else:
                msg_label.config(text="No matching patient found.")
                cb_issue_yes.config(state="disabled")
                cb_issue_no.config(state="disabled")
                cb_details_entry.config(state="normal")
                cb_details_entry.delete(0, "end")
                cb_details_entry.config(state="disabled")
                save_button.config(state="disabled")

        def do_save():
            """Update the matched row in follow_up.csv and close the dialog."""
            issue = cb_issue_var.get()
            details = cb_details_entry.get().strip()

            if issue == "yes" and not details:
                msg_label.config(text="Please enter details about the problem.",
                                 foreground="red")
                return

            search_date = date_entry.get().strip()
            search_mrn = mrn_entry.get().strip()
            update_followup_row(search_date, search_mrn, issue, details)
            dialog.destroy()

        # Row 2: Search button
        search_button = ttk.Button(dialog, text="Search", command=do_search)
        search_button.grid(row=2, column=0, columnspan=2, pady=5)

        # Row 7: Save button
        save_button = ttk.Button(dialog, text="Save", command=do_save, state="disabled")
        save_button.grid(row=7, column=0, columnspan=2, pady=10)

    menubar = tk.Menu(root)
    settings_menu = tk.Menu(menubar, tearoff=0)
    settings_menu.add_command(label="Edit Config", command=open_config)
    settings_menu.add_command(label="Patient Callback", command=open_callback_dialog)
    menubar.add_cascade(label="Tools", menu=settings_menu)
    root.config(menu=menubar)

    # --- Top frame: status bar with count label ---
    top_frame = ttk.Frame(root, padding=10)
    top_frame.pack(fill="x")

    count_label = ttk.Label(top_frame, text="")
    count_label.pack(side="left")

    # --- Middle frame: patient data display ---
    data_frame = ttk.Frame(root, padding=10)
    data_frame.pack(fill="x")

    counter_label = ttk.Label(data_frame, text="", font=("TkDefaultFont", 12, "bold"))
    counter_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

    field_names = [
        "date",
        "name",
        "endo",
        "anaes",
        "nurse",
        "upper",
        "colon",
        "anal",
        "polyp",
        "phone",
    ]
    field_labels = [
        "Date:",
        "Name:",
        "Endo:",
        "Anaes:",
        "Nurse:",
        "Upper:",
        "Colon:",
        "Banding:",
        "Polyp:",
        "Phone:",
    ]

    data_labels = {}
    for i, (field, label_text) in enumerate(zip(field_names, field_labels), start=1):
        ttk.Label(data_frame, text=label_text, font=("TkDefaultFont", 11, "bold")).grid(
            row=i, column=0, sticky="w", padx=(0, 10), pady=2
        )
        value_label = ttk.Label(data_frame, text="", font=("TkDefaultFont", 11))
        value_label.grid(row=i, column=1, sticky="w", pady=2)
        data_labels[field] = value_label

    # Make name bold and phone large + bold so it's easy to read and dial
    data_labels["name"].config(font=("TkDefaultFont", 11, "bold"))
    data_labels["phone"].config(font=("TkDefaultFont", 16, "bold"))

    # --- Entry frame: Answered, Issue, Details ---
    entry_frame = ttk.Frame(root, padding=10)
    entry_frame.pack(fill="x")

    # Answered? radio buttons
    answered_var = tk.StringVar(value="")

    ttk.Label(entry_frame, text="Answered?", font=("TkDefaultFont", 11, "bold")).grid(
        row=0, column=0, sticky="w", padx=(0, 10), pady=5
    )
    answered_yes = ttk.Radiobutton(
        entry_frame,
        text="Yes",
        variable=answered_var,
        value="yes",
        command=lambda: on_answered_change(),
    )
    answered_yes.grid(row=0, column=1, sticky="w", padx=(0, 10), pady=5)

    answered_no = ttk.Radiobutton(
        entry_frame,
        text="No",
        variable=answered_var,
        value="no",
        command=lambda: on_answered_change(),
    )
    answered_no.grid(row=0, column=2, sticky="w", pady=5)

    # Issue? radio buttons
    issue_var = tk.StringVar(value="")

    ttk.Label(entry_frame, text="Issue?", font=("TkDefaultFont", 11, "bold")).grid(
        row=1, column=0, sticky="w", padx=(0, 10), pady=5
    )
    issue_yes = ttk.Radiobutton(
        entry_frame,
        text="Yes",
        variable=issue_var,
        value="yes",
        command=lambda: on_issue_change(),
        state="disabled",
    )
    issue_yes.grid(row=1, column=1, sticky="w", padx=(0, 10), pady=5)

    issue_no = ttk.Radiobutton(
        entry_frame,
        text="No",
        variable=issue_var,
        value="no",
        command=lambda: on_issue_change(),
        state="disabled",
    )
    issue_no.grid(row=1, column=2, sticky="w", pady=5)

    # Details text entry
    ttk.Label(entry_frame, text="Details:", font=("TkDefaultFont", 11, "bold")).grid(
        row=2, column=0, sticky="w", padx=(0, 10), pady=5
    )
    details_entry = ttk.Entry(entry_frame, width=40, state="disabled")
    details_entry.grid(row=2, column=1, columnspan=2, sticky="w", pady=5)

    # Error label (hidden until needed)
    error_label = ttk.Label(entry_frame, text="", foreground="red")
    error_label.grid(row=3, column=0, columnspan=3, sticky="w", pady=(0, 5))

    # --- Callbacks for entry widget behavior ---

    def on_answered_change():
        """Called when the Answered radio buttons change."""
        error_label.config(text="")

        if answered_var.get() == "no":
            # Disable Issue radios and Details, enable Next
            issue_var.set("")
            issue_yes.config(state="disabled")
            issue_no.config(state="disabled")
            # Clear text before disabling (can't edit a disabled entry)
            details_entry.config(state="normal")
            details_entry.delete(0, "end")
            details_entry.config(state="disabled")
            next_button.config(state="normal")

        elif answered_var.get() == "yes":
            # Enable Issue radios, check if Next should be enabled
            issue_yes.config(state="normal")
            issue_no.config(state="normal")
            # Next stays disabled until Issue is chosen
            if issue_var.get() == "":
                next_button.config(state="disabled")
            else:
                on_issue_change()

    def on_issue_change():
        """Called when the Issue radio buttons change."""
        error_label.config(text="")

        if issue_var.get() == "no":
            # Clear text before disabling (can't edit a disabled entry)
            details_entry.config(state="normal")
            details_entry.delete(0, "end")
            details_entry.config(state="disabled")
            next_button.config(state="normal")

        elif issue_var.get() == "yes":
            # Enable Details entry and Next
            details_entry.config(state="normal")
            next_button.config(state="normal")

    def reset_entry_widgets():
        """Clear all entry widgets and disable Issue/Details/Next."""
        answered_var.set("")
        issue_var.set("")

        issue_yes.config(state="disabled")
        issue_no.config(state="disabled")

        # Must enable briefly to clear, then disable again
        details_entry.config(state="normal")
        details_entry.delete(0, "end")
        details_entry.config(state="disabled")

        error_label.config(text="")
        next_button.config(state="disabled")

    # --- Bottom frame: Next button ---
    bottom_frame = ttk.Frame(root, padding=10)
    bottom_frame.pack(fill="x")

    def next_patient():
        """Validate entry, write to CSV, then advance to the next patient."""
        # Validate: if Issue=yes, Details must not be empty
        if issue_var.get() == "yes" and details_entry.get().strip() == "":
            error_label.config(text="Please enter details about the issue.")
            return

        # Build the values to write
        answered = answered_var.get()
        issue = issue_var.get()
        issue_text = details_entry.get().strip()

        # Write this patient's result to CSV
        current_patient = filtered[0][index[0]]
        write_result(current_patient, answered, issue, issue_text)

        total = len(filtered[0])
        called[0] += 1
        remaining = total - index[0] - 1
        count_label.config(text=f"{remaining} outstanding patients")

        # Check if this was the last patient
        if index[0] >= total - 1:
            # All patients done — clear display and show completion message
            clear_display(data_labels, counter_label)
            reset_entry_widgets()
            counter_label.config(text=f"All {total} patients complete")
            return

        # Advance to next patient
        index[0] += 1

        word = "Patient" if called[0] == 1 else "Patients"
        counter_label.config(text=f"{called[0]} {word} called this session")
        display_patient(filtered[0][index[0]], data_labels)

        # Reset entry widgets for the new patient
        reset_entry_widgets()

    next_button = ttk.Button(
        bottom_frame, text="Next >>>", command=next_patient, state="disabled"
    )
    next_button.pack()

    # --- Auto-load outstanding patients on startup ---
    filtered[0] = get_outstanding_patients(all_rows)
    index[0] = 0
    count = len(filtered[0])

    if count > 0:
        count_label.config(text=f"{count} outstanding patients")
        counter_label.config(text=f"0 Patients called this session")
        display_patient(filtered[0][0], data_labels)
    else:
        count_label.config(text="No outstanding patients")

    root.mainloop()


if __name__ == "__main__":
    main()
