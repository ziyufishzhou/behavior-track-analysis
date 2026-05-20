"""EPM 高架十字迷宫绘图 — 调用 plotting 通用引擎"""
import os
import sys
import pandas as pd

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from config.paths import EPM_SUMMARY, EPM_FIGURES
from gui.utils import find_latest_summary
from plotting import plot_experiment
from plotting.chart_types import ChartConfig

EPM_METRICS = [
    ('OA_Time_s', 'Open Arm Time (s)'),
    ('OA_Percent', 'Open Arm Time (%)'),
    ('OA_Entries', 'Open Arm Entries'),
    ('CA_Time_s', 'Closed Arm Time (s)'),
    ('Center_Time_s', 'Center Time (s)'),
    ('Distance_cm', 'Total Distance (cm)'),
]


def plot_epm(df, chart_type="bar", palette_name="nature_classic",
             colors=None, bar_width=0.6, bar_gap=0.2, point_size=18,
             errorbar="sem", alpha=0.05, force_test="",
             title="", fill_alpha=0.7, edge_width=0.8, edge_color="",
             font_size=7, line_width=1.0, figure_width_mm=89,
             pdf=True, png=False, dpi=300, output_dir=None):
    """EPM 绘图入口"""
    out_dir = output_dir or str(EPM_FIGURES)

    if 'OA_Percent' not in df.columns and 'OA_Time_s' in df.columns:
        if 'Total_Time_s' in df.columns:
            total = df['Total_Time_s']
        elif 'Center_Time_s' in df.columns:
            total = df['OA_Time_s'] + df['CA_Time_s'] + df['Center_Time_s']
        else:
            total = df['OA_Time_s'] + df['CA_Time_s']
        df = df.copy()
        df['OA_Percent'] = (df['OA_Time_s'] / total * 100).round(2)

    if 'Distance_cm' not in df.columns and 'Distance_px' in df.columns:
        df = df.copy()
        df['Distance_cm'] = df['Distance_px']

    cfg = ChartConfig(
        bar_width=bar_width, bar_gap=bar_gap, point_size=point_size,
        fill_alpha=fill_alpha, edge_width=edge_width,
        edge_color=edge_color or "#000000",
        errorbar=errorbar, alpha=alpha, force_test=force_test,
        title=title, figure_width_mm=figure_width_mm, dpi=dpi,
    )

    # 选择可用的 metrics
    metrics = [(col, label) for col, label in EPM_METRICS if col in df.columns]

    return plot_experiment(
        df=df, metrics=metrics, group_col="Group", cond_col="Condition",
        chart_type=chart_type, palette_name=palette_name,
        custom_colors=colors, cfg=cfg, output_dir=out_dir,
        filename_prefix="EPM_Standard", paired=True,
        pdf=pdf, png=png, dpi=dpi,
    )


if __name__ == "__main__":
    summary_path = find_latest_summary(str(EPM_SUMMARY), "EPM_Summary")
    if not summary_path:
        print("未找到 EPM 汇总文件")
        sys.exit(1)
    df = pd.read_excel(summary_path)
    plot_epm(df)
