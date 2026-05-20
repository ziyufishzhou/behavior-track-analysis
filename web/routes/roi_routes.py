"""ROI 标注 API"""
import os
import subprocess
from flask import Blueprint, request, jsonify
from config.paths import OF_ROI_JSON, EPM_ROI_JSON, TCT_ROI_JSON

bp = Blueprint('roi', __name__, url_prefix='/api/roi')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@bp.route('/status')
def roi_status():
    return jsonify({
        'of': OF_ROI_JSON.exists(),
        'epm': EPM_ROI_JSON.exists(),
        'tct': TCT_ROI_JSON.exists(),
    })


@bp.route('/launch/<experiment>', methods=['POST'])
def launch(experiment):
    scripts = {
        'of': 'experiments/OF/roi_tool.py',
        'epm': 'experiments/EPM/roi_tool.py',
        'tct': 'experiments/TCT/roi_tool.py',
    }
    script = scripts.get(experiment)
    if not script:
        return jsonify({'error': '未知实验'}), 400
    full_path = os.path.join(PROJECT_ROOT, script)
    subprocess.Popen(['python', full_path], cwd=PROJECT_ROOT)
    return jsonify({'ok': True})
