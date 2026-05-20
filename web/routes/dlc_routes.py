"""DLC 分析 API — 通过 dlc_zzy conda 环境执行"""
import os
import sys
import tempfile
import subprocess
from pathlib import Path
from flask import Blueprint, request, jsonify
from config.paths import MODELS_DIR, get_dlc_python, get_video_dir, resolve_project_path, set_dlc_python
from gui.utils import is_video_file

bp = Blueprint('dlc', __name__, url_prefix='/api/dlc')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@bp.route('/models')
def list_models():
    models = []
    if MODELS_DIR.exists():
        for d in sorted(MODELS_DIR.iterdir()):
            if d.is_dir() and (d / 'config.yaml').exists():
                models.append(str(d))
    return jsonify({'models': models})


@bp.route('/python')
def get_python():
    dlc_python = get_dlc_python()
    exists = bool(dlc_python and dlc_python.is_file())
    return jsonify({'python': str(dlc_python) if dlc_python else '', 'exists': exists})


@bp.route('/python', methods=['POST'])
def save_python():
    data = request.get_json(silent=True) or {}
    path = str(data.get('python', '')).strip()
    if not path:
        return jsonify({'error': 'DLC Python 路径不能为空'}), 400

    dlc_python = resolve_project_path(path)
    if not dlc_python.is_file():
        return jsonify({'error': f'Python 文件不存在: {dlc_python}', 'python': str(dlc_python), 'exists': False}), 400

    set_dlc_python(dlc_python)
    return jsonify({'ok': True, 'python': str(dlc_python), 'exists': True})


@bp.route('/videos')
def list_videos():
    """Recursively list video files under the configured video directory."""
    video_dir = get_video_dir()
    videos = []
    if video_dir.exists():
        for f in sorted(video_dir.rglob("*")):
            if f.is_file() and is_video_file(str(f)):
                videos.append(str(f.relative_to(video_dir)))
    return jsonify({'videos': videos, 'video_dir': str(video_dir), 'exists': video_dir.exists()})


@bp.route('/run', methods=['POST'])
def run_dlc():
    from flask import current_app
    data = request.get_json()
    model_path = data.get('model_path', '').strip()
    shuffle = data.get('shuffle', 1)
    video_names = data.get('video_names', [])  # 可选：指定视频文件名

    config_yaml = os.path.join(model_path, 'config.yaml')
    if not model_path or not os.path.isfile(config_yaml):
        return jsonify({'error': f'config.yaml 不存在于: {model_path}'}), 400

    def _job():
        dlc_python = get_dlc_python()
        if not dlc_python:
            print("[ERROR] 未配置 DLC 环境 Python，请在 Web 的 DLC 分析页面填写 Python 路径")
            return
        if not dlc_python.is_file():
            print(f"[ERROR] DLC Python 文件不存在: {dlc_python}")
            return

        # 收集视频文件
        video_dir = get_video_dir()
        videos = []
        if video_dir.exists():
            if video_names:
                # 指定了视频
                for name in video_names:
                    rel = Path(str(name).replace("\\", "/"))
                    if rel.is_absolute() or ".." in rel.parts:
                        print(f"[WARN] 跳过非法视频路径: {name}")
                        continue
                    f = video_dir / rel
                    if f.is_file() and is_video_file(str(f)):
                        videos.append(str(f))
                    else:
                        print(f"[WARN] 视频不存在或格式不支持: {name}")
            else:
                # 全部视频
                for f in sorted(video_dir.rglob("*")):
                    if f.is_file() and is_video_file(str(f)):
                        videos.append(str(f))

        if not videos:
            print(f"没有找到视频文件，请检查视频目录: {video_dir}")
            return

        print(f"使用 DLC Python: {dlc_python}")
        print(f"模型: {config_yaml}")
        print(f"视频目录: {video_dir}")
        print(f"待分析视频: {len(videos)} 个")
        for v in videos:
            print(f"  - {os.path.relpath(v, video_dir)}")

        # 生成临时脚本，用 dlc_zzy 环境执行
        script = f'''
import sys
sys.path.insert(0, {repr(PROJECT_ROOT)})
import deeplabcut
videos = {repr(videos)}
print(f"DLC 分析开始: {{len(videos)}} 个视频")
deeplabcut.analyze_videos({repr(config_yaml)}, videos, shuffle={shuffle}, save_as_csv=True)
print("DLC 分析完成")
'''
        script_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        )
        script_file.write(script)
        script_file.close()

        try:
            cmd = [str(dlc_python), script_file.name]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                cwd=PROJECT_ROOT, text=True, bufsize=1
            )
            for line in proc.stdout:
                print(line, end='')
            proc.wait()
            if proc.returncode != 0:
                print(f"[ERROR] DLC 分析退出码: {proc.returncode}")
            else:
                print("DLC 分析全部完成")
        finally:
            os.unlink(script_file.name)

    task_id = current_app.task_runner.start(_job)
    if task_id is None:
        return jsonify({'error': '任务正在运行中，请等待完成'}), 409
    return jsonify({'task_id': task_id})
