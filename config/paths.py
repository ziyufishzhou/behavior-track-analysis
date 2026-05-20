import json
import os
from pathlib import Path

# 项目根目录（config/ 的上一级）
PROJECT_ROOT = Path(__file__).parent.parent

# ============ 数据目录 ============
DATA_DIR = PROJECT_ROOT / "data"
RAW_CSV_DIR = DATA_DIR / "raw_csv"          # DLC 原始输出
FIXED_CSV_DIR = DATA_DIR / "fixed_csv"      # 修复后 CSV
GROUPED_DIR = DATA_DIR / "grouped"          # 按实验分组
ROI_DIR = DATA_DIR / "roi"                  # ROI 配置 JSON
METADATA_FILE = DATA_DIR / "metadata.xlsx"  # 标签元数据表

VIDEO_DIR = PROJECT_ROOT / "video"          # 默认视频源文件
APP_SETTINGS_FILE = DATA_DIR / "app_settings.json"

# ============ 输出目录 ============
OUTPUT_DIR = PROJECT_ROOT / "output"

# OF (Open Field)
OF_OUTPUT = OUTPUT_DIR / "of"
OF_TRACING_HEAT = OF_OUTPUT / "tracing_heat"
OF_FIGURES = OF_OUTPUT / "figures"
OF_SUMMARY = OF_OUTPUT / "summary"

# EPM (Elevated Plus Maze)
EPM_OUTPUT = OUTPUT_DIR / "epm"
EPM_TRACING_HEAT = EPM_OUTPUT / "tracing_heat"
EPM_FIGURES = EPM_OUTPUT / "figures"
EPM_SUMMARY = EPM_OUTPUT / "summary"

# TCT (Three-Chamber Test)
TCT_OUTPUT = OUTPUT_DIR / "tct"
TCT_HEAT_TRACING = TCT_OUTPUT / "heat_tracing"
TCT_FIGURES = TCT_OUTPUT / "figures"
TCT_SUMMARY = TCT_OUTPUT / "summary"

# ============ ROI 配置文件路径 ============
OF_ROI_JSON = ROI_DIR / "OF_roi_regions.json"
EPM_ROI_JSON = ROI_DIR / "EPM_ROI.json"
TCT_ROI_JSON = ROI_DIR / "TCT_ROI_Config.json"

# ============ 分组后的 CSV 目录 ============
OF_CSV_DIR = GROUPED_DIR / "OF"
EPM_CSV_DIR = GROUPED_DIR / "EPM"
TCT_CSV_DIR = GROUPED_DIR / "TCT"

# ============ DLC 模型 ============
MODELS_DIR = PROJECT_ROOT / "models"


def _resolve_path(value):
    path = Path(str(value)).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def resolve_project_path(value):
    return _resolve_path(value)


def load_app_settings():
    if not APP_SETTINGS_FILE.exists():
        return {}
    try:
        with APP_SETTINGS_FILE.open("r", encoding="utf-8-sig") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_app_settings(settings):
    APP_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with APP_SETTINGS_FILE.open("w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def get_setting(key, default=None):
    return load_app_settings().get(key, default)


def set_setting(key, value):
    settings = load_app_settings()
    settings[key] = value
    save_app_settings(settings)


def get_video_dir():
    """Return the configured video root directory.

    Priority:
    1. BEHAVIOR_ANALYZE_VIDEO_DIR environment variable.
    2. data/app_settings.json saved by the Web UI.
    3. Project-local video/ directory.
    """
    env_value = os.environ.get("BEHAVIOR_ANALYZE_VIDEO_DIR")
    if env_value:
        return _resolve_path(env_value)

    settings = load_app_settings()
    video_dir = settings.get("video_dir")
    if video_dir:
        return _resolve_path(video_dir)

    return VIDEO_DIR.resolve()


def set_video_dir(path):
    video_dir = _resolve_path(path)
    settings = load_app_settings()
    settings["video_dir"] = str(video_dir)
    save_app_settings(settings)
    return video_dir


def get_dlc_python():
    """Return the configured Python executable for the DLC environment."""
    env_value = os.environ.get("BEHAVIOR_ANALYZE_DLC_PYTHON")
    if env_value:
        return _resolve_path(env_value)

    setting_value = get_setting("dlc_python")
    if setting_value:
        return _resolve_path(setting_value)

    return None


def set_dlc_python(path):
    dlc_python = _resolve_path(path)
    set_setting("dlc_python", str(dlc_python))
    return dlc_python
