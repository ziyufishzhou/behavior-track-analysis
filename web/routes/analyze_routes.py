"""数据分析 API"""
import os
import sys
import importlib.util
from flask import Blueprint, request, jsonify
from config.paths import OF_ROI_JSON, EPM_ROI_JSON, TCT_ROI_JSON

bp = Blueprint('analyze', __name__, url_prefix='/api/analyze')

# 从顶层 config.py 读取默认参数
_cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config.py')
_spec = importlib.util.spec_from_file_location('_project_config', _cfg_path)
_project_config = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_project_config)


@bp.route('/config')
def get_config():
    return jsonify({
        'FPS': _project_config.FPS,
        'LIKELIHOOD_THRESHOLD': _project_config.LIKELIHOOD_THRESHOLD,
        'OF_ANALYSIS_MINUTES': _project_config.OF_ANALYSIS_MINUTES,
        'EPM_ANALYSIS_MINUTES': _project_config.EPM_ANALYSIS_MINUTES,
        'TCT_ANALYSIS_MINUTES': _project_config.TCT_ANALYSIS_MINUTES,
    })


@bp.route('/roi-status')
def roi_status():
    return jsonify({
        'of': OF_ROI_JSON.exists(),
        'epm': EPM_ROI_JSON.exists(),
        'tct': TCT_ROI_JSON.exists(),
    })


@bp.route('/run', methods=['POST'])
def run_analysis():
    from flask import current_app
    data = request.get_json()
    run_of = data.get('of', False)
    run_epm = data.get('epm', False)
    run_tct = data.get('tct', False)
    fps = data.get('fps', 30)
    likelihood = data.get('likelihood', 0.6)
    of_time = data.get('of_time', 15)
    epm_time = data.get('epm_time', 15)
    tct_time = data.get('tct_time', 10)

    def _job():
        from gui.utils import temp_patch

        if run_of:
            import experiments.OF.analyze as of_mod
            with temp_patch(of_mod, ANALYSIS_MINUTES=of_time, FPS=fps,
                            LIKELIHOOD_THRESHOLD=likelihood):
                of_mod.process_all()

        if run_epm:
            import experiments.EPM.analyze as epm_mod
            with temp_patch(epm_mod, ANALYSIS_MINUTES=epm_time, FPS=fps,
                            LIKELIHOOD_THRESHOLD=likelihood):
                epm_mod.process_all()

        if run_tct:
            import experiments.TCT.analyze as tct_mod
            with temp_patch(tct_mod, ANALYSIS_MINUTES=tct_time, FPS=fps,
                            LIKELIHOOD_THRESHOLD=likelihood):
                tct_mod.process_tct_full_visual()

    task_id = current_app.task_runner.start(_job)
    if task_id is None:
        return jsonify({'error': '任务正在运行中'}), 409
    return jsonify({'task_id': task_id})
