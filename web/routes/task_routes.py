"""任务状态 / SSE 日志流 API"""
import json
from flask import Blueprint, Response, jsonify
from web.task_runner import TaskRunner

bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')


@bp.route('/<task_id>/stream')
def task_stream(task_id):
    from flask import current_app
    runner = current_app.task_runner

    def generate():
        for line in runner.iter_lines(task_id):
            progress = runner.get_progress(task_id)
            msg = {'text': line}
            if progress:
                msg['progress'] = progress
            yield f"data: {json.dumps(msg)}\n\n"
        status = runner.get_status(task_id)
        success = status == 'completed'
        final = {'done': True, 'success': success}
        progress = runner.get_progress(task_id)
        if progress:
            final['progress'] = progress
        yield f"data: {json.dumps(final)}\n\n"

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@bp.route('/<task_id>/status')
def task_status(task_id):
    from flask import current_app
    return jsonify({'status': current_app.task_runner.get_status(task_id)})