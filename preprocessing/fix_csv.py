"""Repair DeepLabCut CSV files.

The output is a flat table whose columns look like:
    cage1_nose_x, cage1_nose_y, cage1_nose_likelihood

Supported inputs:
    - DLC 2.x: scorer/bodyparts/coords
    - DLC 3.x multi-animal: scorer/individuals/bodyparts/coords
    - already flattened CSV files
"""
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from config.paths import RAW_CSV_DIR, FIXED_CSV_DIR


COORD_NAMES = {"x", "y", "likelihood"}
HEADER_LABELS = {"scorer", "individuals", "bodyparts", "coords"}


def _clean_part(value) -> str:
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "unnamed: 0_level_0"}:
        return ""
    return text


def detect_header_levels(filepath: Path) -> int:
    """Detect how many header rows a DLC CSV has."""
    preview = pd.read_csv(filepath, header=None, nrows=6, low_memory=False)
    first_col = [_clean_part(v).lower() for v in preview.iloc[:, 0].tolist()]

    if "coords" in first_col:
        return first_col.index("coords") + 1

    if first_col[:4] == ["scorer", "individuals", "bodyparts", "coords"]:
        return 4
    if first_col[:3] == ["scorer", "bodyparts", "coords"]:
        return 3

    # Fallback: count non-numeric rows at the top.
    levels = 0
    for _, row in preview.iterrows():
        label = _clean_part(row.iloc[0]).lower()
        values = row.iloc[1:].dropna().astype(str).str.strip()
        if label in HEADER_LABELS:
            levels += 1
            continue
        numeric = pd.to_numeric(values, errors="coerce").notna().mean() if len(values) else 0
        if numeric >= 0.6:
            break
        levels += 1
    return max(1, min(levels, 4))


def _flatten_columns(columns, n_levels: int) -> list[str]:
    flat_cols = []
    seen = {}

    for col in columns:
        parts = [_clean_part(p) for p in (col if isinstance(col, tuple) else (col,))]
        parts = [p for p in parts if p]

        if n_levels >= 4 and len(parts) >= 4:
            name = f"{parts[1]}_{parts[2]}_{parts[3]}"
        elif n_levels == 3 and len(parts) >= 3:
            name = f"{parts[1]}_{parts[2]}"
        elif parts and parts[-1].lower() in COORD_NAMES and len(parts) >= 2:
            name = "_".join(parts[-3:])
        else:
            name = "_".join(parts) or "column"

        name = name.replace(" ", "_")
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 1
        flat_cols.append(name)

    return flat_cols


def _read_dlc_csv(filepath: Path) -> pd.DataFrame:
    n_levels = detect_header_levels(filepath)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if n_levels > 1:
            df = pd.read_csv(
                filepath,
                header=list(range(n_levels)),
                index_col=0,
                low_memory=False,
            )
            df.columns = _flatten_columns(df.columns, n_levels)
        else:
            df = pd.read_csv(filepath, header=0, index_col=0, low_memory=False)

    df = df.apply(pd.to_numeric, errors="coerce")
    df.index.name = "frame"
    return df


def _repair_coordinates(
    df: pd.DataFrame,
    likelihood_threshold: float,
    interpolate: bool,
    max_gap: int,
) -> tuple[pd.DataFrame, dict[str, int]]:
    stats = {"points_masked": 0, "values_interpolated": 0}

    likelihood_cols = [c for c in df.columns if c.endswith("_likelihood")]
    for lc in likelihood_cols:
        prefix = lc.removesuffix("_likelihood")
        x_col = f"{prefix}_x"
        y_col = f"{prefix}_y"
        if x_col not in df.columns or y_col not in df.columns:
            continue

        before_missing = int(df[[x_col, y_col]].isna().sum().sum())
        mask = df[lc].isna() | (df[lc] < likelihood_threshold)
        stats["points_masked"] += int(mask.sum())
        df.loc[mask, [x_col, y_col]] = np.nan

        if interpolate:
            df[[x_col, y_col]] = df[[x_col, y_col]].interpolate(
                method="linear",
                limit=max_gap,
                limit_area="inside",
            )
            after_missing = int(df[[x_col, y_col]].isna().sum().sum())
            stats["values_interpolated"] += max(0, before_missing + int(mask.sum()) * 2 - after_missing)

    return df, stats


def fix_csv(
    filepath,
    likelihood_threshold: float = 0.6,
    interpolate: bool = True,
    max_gap: int = 15,
) -> pd.DataFrame:
    """Repair one DLC CSV and return a flat numeric DataFrame."""
    df = _read_dlc_csv(Path(filepath))
    df, _ = _repair_coordinates(df, likelihood_threshold, interpolate, max_gap)
    return df


def fix_csv_with_stats(
    filepath,
    likelihood_threshold: float = 0.6,
    interpolate: bool = True,
    max_gap: int = 15,
) -> tuple[pd.DataFrame, dict[str, int]]:
    df = _read_dlc_csv(Path(filepath))
    return _repair_coordinates(df, likelihood_threshold, interpolate, max_gap)


def main():
    """Batch repair all CSV files under data/raw_csv."""
    if not RAW_CSV_DIR.exists():
        print(f"[ERROR] raw_csv directory not found: {RAW_CSV_DIR}")
        return

    csv_files = sorted(RAW_CSV_DIR.glob("*.csv"))
    if not csv_files:
        print("[修复CSV] 未找到 CSV 文件")
        return

    print(f"[修复CSV] 找到 {len(csv_files)} 个文件")
    FIXED_CSV_DIR.mkdir(parents=True, exist_ok=True)

    for i, csv_path in enumerate(csv_files, 1):
        print(f"[PROGRESS] {i}/{len(csv_files)} 修复 {csv_path.name}")
        try:
            df, stats = fix_csv_with_stats(csv_path)
            out_path = FIXED_CSV_DIR / csv_path.name
            df.to_csv(out_path)
            print(
                f"  -> {out_path.name} ({len(df)} 行, {len(df.columns)} 列, "
                f"masked={stats['points_masked']}, interpolated={stats['values_interpolated']})"
            )
        except Exception as e:
            print(f"[ERROR] 处理 {csv_path.name} 失败: {e}")

    print(f"[修复CSV] 完成，输出到 {FIXED_CSV_DIR}")


if __name__ == "__main__":
    main()
