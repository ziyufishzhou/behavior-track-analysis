"""绘图 API — Prism 风格 + AI 生成"""
import os
import json
from flask import Blueprint, request, jsonify, send_file, current_app
import pandas as pd

from config.paths import EPM_FIGURES, OF_FIGURES, TCT_FIGURES, EPM_SUMMARY, OF_SUMMARY, TCT_SUMMARY, OUTPUT_DIR
from gui.utils import find_latest_summary

bp = Blueprint('plot', __name__, url_prefix='/api/plot')

FIGURE_DIRS = {'EPM': EPM_FIGURES, 'OF': OF_FIGURES, 'TCT': TCT_FIGURES}
SUMMARY_DIRS = {'EPM': EPM_SUMMARY, 'OF': OF_SUMMARY, 'TCT': TCT_SUMMARY}
SUMMARY_PREFIXES = {'EPM': 'EPM_Summary', 'OF': 'Summary_15min', 'TCT': 'TCT_Complete_Data'}


def find_summary_file(experiment):
    """Find a summary Excel file, including legacy output locations."""
    exp = experiment.upper()
    prefix = SUMMARY_PREFIXES.get(exp, '')
    summary_dir = SUMMARY_DIRS.get(exp)

    if summary_dir:
        path = find_latest_summary(str(summary_dir), prefix)
        if path:
            return path

    exp_root = OUTPUT_DIR / exp.lower()
    if not exp_root.exists():
        return None

    candidates = [
        p for p in exp_root.rglob('*.xlsx')
        if p.is_file() and (not prefix or p.name.startswith(prefix))
    ]
    if not candidates:
        candidates = [p for p in exp_root.rglob('*.xlsx') if p.is_file()]
    if not candidates:
        return None
    return str(max(candidates, key=lambda p: p.stat().st_mtime))


@bp.route('/palettes')
def list_palettes():
    from plotting.palettes import palette_list
    return jsonify({'palettes': palette_list()})


@bp.route('/chart-types')
def list_chart_types():
    from plotting.chart_types import chart_type_list
    return jsonify({'chart_types': chart_type_list()})


@bp.route('/auto-find/<experiment>')
def auto_find(experiment):
    path = find_summary_file(experiment)
    return jsonify({'path': path})


@bp.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    exp = data.get('experiment', 'EPM').upper()
    source = data.get('source', '').strip()
    chart_type = data.get('chart_type', 'bar')
    palette_name = data.get('palette_name', 'nature_classic')
    force_test = data.get('force_test', '')
    title = data.get('title', '')
    bar_width = float(data.get('bar_width', 0.6))
    bar_gap = float(data.get('bar_gap', 0.2))
    point_size = float(data.get('point_size', 18))
    errorbar = data.get('errorbar', 'sem')
    alpha = float(data.get('alpha', 0.05))
    fill_alpha = float(data.get('fill_alpha', 0.7))
    edge_width = float(data.get('edge_width', 0.8))
    font_size = int(data.get('font_size', 7))
    line_width = float(data.get('line_width', 1.0))
    figure_width_mm = float(data.get('figure_width_mm', 89))
    pdf = data.get('pdf', True)
    png = data.get('png', False)
    dpi = int(data.get('dpi', 300))

    colors = {
        'color_0': data.get('color_0', ''),
        'color_1': data.get('color_1', ''),
        'scatter': data.get('color_scatter', ''),
        'connect': data.get('color_connect', ''),
        'edge': data.get('color_edge', ''),
    }
    colors = {k: v for k, v in colors.items() if v}

    # 自动查找 source
    if not source or not os.path.isfile(source):
        source = find_summary_file(exp)
        if not source:
            return jsonify({'error': '未找到数据文件，请手动指定'}), 400
    if pdf and not png:
        png = True

    def _job():
        import matplotlib
        matplotlib.use('Agg')
        df = pd.read_excel(source)
        print(f"数据: {os.path.basename(source)} ({len(df)} 行)")
        print(f"图表类型: {chart_type}, 配色: {palette_name}")

        if exp == 'EPM':
            import experiments.EPM.plot as epm_plot
            stats = epm_plot.plot_epm(df, chart_type=chart_type, palette_name=palette_name,
                                       colors=colors, bar_width=bar_width, bar_gap=bar_gap,
                                       point_size=point_size, errorbar=errorbar, alpha=alpha,
                                       force_test=force_test, title=title, fill_alpha=fill_alpha,
                                       edge_width=edge_width, pdf=pdf, png=png, dpi=dpi)
        elif exp == 'OF':
            import experiments.OF.plot as of_plot
            stats = of_plot.plot_of(df, chart_type=chart_type, palette_name=palette_name,
                                     colors=colors, bar_width=bar_width, bar_gap=bar_gap,
                                     point_size=point_size, errorbar=errorbar, alpha=alpha,
                                     force_test=force_test, title=title, fill_alpha=fill_alpha,
                                     edge_width=edge_width, pdf=pdf, png=png, dpi=dpi)
        elif exp == 'TCT':
            import experiments.TCT.plot as tct_plot
            for phase in ['S', 'N']:
                tct_plot.plot_tct(df, phase, chart_type=chart_type, palette_name=palette_name,
                                   colors=colors, bar_width=bar_width, bar_gap=bar_gap,
                                   point_size=point_size, errorbar=errorbar, alpha=alpha,
                                   force_test=force_test, title=title, fill_alpha=fill_alpha,
                                   edge_width=edge_width, pdf=pdf, png=png, dpi=dpi)

        # 读取统计结果
        fig_dir = str(FIGURE_DIRS.get(exp, ''))
        stats_files = sorted([f for f in os.listdir(fig_dir) if f.endswith('_stats.json')], reverse=True)
        if stats_files:
            with open(os.path.join(fig_dir, stats_files[0]), 'r', encoding='utf-8') as f:
                stats_data = json.load(f)
            print("\n📊 统计结果:")
            for s in stats_data:
                eff = f" {s.get('effect_name', '')}={s.get('effect_size', '')}" if s.get('effect_size') else ""
                print(f"  {s.get('group', '')} | {s.get('metric', '')}: "
                      f"{s.get('test', '')} p={s.get('p', '')} {s.get('star', '')}{eff}")

    task_id = current_app.task_runner.start(_job)
    if task_id is None:
        return jsonify({'error': '任务正在运行中，请等待完成'}), 409
    return jsonify({'task_id': task_id})


