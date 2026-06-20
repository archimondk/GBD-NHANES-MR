"""
NHANES 1999-2018 Data Download Script (v2)

URL pattern (confirmed 2025):
  https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{begin_year}/DataFiles/{filename}.xpt
"""

import urllib.request
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Cycles: (label, begin_year, suffix)
CYCLES = [
    ("1999-2000", "1999", ""),
    ("2001-2002", "2001", "_B"),
    ("2003-2004", "2003", "_C"),
    ("2005-2006", "2005", "_D"),
    ("2007-2008", "2007", "_E"),
    ("2009-2010", "2009", "_F"),
    ("2011-2012", "2011", "_G"),
    ("2013-2014", "2013", "_H"),
    ("2015-2016", "2015", "_I"),
    ("2017-2018", "2017", "_J"),
]

FILES = [
    ("DEMO", "Demographics"),
    ("PBCD", "Blood Lead, Cadmium & Mercury"),
    ("GLU", "Fasting Glucose"),
    ("RHQ", "Reproductive Health"),
    ("BMX", "Body Measures"),
]


def download_file(url, dest_path, retries=3, timeout=60):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
            with open(dest_path, "wb") as f:
                f.write(data)
            return True
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"    Retry {attempt + 1}/{retries} after {wait}s: {e}")
                time.sleep(wait)
            else:
                print(f"    FAILED: {e}")
                return False


def download_one(cycle_label, begin_year, suffix, file_prefix, desc):
    """Download one NHANES XPT file using confirmed CDC URL pattern."""
    if file_prefix == "PBCD" and cycle_label == "1999-2000":
        actual_prefix = "LAB06"
    else:
        actual_prefix = file_prefix

    filename = f"{actual_prefix}{suffix}.xpt"
    url = f"https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{begin_year}/DataFiles/{filename}"
    dest = RAW_DIR / f"{cycle_label}_{file_prefix}.XPT"

    if dest.exists():
        print(f"  OK {cycle_label} {desc}")
        return True
    print(f"  -> {cycle_label} {desc} ...", end=" ")
    ok = download_file(url, dest)
    print("OK" if ok else "FAILED")
    return ok


def main():
    print("=" * 60)
    print("NHANES 1999-2018 Data Download")
    print(f"Directory: {RAW_DIR}")
    print("=" * 60)

    total = len(CYCLES) * len(FILES)
    ok = failed = 0
    failed_list = []

    for cycle_label, begin_year, suffix in CYCLES:
        print(f"\n-- Cycle {cycle_label} (year={begin_year}) --")
        for file_prefix, desc in FILES:
            if download_one(cycle_label, begin_year, suffix, file_prefix, desc):
                ok += 1
            else:
                failed += 1
                failed_list.append(f"{cycle_label}_{file_prefix}")

    print("\n" + "=" * 60)
    print(f"Done: {ok}/{total} OK", end="")
    if failed:
        print(f", {failed} failed: {failed_list}")
    else:
        print()
    print("=" * 60)


if __name__ == "__main__":
    main()
