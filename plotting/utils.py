"""共享工具函数"""
import re


def extract_mouse_id(filename):
    match = re.search(r'([a-zA-Z]+\d+-?\d?)', str(filename))
    return match.group(0).lower().replace(" ", "") if match else "unknown"


def get_star(p_value, alpha=0.05):
    if p_value is None:
        return 'ns'
    if p_value < 0.001:
        return '***'
    if p_value < 0.01:
        return '**'
    if p_value < alpha:
        return '*'
    return 'ns'


def order_conditions(values):
    """Order experimental conditions with baseline/control conditions first."""
    priority = {
        "saline": 0,
        "sal": 0,
        "vehicle": 0,
        "veh": 0,
        "control": 0,
        "ctrl": 0,
        "baseline": 0,
        "cno": 1,
        "treatment": 1,
        "treated": 1,
        "drug": 1,
    }
    unique = []
    for value in values:
        text = str(value).strip().lower()
        if text and text not in unique:
            unique.append(text)
    return sorted(unique, key=lambda item: (priority.get(item, 50), item))


def pivot_paired_data(df, id_col, cond_col, val_col):
    """配对数据透视：行=个体ID，列=条件"""
    pivot = df.pivot_table(index=id_col, columns=cond_col, values=val_col)
    conditions = sorted(pivot.columns.tolist())
    return pivot, conditions


def prepare_figure(n_rows=1, n_cols=1, width_mm=89, height_mm=None):
    """创建 CNS 尺寸图"""
    from plotting.rc_params import figure_size_mm
    if height_mm is None:
        height_mm = 62 * n_rows
    figsize = figure_size_mm(width_mm, height_mm)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    if n_rows == 1 and n_cols == 1:
        axes = np.array([axes])
    axes = np.atleast_2d(axes)
    return fig, axes


import numpy as np
