"""
日志控制台 — 仿终端风格，捕获 sys.stdout 输出
"""
import tkinter as tk
from tkinter import ttk


class LogConsole(tk.Text):
    """黑底绿字日志控件，实现 write()/flush() 接口可替换 sys.stdout"""

    def __init__(self, parent, **kwargs):
        kwargs.setdefault('bg', '#1e1e1e')
        kwargs.setdefault('fg', '#00ff00')
        kwargs.setdefault('font', ('Consolas', 9))
        kwargs.setdefault('insertbackground', '#00ff00')
        kwargs.setdefault('state', 'disabled')
        kwargs.setdefault('wrap', 'word')
        kwargs.setdefault('height', 8)
        super().__init__(parent, **kwargs)

        self._tags_configured = False

    def _ensure_tags(self):
        if self._tags_configured:
            return
        self.tag_config('error', foreground='#ff6b6b')
        self.tag_config('info', foreground='#69b4ff')
        self._tags_configured = True

    def write(self, message):
        if not message:
            return
        self._ensure_tags()
        self.configure(state='normal')
        tag = ''
        if 'error' in message.lower() or 'traceback' in message.lower():
            tag = 'error'
        self.insert('end', message, tag)
        self.see('end')
        self.configure(state='disabled')

    def flush(self):
        pass

    def clear(self):
        self.configure(state='normal')
        self.delete('1.0', 'end')
        self.configure(state='disabled')

    def redirect_stdout(self):
        """上下文管理器：临时将 sys.stdout 重定向到此控件"""
        import sys
        return _StdoutRedirector(self)


class _StdoutRedirector:
    def __init__(self, console):
        self.console = console
        self._original = None
        self._original_stderr = None

    def __enter__(self):
        import sys
        self._original = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = self.console
        sys.stderr = self.console
        return self.console

    def __exit__(self, *args):
        import sys
        sys.stdout = self._original
        sys.stderr = self._original_stderr
