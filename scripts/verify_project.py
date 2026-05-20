"""Lightweight project health check.

Run from the project root:

    python scripts/verify_project.py

The script avoids test-framework dependencies so it can be used during
graduation-project demos and on fresh machines.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def ok(message: str) -> None:
    print(f"[OK] {message}")


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def check_imports() -> None:
    modules = [
        "config.paths",
        "preprocessing.collect_csv",
        "preprocessing.fix_csv",
        "preprocessing.group_csv",
        "preprocessing.build_metadata",
        "experiments.common",
        "web",
    ]
    for module in modules:
        importlib.import_module(module)
    ok("core modules import successfully")


def check_project_layout() -> None:
    required_dirs = [
        "config",
        "preprocessing",
        "experiments",
        "plotting",
        "web",
        "doc",
        "scripts",
    ]
    required_files = [
        "README.md",
        "requirements.txt",
        "environment.yml",
        "start_web.py",
        "config/app_settings.example.json",
        ".env.example",
    ]

    for item in required_dirs:
        if not (PROJECT_ROOT / item).is_dir():
            fail(f"required directory missing: {item}")
    for item in required_files:
        if not (PROJECT_ROOT / item).is_file():
            fail(f"required file missing: {item}")
    ok("project layout looks organized")


def check_paths() -> None:
    from config.paths import (
        DATA_DIR,
        OUTPUT_DIR,
        PROJECT_ROOT as CONFIG_ROOT,
        get_video_dir,
    )

    if CONFIG_ROOT.resolve() != PROJECT_ROOT.resolve():
        fail(f"config PROJECT_ROOT mismatch: {CONFIG_ROOT} != {PROJECT_ROOT}")

    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    video_dir = get_video_dir()
    ok(f"configured video directory: {video_dir}")


def check_web_endpoints() -> None:
    from web import create_app

    app = create_app()
    client = app.test_client()
    endpoints = [
        "/",
        "/api/status",
        "/api/import/video-dir",
        "/api/import/videos",
        "/api/dlc/python",
        "/api/dlc/videos",
        "/api/analyze/config",
    ]
    for endpoint in endpoints:
        response = client.get(endpoint)
        if response.status_code != 200:
            fail(f"{endpoint} returned HTTP {response.status_code}")
    status_data = client.get("/api/status").get_json()
    required_status_keys = {"video", "dlc", "csv", "metadata", "roi", "summary"}
    missing = required_status_keys - set(status_data or {})
    if missing:
        fail(f"/api/status missing keys: {sorted(missing)}")
    ok("web endpoints respond successfully")


def check_metadata_shape() -> None:
    from config.paths import METADATA_FILE

    if not METADATA_FILE.exists():
        ok("metadata.xlsx not found yet; this is allowed before importing videos")
        return

    import pandas as pd

    required = {"FileName", "Experiment", "Group", "Condition", "MouseID", "Phase"}
    df = pd.read_excel(str(METADATA_FILE))
    missing = required - set(df.columns)
    if missing:
        fail(f"metadata.xlsx missing columns: {sorted(missing)}")
    ok(f"metadata.xlsx shape looks valid: {len(df)} rows")


def main() -> int:
    check_project_layout()
    check_imports()
    check_paths()
    check_web_endpoints()
    check_metadata_shape()
    print("[OK] project health check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
