import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap
import glob
import re
from datetime import datetime
from scipy.ndimage import gaussian_filter

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from config.paths import TCT_CSV_DIR, TCT_ROI_JSON, TCT_HEAT_TRACING, TCT_SUMMARY
from experiments.common import InvalidPoseCsvError, get_bodypart_cols, load_flat_csv, load_roi_regions
from preprocessing.metadata_utils import load_metadata, get_labels

# ================= 配置区 =================
CSV_DIR = str(TCT_CSV_DIR)
ROI_JSON_PATH = str(TCT_ROI_JSON)
OUTPUT_DIR = str(TCT_HEAT_TRACING)
SUMMARY_DIR = str(TCT_SUMMARY)
FPS = 30
ANALYSIS_MINUTES = 10
LIKELIHOOD_THRESHOLD = 0.6
# ==========================================

custom_cmap = LinearSegmentedColormap.from_list('heat', ['white', 'blue', 'yellow', 'red'])


def infer_phase_from_filename(filename):
    match = re.search(r'(?<![A-Za-z])([SNH])(?=\s|_|-|\.|$)', filename)
    if match:
        return match.group(1)
    return "S"


def get_phase_from_metadata(filename, metadata_df=None):
    if metadata_df is not None and 'FileName' in metadata_df.columns and 'Phase' in metadata_df.columns:
        file_series = metadata_df['FileName'].astype(str)
        csv_series = file_series.map(lambda value: f"{os.path.splitext(os.path.basename(str(value)))[0]}_result.csv")
        match = metadata_df[(file_series == filename) | (csv_series == filename)]
        if not match.empty:
            value = str(match.iloc[0].get('Phase', '')).strip()
            phase_map = {'Social': 'S', 'Novel': 'N', 'Habituation': 'H'}
            return phase_map.get(value, value[:1].upper() if value else infer_phase_from_filename(filename))
    return infer_phase_from_filename(filename)


def get_chamber_roles(filename, metadata_df=None):
    phase = get_phase_from_metadata(filename, metadata_df)
    fname_lower = filename.lower()
    role_l, role_r = "Unknown", "Unknown"
    if "honghong" in fname_lower:
        role_l = "Live" if phase == "S" else "Old_Friend"
        role_r = "Toy" if phase == "S" else "New_Friend"
    elif "lanlan" in fname_lower:
        role_l = "Toy" if phase == "S" else "New_Friend"
        role_r = "Live" if phase == "S" else "Old_Friend"
    return phase, role_l, role_r


