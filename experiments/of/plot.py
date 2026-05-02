import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import ttest_rel
import os
import re
import matplotlib as mpl
import glob

from config.paths import OF_SUMMARY, OF_FIGURES

# ==================== 1. Nature 规格配置 ====================
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial"],
    "font.size": 7,
    "axes.labelsize": 7,
    "xtick.labelsize": 6,
    "ytick.labelsize": 6,
    "axes.linewidth": 0.75,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.bbox": "tight",
})

# ==================== 2. 全局参数 ====================
FILE_PATH = str(OF_SUMMARY / "TCT_Complete_Data_0309_1439.xlsx")  # TODO: auto-find latest
OUTPUT_DIR = str(OF_FIGURES)

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# --- 颜色方案更新 ---
# Time图 (Toy/Live): 使用你上传图片中的绿色系
C_TIME_TOY = '#B8DBB3'    # 浅绿色
C_TIME_LIVE = '#72B063'   # 深绿色

# PI图 (Saline/CNO): 保持经典的灰色 + 蓝色
C_PI_GRAY = '#D1D1D1'     
C_PI_BLUE = '#4682B4'     

BAR_W = 0.6
POINT_SIZE = 12 

# 布局参数
GS_TOP = 0.72         
MAIN_TITLE_Y = 0.98   
LEGEND_Y = 0.91       
GROUP_TITLE_Y = 1.12  

def extract_mouse_id(filename):
    match = re.search(r'([a-zA-Z]+\d+-?\d?)', str(filename))
    return match.group(0).lower() if match else "unknown"

def get_star(p):
    if p < 0.001: return '***'
    if p < 0.01: return '**'
    if p < 0.05: return '*'
    return 'ns'

