"""
扫描 data/grouped/ 下的 CSV 文件，从目录结构和文件名自动提取标签，
生成 data/metadata.xlsx 供用户补充和编辑。

工作流：
  1. DLC 分析视频后输出 CSV 到 data/raw_csv/
  2. fix_csv 修复后输出到 data/fixed_csv/
  3. group_csv 按日期分组到 data/grouped/{OF,EPM,TCT}/
  4. 运行此脚本: python -m preprocessing.build_metadata
     → 自动生成 data/metadata.xlsx
  5. 打开 Excel 手动补充标签（Sex, Age, Batch 等额外列）
  6. analyze 脚本运行时自动读取 metadata 合并标签到输出

用法：
    python -m preprocessing.build_metadata          # 首次生成
    python -m preprocessing.build_metadata --update  # 保留手动列，只追加新文件
"""
import os
import re
import argparse
import pandas as pd
from config.paths import GROUPED_DIR, METADATA_FILE


# ==================== 标签提取规则 ====================

# Group: 从路径中提取
GROUP_PATTERNS = [
    (r'hm4di', 'hM4Di'),
    (r'mcherry', 'mCherry'),
]

# Condition: 从路径中提取
CONDITION_PATTERNS = [
    (r'cno', 'CNO'),
    (r'saline', 'Saline'),
    (r'sal', 'Saline'),
]

# MouseID: 从文件名提取
MOUSE_ID_RE = re.compile(r'([a-zA-Z]+\d+(?:-\d+)?)')

# TCT Phase: 从文件名提取
TCT_PHASE_RE = re.compile(r'\s+([SNH])\s*')


def extract_from_path(path_lower):
    """从路径字符串中提取 Group 和 Condition"""
    group = ''
    condition = ''

    for pattern, label in GROUP_PATTERNS:
        if re.search(pattern, path_lower):
            group = label
            break

    for pattern, label in CONDITION_PATTERNS:
        if re.search(pattern, path_lower):
            condition = label
            break

    return group, condition


def extract_mouse_id(filename):
    """从文件名提取 MouseID"""
    m = MOUSE_ID_RE.search(filename)
    return m.group(1) if m else ''


def extract_tct_phase(filename):
    """从 TCT 文件名提取 Phase"""
    m = TCT_PHASE_RE.search(filename)
    if m:
        phase_map = {'S': 'Social', 'N': 'Novel', 'H': 'Habituation'}
        return phase_map.get(m.group(1), m.group(1))
    return ''


def scan_csv_files():
    """扫描 grouped 目录，为每个 CSV 构建一条记录"""
    records = []

    for exp in ['OF', 'EPM', 'TCT']:
        exp_dir = GROUPED_DIR / exp
        if not exp_dir.exists():
            continue

        for root, dirs, files in os.walk(str(exp_dir)):
            for f in sorted(files):
                if not f.endswith('.csv'):
                    continue

                path_lower = (root + '/' + f).lower()
                group, condition = extract_from_path(path_lower)
                mouse_id = extract_mouse_id(f)

                record = {
                    'FileName': f,
                    'Experiment': exp,
                    'Group': group,
                    'Condition': condition,
                    'MouseID': mouse_id,
                }

                if exp == 'TCT':
                    record['Phase'] = extract_tct_phase(f)

                records.append(record)

    return records


def build_metadata(update=False):
    """生成或更新 metadata.xlsx"""
    print("扫描 CSV 文件...")
    records = scan_csv_files()
    df_new = pd.DataFrame(records)

    if df_new.empty:
        print("未找到任何 CSV 文件")
        return

    print(f"找到 {len(df_new)} 条记录")

    if update and METADATA_FILE.exists():
        df_old = pd.read_excel(str(METADATA_FILE))
        user_cols = [c for c in df_old.columns if c not in df_new.columns and c != 'FilePath']
        df_merged = df_new.merge(df_old[['FileName'] + user_cols], on='FileName', how='left')
        df_out = df_merged
    else:
        df_out = df_new

    core_cols = ['FileName', 'Experiment', 'Group', 'Condition', 'MouseID']
    if 'Phase' in df_out.columns:
        core_cols.append('Phase')
    extra_cols = [c for c in df_out.columns if c not in core_cols]
    df_out = df_out[core_cols + extra_cols]
    df_out = df_out.sort_values(['Experiment', 'Group', 'Condition', 'MouseID']).reset_index(drop=True)

    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_excel(str(METADATA_FILE), index=False)

    print(f"\n已生成: {METADATA_FILE}")
    print(f"共 {len(df_out)} 条记录")
    print(f"\n你可以打开此 Excel 手动添加额外列（Sex, Age, Batch 等）")
    print(f"analyze 脚本运行时会自动读取并合并这些标签")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='生成/更新视频标签元数据表')
    parser.add_argument('--update', action='store_true', help='保留手动列，只追加新文件')
    args = parser.parse_args()
    build_metadata(update=args.update)