def process_tct_full_visual():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    if not os.path.exists(SUMMARY_DIR):
        os.makedirs(SUMMARY_DIR)
    regions = load_roi_regions(ROI_JSON_PATH)
    frames_limit = ANALYSIS_MINUTES * 60 * FPS
    csv_files = glob.glob(os.path.join(CSV_DIR, "**", "*.csv"), recursive=True)

    all_results = []
    run_timestamp = datetime.now().strftime("%m%d_%H%M")
    metadata_df = load_metadata()

    total = len(csv_files) * 4
    step = 0

    for csv_path in csv_files:
        filename = os.path.basename(csv_path)
        path_lower = csv_path.lower()
        group, condition = get_labels(filename, path_lower, metadata_df)
        phase, role_l, role_r = get_chamber_roles(filename, metadata_df)

        try:
            df = load_flat_csv(csv_path, frames_limit)

            fig, axes = plt.subplots(4, 1, figsize=(12, 24))

            for idx, cage_num in enumerate(["1", "2", "3", "4"]):
                step += 1
                print(f"[PROGRESS] {step}/{total} TCT {filename} cage{cage_num}")
                ax = axes[idx]
                prefix = f"{cage_num}_"
                if f"{prefix}L" not in regions:
                    continue

                col_x, col_y, col_l = get_bodypart_cols(df, f"cage{cage_num}", 'nose')
                if col_x is None:
                    continue

                vx, vy = df[col_x].values, df[col_y].values
                mask = np.ones(len(vx), dtype=bool)
                if col_l:
                    vp = df[col_l].values
                    mask = (~np.isnan(vp)) & (vp > LIKELIHOOD_THRESHOLD)
                mx, my = vx[mask], vy[mask]

                if len(mx) < 2:
                    continue

                time_frames = {"L": 0, "Center": 0, "R": 0}
                entry_counts = {"L": 0, "Center": 0, "R": 0}
                last_zone = None

                roi_l, roi_c, roi_r = regions[f"{prefix}L"], regions[f"{prefix}Center"], regions[f"{prefix}R"]

                for i in range(len(vx)):
                    if not mask[i]:
                        continue
                    cx, cy = vx[i], vy[i]
                    curr_zone = None
                    if (roi_l['x1'] <= cx <= roi_l['x2']) and (roi_l['y1'] <= cy <= roi_l['y2']):
                        curr_zone = "L"
                    elif (roi_c['x1'] <= cx <= roi_c['x2']) and (roi_c['y1'] <= cy <= roi_c['y2']):
                        curr_zone = "Center"
                    elif (roi_r['x1'] <= cx <= roi_r['x2']) and (roi_r['y1'] <= cy <= roi_r['y2']):
                        curr_zone = "R"

                    if curr_zone:
                        time_frames[curr_zone] += 1
                        if curr_zone != last_zone:
                            entry_counts[curr_zone] += 1
                    last_zone = curr_zone

                is_l_target = (role_l in ["Live", "New_Friend"])
                e_target = entry_counts["L"] if is_l_target else entry_counts["R"]
                e_control = entry_counts["R"] if is_l_target else entry_counts["L"]
                target_time_s = (time_frames["L"] if is_l_target else time_frames["R"]) / FPS
                control_time_s = (time_frames["R"] if is_l_target else time_frames["L"]) / FPS
                preference_index = (
                    (target_time_s - control_time_s) / (target_time_s + control_time_s)
                    if (target_time_s + control_time_s) > 0 else 0
                )

                extent = [roi_l['x1']-50, roi_r['x2']+50, min(my)-50, max(my)+50]
                heatmap, xedges, yedges = np.histogram2d(mx, my, bins=100,
                                                          range=[[extent[0], extent[1]], [extent[2], extent[3]]])
                ax.imshow(gaussian_filter(heatmap.T, 1.5), extent=extent, origin='lower',
                          cmap=custom_cmap, interpolation='gaussian', alpha=0.8, aspect='auto')

                ax.plot(mx, my, color='black', lw=0.6, alpha=0.4)

                for r_k, color, label in [(f"{prefix}L", "red", role_l),
                                          (f"{prefix}Center", "green", "Center"),
                                          (f"{prefix}R", "blue", role_r)]:
                    r = regions[r_k]
                    zone_key = r_k[-1] if r_k[-1] in "LR" else "Center"
                    ax.add_patch(Rectangle((r['x1'], r['y1']), r['x2']-r['x1'], r['y2']-r['y1'],
                                          fill=False, edgecolor=color, lw=2.5))
                    ax.text(r['x1'], r['y1']-10, f"{label}\nEntries: {entry_counts[zone_key]}",
                            color=color, fontsize=10, fontweight='bold',
                            bbox=dict(facecolor='white', alpha=0.6))

                ax.set_title(f"Cage {cage_num} | Phase: {phase} | Target Entries: {e_target}")
                ax.invert_yaxis()

                all_results.append({
                    'FileName': filename, 'Group': group, 'Condition': condition,
                    'Phase': phase, 'Cage': cage_num,
                    'Left_Role': role_l,
                    'Right_Role': role_r,
                    'Left_Time_s': round(time_frames["L"] / FPS, 2),
                    'Right_Time_s': round(time_frames["R"] / FPS, 2),
                    'Left_Entries': entry_counts["L"],
                    'Right_Entries': entry_counts["R"],
                    'Target_Role': role_l if is_l_target else role_r,
                    'Control_Role': role_r if is_l_target else role_l,
                    'Target_Time_s': round(target_time_s, 2),
                    'Target_Entries': e_target,
                    'Control_Time_s': round(control_time_s, 2),
                    'Control_Entries': e_control,
                    'Center_Time_s': round(time_frames["Center"] / FPS, 2),
                    'Preference_Index': round(preference_index, 4)
                })

            plt.tight_layout()
            plt.savefig(os.path.join(OUTPUT_DIR, f"FullVisual_{filename}.png"), dpi=150)
            plt.close()

        except InvalidPoseCsvError as e:
            print(f"[ERROR] 输入 CSV 格式错误: {e}")
            raise
        except Exception as e:
            print(f"❌ Error {filename}: {e}")

    if all_results:
        pd.DataFrame(all_results).to_excel(
            os.path.join(SUMMARY_DIR, f"TCT_Complete_Data_{run_timestamp}.xlsx"), index=False)
        print(f"✅ 分析完毕！图片已存至: {OUTPUT_DIR}")
        print(f"✅ 汇总表已存至: {SUMMARY_DIR}")


if __name__ == "__main__":
    process_tct_full_visual()
