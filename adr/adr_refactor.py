"""
ADR (Adenoma Detection Rate) Analysis Tool
Analyzes colonoscopy procedure data and calculates detection rates.
"""

import csv
import tkinter as tk
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter.filedialog import askopenfilename
from typing import Dict, List, Tuple
import re


@dataclass
class Episode:
    """Represents a single colonoscopy episode."""
    date: str = ""
    surname: str = ""
    mrn: str = ""
    dob: str = ""
    doc: str = ""
    procedure: str = ""
    ta: str = ""  # Tubular adenoma
    sa: str = ""  # Serrated adenoma
    tva: str = ""  # Tubulovillous adenoma
    malig: str = ""  # Malignancy codes

    def to_list(self) -> List[str]:
        """Convert episode to list for CSV writing."""
        return [
            self.date,
            self.surname,
            self.mrn,
            self.dob,
            self.doc,
            self.procedure,
            self.ta,
            self.sa,
            self.tva,
            self.malig,
        ]


class DateRange:
    """Tracks the date range of procedures."""
    
    def __init__(self):
        self.start: str = ""
        self.end: str = ""
    
    def update(self, procedure_date: str) -> None:
        """Update date range with a new procedure date (ddmmyyyy format)."""
        iso_date = f"{procedure_date[4:8]}{procedure_date[2:4]}{procedure_date[0:2]}"
        
        if not self.start:
            self.start = iso_date
            self.end = iso_date
        else:
            if iso_date < self.start:
                self.start = iso_date
            if iso_date > self.end:
                self.end = iso_date
    
    def format_date(self, iso_date: str) -> str:
        """Convert yyyymmdd to dd-mm-yyyy format."""
        return f"{iso_date[6:8]}-{iso_date[4:6]}-{iso_date[0:4]}"
    
    def get_formatted_range(self) -> Tuple[str, str]:
        """Return formatted start and end dates."""
        return self.format_date(self.start), self.format_date(self.end)


class DoctorDictionary:
    """Manages doctor lookup dictionaries from episodes.csv."""
    
    def __init__(self, episodes_file: str = "episodes.csv"):
        self.primary: Dict[str, Tuple[str, str, str]] = {}
        self.by_date_dob: Dict[str, Tuple[str, str, str]] = {}
        self.by_date_name: Dict[str, Tuple[str, str, str]] = {}
        self._load_from_file(episodes_file)
    
    def _normalize_dob(self, dob: str) -> str:
        """Normalize DOB to ddmmyyyy format."""
        dob = dob.replace("/", "")
        return f"0{dob}" if len(dob) == 7 else dob
    
    def _load_from_file(self, filename: str) -> None:
        """Load doctor information from episodes CSV file."""
        with open(filename, "r") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            
            for entry in reader:
                date = entry[0].replace("-", "")
                dob = self._normalize_dob(entry[18])
                name = entry[17].lower()
                doctor_info = (entry[5].lower(), entry[1], dob)
                
                # Create multiple keys for lookup flexibility
                self.primary[f"{date}{dob}{name}"] = doctor_info
                self.by_date_dob[f"{date}{dob}"] = doctor_info
                self.by_date_name[f"{date}{name}"] = doctor_info
    
    def lookup(self, date: str, dob: str, surname: str) -> Tuple[str, str, str]:
        """Look up doctor info with fallback strategies."""
        primary_key = f"{date}{dob}{surname}"
        
        if primary_key in self.primary:
            return self.primary[primary_key]
        
        secondary_key = f"{date}{dob}"
        if secondary_key in self.by_date_dob:
            return self.by_date_dob[secondary_key]
        
        tertiary_key = f"{date}{surname}"
        return self.by_date_name.get(tertiary_key, ("unknown", "?", "?"))


