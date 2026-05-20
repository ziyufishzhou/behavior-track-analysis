"""
metadata 辅助函数 — 供各 analyze 脚本共享。

优先从 data/metadata.xlsx 读取标签，找不到则回退到路径推断。
"""
import os
import sys
import pandas as pd
from pathlib import Path

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from config.paths import METADATA_FILE


def load_metadata():
    """读取 metadata.xlsx，返回 DataFrame 或 None"""
    if not METADATA_FILE.exists():
        return None
    return pd.read_excel(str(METADATA_FILE))


def metadata_filename_to_csv(filename):
    """Map metadata FileName values such as videos to normalized result CSV names."""
    name = str(filename).strip().replace("\\", "/")
    base = Path(name).name
    stem = Path(base).stem
    if base.lower().endswith(".csv"):
        return base
    if base.lower().endswith((".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv")):
        return f"{stem}_result.csv"
    return base


def get_labels(filename, path_lower, metadata_df=None):
    """从 metadata 获取 Group/Condition 标签，不存在则回退到路径推断"""
    group, condition = '', ''

    if metadata_df is not None and 'FileName' in metadata_df.columns:
        file_series = metadata_df['FileName'].astype(str)
        csv_series = file_series.map(metadata_filename_to_csv)
        base_series = file_series.map(lambda value: Path(str(value).replace("\\", "/")).name)
        match = metadata_df[(file_series == filename) | (csv_series == filename) | (base_series == filename)]
        if not match.empty:
            group = str(match.iloc[0].get('Group', ''))
            condition = str(match.iloc[0].get('Condition', ''))

    if not group:
        group = 'hm4di' if 'hm4di' in path_lower else ('mcherry' if 'mcherry' in path_lower else 'others')
    if not condition:
        condition = 'cno' if 'cno' in path_lower else ('saline' if 'saline' in path_lower else 'unknown')

    return group, condition
