"""深色终端风格日志控制台"""
import sys
from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat
from PySide6.QtCore import Qt


class LogConsole(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('log_console')
        self.setReadOnly(True)
        self.setMaximumHeight(180)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

    def write(self, message):
        if not message:
            return
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        fmt = QTextCharFormat()
        low = message.lower()
        if 'error' in low or 'traceback' in low or '❌' in message:
            fmt.setForeground(QColor('#F38BA8'))
        elif 'warn' in low or '⚠' in message:
            fmt.setForeground(QColor('#FAB387'))
        else:
            fmt.setForeground(QColor('#A6E3A1'))

        cursor.insertText(message, fmt)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def flush(self):
        pass

    def clear(self):
        super().clear()

    def redirect_stdout(self):
        return _StdoutRedirector(self)


class _StdoutRedirector:
    def __init__(self, console):
        self.console = console
        self._old_stdout = None
        self._old_stderr = None

    def __enter__(self):
        self._old_stdout = sys.stdout
        self._old_stderr = sys.stderr
        sys.stdout = self.console
        sys.stderr = self.console
        return self.console

    def __exit__(self, *args):
        sys.stdout = self._old_stdout
        sys.stderr = self._old_stderr