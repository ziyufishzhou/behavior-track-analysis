"""CNS 出版级 matplotlib 样式配置"""
import matplotlib.pyplot as plt


def apply_cns_style():
    """SciencePlots nature 风格 + CNS 覆盖"""
    import scienceplots
    plt.style.use(['science', 'no-latex', 'nature', 'bright'])
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 7,
        "axes.labelsize": 7,
        "xtick.labelsize": 6,
        "ytick.labelsize": 6,
        "legend.fontsize": 6,
        "axes.titlesize": 7,
        "figure.figsize": (89 / 25.4, 2.45),
        "axes.linewidth": 0.75,
        "lines.linewidth": 1.2,
        "lines.markersize": 3.5,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "savefig.bbox": "tight",
    })


def apply_custom_overrides(overrides: dict):
    """运行时覆盖个别 rcParams"""
    plt.rcParams.update(overrides)


def figure_size_mm(width_mm=89, height_mm=62):
    """毫米 → 英寸"""
    return (width_mm / 25.4, height_mm / 25.4)
