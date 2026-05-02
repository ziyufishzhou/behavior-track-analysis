import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import ttest_rel, shapiro, wilcoxon
import matplotlib as mpl
import os
import re
import glob

from config.paths import EPM_SUMMARY, EPM_FIGURES

# ==================== 1. 规格参数 ====================
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica"],
    "font.size": 7,
    "axes.labelsize": 7,
    "xtick.labelsize": 6,
    "ytick.labelsize": 6,
    "axes.linewidth": 0.75,
    "lines.linewidth": 1.0,
    "pdf.fonttype": 42,
    "savefig.bbox": "tight",
    "xtick.minor.visible": False,
    "ytick.minor.visible": False
})

# ==================== 2. 美化参数 ====================
MAIN_TITLE = "EPM (Elevated Plus Maze)"
TOTAL_TIME_S = 900 
# 颜色修正：Saline灰，CNO蓝
BAR_COLORS = ['#D1D1D1', '#4682B4'] 

# 标题装饰线位置
TOP_LINE_Y = [0.91, 0.38]
LINE_START, LINE_END = 0.15, 0.85
TEXT_GAP = 0.08

BAR_WIDTH = 0.6
POINT_SIZE = 18

# ==================== 3. 功能函数 ====================
def extract_mouse_id(filename):
    match = re.search(r'([a-zA-Z]+\d+-?\d?)', str(filename))
    return match.group(0).lower().replace(" ", "") if match else "unknown"

def run_statistics(paired_df):
    g_saline, g_cno = paired_df['saline'], paired_df['cno']
    diff = g_cno - g_saline
    if len(paired_df) < 2: return None
    try:
        _, p_norm = shapiro(diff) if len(paired_df) >= 3 else (0, 1.0)
        p_val = ttest_rel(g_saline, g_cno)[1] if p_norm > 0.05 else wilcoxon(g_saline, g_cno)[1]
    except: p_val = ttest_rel(g_saline, g_cno)[1]
    return p_val

# ==================== 4. 绘图逻辑 ====================
FILE_PATH = str(EPM_SUMMARY / "EPM_Summary_with_Dist_0309_1412.xlsx")  # TODO: auto-find latest
OUTPUT_DIR = str(EPM_FIGURES)

df = pd.read_excel(FILE_PATH)
df['MouseID'] = df['FileName'].apply(extract_mouse_id)
df['Maze_Clean'] = df['Maze'].astype(str).str.lower().str.strip()
df['UniqueID'] = df['MouseID'] + "_" + df['Maze_Clean']
df['Condition'] = df['Condition'].str.lower().str.strip() # 强制小写防止 Key 找不到
df['OA_Percent'] = (df['OA_Time_s'] / TOTAL_TIME_S) * 100
df['Group'] = df['Group'].str.strip() # 保持原始录入，不强行转大写

metrics = [
    ('OA_Time_s', 'Open Arm Time (s)'),
    ('OA_Percent', 'Open Arm Time (%)'),
    ('OA_Entries', 'Open Arm Entries')
]

# 这里对应你手动修改后的名称
target_groups = sorted(df['Group'].str.strip().unique())

fig, axes = plt.subplots(len(target_groups), 3, figsize=(89/25.4, 6.2))
plt.subplots_adjust(wspace=0.6, hspace=1.4)
fig.text(0.5, 0.97, MAIN_TITLE, ha='center', va='center', fontsize=8, fontweight='bold')

for row_idx, group_name in enumerate(target_groups):
    # 过滤数据：不分大小写匹配组名
    sub_df = df[df['Group'].str.lower() == group_name.lower()].copy()
    
    # --- 绘制【横线-文字-横线】装饰 ---
    y_pos = TOP_LINE_Y[row_idx]
    mid_x = 0.5
    fig.add_artist(plt.Line2D([LINE_START, mid_x-TEXT_GAP], [y_pos, y_pos], color='black', lw=0.75, transform=fig.transFigure))
    fig.text(mid_x, y_pos, group_name, ha='center', va='center', fontsize=7, fontweight='bold', transform=fig.transFigure)
    fig.add_artist(plt.Line2D([mid_x+TEXT_GAP, LINE_END], [y_pos, y_pos], color='black', lw=0.75, transform=fig.transFigure))

    for col_idx, (col, label) in enumerate(metrics):
        ax = axes[row_idx, col_idx]
        
        # 透视表逻辑：增加防崩溃检查
        pivot = sub_df.pivot_table(index='UniqueID', columns='Condition', values=col)
        
        # 核心修正：确保 saline 和 cno 列都存在且不是空的
        if 'saline' not in pivot.columns or 'cno' not in pivot.columns:
            ax.axis('off')
            continue
            
        pivot = pivot.dropna(subset=['saline', 'cno'])
        if pivot.empty: 
            ax.axis('off')
            continue

        # 1. 柱状图：Saline(灰)在左，CNO(蓝)在右
        sns.barplot(data=sub_df[sub_df['UniqueID'].isin(pivot.index)], 
                    x='Condition', y=col, order=['saline', 'cno'], ax=ax,
                    palette=BAR_COLORS, alpha=0.7, width=BAR_WIDTH, errorbar='se', 
                    capsize=.15, edgecolor='black', linewidth=0.8, hue='Condition', 
                    hue_order=['saline', 'cno'], legend=False)

        # 2. 配对连线
        for idx in pivot.index:
            pts = pivot.loc[idx, ['saline', 'cno']]
            ax.plot([0, 1], pts, color='#4D4D4D', lw=0.5, alpha=0.3)
            ax.scatter([0, 1], pts, color='black', s=POINT_SIZE, alpha=0.8, edgecolors='none')

        # 3. Y 轴定格与刻度方向
        ax.set_ylim(0, None)
        plt.draw() 
        yticks = ax.get_yticks()
        y_data_max = pivot.values.max()
        max_tick = yticks[yticks >= y_data_max * 1.1][0] if any(yticks >= y_data_max * 1.1) else yticks[-1]
        
        ax.set_ylim(0, max_tick)
        ax.spines['left'].set_bounds(0, max_tick) # Y轴定格
        
        ax.tick_params(axis='y', direction='out', length=3) # Y轴向外
        ax.tick_params(axis='x', direction='in', length=3)  # X轴刻度向上
        
        # 4. 统计与显著性
        p_val = run_statistics(pivot)
        star = 'ns'
        if p_val is not None and p_val < 0.05:
            star = '***' if p_val < 0.001 else '**' if p_val < 0.01 else '*'
        
        line_y = max_tick * 0.9
        ax.plot([0, 0, 1, 1], [line_y, line_y + max_tick*0.02, line_y + max_tick*0.02, line_y], color='black', lw=0.7)
        ax.text(0.5, line_y + max_tick*0.02, star, ha='center', va='bottom', fontsize=6)

        ax.set_ylabel(label)
        ax.set_xlabel("")
        ax.set_xticklabels(['Saline', 'CNO'])
        sns.despine(ax=ax, trim=False) # X轴自然突出

# 保存
if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
plt.savefig(os.path.join(OUTPUT_DIR, "EPM_Standard_Final.pdf"))
plt.show()