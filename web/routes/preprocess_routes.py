"""预处理 API"""
from flask import Blueprint, request, jsonify

bp = Blueprint('preprocess', __name__, url_prefix='/api/preprocess')


@bp.route('/collect', methods=['POST'])
def run_collect():
    from flask import current_app

    def _job():
        from preprocessing.collect_csv import main
        main()

    task_id = current_app.task_runner.start(_job)
    if task_id is None:
        return jsonify({'error': '任务正在运行中'}), 409
    return jsonify({'task_id': task_id})


@bp.route('/fix', methods=['POST'])
def run_fix():
    from flask import current_app

    def _job():
        from preprocessing.fix_csv import main
        main()

    task_id = current_app.task_runner.start(_job)
    if task_id is None:
        return jsonify({'error': '任务正在运行中'}), 409
    return jsonify({'task_id': task_id})


@bp.route('/group', methods=['POST'])
def run_group():
    from flask import current_app

    def _job():
        from preprocessing.group_csv import group_by_metadata
        group_by_metadata()

    task_id = current_app.task_runner.start(_job)
    if task_id is None:
        return jsonify({'error': '任务正在运行中'}), 409
    return jsonify({'task_id': task_id})


@bp.route('/metadata', methods=['POST'])
def run_metadata():
    from flask import current_app
    data = request.get_json(silent=True) or {}
    update = bool(data.get('update', True))

    def _job():
        from preprocessing.build_metadata import build_metadata
        build_metadata(update=update)

    task_id = current_app.task_runner.start(_job)
    if task_id is None:
        return jsonify({'error': '任务正在运行中'}), 409
    return jsonify({'task_id': task_id})


@bp.route('/all', methods=['POST'])
def run_all():
    from flask import current_app
    data = request.get_json(silent=True) or {}
    update = bool(data.get('update', True))

    def _job():
        print("[预处理] 1/4 收集 DLC CSV")
        from preprocessing.collect_csv import main as collect_main
        collect_main()

        print("[预处理] 2/4 修复 CSV")
        from preprocessing.fix_csv import main as fix_main
        fix_main()

        print("[预处理] 3/4 按 metadata 分组")
        from preprocessing.group_csv import group_by_metadata
        group_by_metadata()

        print("[预处理] 4/4 生成/更新 metadata")
        from preprocessing.build_metadata import build_metadata
        build_metadata(update=update)

    task_id = current_app.task_runner.start(_job)
    if task_id is None:
        return jsonify({'error': '任务正在运行中'}), 409
    return jsonify({'task_id': task_id})
