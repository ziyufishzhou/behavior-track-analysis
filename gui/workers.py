"""
后台线程执行器 — 在工作线程中运行耗时操作，保持 GUI 响应
"""
import threading
import tkinter as tk


class ThreadWorker:
    """在后台线程中执行函数，通过 LogConsole 捕获输出"""

    def __init__(self, log_console):
        self.console = log_console
        self._running = False

    @property
    def running(self):
        return self._running

    def run(self, func, on_done=None, **kwargs):
        """在后台线程中运行 func，完成后回调 on_done(success: bool)"""
        if self._running:
            self.console.write("[提示] 已有任务在运行中\n")
            return

        self._running = True

        def _worker():
            success = True
            try:
                with self.console.redirect_stdout():
                    func(**kwargs)
            except Exception as e:
                self.console.write(f"\n[错误] {e}\n")
                success = False
            finally:
                self._running = False
                if on_done:
                    # 在主线程中回调
                    try:
                        tk._default_root.after(0, lambda: on_done(success))
                    except Exception:
                        pass

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