class PHISCDataParser:
    """Parses PHISCData text files and extracts colonoscopy episodes."""
    
    PROCEDURE_CODES = {"32090", "32093"}
    ADENOMA_CODES = {
        "2M8211/0": "ta",  # Tubular adenoma
        "2M8213/0": "sa",  # Serrated adenoma
        "2M8263/0": "tva",  # Tubulovillous adenoma
    }
    
    def __init__(self, doctor_dict: DoctorDictionary):
        self.doctor_dict = doctor_dict
    
    def parse_files(self, file_paths: List[str], output_file: str = "adr.csv") -> None:
        """Parse multiple PHISC data files and write to CSV."""
        for idx, file_path in enumerate(file_paths):
            mode = "w" if idx == 0 else "a"
            self._parse_single_file(file_path, output_file, mode, write_header=(idx == 0))
    
    def _parse_single_file(self, file_path: str, output_file: str, mode: str, write_header: bool) -> None:
        """Parse a single PHISC data file."""
        headers = ["date", "surname", "mrn", "dob", "doc", "procedure", 
                   "ta", "sa", "tva", "malig"]
        
        with open(file_path) as infile, open(output_file, mode) as outfile:
            writer = csv.writer(outfile)
            if write_header:
                writer.writerow(headers)
            
            infile.readline()  # Skip first line
            for line in infile:
                episode = self._parse_line(line)
                if episode:
                    writer.writerow(episode.to_list())
    
    def _parse_line(self, line: str) -> Episode:
        """Parse a single line from PHISC data file."""
        entry = line.split()
        procedure_codes = entry[-2]
        
        # Check if line contains relevant procedure codes
        relevant_code = next((code for code in self.PROCEDURE_CODES if code in procedure_codes), None)
        if not relevant_code:
            return None
        
        episode = Episode(procedure=relevant_code, surname=entry[2].lower())
        
        # Find ICD codes starting point (04 or 04G prefix)
        icd_index = next(
            (i for i, item in enumerate(entry) if item == "04" or item.startswith("04G")),
            -1
        )
        
        if icd_index == -1:
            return None
        
        # Extract date and DOB
        episode.date = entry[icd_index - 2][:8]
        digits_only = re.sub(r"[^0-9]", "", entry[icd_index - 3])
        episode.dob = digits_only[4:12]
        
        # Parse ICD codes for adenomas (only for procedure 32093)
        if episode.procedure == "32093":
            self._parse_icd_codes(entry, icd_index + 1, episode)
        
        # Lookup doctor information
        self._lookup_doctor_info(episode)
        
        return episode
    
    def _parse_icd_codes(self, entry: List[str], start_idx: int, episode: Episode) -> None:
        """Parse ICD codes starting from given index."""
        i = start_idx
        while i < len(entry):
            code = entry[i]
            
            if code == "2":
                break
            elif code in self.ADENOMA_CODES:
                setattr(episode, self.ADENOMA_CODES[code], self.ADENOMA_CODES[code])
            elif code.startswith("2M"):
                # Other malignancy codes
                episode.malig = f"{episode.malig} {code}".strip()
            
            i += 1
    
    def _lookup_doctor_info(self, episode: Episode) -> None:
        """Look up and populate doctor information for an episode."""
        doctor_info = self.doctor_dict.lookup(episode.date, episode.dob, episode.surname)
        episode.doc, episode.mrn, fallback_dob = doctor_info
        
        # Use fallback DOB if current one is invalid
        if not episode.dob or not self._is_valid_date(episode.dob):
            episode.dob = fallback_dob
    
    @staticmethod
    def _is_valid_date(date_str: str) -> bool:
        """Check if date string is valid ddmmyyyy format."""
        try:
            datetime.strptime(date_str, "%d%m%Y")
            return True
        except ValueError:
            return False


