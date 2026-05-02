import os
import shutil
from config.paths import FIXED_CSV_DIR, GROUPED_DIR, OF_CSV_DIR, EPM_CSV_DIR, TCT_CSV_DIR

# ================= 配置区 =================
input_dir = str(FIXED_CSV_DIR)
output_base = str(GROUPED_DIR)

# 分组关键词映射
GROUP_RULES = {
    "OF": {"keywords": ["OF", "of", "OpenField", "openfield"], "dir": str(OF_CSV_DIR)},
    "EPM": {"keywords": ["EPM", "epm", "PlusMaze", "plusmaze"], "dir": str(EPM_CSV_DIR)},
    "TCT": {"keywords": ["TCT", "tct", "ThreeChamber", "threechamber", "Social"], "dir": str(TCT_CSV_DIR)},
}
# ==========================================

for group_name, rule in GROUP_RULES.items():
    os.makedirs(rule["dir"], exist_ok=True)


def classify_file(filename):
    """根据文件名中的关键词分组"""
    for group_name, rule in GROUP_RULES.items():
        for kw in rule["keywords"]:
            if kw in filename:
                return group_name, rule["dir"]
    return None, None


def main():
    csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
    print(f"找到 {len(csv_files)} 个 CSV 文件待分组")

    stats = {k: 0 for k in GROUP_RULES}
    unclassified = []

    for csv_file in csv_files:
        group, dest_dir = classify_file(csv_file)
        if group:
            src = os.path.join(input_dir, csv_file)
            dst = os.path.join(dest_dir, csv_file)
            shutil.copy2(src, dst)
            stats[group] += 1
            print(f"  ✅ {csv_file} -> {group}")
        else:
            unclassified.append(csv_file)
            print(f"  ⚠️ 无法分组: {csv_file}")

    print(f"\n✨ 分组完成！")
    for k, v in stats.items():
        print(f"  {k}: {v} 个文件")
    if unclassified:
        print(f"  未分组: {len(unclassified)} 个文件")
        for f in unclassified:
            print(f"    - {f}")


if __name__ == "__main__":
    main()
