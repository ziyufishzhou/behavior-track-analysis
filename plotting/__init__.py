"""Prism 风格绘图系统 — plot_experiment() 通用入口"""
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from plotting.rc_params import apply_cns_style, figure_size_mm
from plotting.palettes import get_palette, Palette
from plotting.chart_types import (
    ChartConfig, draw_bar_chart, draw_box_plot, draw_violin_plot,
    draw_scatter_plot, draw_paired_plot, draw_timecourse,
    get_draw_func, CHART_TYPES
)
from plotting.statistics import TestResult
from plotting.utils import extract_mouse_id, order_conditions


def plot_experiment(
    df: pd.DataFrame,
    metrics: list,
    group_col: str = "Group",
    cond_col: str = "Condition",
    id_col: str = "UniqueID",
    chart_type: str = "bar",
    palette_name: str = "nature_classic",
    custom_colors: dict = None,
    cfg: ChartConfig = None,
    output_dir: str = ".",
    filename_prefix: str = "Result",
    paired: bool = True,
    pdf: bool = True,
    png: bool = False,
    dpi: int = 300,
):
    """
    通用绘图入口。每个实验只需定义 metrics 列表即可。

    Parameters
    ----------
    df : DataFrame — 汇总数据
    metrics : list of (col_name, display_label) — 要绘制的指标
    group_col : 分组列 (如 hM4Di / mCherry)
    cond_col : 条件列 (如 saline / cno)
    id_col : 个体 ID 列
    chart_type : bar / box / violin / scatter / paired / timecourse
    palette_name : 预设配色名
    custom_colors : 覆盖颜色 {"color_0": ..., "color_1": ..., "scatter": ..., "connect": ..., "edge": ...}
    cfg : ChartConfig 实例 (如 None 则用默认)
    output_dir : 输出目录
    filename_prefix : 文件名前缀
    paired : 是否配对设计
    """
    apply_cns_style()
    if cfg is None:
        cfg = ChartConfig()

    # 准备数据
    df = df.copy()
    if id_col not in df.columns:
        df['UniqueID'] = df['FileName'].apply(extract_mouse_id)
        if 'Maze' in df.columns:
            df['UniqueID'] = df['UniqueID'] + "_" + df['Maze'].astype(str).str.lower().str.strip()
        if 'Cage' in df.columns:
            df['UniqueID'] = df['UniqueID'] + "_" + df['Cage'].astype(str).str.lower().str.strip()
        id_col = 'UniqueID'
    df[cond_col] = df[cond_col].astype(str).str.lower().str.strip()
    df[group_col] = df[group_col].astype(str).str.strip()

    # 配色
    pal = get_palette(palette_name)
    palette_colors = list(pal.colors)
    scatter_color = pal.scatter
    connect_color = pal.connect
    edge_color = pal.edge

    if custom_colors:
        if 'color_0' in custom_colors:
            palette_colors[0] = custom_colors['color_0']
        if 'color_1' in custom_colors and len(palette_colors) > 1:
            palette_colors[1] = custom_colors['color_1']
        if 'color_2' in custom_colors and len(palette_colors) > 2:
            palette_colors[2] = custom_colors['color_2']
        scatter_color = custom_colors.get('scatter', scatter_color)
        connect_color = custom_colors.get('connect', connect_color)
        edge_color = custom_colors.get('edge', edge_color)

    cfg.scatter_color = scatter_color
    cfg.connect_color = connect_color
    cfg.edge_color = edge_color

    # 条件列表
    conditions = order_conditions(df[cond_col].unique().tolist())
    groups = sorted(df[group_col].str.lower().unique())

    n_groups = len(groups)
    n_metrics = len(metrics)
    width_mm = cfg.figure_width_mm
    height_mm = cfg.figure_height_mm or (62 * n_groups + 10)

    fig, axes = plt.subplots(n_groups, n_metrics,
                              figsize=figure_size_mm(width_mm, height_mm))
    axes = np.atleast_2d(axes)
    if n_groups == 1:
        axes = axes.reshape(1, -1)

    all_stats = []
    draw_func = get_draw_func(chart_type)

    for ri, grp_name in enumerate(groups):
        sub_df = df[df[group_col].str.lower() == grp_name].copy()
        display_name = grp_name[0].upper() + grp_name[1:] if grp_name else grp_name

        for ci, (col, label) in enumerate(metrics):
            ax = axes[ri, ci]
            if col not in sub_df.columns:
                ax.axis('off')
                continue

            result = draw_func(ax, sub_df, col, cond_col, id_col, conditions,
                               palette_colors, cfg, paired=paired)

            if result and isinstance(result, TestResult):
                all_stats.append({
                    'group': display_name, 'metric': label,
                    'test': result.test_name, 'p': round(result.p_value, 4),
                    'star': result.star_label,
                    'effect_size': round(result.effect_size, 3) if result.effect_size else None,
                    'effect_name': result.effect_name,
                })

            ax.set_ylabel(label if ri == 0 or n_groups > 1 else "")
            if ci == 0 and n_groups > 1:
                ax.set_title(display_name, fontsize=7, fontweight='bold')
            ax.set_xticks(range(len(conditions)))
            ax.set_xticklabels([c.capitalize() for c in conditions])
            if chart_type in ("bar", "box", "violin", "paired"):
                ax.set_ylim(bottom=0)

    plt.tight_layout()

    # 保存
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if pdf:
        fig.savefig(os.path.join(output_dir, f"{filename_prefix}.pdf"), dpi=dpi)
    if png:
        fig.savefig(os.path.join(output_dir, f"{filename_prefix}.png"), dpi=dpi)
    if not pdf and not png:
        fig.savefig(os.path.join(output_dir, f"{filename_prefix}.pdf"), dpi=dpi)
    plt.close(fig)

    # 统计结果 JSON
    stats_path = os.path.join(output_dir, f"{filename_prefix}_stats.json")
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(all_stats, f, ensure_ascii=False, indent=2)

    print(f"图表已保存至: {output_dir}")
    if all_stats:
        print(f"统计结果: {len(all_stats)} 项检验")
        for s in all_stats:
            eff = f" {s['effect_name']}={s['effect_size']}" if s['effect_size'] else ""
            print(f"  {s['group']} | {s['metric']}: {s['test']} p={s['p']:.4f} {s['star']}{eff}")

    return all_stats
