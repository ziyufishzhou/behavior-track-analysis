"""OF 旷场实验绘图 — 调用 plotting 通用引擎"""
import os
import sys
import pandas as pd

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from config.paths import OF_SUMMARY, OF_FIGURES
from gui.utils import find_latest_summary
from plotting import plot_experiment
from plotting.chart_types import ChartConfig

OF_METRICS = [
    ('Total_Distance_cm', 'Total Distance (cm)'),
    ('Center_Time_s', 'Center Time (s)'),
    ('Entries', 'Center Entries'),
    ('Center_Percent', 'Center Time (%)'),
]


def plot_of(df, chart_type="bar", palette_name="nature_classic",
            colors=None, bar_width=0.6, bar_gap=0.2, point_size=18,
            errorbar="sem", alpha=0.05, force_test="",
            title="", fill_alpha=0.7, edge_width=0.8, edge_color="",
            font_size=7, line_width=1.0, figure_width_mm=89,
            pdf=True, png=False, dpi=300, output_dir=None):
    """OF 绘图入口"""
    out_dir = output_dir or str(OF_FIGURES)

    if 'Center_Percent' not in df.columns and 'Center_Time_s' in df.columns:
        df = df.copy()
        if 'Total_Time_s' in df.columns:
            total_time = df['Total_Time_s']
        else:
            total_time = df.groupby('FileName')['Center_Time_s'].transform('max') * 5
        df['Center_Percent'] = (df['Center_Time_s'] / total_time * 100).round(2)

    cfg = ChartConfig(
        bar_width=bar_width, bar_gap=bar_gap, point_size=point_size,
        fill_alpha=fill_alpha, edge_width=edge_width,
        edge_color=edge_color or "#000000",
        errorbar=errorbar, alpha=alpha, force_test=force_test,
        title=title, figure_width_mm=figure_width_mm, dpi=dpi,
    )

    metrics = [(col, label) for col, label in OF_METRICS if col in df.columns]

    return plot_experiment(
        df=df, metrics=metrics, group_col="Group", cond_col="Condition",
        chart_type=chart_type, palette_name=palette_name,
        custom_colors=colors, cfg=cfg, output_dir=out_dir,
        filename_prefix="OF_Standard", paired=True,
        pdf=pdf, png=png, dpi=dpi,
    )


if __name__ == "__main__":
    summary_path = find_latest_summary(str(OF_SUMMARY), "Summary_15min")
    if not summary_path:
        print("未找到 OF 汇总文件")
        sys.exit(1)
    df = pd.read_excel(summary_path)
    plot_of(df)