def plot_tct_green_palette(df, phase):
    df_p = df[df['Phase'] == phase].copy()
    df_p['MouseID'] = df_p['FileName'].apply(extract_mouse_id)
    df_p['PI'] = (df_p['Target_Time_s'] - df_p['Control_Time_s']) / (df_p['Target_Time_s'] + df_p['Control_Time_s'])
    
    l_lab, r_lab = ("Toy", "Live") if phase == "S" else ("Old", "New")
    fig = plt.figure(figsize=(180 / 25.4, 3.8))
    gs = fig.add_gridspec(1, 4, width_ratios=[1.2, 0.7, 1.2, 0.7], wspace=0.5, top=GS_TOP) 
    fig.suptitle(f"TCT ({phase} phase)", fontsize=8, fontweight='bold', y=MAIN_TITLE_Y)
    
    groups = sorted(df_p['Group'].str.lower().unique())
    group_display = {g: g[0].upper() + g[1:] for g in groups}

    for i, grp_name in enumerate(groups):
        data = df_p[df_p['Group'].str.lower() == grp_name]
        if data.empty: continue
        col_base = i * 2

        # --- 子图 1: Time (s) [浅绿 vs 深绿] ---
        ax1 = fig.add_subplot(gs[0, col_base])
        pos = [0, 0.8, 2.2, 3.0]
        current_handles = []
        
        for c_idx, c_name in enumerate(['saline', 'cno']):
            d = data[data['Condition'].str.lower() == c_name]
            if d.empty: continue
            vt, vc = d['Target_Time_s'].values, d['Control_Time_s'].values
            p_l, p_r = pos[c_idx*2], pos[c_idx*2+1]
            
            b1 = ax1.bar(p_l, vc.mean(), yerr=d['Control_Time_s'].sem(), color=C_TIME_TOY, edgecolor='black', width=BAR_W, capsize=1.5, lw=0.8, zorder=1)
            b2 = ax1.bar(p_r, vt.mean(), yerr=d['Target_Time_s'].sem(), color=C_TIME_LIVE, edgecolor='black', width=BAR_W, capsize=1.5, lw=0.8, zorder=1)
            
            if c_idx == 0: current_handles = [b1, b2]
            
            for j in range(len(vt)):
                ax1.plot([p_l, p_r], [vc[j], vt[j]], color='gray', alpha=0.3, lw=0.4, zorder=2)
                ax1.scatter(p_l, vc[j], color='black', s=POINT_SIZE, alpha=0.6, zorder=3, lw=0)
                ax1.scatter(p_r, vt[j], color='black', s=POINT_SIZE, alpha=0.6, zorder=3, lw=0)
            
            _, p_val = ttest_rel(vt, vc)
            mark = get_star(p_val)
            
            y_data_max = max(vt.max(), vc.max())
            ax1.set_ylim(0, y_data_max * 1.25)
            plt.draw()
            max_y_tick = ax1.get_yticks()[-1]
            ax1.set_ylim(0, max_y_tick)
            ax1.spines['left'].set_bounds(0, max_y_tick)

            line_y = y_data_max * 1.1
            ax1.plot([p_l, p_l, p_r, p_r], [line_y-max_y_tick*0.02, line_y, line_y, line_y-max_y_tick*0.02], color='black', lw=0.6)
            ax1.text((p_l+p_r)/2, line_y, mark, ha='center', va='bottom', fontsize=7)

        ax1.set_xticks([0.4, 2.6]); ax1.set_xticklabels(['Saline', 'CNO'])
        ax1.set_ylabel("Time (s)")
        sns.despine(ax=ax1)

        # 双图例
        leg_x_pos = 0.16 if i == 0 else 0.58
        fig.legend(current_handles, [l_lab, r_lab], loc='upper left', 
                   bbox_to_anchor=(leg_x_pos, LEGEND_Y), ncol=2, frameon=False, columnspacing=1.0)

        # --- 子图 2: PI [灰色 vs 蓝色] ---
        ax2 = fig.add_subplot(gs[0, col_base + 1])
        sal_pi = data[data['Condition'].str.lower() == 'saline']['PI']
        cno_pi = data[data['Condition'].str.lower() == 'cno']['PI']
        
        ax2.bar(0, sal_pi.mean(), yerr=sal_pi.sem(), color=C_PI_GRAY, edgecolor='black', width=BAR_W, capsize=1.5, lw=0.8)
        ax2.bar(0.8, cno_pi.mean(), yerr=cno_pi.sem(), color=C_PI_BLUE, edgecolor='black', width=BAR_W, capsize=1.5, lw=0.8)

        merged_pi = pd.merge(data[data['Condition'].str.lower() == 'saline'][['MouseID', 'PI']], 
                             data[data['Condition'].str.lower() == 'cno'][['MouseID', 'PI']], on='MouseID', suffixes=('_s', '_c'))
        for _, row in merged_pi.iterrows():
            ax2.plot([0, 0.8], [row['PI_s'], row['PI_c']], color='gray', alpha=0.3, lw=0.4, zorder=2)
            ax2.scatter(0, row['PI_s'], color='black', s=POINT_SIZE, alpha=0.6, zorder=3, lw=0)
            ax2.scatter(0.8, row['PI_c'], color='black', s=POINT_SIZE, alpha=0.6, zorder=3, lw=0)

        if not merged_pi.empty:
            _, p_pi = ttest_rel(merged_pi['PI_c'], merged_pi['PI_s'])
            mark_pi = get_star(p_pi)
            ax2.set_ylim(-1, 1.4) 
            line_y_pi = 1.15
            ax2.plot([0, 0, 0.8, 0.8], [line_y_pi-0.05, line_y_pi, line_y_pi, line_y_pi-0.05], color='black', lw=0.6)
            ax2.text(0.4, line_y_pi, mark_pi, ha='center', va='bottom', fontsize=7)

        ax2.spines['left'].set_bounds(-1, 1)
        ax2.axhline(0, color='black', lw=0.6, ls='--')
        ax2.set_ylabel("PI")
        ax2.set_xticks([0, 0.8]); ax2.set_xticklabels(['Saline', 'CNO'])
        sns.despine(ax=ax2)

        # 组标题
        name = group_display.get(grp_name, grp_name.upper())
        ax1.text(0.8, GROUP_TITLE_Y, name, transform=ax1.transAxes, ha='center', fontweight='bold', fontsize=7)
        ax1.annotate('', xy=(0.0, GROUP_TITLE_Y), xytext=(0.65, GROUP_TITLE_Y), xycoords='axes fraction', arrowprops=dict(arrowstyle='-', lw=0.6))
        ax1.annotate('', xy=(1.0, GROUP_TITLE_Y), xytext=(1.8, GROUP_TITLE_Y), xycoords='axes fraction', arrowprops=dict(arrowstyle='-', lw=0.6))

    plt.savefig(os.path.join(OUTPUT_DIR, f"TCT_Nature_Green_Blue_{phase}.pdf"))
    plt.show()

if __name__ == "__main__":
    raw_df = pd.read_excel(FILE_PATH)
    for p in ['S', 'N']: plot_tct_green_palette(raw_df, p)