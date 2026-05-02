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

VIDEO_DIR = PROJECT_ROOT / "video"          # 视频源文件

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
