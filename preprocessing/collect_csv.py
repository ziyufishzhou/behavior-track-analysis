"""Collect DeepLabCut CSV outputs into data/raw_csv."""
import os
import sys
import shutil
from pathlib import Path

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from config.paths import RAW_CSV_DIR, get_video_dir


def dlc_csv_to_result_name(csv_path: Path) -> str:
    """Convert a DLC output name to the normalized *_result.csv name."""
    stem = csv_path.stem
    if "DLC" in stem:
        stem = stem.split("DLC", 1)[0]
    stem = stem.rstrip("_- ")
    return f"{stem}_result.csv"


def collect_dlc_csv(video_root: Path | None = None, output_dir: Path = RAW_CSV_DIR) -> int:
    """Copy DLC CSV files from the video tree to raw_csv and return copied count."""
    video_root = Path(video_root) if video_root is not None else get_video_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[收集CSV] 从 {video_root} 递归查找 DLC CSV...")

    if not video_root.exists():
        print(f"[ERROR] 视频目录不存在: {video_root}")
        return 0

    csv_files = sorted(
        p for p in video_root.rglob("*.csv")
        if p.is_file() and "DLC" in p.name and output_dir not in p.parents
    )

    if not csv_files:
        print("[收集CSV] 未找到 DLC CSV 文件")
        return 0

    copied = 0
    used_dest_names = set()
    for i, src in enumerate(csv_files, 1):
        dest_name = dlc_csv_to_result_name(src)
        dest = output_dir / dest_name

        # Multiple source files in one run can normalize to the same name; only
        # then add a suffix. Across different runs, overwrite the same target so
        # repeated collection remains idempotent.
        if dest_name in used_dest_names:
            suffix = 2
            while True:
                alt_name = f"{Path(dest_name).stem}_{suffix}.csv"
                if alt_name not in used_dest_names:
                    dest = output_dir / alt_name
                    dest_name = alt_name
                    break
                suffix += 1

        shutil.copy2(src, dest)
        used_dest_names.add(dest_name)
        copied += 1
        print(f"[PROGRESS] {i}/{len(csv_files)} {src.name} -> {dest.name}")

    print(f"[收集CSV] 完成，共复制 {copied} 个文件到 {output_dir}")
    return copied


def main():
    collect_dlc_csv()


if __name__ == "__main__":
    main()
