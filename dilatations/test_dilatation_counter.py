import csv
from dilatation_counter import count_procedures


# Helper to write a small CSV file for testing
def write_test_csv(path, rows):
    fieldnames = ["date", "mrn", "in", "out", "anaes", "endo", "asa",
                  "upper", "colon", "anal", "nurse", "clips", "p_recall",
                  "c_recall", "caecum", "title", "firstname", "surname",
                  "dob", "email", "consult", "polyp"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # Fill missing fields with empty strings
            full_row = {field: "" for field in fieldnames}
            full_row.update(row)
            writer.writerow(full_row)


def test_counts_dilatations(tmp_path):
    """Rows with upper=='30475' should be counted as dilatations."""
    csv_file = tmp_path / "episodes.csv"
    write_test_csv(csv_file, [
        {"date": "10-03-2025", "upper": "30475"},
        {"date": "15-04-2025", "upper": "30475"},
        {"date": "20-05-2025", "upper": "30473"},
    ])
    results = count_procedures(str(csv_file), "2025", 1, 6)
    assert results["dilatation"] == 2


def test_counts_upper_endoscopies(tmp_path):
    """Any row with a non-empty upper field should count as an upper endoscopy."""
    csv_file = tmp_path / "episodes.csv"
    write_test_csv(csv_file, [
        {"date": "10-03-2025", "upper": "30475"},
        {"date": "15-04-2025", "upper": "30473"},
        {"date": "20-05-2025", "upper": ""},
    ])
    results = count_procedures(str(csv_file), "2025", 1, 6)
    assert results["upper_endoscopy"] == 2


def test_no_matching_rows_returns_zero(tmp_path):
    """A period with no matching rows should return 0 for both counts."""
    csv_file = tmp_path / "episodes.csv"
    write_test_csv(csv_file, [
        {"date": "10-03-2025", "upper": "30475"},
        {"date": "15-04-2025", "upper": "30473"},
    ])
    # Ask for July-December — no rows match
    results = count_procedures(str(csv_file), "2025", 7, 12)
    assert results["upper_endoscopy"] == 0
    assert results["dilatation"] == 0


def test_rows_outside_date_range_excluded(tmp_path):
    """Rows in a different year or month range should not be counted."""
    csv_file = tmp_path / "episodes.csv"
    write_test_csv(csv_file, [
        {"date": "10-03-2025", "upper": "30475"},   # in range
        {"date": "15-08-2025", "upper": "30475"},   # wrong month (Jul-Dec)
        {"date": "10-03-2024", "upper": "30475"},   # wrong year
    ])
    results = count_procedures(str(csv_file), "2025", 1, 6)
    assert results["upper_endoscopy"] == 1
    assert results["dilatation"] == 1


# ---------------------------------------------------------------------------
# LEARNING EXAMPLES: capsys and monkeypatch fixtures
# These tests demonstrate how the fixtures work. They don't test
# count_procedures — they're here as reference for studying pytest.
# ---------------------------------------------------------------------------


def test_capsys_example(capsys):
    """capsys captures anything printed with print().
    After printing, call capsys.readouterr() to get the output.
    Then you can check it with assert."""

    # This is just a plain print — could be any function that prints
    print("Hello, pytest!")
    print("Second line")

    # readouterr() returns what was printed
    captured = capsys.readouterr()

    # captured.out is a single string with all the printed text
    assert "Hello, pytest!" in captured.out
    assert "Second line" in captured.out

    # You can also check exact output — note print() adds \n at the end
    assert captured.out == "Hello, pytest!\nSecond line\n"


def test_monkeypatch_fake_input(monkeypatch):
    """monkeypatch.setattr can replace built-in functions like input().
    This is useful when your program asks the user to type something
    and you want to provide answers automatically in a test."""

    # Replace input() with a function that always returns "42"
    monkeypatch.setattr("builtins.input", lambda prompt: "42")

    # Now input() returns "42" no matter what prompt you give it
    answer = input("Enter a number: ")
    assert answer == "42"


def test_monkeypatch_multiple_inputs(monkeypatch):
    """When your program calls input() more than once, use iter() and next()
    to return a different answer each time."""

    # iter() turns a list into an iterator — you pull items one at a time
    # next() pulls the next item from the iterator
    answers = iter(["2025", "1"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))

    # First call to input() returns "2025"
    year = input("Enter year: ")
    assert year == "2025"

    # Second call to input() returns "1"
    choice = input("Enter 1 or 2: ")
    assert choice == "1"


def test_monkeypatch_setattr_variable(monkeypatch):
    """monkeypatch.setattr can also replace things in a module.
    The string format is "module_name.thing_to_replace".
    Here we temporarily make platform.system() return "Windows"
    even though we're on macOS."""

    import platform

    # Before: platform.system() returns your real OS (e.g. "Darwin" on macOS)
    real_os = platform.system()

    # Temporarily make it return "Windows"
    monkeypatch.setattr("platform.system", lambda: "Windows")

    # Now it reports "Windows"
    assert platform.system() == "Windows"
    assert platform.system() != real_os

    # After this test ends, monkeypatch restores the original
    # platform.system() automatically — no cleanup needed
