"""
工具函数
"""
import re
import contextlib
from pathlib import Path


# MouseID 提取正则（与 build_metadata.py 一致）
MOUSE_ID_RE = re.compile(r'([a-zA-Z]+\d+(?:-\d+)?)')


def extract_mouse_id(filename):
    """从文件名提取 MouseID"""
    m = MOUSE_ID_RE.search(filename)
    return m.group(1) if m else ''


@contextlib.contextmanager
def temp_patch(module, **overrides):
    """临时覆盖模块级变量，退出后恢复"""
    original = {}
    for key, value in overrides.items():
        original[key] = getattr(module, key)
        setattr(module, key, value)
    try:
        yield
    finally:
        for key, value in original.items():
            setattr(module, key, value)


def find_latest_summary(summary_dir, prefix=''):
    """在 summary 目录中查找最新的 Excel 文件"""
    summary_path = Path(summary_dir)
    if not summary_path.exists():
        return None
    xlsx_files = list(summary_path.glob(f'{prefix}*.xlsx'))
    if not xlsx_files:
        return None
    return str(max(xlsx_files, key=lambda p: p.stat().st_mtime))


def video_to_csv_name(video_name):
    """将视频文件名转换为可能的 DLC 输出 CSV 文件名"""
    stem = Path(video_name).stem
    return f"{stem}.csv"


def is_video_file(path):
    """判断是否为视频文件"""
    ext = Path(path).suffix.lower()
    return ext in {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'}
