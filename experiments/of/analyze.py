import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import glob
from datetime import datetime

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from config.paths import OF_CSV_DIR, OF_ROI_JSON, OF_TRACING_HEAT, OF_SUMMARY
from experiments.common import InvalidPoseCsvError, get_bodypart_cols, load_flat_csv, load_roi_regions
from preprocessing.metadata_utils import load_metadata, get_labels

# ================= 配置区 =================
CSV_DIR = str(OF_CSV_DIR)
ROI_JSON_PATH = str(OF_ROI_JSON)
OUTPUT_DIR = str(OF_TRACING_HEAT)
SUMMARY_DIR = str(OF_SUMMARY)
FPS = 30
ANALYSIS_MINUTES = 15
LIKELIHOOD_THRESHOLD = 0.6
ARENA_SIZE_CM = 50.0
# ==========================================

def process_all():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    if not os.path.exists(SUMMARY_DIR):
        os.makedirs(SUMMARY_DIR)

    regions = load_roi_regions(ROI_JSON_PATH)
    limit_frames = ANALYSIS_MINUTES * 60 * FPS
    csv_files = glob.glob(os.path.join(CSV_DIR, "**", "*.csv"), recursive=True)

    if not csv_files:
        print(f"❌ 未找到 CSV 文件，请检查路径: {CSV_DIR}")
        return

    all_summary_results = []
    run_timestamp = datetime.now().strftime("%m%d_%H%M")
    metadata_df = load_metadata()

    total = len(csv_files) * 4
    step = 0

    for csv_idx, csv_path in enumerate(csv_files):
        filename = os.path.basename(csv_path)
        path_lower = csv_path.lower()
        group_tag, condition_tag = get_labels(filename, path_lower, metadata_df)

        print(f"正在分析: [{group_tag}-{condition_tag}] {filename}")

        try:
            df = load_flat_csv(csv_path, limit_frames)

            plt.close('all')
            fig, axes = plt.subplots(4, 2, figsize=(15, 24))
            axes = axes.flatten()

            for i in range(4):
                step += 1
                print(f"[PROGRESS] {step}/{total} OF {filename} cage{i+1}")
                ax_traj, ax_heat = axes[i], axes[i+4]
                cage_num = i + 1

                cage_key = f"cage{cage_num}"
                center_key = f"cage{cage_num}_center_1_4"

                if cage_key not in regions or center_key not in regions:
                    continue

                c_roi, ct_roi = regions[cage_key], regions[center_key]

                # 获取列
                col_x, col_y, col_l = get_bodypart_cols(df, cage_key, 'nose')
                if col_x is None:
                    continue

                pixel_width = c_roi['x2'] - c_roi['x1']
                px_to_cm = ARENA_SIZE_CM / pixel_width

                vx, vy = df[col_x].values, df[col_y].values
                if col_l:
                    vp = df[col_l].values
                    valid_mask = (~np.isnan(vp)) & (vp > LIKELIHOOD_THRESHOLD)
                    vx, vy = vx[valid_mask], vy[valid_mask]

                if len(vx) < 10:
                    continue

                valid_frames = len(vx)
                total_time_s = valid_frames / FPS
                dist_px = np.sum(np.sqrt(np.diff(vx)**2 + np.diff(vy)**2))
                dist_cm = dist_px * px_to_cm

                in_c = (vx >= ct_roi['x1']) & (vx <= ct_roi['x2']) & \
                       (vy >= ct_roi['y1']) & (vy <= ct_roi['y2'])
                center_time_s = np.sum(in_c) / FPS
                center_percent = center_time_s / total_time_s * 100 if total_time_s > 0 else 0

                all_summary_results.append({
                    'Group': group_tag, 'Condition': condition_tag, 'FileName': filename,
                    'Cage': cage_key, 'Total_Distance_px': round(dist_px, 2),
                    'Total_Distance_cm': round(dist_cm, 2),
                    'Total_Time_s': round(total_time_s, 2),
                    'Center_Time_s': round(center_time_s, 2),
                    'Center_Percent': round(center_percent, 2),
                    'Entries': int(np.sum((in_c[:-1] == False) & (in_c[1:] == True)))
                })

                ax_traj.plot(vx, vy, color='gray', alpha=0.3, linewidth=0.8, zorder=1)

                vx_red, vy_red = vx.copy(), vy.copy()
                vx_red[~in_c] = np.nan
                vy_red[~in_c] = np.nan
                ax_traj.plot(vx_red, vy_red, color='red', linewidth=1.2, alpha=0.9, zorder=2)

                ax_traj.add_patch(Rectangle((c_roi['x1'], c_roi['y1']), c_roi['x2']-c_roi['x1'],
                                            c_roi['y2']-c_roi['y1'], fill=False, edgecolor='blue', lw=1))
                ax_traj.add_patch(Rectangle((ct_roi['x1'], ct_roi['y1']), ct_roi['x2']-ct_roi['x1'],
                                            ct_roi['y2']-ct_roi['y1'], fill=False, edgecolor='red', lw=1.5))

                ax_traj.set_title(f"Cage {cage_num} (Dist: {round(dist_cm/100, 2)}m)")
                ax_traj.invert_yaxis()

                hb = ax_heat.hist2d(vx, vy, bins=50, cmap='jet',
                                    range=[[c_roi['x1'], c_roi['x2']], [c_roi['y1'], c_roi['y2']]])

                ax_heat.add_patch(Rectangle((ct_roi['x1'], ct_roi['y1']), ct_roi['x2']-ct_roi['x1'],
                                            ct_roi['y2']-ct_roi['y1'], fill=False, edgecolor='white', lw=1.5, ls='--'))

                ax_heat.set_title(f"Cage {cage_num} Heatmap")
                ax_heat.invert_yaxis()
                plt.colorbar(hb[3], ax=ax_heat, fraction=0.046, pad=0.04)

            plt.tight_layout()
            save_name = f"{group_tag}_{condition_tag}_{os.path.splitext(filename)[0]}_15min.png"
            plt.savefig(os.path.join(OUTPUT_DIR, save_name), dpi=100)
            plt.close()

        except InvalidPoseCsvError as e:
            print(f"[ERROR] 输入 CSV 格式错误: {e}")
            raise
        except Exception as e:
            print(f"❌ 出错 {filename}: {e}")

    if all_summary_results:
        res_df = pd.DataFrame(all_summary_results)
        res_df.to_excel(os.path.join(SUMMARY_DIR, f"Summary_15min_{run_timestamp}.xlsx"), index=False)
        print(f"✅ 处理完成！图片已存至: {OUTPUT_DIR}")
        print(f"✅ 汇总表已存至: {SUMMARY_DIR}")

if __name__ == "__main__":
    process_all()