@bp.route('/figures/<experiment>')
def list_figures(experiment):
    fig_dir = str(FIGURE_DIRS.get(experiment.upper(), ''))
    if not os.path.isdir(fig_dir):
        return jsonify({'figures': []})
    figures = [
        f for f in os.listdir(fig_dir)
        if f.endswith(('.pdf', '.png'))
    ]
    figures = sorted(figures, key=lambda f: os.path.getmtime(os.path.join(fig_dir, f)), reverse=True)
    return jsonify({'figures': figures})


@bp.route('/figure/<experiment>/<filename>')
def serve_figure(experiment, filename):
    fig_dir = str(FIGURE_DIRS.get(experiment.upper(), ''))
    path = os.path.join(fig_dir, filename)
    if not os.path.isfile(path):
        return jsonify({'error': '文件不存在'}), 404
    return send_file(path)


@bp.route('/stats/<experiment>')
def get_stats(experiment):
    fig_dir = str(FIGURE_DIRS.get(experiment.upper(), ''))
    if not os.path.isdir(fig_dir):
        return jsonify({'stats': []})
    stats_files = sorted([f for f in os.listdir(fig_dir) if f.endswith('_stats.json')], reverse=True)
    if not stats_files:
        return jsonify({'stats': []})
    with open(os.path.join(fig_dir, stats_files[0]), 'r', encoding='utf-8') as f:
        return jsonify({'stats': json.load(f), 'file': stats_files[0]})


@bp.route('/ai-generate', methods=['POST'])
def ai_generate():
    """AI 图表生成：上传示例图 → Claude Vision 分析 → 生成代码"""
    from plotting.ai_generator import is_available, analyze_and_generate

    if not is_available():
        return jsonify({'error': 'AI 功能未配置。请设置 ANTHROPIC_API_KEY 环境变量。'}), 400

    image_path = request.form.get('image_path', '').strip()
    source = request.form.get('source', '').strip()
    experiment = request.form.get('experiment', 'EPM').upper()

    # 支持文件上传
    if 'image' in request.files:
        f = request.files['image']
        if f.filename:
            import tempfile
            tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            f.save(tmp.name)
            image_path = tmp.name

    if not image_path or not os.path.isfile(image_path):
        return jsonify({'error': '请上传示例图片或提供图片路径'}), 400

    if not source or not os.path.isfile(source):
        source = find_summary_file(experiment)

    def _job():
        print("AI 分析示例图...")
        fig_dir = str(FIGURE_DIRS.get(experiment, ''))
        result = analyze_and_generate(image_path, source, experiment, fig_dir)
        if result:
            print("AI 图表生成完成")
        else:
            print("AI 图表生成失败")

    task_id = current_app.task_runner.start(_job)
    if task_id is None:
        return jsonify({'error': '任务正在运行中'}), 409
    return jsonify({'task_id': task_id})
