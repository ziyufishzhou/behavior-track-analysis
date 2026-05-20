import os
from pathlib import Path
import re
import shutil

import pandas as pd

from config.paths import (
    FIXED_CSV_DIR,
    GROUPED_DIR,
    OF_CSV_DIR,
    EPM_CSV_DIR,
    TCT_CSV_DIR,
    METADATA_FILE,
)


input_dir = str(FIXED_CSV_DIR)
output_base = str(GROUPED_DIR)

GROUP_RULES = {
    "OF": {"keywords": ["OF", "of", "OpenField", "openfield"], "dir": str(OF_CSV_DIR)},
    "EPM": {"keywords": ["EPM", "epm", "PlusMaze", "plusmaze"], "dir": str(EPM_CSV_DIR)},
    "TCT": {"keywords": ["TCT", "tct", "ThreeChamber", "threechamber", "Social"], "dir": str(TCT_CSV_DIR)},
}

for group_name, rule in GROUP_RULES.items():
    os.makedirs(rule["dir"], exist_ok=True)


def classify_file(filename):
    """Classify a CSV by experiment keyword in its file name."""
    for group_name, rule in GROUP_RULES.items():
        for kw in rule["keywords"]:
            if kw in filename:
                return group_name, rule["dir"]
    return None, None


def metadata_filename_to_csv(filename):
    """Map metadata FileName values to the CSV names produced by collect_csv."""
    name = str(filename).strip().replace("\\", "/")
    base = Path(name).name
    stem = Path(base).stem

    if base.lower().endswith(".csv"):
        return base
    if base.lower().endswith((".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv")):
        return f"{stem}_result.csv"
    return base


def find_source_csv(filename):
    """Find the repaired CSV that matches a metadata FileName value."""
    csv_name = metadata_filename_to_csv(filename)
    path = FIXED_CSV_DIR / csv_name
    if path.exists():
        return path, csv_name

    stem = Path(csv_name).stem.replace("_result", "")
    matches = sorted(FIXED_CSV_DIR.glob(f"{stem}*_result.csv"))
    if matches:
        return matches[0], matches[0].name

    timestamp = re.match(r"\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}", stem)
    if timestamp:
        matches = sorted(FIXED_CSV_DIR.glob(f"{timestamp.group(0)}*_result.csv"))
        if matches:
            return matches[0], matches[0].name
    return None, csv_name


def _require_fixed_csvs():
    """Return repaired CSV files or fail with an actionable message."""
    if not FIXED_CSV_DIR.exists():
        raise RuntimeError(f"fixed_csv directory not found: {FIXED_CSV_DIR}. Run Fix CSV first.")

    csv_files = sorted(FIXED_CSV_DIR.glob("*.csv"))
    if not csv_files:
        raise RuntimeError(f"fixed_csv is empty: {FIXED_CSV_DIR}. Run Fix CSV before grouping.")
    return csv_files


def _clear_grouped_csvs():
    """Remove stale grouped CSV copies before writing a fresh synchronized view."""
    if not GROUPED_DIR.exists():
        return 0

    removed = 0
    for path in GROUPED_DIR.rglob("*.csv"):
        if path.is_file():
            path.unlink()
            removed += 1
    return removed


def main():
    csv_paths = _require_fixed_csvs()
    removed = _clear_grouped_csvs()
    if removed:
        print(f"Cleared {removed} stale grouped CSV files.")

    csv_files = [p.name for p in csv_paths]
    print(f"Found {len(csv_files)} CSV files to group.")

    stats = {k: 0 for k in GROUP_RULES}
    unclassified = []

    for csv_file in csv_files:
        group, dest_dir = classify_file(csv_file)
        if group:
            src = os.path.join(input_dir, csv_file)
            dst = os.path.join(dest_dir, csv_file)
            shutil.copy2(src, dst)
            stats[group] += 1
            print(f"  OK {csv_file} -> {group}")
        else:
            unclassified.append(csv_file)
            print(f"  Unclassified: {csv_file}")

    print("\n=== Grouping complete ===")
    for k, v in stats.items():
        print(f"  {k}: {v} files")
    if unclassified:
        print(f"  Unclassified: {len(unclassified)} files")
        for f in unclassified:
            print(f"    - {f}")


def group_by_metadata():
    """Copy CSV files to grouped/{Experiment}/{Group}/{Condition} by metadata."""
    _require_fixed_csvs()

    if not METADATA_FILE.exists():
        print("metadata.xlsx not found; falling back to keyword grouping.")
        main()
        return

    df = pd.read_excel(str(METADATA_FILE))
    if df.empty:
        print("metadata.xlsx is empty.")
        return

    required = {"FileName", "Experiment"}
    missing = required - set(df.columns)
    if missing:
        print(f"metadata.xlsx missing required columns: {', '.join(sorted(missing))}")
        return

    removed = _clear_grouped_csvs()
    if removed:
        print(f"Cleared {removed} stale grouped CSV files.")

    count = 0
    missing_files = []
    for _, row in df.iterrows():
        exp = str(row.get("Experiment", "")).strip()
        group = str(row.get("Group", "")).strip()
        condition = str(row.get("Condition", "")).strip()
        filename = str(row.get("FileName", "")).strip()

        if not exp or not filename:
            continue

        src, csv_name = find_source_csv(filename)
        if src is None:
            print(f"  Skip: CSV not found for {filename} -> {csv_name}")
            missing_files.append(f"{filename} -> {csv_name}")
            continue

        dest_dir = GROUPED_DIR / exp / group / condition
        dest_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy2(str(src), str(dest_dir / csv_name))
        count += 1

    if missing_files:
        preview = "\n    ".join(missing_files[:10])
        extra = f"\n    ... and {len(missing_files) - 10} more" if len(missing_files) > 10 else ""
        raise RuntimeError(
            "Some metadata rows do not have repaired CSV files in fixed_csv. "
            "Run Collect CSV and Fix CSV, then group again:\n    "
            f"{preview}{extra}"
        )

    print(f"\nGrouped by metadata: copied {count} files.")


if __name__ == "__main__":
    main()
