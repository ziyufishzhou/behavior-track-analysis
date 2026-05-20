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

from config.paths import EPM_CSV_DIR, EPM_ROI_JSON, EPM_TRACING_HEAT, EPM_SUMMARY
from experiments.common import InvalidPoseCsvError, get_bodypart_cols, load_flat_csv, load_roi_regions
from preprocessing.metadata_utils import load_metadata, get_labels

# ================= 配置区 =================
CSV_DIR = str(EPM_CSV_DIR)
ROI_JSON_PATH = str(EPM_ROI_JSON)
OUTPUT_DIR = str(EPM_TRACING_HEAT)
SUMMARY_DIR = str(EPM_SUMMARY)
FPS = 30
ANALYSIS_MINUTES = 15
LIKELIHOOD_THRESHOLD = 0.6
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

    total = len(csv_files) * 2
    step = 0

    for csv_path in csv_files:
        filename = os.path.basename(csv_path)
        path_lower = csv_path.lower()
        group_tag, condition_tag = get_labels(filename, path_lower, metadata_df)
        print(f"正在分析: [{group_tag}-{condition_tag}] {filename}")

        try:
            df = load_flat_csv(csv_path, limit_frames)

            plt.close('all')
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            axes = axes.flatten()

            for idx, prefix in enumerate(["cage1", "cage2"]):
                step += 1
                print(f"[PROGRESS] {step}/{total} EPM {filename} {prefix}")

                if prefix not in regions:
                    print(f"⚠️ ROI '{prefix}' 不存在，跳过")
                    continue

                open_arms = [r for r in regions if r.startswith(f"{prefix}_OA")]
                closed_arms = [r for r in regions if r.startswith(f"{prefix}_CA")]
                center_key = f"{prefix}_center"

                if center_key not in regions:
                    print(f"⚠️ ROI '{center_key}' 不存在，跳过")
                    continue

                col_x, col_y, col_l = get_bodypart_cols(df, prefix, 'nose')
                if col_x is None:
                    continue

                vx, vy = df[col_x].values, df[col_y].values
                if col_l:
                    vp = df[col_l].values
                    valid_mask = (~np.isnan(vp)) & (vp > LIKELIHOOD_THRESHOLD)
                    vx, vy = vx[valid_mask], vy[valid_mask]

                if len(vx) < 10:
                    continue

                total_frames = len(vx)
                total_time_s = total_frames / FPS

                oa_time, ca_time = 0.0, 0.0
                oa_entries, ca_entries = 0, 0

                for arm_name in open_arms:
                    if arm_name not in regions:
                        continue
                    arm = regions[arm_name]
                    in_arm = (vx >= arm['x1']) & (vx <= arm['x2']) & \
                             (vy >= arm['y1']) & (vy <= arm['y2'])
                    oa_time += np.sum(in_arm)
                    oa_entries += np.sum((in_arm[:-1] == False) & (in_arm[1:] == True))

                for arm_name in closed_arms:
                    if arm_name not in regions:
                        continue
                    arm = regions[arm_name]
                    in_arm = (vx >= arm['x1']) & (vx <= arm['x2']) & \
                             (vy >= arm['y1']) & (vy <= arm['y2'])
                    ca_time += np.sum(in_arm)
                    ca_entries += np.sum((in_arm[:-1] == False) & (in_arm[1:] == True))

                center = regions[center_key]
                in_center = (vx >= center['x1']) & (vx <= center['x2']) & \
                            (vy >= center['y1']) & (vy <= center['y2'])
                center_time = np.sum(in_center)
                center_entries = np.sum((in_center[:-1] == False) & (in_center[1:] == True))

                dist_px = np.sum(np.sqrt(np.diff(vx)**2 + np.diff(vy)**2))

                oa_time_s = round(oa_time / FPS, 2)
                ca_time_s = round(ca_time / FPS, 2)
                center_time_s = round(center_time / FPS, 2)
                oa_pct = round(oa_time / total_frames * 100, 2) if total_frames > 0 else 0

                all_summary_results.append({
                    'Group': group_tag, 'Condition': condition_tag,
                    'FileName': filename, 'Cage': prefix,
                    'OA_Time_s': oa_time_s, 'CA_Time_s': ca_time_s,
                    'Center_Time_s': center_time_s,
                    'Total_Time_s': round(total_time_s, 2),
                    'OA_Percent': oa_pct,
                    'OA_Entries': int(oa_entries), 'CA_Entries': int(ca_entries),
                    'Center_Entries': int(center_entries),
                    'Distance_px': round(dist_px, 2),
                })

                ax = axes[idx]
                ax.plot(vx, vy, color='gray', alpha=0.3, linewidth=0.8, zorder=1)

                for arm_name in open_arms:
                    arm = regions[arm_name]
                    in_arm = (vx >= arm['x1']) & (vx <= arm['x2']) & \
                             (vy >= arm['y1']) & (vy <= arm['y2'])
                    vx_oa, vy_oa = vx.copy(), vy.copy()
                    vx_oa[~in_arm] = np.nan
                    vy_oa[~in_arm] = np.nan
                    ax.plot(vx_oa, vy_oa, color='red', linewidth=1.2, alpha=0.9, zorder=2)
                    ax.add_patch(Rectangle((arm['x1'], arm['y1']),
                                          arm['x2']-arm['x1'], arm['y2']-arm['y1'],
                                          fill=False, edgecolor='green', lw=1.5))

                for arm_name in closed_arms:
                    arm = regions[arm_name]
                    ax.add_patch(Rectangle((arm['x1'], arm['y1']),
                                          arm['x2']-arm['x1'], arm['y2']-arm['y1'],
                                          fill=False, edgecolor='blue', lw=1.5))

                ax.add_patch(Rectangle((center['x1'], center['y1']),
                                      center['x2']-center['x1'], center['y2']-center['y1'],
                                      fill=False, edgecolor='orange', lw=1.5, ls='--'))

                ax.set_title(f"{prefix} (OA: {oa_time_s}s, {oa_pct}%)")
                ax.invert_yaxis()

                ax_heat = axes[idx + 2]
                cage_roi = regions[prefix]
                hb = ax_heat.hist2d(vx, vy, bins=50, cmap='jet',
                                    range=[[cage_roi['x1'], cage_roi['x2']],
                                           [cage_roi['y1'], cage_roi['y2']]])
                ax_heat.set_title(f"{prefix} Heatmap")
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
        res_df.to_excel(os.path.join(SUMMARY_DIR, f"EPM_Summary_{run_timestamp}.xlsx"), index=False)
        print(f"✅ 处理完成！图片已存至: {OUTPUT_DIR}")
        print(f"✅ 汇总表已存至: {SUMMARY_DIR}")


if __name__ == "__main__":
    process_all()
