"""Prism 风格显著性标注 — 括号 + 星号"""
import matplotlib.pyplot as plt
import numpy as np


def draw_significance_bracket(ax, x1, x2, y, label, lw=0.7, fontsize=6, y_offset=None):
    if y_offset is None:
        y_offset = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.02
    ax.plot([x1, x1, x2, x2],
            [y - y_offset, y, y, y - y_offset],
            color='black', lw=lw, clip_on=False)
    ax.text((x1 + x2) / 2, y + y_offset * 0.3, label,
            ha='center', va='bottom', fontsize=fontsize)


def draw_multiple_brackets(ax, brackets, y_base=None, y_step=None):
    if not brackets:
        return
    ylim = ax.get_ylim()
    if y_base is None:
        y_base = ylim[1] * 0.88
    if y_step is None:
        y_step = (ylim[1] - ylim[0]) * 0.08

    for i, (x1, x2, label) in enumerate(brackets):
        y = y_base + i * y_step
        draw_significance_bracket(ax, x1, x2, y, label)


def compute_bracket_y(ax, y_data_max, n_brackets=1):
    ylim = ax.get_ylim()
    y_range = ylim[1] - ylim[0]
    y_base = y_data_max + y_range * 0.08
    y_step = y_range * 0.07
    return y_base, y_step
