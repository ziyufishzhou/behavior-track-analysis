"""Shared helpers for behavior experiment analysis."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


class InvalidPoseCsvError(ValueError):
    """Raised when analysis receives a CSV that was not repaired/flattened."""


def load_roi_regions(json_path) -> dict:
    """Load ROI JSON and return a name -> region mapping."""
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"ROI file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        roi_data = json.load(f)

    regions = roi_data.get("regions", [])
    if not isinstance(regions, list):
        raise ValueError(f"Invalid ROI file, 'regions' must be a list: {path}")
    return {r["name"]: r for r in regions if isinstance(r, dict) and "name" in r}


def load_flat_csv(csv_path, limit_frames: int | None = None) -> pd.DataFrame:
    """Load a fixed flat CSV as numeric data."""
    path = Path(csv_path)
    if _looks_like_dlc_raw_csv(path):
        raise InvalidPoseCsvError(
            f"{path.name} appears to be a raw DLC CSV with multi-row headers. "
            "Run Fix CSV first, then group the repaired fixed_csv files."
        )

    nrows = int(limit_frames) if limit_frames and limit_frames > 0 else None
    df = pd.read_csv(path, index_col=0, low_memory=False, nrows=nrows)
    _validate_flat_pose_columns(df, path)
    df = df.apply(pd.to_numeric, errors="coerce")
    return df


def _looks_like_dlc_raw_csv(path: Path) -> bool:
    """Detect DLC 2.x/3.x multi-row header CSVs before numeric coercion."""
    try:
        preview = pd.read_csv(path, header=None, nrows=5, low_memory=False)
    except pd.errors.EmptyDataError:
        raise InvalidPoseCsvError(f"{path.name} is empty.")

    if preview.empty or preview.shape[1] == 0:
        raise InvalidPoseCsvError(f"{path.name} is empty.")

    first_col = preview.iloc[:, 0].astype(str).str.strip().str.lower().tolist()
    header_markers = {"scorer", "individuals", "bodyparts", "coords"}
    return "coords" in first_col or len(header_markers.intersection(first_col[:4])) >= 3


def _validate_flat_pose_columns(df: pd.DataFrame, path: Path) -> None:
    x_prefixes = {c[:-2] for c in df.columns if isinstance(c, str) and c.endswith("_x")}
    y_prefixes = {c[:-2] for c in df.columns if isinstance(c, str) and c.endswith("_y")}
    if not x_prefixes.intersection(y_prefixes):
        raise InvalidPoseCsvError(
            f"{path.name} does not contain flat pose columns like cage1_nose_x/cage1_nose_y. "
            "Run Fix CSV first and regroup from data/fixed_csv."
        )


def get_bodypart_cols(df: pd.DataFrame, cage: str, bodypart: str = "nose"):
    """Return x/y/likelihood column names for a cage bodypart."""
    candidates = [
        f"{cage}_{bodypart}",
        f"{cage.lower()}_{bodypart}",
        f"{cage.upper()}_{bodypart}",
    ]

    for prefix in candidates:
        x_col = f"{prefix}_x"
        y_col = f"{prefix}_y"
        l_col = f"{prefix}_likelihood"
        if x_col in df.columns and y_col in df.columns:
            return x_col, y_col, l_col if l_col in df.columns else None

    return None, None, None


def require_regions(regions: dict, *names: str) -> bool:
    """Return True when all ROI names exist, printing missing names otherwise."""
    missing = [name for name in names if name not in regions]
    if missing:
        print(f"[WARN] 缺少 ROI: {', '.join(missing)}")
        return False
    return True
