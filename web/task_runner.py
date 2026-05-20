"""后台任务执行器 — 线程 + stdout 捕获 + SSE 流"""
import re
import threading
import queue
import sys
import io
import time
import uuid
import contextlib

_PROGRESS_RE = re.compile(r'\[PROGRESS\]\s+(\d+)/(\d+)\s+(.*)')


class _QueueWriter:
    def __init__(self, q):
        self.q = q

    def write(self, text):
        if text:
            self.q.put(text)

    def flush(self):
        pass


class TaskRunner:
    def __init__(self):
        self._tasks = {}
        self._current_id = None

    def start(self, func, **kwargs):
        if self._current_id and self.is_running(self._current_id):
            return None

        task_id = str(uuid.uuid4())[:8]
        q = queue.Queue()
        self._tasks[task_id] = {
            'queue': q,
            'status': 'running',
            'started': time.time(),
            'progress': None,  # {'current': int, 'total': int, 'percent': int, 'message': str}
        }
        self._current_id = task_id

        def _job():
            writer = _QueueWriter(q)
            try:
                with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer):
                    func(**kwargs)
                self._tasks[task_id]['status'] = 'completed'
            except Exception as e:
                q.put(f"[ERROR] {e}\n")
                self._tasks[task_id]['status'] = 'failed'
            finally:
                q.put(None)

        t = threading.Thread(target=_job, daemon=True)
        self._tasks[task_id]['thread'] = t
        t.start()
        return task_id

    def is_running(self, task_id=None):
        tid = task_id or self._current_id
        task = self._tasks.get(tid)
        return task is not None and task['status'] == 'running'

    def get_status(self, task_id):
        task = self._tasks.get(task_id)
        if not task:
            return 'not_found'
        return task['status']

    def iter_lines(self, task_id):
        task = self._tasks.get(task_id)
        if not task:
            return
        q = task['queue']
        while True:
            try:
                line = q.get(timeout=0.5)
                if line is None:
                    break
                m = _PROGRESS_RE.search(line)
                if m:
                    current, total = int(m.group(1)), int(m.group(2))
                    msg = m.group(3).strip()
                    percent = int(current / total * 100) if total > 0 else 0
                    task['progress'] = {
                        'current': current,
                        'total': total,
                        'percent': percent,
                        'message': msg,
                    }
                yield line
            except queue.Empty:
                if task['status'] != 'running':
                    break

    def get_progress(self, task_id):
        task = self._tasks.get(task_id)
        return task.get('progress') if task else None
