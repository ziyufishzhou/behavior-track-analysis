import pandas as pd
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap
import os
import glob
from datetime import datetime
from scipy.ndimage import gaussian_filter

from config.paths import TCT_CSV_DIR, TCT_ROI_JSON, TCT_HEAT_TRACING
from preprocessing.metadata_utils import load_metadata, get_labels

# ================= 配置区 =================
CSV_DIR = str(TCT_CSV_DIR)
ROI_JSON_PATH = str(TCT_ROI_JSON)
OUTPUT_DIR = str(TCT_HEAT_TRACING)
FPS = 30
ANALYSIS_MINUTES = 10
LIKELIHOOD_THRESHOLD = 0.6
# ==========================================

# 定义热图颜色：从白到蓝到黄到红
custom_cmap = LinearSegmentedColormap.from_list('heat', ['white', 'blue', 'yellow', 'red'])

def load_roi_data(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        roi_data = json.load(f)
    return {r['name']: r for r in roi_data['regions']}

def get_chamber_roles(filename):
    phase = "N" if "N" in filename else "S"
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
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    regions = load_roi_data(ROI_JSON_PATH)
    frames_limit = ANALYSIS_MINUTES * 60 * FPS
    csv_files = glob.glob(os.path.join(CSV_DIR, "**", "*.csv"), recursive=True)
    
    all_results = []
    run_timestamp = datetime.now().strftime("%m%d_%H%M")
    metadata_df = load_metadata()

    for csv_path in csv_files:
        filename = os.path.basename(csv_path)
        path_lower = csv_path.lower()
        group, condition = get_labels(filename, path_lower, metadata_df)
        phase, role_l, role_r = get_chamber_roles(filename)
        
        try:
            df_raw = pd.read_csv(csv_path, skiprows=3, header=None, low_memory=False)
            df_raw = df_raw.head(frames_limit).apply(pd.to_numeric, errors='coerce')

            fig, axes = plt.subplots(4, 1, figsize=(12, 24))
            
            for idx, cage_num in enumerate(["1", "2", "3", "4"]):
                ax = axes[idx]
                prefix = f"{cage_num}_"
                if f"{prefix}L" not in regions: continue
                
                base_col = 1 + (idx * 9) + 3 
                vx, vy, vp = df_raw.iloc[:, base_col].values, df_raw.iloc[:, base_col+1].values, df_raw.iloc[:, base_col+2].values
                mask = (~np.isnan(vp)) & (vp > LIKELIHOOD_THRESHOLD)
                mx, my = vx[mask], vy[mask]
                
                if len(mx) < 2: continue

                # 统计逻辑
                time_frames = {"L": 0, "Center": 0, "R": 0}
                entry_counts = {"L": 0, "Center": 0, "R": 0}
                last_zone = None
                
                roi_l, roi_c, roi_r = regions[f"{prefix}L"], regions[f"{prefix}Center"], regions[f"{prefix}R"]
                
                for i in range(len(vx)):
                    if not mask[i]: continue
                    cx, cy = vx[i], vy[i]
                    curr_zone = None
                    if (roi_l['x1'] <= cx <= roi_l['x2']) and (roi_l['y1'] <= cy <= roi_l['y2']): curr_zone = "L"
                    elif (roi_c['x1'] <= cx <= roi_c['x2']) and (roi_c['y1'] <= cy <= roi_c['y2']): curr_zone = "Center"
                    elif (roi_r['x1'] <= cx <= roi_r['x2']) and (roi_r['y1'] <= cy <= roi_r['y2']): curr_zone = "R"
                    
                    if curr_zone:
                        time_frames[curr_zone] += 1
                        if curr_zone != last_zone: entry_counts[curr_zone] += 1
                    last_zone = curr_zone

                # 角色分配
                is_l_target = (role_l in ["Live", "New_Friend"])
                e_target = entry_counts["L"] if is_l_target else entry_counts["R"]
                e_control = entry_counts["R"] if is_l_target else entry_counts["L"]

                # --- 1. 绘制底层热图 ---
                extent = [roi_l['x1']-50, roi_r['x2']+50, min(my)-50, max(my)+50]
                heatmap, xedges, yedges = np.histogram2d(mx, my, bins=100, range=[[extent[0], extent[1]], [extent[2], extent[3]]])
                ax.imshow(gaussian_filter(heatmap.T, 1.5), extent=extent, origin='lower', cmap=custom_cmap, interpolation='gaussian', alpha=0.8, aspect='auto')

                # --- 2. 绘制轨迹线 ---
                ax.plot(mx, my, color='black', lw=0.6, alpha=0.4)

                # --- 3. 绘制 ROI 框并标注进入次数 ---
                for r_k, color, label in [(f"{prefix}L", "red", role_l), (f"{prefix}Center", "green", "Center"), (f"{prefix}R", "blue", role_r)]:
                    r = regions[r_k]
                    zone_key = r_k[-1] if r_k[-1] in "LR" else "Center"
                    ax.add_patch(Rectangle((r['x1'], r['y1']), r['x2']-r['x1'], r['y2']-r['y1'], fill=False, edgecolor=color, lw=2.5))
                    ax.text(r['x1'], r['y1']-10, f"{label}\nEntries: {entry_counts[zone_key]}", color=color, fontsize=10, fontweight='bold', bbox=dict(facecolor='white', alpha=0.6))

                ax.set_title(f"Cage {cage_num} | Phase: {phase} | Target Entries: {e_target}")
                ax.invert_yaxis()

                all_results.append({
                    'FileName': filename, 'Group': group, 'Condition': condition, 'Phase': phase, 'Cage': cage_num,
                    'Target_Time_s': round((time_frames["L"] if is_l_target else time_frames["R"])/FPS, 2),
                    'Target_Entries': e_target,
                    'Control_Time_s': round((time_frames["R"] if is_l_target else time_frames["L"])/FPS, 2),
                    'Control_Entries': e_control,
                    'Center_Time_s': round(time_frames["Center"]/FPS, 2)
                })

            plt.tight_layout()
            plt.savefig(os.path.join(OUTPUT_DIR, f"FullVisual_{filename}.png"), dpi=150)
            plt.close()

        except Exception as e: print(f"Error processing {filename}: {e}")

    if all_results:
        pd.DataFrame(all_results).to_excel(os.path.join(OUTPUT_DIR, f"TCT_Complete_Data_{run_timestamp}.xlsx"), index=False)
        print(f"📊 分析完毕！热图轨迹图与 Excel 统计已保存至：{OUTPUT_DIR}")

if __name__ == "__main__":
    process_tct_full_visual()