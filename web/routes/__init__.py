"""路由注册"""
from web.routes import (
    import_routes, dlc_routes, preprocess_routes,
    roi_routes, analyze_routes, plot_routes,
    metadata_routes, status_routes, task_routes,
)


def register_all(app):
    app.register_blueprint(import_routes.bp)
    app.register_blueprint(dlc_routes.bp)
    app.register_blueprint(preprocess_routes.bp)
    app.register_blueprint(roi_routes.bp)
    app.register_blueprint(analyze_routes.bp)
    app.register_blueprint(plot_routes.bp)
    app.register_blueprint(metadata_routes.bp)
    app.register_blueprint(status_routes.bp)
    app.register_blueprint(task_routes.bp)

    @app.route('/')
    def index():
        from flask import render_template
        return render_template('base.html')
