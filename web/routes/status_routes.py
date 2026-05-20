"""Project status API for the Web workstation."""
from pathlib import Path

import pandas as pd
from flask import Blueprint, jsonify

from config.paths import (
    EPM_ROI_JSON,
    EPM_SUMMARY,
    FIXED_CSV_DIR,
    GROUPED_DIR,
    METADATA_FILE,
    OF_ROI_JSON,
    OF_SUMMARY,
    RAW_CSV_DIR,
    TCT_ROI_JSON,
    TCT_SUMMARY,
    get_dlc_python,
    get_video_dir,
)
from gui.utils import is_video_file


bp = Blueprint("status", __name__, url_prefix="/api/status")


def _count_files(path: Path, pattern: str) -> int:
    if not path.exists():
        return 0
    return sum(1 for p in path.rglob(pattern) if p.is_file())


def _latest_file(path: Path, pattern: str) -> str:
    if not path.exists():
        return ""
    files = [p for p in path.glob(pattern) if p.is_file()]
    if not files:
        return ""
    return str(max(files, key=lambda p: p.stat().st_mtime))


@bp.route("")
def project_status():
    video_dir = get_video_dir()
    video_count = 0
    if video_dir.exists():
        video_count = sum(1 for p in video_dir.rglob("*") if p.is_file() and is_video_file(str(p)))

    metadata_rows = 0
    metadata_columns = []
    if METADATA_FILE.exists():
        try:
            df = pd.read_excel(str(METADATA_FILE))
            metadata_rows = len(df)
            metadata_columns = list(df.columns)
        except Exception as exc:
            metadata_columns = [f"读取失败: {exc}"]

    dlc_python = get_dlc_python()

    return jsonify({
        "video": {
            "path": str(video_dir),
            "exists": video_dir.exists(),
            "count": video_count,
        },
        "dlc": {
            "python": str(dlc_python) if dlc_python else "",
            "python_exists": bool(dlc_python and dlc_python.is_file()),
        },
        "csv": {
            "raw": _count_files(RAW_CSV_DIR, "*.csv"),
            "fixed": _count_files(FIXED_CSV_DIR, "*.csv"),
            "grouped": _count_files(GROUPED_DIR, "*.csv"),
        },
        "metadata": {
            "path": str(METADATA_FILE),
            "exists": METADATA_FILE.exists(),
            "rows": metadata_rows,
            "columns": metadata_columns,
        },
        "roi": {
            "OF": OF_ROI_JSON.exists(),
            "EPM": EPM_ROI_JSON.exists(),
            "TCT": TCT_ROI_JSON.exists(),
        },
        "summary": {
            "OF": _latest_file(OF_SUMMARY, "*.xlsx"),
            "EPM": _latest_file(EPM_SUMMARY, "*.xlsx"),
            "TCT": _latest_file(TCT_SUMMARY, "*.xlsx"),
        },
    })
