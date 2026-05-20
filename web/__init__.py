"""Flask Web 应用 — 行为分析工作台"""
import os
import sys

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import matplotlib
matplotlib.use('Agg')

from flask import Flask


def create_app():
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    app.config['SECRET_KEY'] = 'behavior-analyze-local'

    from web.task_runner import TaskRunner
    app.task_runner = TaskRunner()

    from web.routes import register_all
    register_all(app)

    return app