class ADRAnalyzer:
    """Analyzes ADR data and generates reports."""
    
    def __init__(self, data_file: str = "adr.csv"):
        self.data_file = data_file
        self.date_range = DateRange()
    
    def analyze(self) -> None:
        """Analyze ADR data and generate output files."""
        stats = self._calculate_statistics()
        self._write_text_report(stats)
        self._write_csv_report(stats)
    
    def _calculate_statistics(self) -> Dict:
        """Calculate ADR statistics from CSV data."""
        stats = {
            'all': defaultdict(lambda: {'colons': 0, 'polyps': 0, 'ssa': 0}),
            'under50': defaultdict(lambda: {'colons': 0, 'polyps': 0}),
            'over50': defaultdict(lambda: {'colons': 0, 'polyps': 0, 'ssa': 0}),
            'total_over50': {'colons': 0, 'polyps': 0, 'ssa': 0}
        }
        
        with open(self.data_file, "r") as f:
            reader = csv.DictReader(f)
            for entry in reader:
                self.date_range.update(entry["date"])
                
                if entry["dob"] in {"?", ""}:
                    continue
                
                doctor = entry["doc"]
                has_polyp = bool(entry["ta"] or entry["sa"] or entry["tva"])
                has_ssa = bool(entry["sa"])
                
                # All ages
                stats['all'][doctor]['colons'] += 1
                if has_polyp:
                    stats['all'][doctor]['polyps'] += 1
                if has_ssa:
                    stats['all'][doctor]['ssa'] += 1
                
                # Age-stratified
                if self._is_under_50(entry["date"], entry["dob"]):
                    stats['under50'][doctor]['colons'] += 1
                    if has_polyp:
                        stats['under50'][doctor]['polyps'] += 1
                else:
                    stats['over50'][doctor]['colons'] += 1
                    stats['total_over50']['colons'] += 1
                    if has_polyp:
                        stats['over50'][doctor]['polyps'] += 1
                        stats['total_over50']['polyps'] += 1
                    if has_ssa:
                        stats['over50'][doctor]['ssa'] += 1
                        stats['total_over50']['ssa'] += 1
        
        return stats
    
    @staticmethod
    def _is_under_50(procedure_date: str, birth_date: str) -> bool:
        """Check if patient is under 50 on procedure date."""
        proc_dt = datetime.strptime(procedure_date, "%d%m%Y")
        birth_dt = datetime.strptime(birth_date, "%d%m%Y")
        
        age = proc_dt.year - birth_dt.year
        if (proc_dt.month, proc_dt.day) < (birth_dt.month, birth_dt.day):
            age -= 1
        
        return age < 50
    
    @staticmethod
    def _calculate_rate(numerator: int, denominator: int) -> int:
        """Calculate percentage rate, return -1 if denominator is 0."""
        if denominator == 0:
            return -1
        return round((numerator / denominator) * 100)
    
    def _write_text_report(self, stats: Dict) -> None:
        """Write formatted text report."""
        start_date, end_date = self.date_range.get_formatted_range()
        doctors = sorted(stats['all'].keys())
        
        with open("adr.txt", "w") as f:
            f.write(f"ADR Results from {start_date} to {end_date}\n")
            f.write(" " * 20 + "Total Cols     ADR       ADR<50      ADR>50   SSA(all ages)\n")
            
            for doctor in doctors:
                adr_all = self._calculate_rate(
                    stats['all'][doctor]['polyps'],
                    stats['all'][doctor]['colons']
                )
                adr_under50 = self._calculate_rate(
                    stats['under50'][doctor]['polyps'],
                    stats['under50'][doctor]['colons']
                )
                adr_over50 = self._calculate_rate(
                    stats['over50'][doctor]['polyps'],
                    stats['over50'][doctor]['colons']
                )
                ssa_rate = self._calculate_rate(
                    stats['all'][doctor]['ssa'],
                    stats['all'][doctor]['colons']
                )
                
                f.write(
                    f"{doctor.title().ljust(20)}  "
                    f"{str(stats['all'][doctor]['colons']).ljust(10)}  "
                    f"{str(adr_all).ljust(10)}  "
                    f"{str(adr_under50).ljust(10)} "
                    f"{str(adr_over50).ljust(10)} "
                    f"{str(ssa_rate).ljust(10)}\n"
                )
            
            # Summary statistics
            unit_adr = self._calculate_rate(
                stats['total_over50']['polyps'],
                stats['total_over50']['colons']
            )
            unit_ssa = self._calculate_rate(
                stats['total_over50']['ssa'],
                stats['total_over50']['colons']
            )
            
            f.write("\n\n")
            f.write(f"Total colonoscopies done on patients over 50 years:  {stats['total_over50']['colons']}\n")
            f.write(f"Unit wide ADR for over 50 years:  {unit_adr}%\n")
            f.write(f"Unit wide SSA for over 50 years:  {unit_ssa}%\n")
    
    def _write_csv_report(self, stats: Dict) -> None:
        """Write CSV report."""
        doctors = sorted(stats['all'].keys())
        
        with open("output.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Doctor", "Total Cols", "%ADR", "%ADR<50", "%ADR>50", "%SSA(all ages)"])
            
            for doctor in doctors:
                adr_all = self._calculate_rate(
                    stats['all'][doctor]['polyps'],
                    stats['all'][doctor]['colons']
                )
                adr_under50 = self._calculate_rate(
                    stats['under50'][doctor]['polyps'],
                    stats['under50'][doctor]['colons']
                )
                adr_over50 = self._calculate_rate(
                    stats['over50'][doctor]['polyps'],
                    stats['over50'][doctor]['colons']
                )
                ssa_rate = self._calculate_rate(
                    stats['all'][doctor]['ssa'],
                    stats['all'][doctor]['colons']
                )
                
                writer.writerow([
                    doctor.title(),
                    stats['all'][doctor]['colons'],
                    adr_all,
                    adr_under50,
                    adr_over50,
                    ssa_rate
                ])


class ADRApplication:
    """GUI application for ADR analysis."""
    
    def __init__(self):
        self.files_list: List[str] = []
        self.doctor_dict = None
        self._setup_gui()
    
    def _setup_gui(self) -> None:
        """Set up the GUI window and buttons."""
        self.root = tk.Tk()
        self.root.title("ADR Analysis Tool")
        self.root.geometry("200x400")
        
        buttons = [
            ("Open Files", self._open_files),
            ("Create datafile", self._create_datafile),
            ("Analyse", self._analyse),
            ("Open as csv", self._open_csv),
            ("Open as text", self._open_text),
        ]
        
        for text, command in buttons:
            btn = tk.Button(self.root, text=text, command=command, width=15, height=2)
            btn.pack(pady=10)
        
        self.root.attributes("-topmost", True)
    
    def _open_files(self) -> None:
        """Open file dialog and add selected file to list."""
        filename = askopenfilename()
        if filename:
            self.files_list.append(filename)
    
    def _create_datafile(self) -> None:
        """Parse selected files and create data file."""
        if not self.files_list:
            return
        
        self.doctor_dict = DoctorDictionary()
        parser = PHISCDataParser(self.doctor_dict)
        parser.parse_files(self.files_list)
    
    def _analyse(self) -> None:
        """Analyze data and generate reports."""
        analyzer = ADRAnalyzer()
        analyzer.analyze()
    
    def _open_csv(self) -> None:
        """Open output CSV file."""
        # TODO: Implement CSV file opening
        pass
    
    def _open_text(self) -> None:
        """Open output text file."""
        # TODO: Implement text file opening
        pass
    
    def run(self) -> None:
        """Start the GUI application."""
        self.root.mainloop()


if __name__ == "__main__":
    app = ADRApplication()
    app.run()
