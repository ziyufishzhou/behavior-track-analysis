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

from config.paths import EPM_CSV_DIR, EPM_ROI_JSON, EPM_TRACING_HEAT
from preprocessing.metadata_utils import load_metadata, get_labels

# ================= 配置区 =================
CSV_DIR = str(EPM_CSV_DIR)
ROI_JSON_PATH = str(EPM_ROI_JSON)
OUTPUT_DIR = str(EPM_TRACING_HEAT)
FPS = 30
ANALYSIS_MINUTES = 15
LIKELIHOOD_THRESHOLD = 0.6
# ==========================================

custom_cmap = LinearSegmentedColormap.from_list('heat', ['white', 'blue', 'yellow', 'red'])

def load_roi_data(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        roi_data = json.load(f)
    regions = {}
    for r in roi_data['regions']:
        name = r['name'].replace('cage11', 'cage1') 
        regions[name] = r
    return regions

def is_in_box(x, y, roi):
    return (x >= roi['x1']) and (x <= roi['x2']) and (y >= roi['y1']) and (y <= roi['y2'])

def process_epm_with_distance():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    regions = load_roi_data(ROI_JSON_PATH)
    frames_to_analyze = ANALYSIS_MINUTES * 60 * FPS
    csv_files = glob.glob(os.path.join(CSV_DIR, "**", "*.csv"), recursive=True)
    
    all_summary_results = []
    run_timestamp = datetime.now().strftime("%m%d_%H%M")
    metadata_df = load_metadata()

    print(f"\n🚀 EPM 分析启动 | 包含移动像素统计 | 目标时长: {ANALYSIS_MINUTES}min")
    print("-" * 60)

    for csv_path in csv_files:
        filename = os.path.basename(csv_path)
        path_lower = csv_path.lower()
        group_tag, condition_tag = get_labels(filename, path_lower, metadata_df)
        
        try:
            df_raw = pd.read_csv(csv_path, skiprows=3, header=None, low_memory=False)
            df_raw = df_raw.apply(pd.to_numeric, errors='coerce')

            plt.close('all') 
            fig, axes = plt.subplots(1, 2, figsize=(16, 8))
            
            for idx, prefix in enumerate(["cage1", "cage2"]):
                ax = axes[idx]
                current_rois = {k: v for k, v in regions.items() if k.startswith(prefix)}
                center_key = f"{prefix}_center_zone"
                center_roi = current_rois.get(center_key)
                
                if not current_rois or center_roi is None:
                    continue

                base_col = 1 + (idx * 9) + 3 
                col_x, col_y, col_p = base_col, base_col + 1, base_col + 2

                # 寻找触发帧
                trigger_frame = None
                for i in range(len(df_raw)):
                    tx, ty, tp = df_raw.iloc[i, [col_x, col_y, col_p]]
                    if tp > LIKELIHOOD_THRESHOLD and is_in_box(tx, ty, center_roi):
                        trigger_frame = i
                        break
                
                if trigger_frame is None:
                    print(f"⚠️ {filename} | {prefix}: [未触发]")
                    vx, vy = [], []
                else:
                    print(f"✅ {filename} | {prefix}: [{group_tag}-{condition_tag}] 触发于 {trigger_frame/FPS:.1f}s")
                    df = df_raw.iloc[trigger_frame : trigger_frame + frames_to_analyze].reset_index(drop=True)
                    x_all, y_all, p_all = df[col_x].values, df[col_y].values, df[col_p].values
                    valid_mask = (~np.isnan(p_all)) & (p_all > LIKELIHOOD_THRESHOLD)
                    vx, vy = x_all[valid_mask], y_all[valid_mask]

                    # --- 核心统计逻辑 (新增 Distance_px) ---
                    total_dist_px = 0.0
                    time_stats = {"Open": 0, "Closed": 0, "Center": 0}
                    entry_stats = {"Open": 0, "Closed": 0, "Center": 0}
                    last_zone = None
                    last_pos = None

                    for i in range(len(df)):
                        if not valid_mask[i]:
                            last_pos = None
                            continue
                        
                        cx, cy = x_all[i], y_all[i]

                        # 1. 计算移动距离 (像素点)
                        if last_pos is not None:
                            d = np.sqrt((cx - last_pos[0])**2 + (cy - last_pos[1])**2)
                            if d < 150: # 过滤异常跳变
                                total_dist_px += d
                        last_pos = (cx, cy)
                        
                        # 2. 区域判定
                        if is_in_box(cx, cy, center_roi):
                            fz = "Center"
                        else:
                            fz = "Other"
                            for rn, rv in current_rois.items():
                                if "open" in rn.lower() and is_in_box(cx, cy, rv): fz = "Open"; break
                                if "close" in rn.lower() and is_in_box(cx, cy, rv): fz = "Closed"; break
                        
                        if fz in time_stats:
                            time_stats[fz] += 1
                            if fz != last_zone: entry_stats[fz] += 1
                        last_zone = fz

                    # 存储结果
                    all_summary_results.append({
                        'FileName': filename, 
                        'Maze': prefix, 
                        'Group': group_tag, 
                        'Condition': condition_tag,
                        'Trigger_s': round(trigger_frame/FPS, 2),
                        'Distance_px': round(total_dist_px, 1), # <-- 新增字段
                        'OA_Time_s': round(time_stats["Open"]/FPS, 2), 
                        'OA_Entries': entry_stats["Open"],
                        'CA_Time_s': round(time_stats["Closed"]/FPS, 2), 
                        'CA_Entries': entry_stats["Closed"],
                        'Center_Time_s': round(time_stats["Center"]/FPS, 2)
                    })

                    # 绘图逻辑 (热图+轨迹)
                    if len(vx) > 0:
                        all_rx = [v['x1'] for v in current_rois.values()] + [v['x2'] for v in current_rois.values()]
                        all_ry = [v['y1'] for v in current_rois.values()] + [v['y2'] for v in current_rois.values()]
                        extent = [min(all_rx)-20, max(all_rx)+20, min(all_ry)-20, max(all_ry)+20]

                        heatmap, xedges, yedges = np.histogram2d(vx, vy, bins=60, range=[[extent[0], extent[1]], [extent[2], extent[3]]])
                        heatmap = gaussian_filter(heatmap, sigma=1.2)
                        ax.imshow(heatmap.T, extent=extent, origin='lower', cmap=custom_cmap, interpolation='gaussian', alpha=0.7, aspect='auto')
                        ax.plot(vx, vy, color='gray', alpha=0.3, lw=0.6)

                # 绘制 ROI 框
                for r_name, r_val in current_rois.items():
                    c = 'cyan' if 'center' in r_name else ('green' if 'open' in r_name else 'red')
                    ax.add_patch(Rectangle((r_val['x1'], r_val['y1']), r_val['x2']-r_val['x1'], r_val['y2']-r_val['y1'], fill=False, edgecolor=c, lw=2))
                
                ax.set_title(f"{prefix} ({group_tag}-{condition_tag})\nDist: {total_dist_px:.0f}px")
                ax.invert_yaxis()

            plt.tight_layout()
            plt.savefig(os.path.join(OUTPUT_DIR, f"Result_{filename}.png"), dpi=200)
            plt.close()

        except Exception as e:
            print(f"❌ 运行报错 {filename}: {e}")

    if all_summary_results:
        summary_df = pd.DataFrame(all_summary_results)
        save_path = os.path.join(OUTPUT_DIR, f"EPM_Summary_with_Dist_{run_timestamp}.xlsx")
        summary_df.to_excel(save_path, index=False)
        print(f"\n📊 统计完毕！Distance_px 已存入 Excel: {save_path}")

if __name__ == "__main__":
    process_epm_with_distance()