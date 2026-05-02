import pandas as pd
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import os
import glob
from datetime import datetime

from config.paths import OF_CSV_DIR, OF_ROI_JSON, OF_TRACING_HEAT
from preprocessing.metadata_utils import load_metadata, get_labels

# ================= 配置区 =================
CSV_DIR = str(OF_CSV_DIR)
ROI_JSON_PATH = str(OF_ROI_JSON)
OUTPUT_DIR = str(OF_TRACING_HEAT)
FPS = 30
ANALYSIS_MINUTES = 15
LIKELIHOOD_THRESHOLD = 0.1
ARENA_SIZE_CM = 50.0  # 旷场实际边长 (cm)
# ==========================================

def load_roi_data(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        roi_data = json.load(f)
    return {r['name']: r for r in roi_data['regions']}

def process_all():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    regions = load_roi_data(ROI_JSON_PATH)
    limit_frames = ANALYSIS_MINUTES * 60 * FPS
    csv_files = glob.glob(os.path.join(CSV_DIR, "**", "*.csv"), recursive=True)
    
    if not csv_files:
        print(f"❌ 未找到 CSV 文件，请检查路径: {CSV_DIR}")
        return

    all_summary_results = []
    run_timestamp = datetime.now().strftime("%m%d_%H%M")
    metadata_df = load_metadata()

    for csv_path in csv_files:
        filename = os.path.basename(csv_path)
        path_lower = csv_path.lower()
        group_tag, condition_tag = get_labels(filename, path_lower, metadata_df)

        print(f"正在分析: [{group_tag}-{condition_tag}] {filename}")
        
        try:
            # 读取 DLC 数据
            df = pd.read_csv(csv_path, skiprows=3, header=None, low_memory=False)
            if len(df) > limit_frames:
                df = df.head(limit_frames)
            df = df.apply(pd.to_numeric, errors='coerce')

            plt.close('all') 
            fig, axes = plt.subplots(4, 2, figsize=(15, 24)) 
            axes = axes.flatten()
            
            for i in range(4):
                # 轨迹图位置: 0,1,2,3 | 热图位置: 4,5,6,7
                ax_traj, ax_heat = axes[i], axes[i+4]
                cage_num = i + 1
                
                # DLC 列索引 (x, y, likelihood)
                col_x, col_y, col_l = 4 + (i * 9), 5 + (i * 9), 6 + (i * 9)
                
                # 适配你的 JSON 命名: cage1 和 cage1_center_1_4
                cage_key = f"cage{cage_num}"
                center_key = f"cage{cage_num}_center_1_4"
                
                if cage_key not in regions or center_key not in regions:
                    continue
                
                c_roi, ct_roi = regions[cage_key], regions[center_key]

                # 换算比例尺 (cm/px)
                pixel_width = c_roi['x2'] - c_roi['x1']
                px_to_cm = ARENA_SIZE_CM / pixel_width

                # 提取有效坐标
                coords = df[[col_x, col_y, col_l]].values
                valid_mask = (~np.isnan(coords[:, 2])) & (coords[:, 2] > LIKELIHOOD_THRESHOLD)
                vx, vy = coords[valid_mask, 0], coords[valid_mask, 1]
                
                if len(vx) < 10: continue

                # 1. 距离计算
                dist_px = np.sum(np.sqrt(np.diff(vx)**2 + np.diff(vy)**2))
                dist_cm = dist_px * px_to_cm
                
                # 2. 中心区域判断
                in_c = (vx >= ct_roi['x1']) & (vx <= ct_roi['x2']) & \
                       (vy >= ct_roi['y1']) & (vy <= ct_roi['y2'])
                
                all_summary_results.append({
                    'Group': group_tag, 'Condition': condition_tag, 'FileName': filename,
                    'Cage': cage_key, 'Total_Distance_px': round(dist_px, 2),
                    'Total_Distance_cm': round(dist_cm, 2),
                    'Center_Time_s': round(np.sum(in_c) / FPS, 2),
                    'Entries': int(np.sum((in_c[:-1] == False) & (in_c[1:] == True)))
                })

                # --- 绘制轨迹图 ---
                # 底色轨迹 (灰色)
                ax_traj.plot(vx, vy, color='gray', alpha=0.3, linewidth=0.8, zorder=1)
                
                # 【新增】中心区域轨迹标红
                vx_red, vy_red = vx.copy(), vy.copy()
                vx_red[~in_c] = np.nan
                vy_red[~in_c] = np.nan
                ax_traj.plot(vx_red, vy_red, color='red', linewidth=1.2, alpha=0.9, zorder=2)

                # 画外框 (蓝色) 和 中心框 (红色)
                ax_traj.add_patch(Rectangle((c_roi['x1'], c_roi['y1']), c_roi['x2']-c_roi['x1'], 
                                            c_roi['y2']-c_roi['y1'], fill=False, edgecolor='blue', lw=1))
                ax_traj.add_patch(Rectangle((ct_roi['x1'], ct_roi['y1']), ct_roi['x2']-ct_roi['x1'], 
                                            ct_roi['y2']-ct_roi['y1'], fill=False, edgecolor='red', lw=1.5))
                
                ax_traj.set_title(f"Cage {cage_num} (Dist: {round(dist_cm/100, 2)}m)")
                ax_traj.invert_yaxis()

                # --- 绘制热图 ---
                hb = ax_heat.hist2d(vx, vy, bins=50, cmap='jet', 
                                    range=[[c_roi['x1'], c_roi['x2']], [c_roi['y1'], c_roi['y2']]])
                
                # 热图也加上中心红框 (白色虚线避免遮挡)
                ax_heat.add_patch(Rectangle((ct_roi['x1'], ct_roi['y1']), ct_roi['x2']-ct_roi['x1'], 
                                            ct_roi['y2']-ct_roi['y1'], fill=False, edgecolor='white', lw=1.5, ls='--'))
                
                ax_heat.set_title(f"Cage {cage_num} Heatmap")
                ax_heat.invert_yaxis()
                plt.colorbar(hb[3], ax=ax_heat, fraction=0.046, pad=0.04)

            plt.tight_layout()
            save_name = f"{group_tag}_{condition_tag}_{os.path.splitext(filename)[0]}_15min.png"
            plt.savefig(os.path.join(OUTPUT_DIR, save_name), dpi=100)
            plt.close()
            
        except Exception as e:
            print(f"❌ 出错 {filename}: {e}")

    if all_summary_results:
        res_df = pd.DataFrame(all_summary_results)
        res_df.to_excel(os.path.join(OUTPUT_DIR, f"Summary_15min_{run_timestamp}.xlsx"), index=False)
        print(f"✅ 处理完成！统计表和图片已存至: {OUTPUT_DIR}")

if __name__ == "__main__":
    process_all()