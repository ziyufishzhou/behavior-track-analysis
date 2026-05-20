"""图表渲染引擎 — Prism 风格 6 种图表类型"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass, field
from typing import List, Optional, Dict

from plotting.statistics import auto_test, TestResult
from plotting.significance import draw_significance_bracket, compute_bracket_y
from plotting.utils import get_star


@dataclass
class ChartConfig:
    bar_width: float = 0.6
    bar_gap: float = 0.2
    point_size: float = 18
    point_alpha: float = 0.8
    fill_alpha: float = 0.7
    edge_color: str = "#000000"
    edge_width: float = 0.8
    connect_color: str = "#4D4D4D"
    scatter_color: str = "#000000"
    errorbar: str = "sem"
    title: str = ""
    ylabel: str = ""
    xlabel: str = ""
    figure_width_mm: float = 89
    figure_height_mm: float = None
    dpi: int = 300
    alpha: float = 0.05
    force_test: str = ""


def _error_data(values, errorbar="sem"):
    if len(values) == 0:
        return 0, 0
    m = np.nanmean(values)
    if len(values) < 2:
        return m, 0
    if errorbar == "sd":
        e = np.nanstd(values, ddof=1)
    elif errorbar == "ci95":
        e = 1.96 * np.nanstd(values, ddof=1) / np.sqrt(len(values))
    else:
        e = np.nanstd(values, ddof=1) / np.sqrt(len(values))
    return m, e


# ──────────────────────────────────────────────
# 1. Bar + Scatter (Prism 风格)
# ──────────────────────────────────────────────
def draw_bar_chart(ax, df, val_col, cond_col, id_col, conditions, palette_colors, cfg: ChartConfig, paired=True):
    n_cond = len(conditions)
    total_width = n_cond * cfg.bar_width + (n_cond - 1) * cfg.bar_gap
    x_offset = -total_width / 2 + cfg.bar_width / 2

    pivot = df.pivot_table(index=id_col, columns=cond_col, values=val_col)
    pivot = pivot.dropna()

    brackets = []
    for ci, cond in enumerate(conditions):
        x = x_offset + ci * (cfg.bar_width + cfg.bar_gap)
        vals = df[df[cond_col] == cond][val_col].dropna().values
        if len(vals) == 0:
            continue
        mean_val, err_val = _error_data(vals, cfg.errorbar)
        ax.bar(x, mean_val, yerr=err_val, width=cfg.bar_width,
               color=palette_colors[ci % len(palette_colors)],
               edgecolor=cfg.edge_color, linewidth=cfg.edge_width,
               alpha=cfg.fill_alpha, capsize=1.5, zorder=1)

        individual = pivot[cond].dropna().values if cond in pivot.columns else np.array([])
        ax.scatter(np.full_like(individual, x), individual,
                   color=cfg.scatter_color, s=cfg.point_size, alpha=cfg.point_alpha,
                   zorder=3, edgecolors='none')

    # 配对连线
    if paired and len(conditions) == 2 and not pivot.empty:
        c0, c1 = conditions
        if c0 in pivot.columns and c1 in pivot.columns:
            for _, row in pivot.iterrows():
                if pd.notna(row[c0]) and pd.notna(row[c1]):
                    x0 = x_offset
                    x1 = x_offset + (cfg.bar_width + cfg.bar_gap)
                    ax.plot([x0, x1], [row[c0], row[c1]],
                            color=cfg.connect_color, lw=0.5, alpha=0.3, zorder=2)

    # 统计检验
    if len(conditions) == 2 and not pivot.empty:
        c0, c1 = conditions
        if c0 in pivot.columns and c1 in pivot.columns:
            g1, g2 = pivot[c0].dropna().values, pivot[c1].dropna().values
            if len(g1) >= 2 and len(g2) >= 2:
                result = auto_test(g1, g2, paired=paired, alpha=cfg.alpha, force_test=cfg.force_test)
                y_data_max = max(g1.max(), g2.max())
                y_base, _ = compute_bracket_y(ax, y_data_max * 1.1)
                x0 = x_offset
                x1 = x_offset + (cfg.bar_width + cfg.bar_gap)
                draw_significance_bracket(ax, x0, x1, y_base, result.star_label)
                ax.set_ylim(bottom=0)
                _adjust_ylim(ax, y_base + (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.05)
                return result

    ax.set_ylim(bottom=0)
    return None


# ──────────────────────────────────────────────
# 2. Box + Scatter
# ──────────────────────────────────────────────
def draw_box_plot(ax, df, val_col, cond_col, id_col, conditions, palette_colors, cfg: ChartConfig, paired=True):
    positions = list(range(len(conditions)))
    box_data = [df[df[cond_col] == cond][val_col].dropna().values for cond in conditions]

    bp = ax.boxplot(box_data, positions=positions, widths=cfg.bar_width,
                    patch_artist=True, showfliers=False,
                    boxprops=dict(linewidth=cfg.edge_width),
                    whiskerprops=dict(linewidth=cfg.edge_width),
                    capprops=dict(linewidth=cfg.edge_width),
                    medianprops=dict(color='black', linewidth=1.0))

    for i, patch in enumerate(bp['boxes']):
        patch.set_facecolor(palette_colors[i % len(palette_colors)])
        patch.set_alpha(cfg.fill_alpha)
        patch.set_edgecolor(cfg.edge_color)

    pivot = df.pivot_table(index=id_col, columns=cond_col, values=val_col).dropna()
    for ci, cond in enumerate(conditions):
        if cond in pivot.columns:
            vals = pivot[cond].dropna().values
            jitter = np.random.default_rng(42).uniform(-0.08, 0.08, len(vals))
            ax.scatter(np.full(len(vals), positions[ci]) + jitter, vals,
                       color=cfg.scatter_color, s=cfg.point_size * 0.7, alpha=cfg.point_alpha,
                       zorder=3, edgecolors='none')

    # 配对连线
    if paired and len(conditions) == 2 and not pivot.empty:
        c0, c1 = conditions
        if c0 in pivot.columns and c1 in pivot.columns:
            for _, row in pivot.iterrows():
                if pd.notna(row[c0]) and pd.notna(row[c1]):
                    ax.plot([0, 1], [row[c0], row[c1]],
                            color=cfg.connect_color, lw=0.4, alpha=0.25, zorder=2)

    # 统计
    if len(conditions) == 2 and not pivot.empty:
        c0, c1 = conditions
        if c0 in pivot.columns and c1 in pivot.columns:
            g1, g2 = pivot[c0].dropna().values, pivot[c1].dropna().values
            if len(g1) >= 2 and len(g2) >= 2:
                result = auto_test(g1, g2, paired=paired, alpha=cfg.alpha, force_test=cfg.force_test)
                y_data_max = max(np.nanmax(box_data[0]) if len(box_data[0]) else 0,
                                 np.nanmax(box_data[1]) if len(box_data[1]) else 0)
                y_base, _ = compute_bracket_y(ax, y_data_max)
                draw_significance_bracket(ax, 0, 1, y_base, result.star_label)
                return result
    return None


# ──────────────────────────────────────────────
# 3. Violin + Scatter
# ──────────────────────────────────────────────
def draw_violin_plot(ax, df, val_col, cond_col, id_col, conditions, palette_colors, cfg: ChartConfig, paired=True):
    plot_data = df[df[cond_col].isin(conditions)].copy()
    parts = ax.violinplot([plot_data[plot_data[cond_col] == c][val_col].dropna().values for c in conditions],
                          positions=range(len(conditions)), widths=cfg.bar_width * 1.5,
                          showmeans=False, showmedians=False, showextrema=False)

    for i, body in enumerate(parts['bodies']):
        body.set_facecolor(palette_colors[i % len(palette_colors)])
        body.set_alpha(cfg.fill_alpha * 0.5)
        body.set_edgecolor(cfg.edge_color)
        body.set_linewidth(cfg.edge_width)

    # 内箱线图
    for ci, cond in enumerate(conditions):
        vals = plot_data[plot_data[cond_col] == cond][val_col].dropna().values
        if len(vals) == 0:
            continue
        q1, med, q3 = np.percentile(vals, [25, 50, 75])
        ax.plot([ci - 0.05, ci + 0.05], [med, med], color='black', lw=0.8, zorder=4)
        ax.plot([ci, ci], [q1, q3], color='black', lw=0.6, zorder=4)
        ax.plot([ci - 0.05, ci + 0.05], [q1, q1], color='black', lw=0.6, zorder=4)
        ax.plot([ci - 0.05, ci + 0.05], [q3, q3], color='black', lw=0.6, zorder=4)

    # 散点
    pivot = df.pivot_table(index=id_col, columns=cond_col, values=val_col).dropna()
    for ci, cond in enumerate(conditions):
        if cond in pivot.columns:
            vals = pivot[cond].dropna().values
            jitter = np.random.default_rng(42).uniform(-0.1, 0.1, len(vals))
            ax.scatter(np.full(len(vals), ci) + jitter, vals,
                       color=cfg.scatter_color, s=cfg.point_size * 0.6, alpha=cfg.point_alpha,
                       zorder=5, edgecolors='none')

    # 配对连线
    if paired and len(conditions) == 2 and not pivot.empty:
        c0, c1 = conditions
        if c0 in pivot.columns and c1 in pivot.columns:
            for _, row in pivot.iterrows():
                if pd.notna(row[c0]) and pd.notna(row[c1]):
                    ax.plot([0, 1], [row[c0], row[c1]],
                            color=cfg.connect_color, lw=0.4, alpha=0.25, zorder=2)

    # 统计
    if len(conditions) == 2 and not pivot.empty:
        c0, c1 = conditions
        if c0 in pivot.columns and c1 in pivot.columns:
            g1, g2 = pivot[c0].dropna().values, pivot[c1].dropna().values
            if len(g1) >= 2 and len(g2) >= 2:
                result = auto_test(g1, g2, paired=paired, alpha=cfg.alpha, force_test=cfg.force_test)
                y_data_max = max(g1.max(), g2.max())
                y_base, _ = compute_bracket_y(ax, y_data_max)
                draw_significance_bracket(ax, 0, 1, y_base, result.star_label)
                return result
    return None


# ──────────────────────────────────────────────
# 4. Scatter (with optional regression)
# ──────────────────────────────────────────────
def draw_scatter_plot(ax, df, val_col, cond_col, id_col, conditions, palette_colors, cfg: ChartConfig, paired=False):
    for ci, cond in enumerate(conditions):
        vals = df[df[cond_col] == cond][val_col].dropna().values
        ax.scatter(np.full(len(vals), ci), vals,
                   color=palette_colors[ci % len(palette_colors)],
                   s=cfg.point_size * 1.5, alpha=cfg.point_alpha,
                   edgecolors=cfg.edge_color, linewidth=0.3, zorder=3,
                   label=cond)
    return None


# ──────────────────────────────────────────────
# 5. Before-After (Paired) Line
# ──────────────────────────────────────────────
def draw_paired_plot(ax, df, val_col, cond_col, id_col, conditions, palette_colors, cfg: ChartConfig, paired=True):
    pivot = df.pivot_table(index=id_col, columns=cond_col, values=val_col).dropna()
    if len(conditions) != 2:
        return None

    c0, c1 = conditions
    if c0 not in pivot.columns or c1 not in pivot.columns:
        return None

    for i, (_, row) in enumerate(pivot.iterrows()):
        color = palette_colors[0] if row[c1] > row[c0] else palette_colors[1]
        ax.plot([0, 1], [row[c0], row[c1]], color=color, alpha=0.5, lw=1.0, zorder=1)
        ax.scatter([0], [row[c0]], color=palette_colors[0], s=cfg.point_size,
                   alpha=cfg.point_alpha, edgecolors='none', zorder=3)
        ax.scatter([1], [row[c1]], color=palette_colors[1], s=cfg.point_size,
                   alpha=cfg.point_alpha, edgecolors='none', zorder=3)

    # 均值线
    m0, m1 = pivot[c0].mean(), pivot[c1].mean()
    ax.plot([0, 1], [m0, m1], color='black', lw=1.5, zorder=4)

    # 统计
    g1, g2 = pivot[c0].values, pivot[c1].values
    if len(g1) >= 2:
        result = auto_test(g1, g2, paired=True, alpha=cfg.alpha, force_test=cfg.force_test)
        y_data_max = max(g1.max(), g2.max())
        y_base, _ = compute_bracket_y(ax, y_data_max)
        draw_significance_bracket(ax, 0, 1, y_base, result.star_label)
        return result
    return None


# ──────────────────────────────────────────────
# 6. Time Course (mean ± SEM ribbon)
# ──────────────────────────────────────────────
def draw_timecourse(ax, df, val_col, time_col, group_col, groups, palette_colors, cfg: ChartConfig):
    for gi, grp in enumerate(groups):
        sub = df[df[group_col] == grp]
        if sub.empty:
            continue
        t = sub[time_col].values
        y = sub[val_col].values
        mean_y, sem_y = _error_data(y, "sem")
        ax.plot(t, y, color=palette_colors[gi % len(palette_colors)], lw=1.0, label=grp)
        ax.fill_between(t, y - sem_y, y + sem_y,
                        color=palette_colors[gi % len(palette_colors)], alpha=0.15)
    return None


# ──────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────
def _adjust_ylim(ax, y_top):
    current = ax.get_ylim()
    ax.set_ylim(current[0], max(current[1], y_top))


# 图表类型注册表
CHART_TYPES = {
    "bar": ("Bar + Scatter", draw_bar_chart),
    "box": ("Box + Scatter", draw_box_plot),
    "violin": ("Violin + Scatter", draw_violin_plot),
    "scatter": ("Scatter", draw_scatter_plot),
    "paired": ("Before-After (Paired)", draw_paired_plot),
    "timecourse": ("Time Course", draw_timecourse),
}


def chart_type_list():
    return [{"id": k, "name": v[0]} for k, v in CHART_TYPES.items()]


def get_draw_func(chart_type: str):
    entry = CHART_TYPES.get(chart_type)
    return entry[1] if entry else draw_bar_chart
