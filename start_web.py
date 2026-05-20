"""Start the behavior analysis web workstation.

This launcher always uses the behavioranalyze Conda environment, waits until
the Flask server is reachable, and then opens the browser.
"""
from __future__ import annotations

import os
import json
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
ENV_NAME = os.environ.get("BEHAVIOR_ANALYZE_ENV", "behavioranalyze")
HOST = "127.0.0.1"
PORT = 5000
URL = f"http://{HOST}:{PORT}"
LOG_DIR = PROJECT_ROOT / "output"
APP_SETTINGS_FILE = PROJECT_ROOT / "data" / "app_settings.json"
STDOUT_LOG = LOG_DIR / "web_start.log"
STDERR_LOG = LOG_DIR / "web_start.err.log"


def is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def wait_until_ready(timeout_seconds: int = 20) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if is_port_open(HOST, PORT):
            return True
        time.sleep(0.3)
    return False


def start_server() -> subprocess.Popen:
    LOG_DIR.mkdir(exist_ok=True)
    stdout = STDOUT_LOG.open("w", encoding="utf-8")
    stderr = STDERR_LOG.open("w", encoding="utf-8")
    command = get_server_command()

    return subprocess.Popen(
        command,
        cwd=str(PROJECT_ROOT),
        stdout=stdout,
        stderr=stderr,
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
    )


def get_configured_python() -> str:
    env_python = os.environ.get("BEHAVIOR_ANALYZE_SERVER_PYTHON")
    if env_python and Path(env_python).is_file():
        return env_python

    if APP_SETTINGS_FILE.exists():
        try:
            with APP_SETTINGS_FILE.open("r", encoding="utf-8-sig") as f:
                settings = json.load(f)
            configured = settings.get("server_python")
            if configured and Path(configured).is_file():
                return configured
        except (OSError, json.JSONDecodeError):
            pass

    return ""


def get_server_command() -> list[str]:
    if os.environ.get("CONDA_DEFAULT_ENV") == ENV_NAME:
        return [sys.executable, str(PROJECT_ROOT / "run_web_no_browser.py")]

    configured_python = get_configured_python()
    if configured_python:
        return [configured_python, str(PROJECT_ROOT / "run_web_no_browser.py")]

    conda_exe = os.environ.get("CONDA_EXE") or shutil.which("conda")
    if conda_exe:
        return [
            conda_exe,
            "run",
            "-n",
            ENV_NAME,
            "python",
            str(PROJECT_ROOT / "run_web_no_browser.py"),
        ]

    return [sys.executable, str(PROJECT_ROOT / "run_web_no_browser.py")]


def main() -> int:
    if is_port_open(HOST, PORT):
        print(f"Web 服务已经在运行: {URL}")
        webbrowser.open(URL)
        return 0

    print("正在启动行为分析 Web 服务...")
    print("启动命令:", " ".join(get_server_command()))
    start_server()

    if wait_until_ready():
        print(f"启动成功: {URL}")
        webbrowser.open(URL)
        return 0

    print("启动超时，请查看日志：")
    print(f"  {STDOUT_LOG}")
    print(f"  {STDERR_LOG}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
