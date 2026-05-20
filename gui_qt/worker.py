"""QThread 后台任务执行器"""
import threading
from PySide6.QtCore import QThread, Signal, QObject


class _WorkerSignals(QObject):
    finished = Signal(bool)
    message = Signal(str)


class ThreadWorker:
    """单任务后台执行器，用 QThread 通知主线程"""

    def __init__(self, log_console=None):
        self.console = log_console
        self._running = False
        self._signals = _WorkerSignals()

    @property
    def running(self):
        return self._running

    @property
    def finished(self):
        return self._signals.finished

    def run(self, func, on_done=None, **kwargs):
        if self._running:
            if self.console:
                self.console.write("[提示] 任务正在运行中，请等待完成\n")
            return

        self._running = True

        def _job():
            success = True
            try:
                if self.console:
                    with self.console.redirect_stdout():
                        func(**kwargs)
                else:
                    func(**kwargs)
            except Exception as e:
                if self.console:
                    self.console.write(f"[错误] {e}\n")
                success = False
            finally:
                self._running = False
                self._signals.finished.emit(success)
                if on_done:
                    on_done(success)

        t = threading.Thread(target=_job, daemon=True)
        t.start()