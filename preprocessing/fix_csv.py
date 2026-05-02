import os
import numpy as np
import pandas as pd
from config.paths import RAW_CSV_DIR, FIXED_CSV_DIR

# ================= 配置区 =================
input_dir = str(RAW_CSV_DIR)
output_dir = str(FIXED_CSV_DIR)
CONFIDENCE_THRESHOLD = 0.6       # 低于此阈值的坐标视为无效
CAGE_THRESHOLD = 200             # 空笼判定阈值（像素）
QUADRANT_GRID_SIZE = 2           # 按几×几网格分拣
INTERPOLATION_LIMIT = 30         # 插值最大间隔帧数
# ==========================================

if not os.path.exists(output_dir):
    os.makedirs(output_dir)


def load_dlc_csv(filepath):
    """加载DLC生成的CSV（处理多层表头）"""
    df = pd.read_csv(filepath, header=[0, 1, 2], index_col=0)
    return df


def check_confidence(df, threshold=CONFIDENCE_THRESHOLD):
    """低置信度坐标设为NaN"""
    scorer = df.columns.get_level_values(0)[0]
    bodyparts = df.columns.get_level_values(1).unique()

    for bp in bodyparts:
        likelihood_col = (scorer, bp, 'likelihood')
        x_col = (scorer, bp, 'x')
        y_col = (scorer, bp, 'y')

        mask = df[likelihood_col] < threshold
        df.loc[mask, x_col] = np.nan
        df.loc[mask, y_col] = np.nan

    return df


def sort_by_quadrant(df, grid_size=QUADRANT_GRID_SIZE):
    """按象限分拣数据点"""
    scorer = df.columns.get_level_values(0)[0]
    bodyparts = df.columns.get_level_values(1).unique()

    for bp in bodyparts:
        x_col = (scorer, bp, 'x')
        y_col = (scorer, bp, 'y')

        valid = df[[x_col, y_col]].dropna()
        if len(valid) == 0:
            continue

        x_vals = valid[x_col]
        y_vals = valid[y_col]

        x_bins = pd.cut(x_vals, bins=grid_size, labels=False)
        y_bins = pd.cut(y_vals, bins=grid_size, labels=False)

        for qx in range(grid_size):
            for qy in range(grid_size):
                mask = (x_bins == qx) & (y_bins == qy)
                if mask.sum() > 1:
                    indices = valid.index[mask]
                    for col in [x_col, y_col]:
                        df.loc[indices, col] = df.loc[indices, col].interpolate(
                            limit=INTERPOLATION_LIMIT
                        )

    return df


def linear_interpolate(df, limit=INTERPOLATION_LIMIT):
    """线性插值填充NaN"""
    scorer = df.columns.get_level_values(0)[0]
    bodyparts = df.columns.get_level_values(1).unique()

    for bp in bodyparts:
        for coord in ['x', 'y']:
            col = (scorer, bp, coord)
            df[col] = df[col].interpolate(limit=limit)

    return df


def detect_empty_cage(df, threshold=CAGE_THRESHOLD):
    """检测空笼数据（总移动距离过小）"""
    scorer = df.columns.get_level_values(0)[0]
    bodyparts = df.columns.get_level_values(1).unique()

    for bp in bodyparts:
        x_col = (scorer, bp, 'x')
        y_col = (scorer, bp, 'y')

        valid = df[[x_col, y_col]].dropna()
        if len(valid) < 2:
            continue

        dx = valid[x_col].diff().dropna()
        dy = valid[y_col].diff().dropna()
        total_dist = np.sqrt(dx**2 + dy**2).sum()

        if total_dist < threshold:
            print(f"  ⚠️ 检测到空笼数据: {bp} (总移动距离={total_dist:.1f})")

    return df


def process_file(filepath, output_path):
    """处理单个CSV文件"""
    print(f"处理: {os.path.basename(filepath)}")

    df = load_dlc_csv(filepath)
    df = check_confidence(df)
    df = sort_by_quadrant(df)
    df = linear_interpolate(df)
    df = detect_empty_cage(df)

    df.to_csv(output_path)
    print(f"  ✅ 已保存: {os.path.basename(output_path)}")


def main():
    csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
    print(f"找到 {len(csv_files)} 个 CSV 文件待处理")

    for csv_file in csv_files:
        input_path = os.path.join(input_dir, csv_file)
        output_path = os.path.join(output_dir, csv_file)
        process_file(input_path, output_path)

    print(f"\n✨ 全部处理完成！输出目录: {output_dir}")


if __name__ == "__main__":
    main()
