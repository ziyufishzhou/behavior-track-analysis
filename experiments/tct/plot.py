"""TCT 三箱社交实验绘图 — 自定义双图布局 (Time + PI)"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import ttest_rel

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from config.paths import TCT_SUMMARY, TCT_FIGURES
from gui.utils import find_latest_summary
from plotting.rc_params import apply_cns_style, figure_size_mm
from plotting.palettes import get_palette
from plotting.chart_types import ChartConfig
from plotting.statistics import auto_test
from plotting.significance import draw_significance_bracket, compute_bracket_y
from plotting.utils import extract_mouse_id, get_star


def _sem(values):
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]
    if len(values) < 2:
        return 0
    return np.std(values, ddof=1) / np.sqrt(len(values))


def plot_tct(df, phase, chart_type="bar", palette_name="nature_classic",
             colors=None, bar_width=0.6, bar_gap=0.2, point_size=18,
             errorbar="sem", alpha=0.05, force_test="",
             title="", fill_alpha=0.7, edge_width=0.8, edge_color="",
             font_size=7, line_width=1.0, figure_width_mm=180,
             pdf=True, png=False, dpi=300, output_dir=None):
    """TCT 绘图 — Time + PI 双图布局"""
    out_dir = output_dir or str(TCT_FIGURES)
    apply_cns_style()

    pal = get_palette(palette_name)
    palette_colors = list(pal.colors)
    scatter_color = pal.scatter
    connect_color = pal.connect
    edge_c = pal.edge

    if colors:
        if 'color_0' in colors: palette_colors[0] = colors['color_0']
        if 'color_1' in colors and len(palette_colors) > 1: palette_colors[1] = colors['color_1']
        scatter_color = colors.get('scatter', scatter_color)
        connect_color = colors.get('connect', connect_color)
        edge_c = colors.get('edge', edge_c)

    # TCT 特殊颜色
    c_toy = palette_colors[0]
    c_live = palette_colors[1]

    df_p = df[df['Phase'] == phase].copy()
    df_p['MouseID'] = df_p['FileName'].apply(extract_mouse_id)
    df_p['Condition'] = df_p['Condition'].astype(str).str.lower().str.strip()
    df_p['Group'] = df_p['Group'].astype(str).str.strip()
    if 'Preference_Index' in df_p.columns:
        df_p['PI'] = df_p['Preference_Index']
    else:
        df_p['PI'] = (df_p['Target_Time_s'] - df_p['Control_Time_s']) / (
            df_p['Target_Time_s'] + df_p['Control_Time_s'])

    l_lab, r_lab = ("Toy", "Live") if phase == "S" else ("Old", "New")
    fig = plt.figure(figsize=figure_size_mm(figure_width_mm, 80))
    gs = fig.add_gridspec(1, 4, width_ratios=[1.2, 0.7, 1.2, 0.7], wspace=0.5, top=0.72)
    fig.suptitle(f"TCT ({phase} phase)", fontsize=8, fontweight='bold', y=0.98)

    groups = sorted(df_p['Group'].str.lower().unique())
    all_stats = []

    for i, grp_name in enumerate(groups):
        data = df_p[df_p['Group'].str.lower() == grp_name]
        if data.empty:
            continue
        col_base = i * 2
        display_name = grp_name[0].upper() + grp_name[1:]

        # ── 子图 1: Time (s) ──
        ax1 = fig.add_subplot(gs[0, col_base])
        pos = [0, 0.8, 2.2, 3.0]
        current_handles = []

        for c_idx, c_name in enumerate(['saline', 'cno']):
            d = data[data['Condition'] == c_name]
            if d.empty:
                continue
            vt, vc = d['Target_Time_s'].values, d['Control_Time_s'].values
            p_l, p_r = pos[c_idx * 2], pos[c_idx * 2 + 1]

            b1 = ax1.bar(p_l, vc.mean(), yerr=_sem(vc), color=c_toy,
                         edgecolor=edge_c, width=bar_width, capsize=1.5,
                         lw=edge_width, alpha=fill_alpha, zorder=1)
            b2 = ax1.bar(p_r, vt.mean(), yerr=_sem(vt), color=c_live,
                         edgecolor=edge_c, width=bar_width, capsize=1.5,
                         lw=edge_width, alpha=fill_alpha, zorder=1)

            if c_idx == 0:
                current_handles = [b1, b2]

            for j in range(len(vt)):
                ax1.plot([p_l, p_r], [vc[j], vt[j]], color=connect_color, alpha=0.3, lw=0.4, zorder=2)
                ax1.scatter(p_l, vc[j], color=scatter_color, s=point_size, alpha=0.8, zorder=3, lw=0)
                ax1.scatter(p_r, vt[j], color=scatter_color, s=point_size, alpha=0.8, zorder=3, lw=0)

            # 配对 t-test (toy vs live)
            result = auto_test(vc, vt, paired=True, alpha=alpha, force_test=force_test)
            mark = result.star_label
            y_data_max = max(vt.max(), vc.max())
            ax1.set_ylim(0, y_data_max * 1.25)
            plt.draw()
            max_y_tick = ax1.get_yticks()[-1]
            ax1.set_ylim(0, max_y_tick)
            line_y = y_data_max * 1.1
            draw_significance_bracket(ax1, p_l, p_r, line_y, mark)

            all_stats.append({
                'group': display_name, 'condition': c_name,
                'metric': f'{l_lab} vs {r_lab} Time',
                'test': result.test_name, 'p': round(result.p_value, 4),
                'star': result.star_label,
                'effect_size': round(result.effect_size, 3) if result.effect_size else None,
                'effect_name': result.effect_name,
            })

        ax1.set_xticks([0.4, 2.6])
        ax1.set_xticklabels(['Saline', 'CNO'])
        ax1.set_ylabel("Time (s)")
        sns.despine(ax=ax1)

        # 图例
        leg_x = 0.16 if i == 0 else 0.58
        fig.legend(current_handles, [l_lab, r_lab], loc='upper left',
                   bbox_to_anchor=(leg_x, 0.91), ncol=2, frameon=False, columnspacing=1.0)

        # ── 子图 2: PI ──
        ax2 = fig.add_subplot(gs[0, col_base + 1])
        sal_pi = data[data['Condition'] == 'saline']['PI']
        cno_pi = data[data['Condition'] == 'cno']['PI']

        ax2.bar(0, sal_pi.mean(), yerr=sal_pi.sem(), color=palette_colors[0],
                edgecolor=edge_c, width=bar_width, capsize=1.5, lw=edge_width, alpha=fill_alpha)
        ax2.bar(0.8, cno_pi.mean(), yerr=cno_pi.sem(), color=palette_colors[1],
                edgecolor=edge_c, width=bar_width, capsize=1.5, lw=edge_width, alpha=fill_alpha)

        merged = pd.merge(
            data[data['Condition'] == 'saline'][['MouseID', 'PI']],
            data[data['Condition'] == 'cno'][['MouseID', 'PI']],
            on='MouseID', suffixes=('_s', '_c'))
        for _, row in merged.iterrows():
            ax2.plot([0, 0.8], [row['PI_s'], row['PI_c']], color=connect_color, alpha=0.3, lw=0.4, zorder=2)
            ax2.scatter(0, row['PI_s'], color=scatter_color, s=point_size, alpha=0.8, zorder=3, lw=0)
            ax2.scatter(0.8, row['PI_c'], color=scatter_color, s=point_size, alpha=0.8, zorder=3, lw=0)

        if not merged.empty:
            result = auto_test(merged['PI_s'].values, merged['PI_c'].values,
                               paired=True, alpha=alpha, force_test=force_test)
            ax2.set_ylim(-1, 1.4)
            draw_significance_bracket(ax2, 0, 0.8, 1.15, result.star_label)

            all_stats.append({
                'group': display_name, 'metric': 'PI',
                'test': result.test_name, 'p': round(result.p_value, 4),
                'star': result.star_label,
                'effect_size': round(result.effect_size, 3) if result.effect_size else None,
                'effect_name': result.effect_name,
            })

        ax2.axhline(0, color='black', lw=0.6, ls='--')
        ax2.set_ylabel("PI")
        ax2.set_xticks([0, 0.8])
        ax2.set_xticklabels(['Saline', 'CNO'])
        sns.despine(ax=ax2)

        # 组标题
        ax1.text(0.5, 1.12, display_name, transform=ax1.transAxes,
                 ha='center', fontweight='bold', fontsize=7)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    basename = f"TCT_Palette_Final_{phase}"
    if pdf:
        plt.savefig(os.path.join(out_dir, f"{basename}.pdf"), dpi=dpi)
    if png:
        plt.savefig(os.path.join(out_dir, f"{basename}.png"), dpi=dpi)
    if not pdf and not png:
        plt.savefig(os.path.join(out_dir, f"{basename}.pdf"), dpi=dpi)
    plt.close()

    # 保存统计结果
    import json
    stats_path = os.path.join(out_dir, f"{basename}_stats.json")
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(all_stats, f, ensure_ascii=False, indent=2)

    print(f"TCT ({phase}) 图表已保存至: {out_dir}")
    return all_stats


plot_tct_new_palette = plot_tct


if __name__ == "__main__":
    summary_path = find_latest_summary(str(TCT_SUMMARY), "TCT_Complete_Data")
    if not summary_path:
        print("未找到 TCT 汇总文件")
        sys.exit(1)
    df = pd.read_excel(summary_path)
    for p in ['S', 'N']:
        plot_tct(df, p)
