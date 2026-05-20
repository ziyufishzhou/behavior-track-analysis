"""
预处理流水线
"""
import tkinter as tk
from tkinter import ttk

from gui.i18n import (
    PREP_TITLE, PREP_FIX, PREP_GROUP, PREP_METADATA,
    PREP_RUN_ALL, PREP_UPDATE_MODE,
    STATUS_IDLE, STATUS_RUNNING, STATUS_DONE,
)


class PreprocessFrame(ttk.Frame):
    def __init__(self, parent, app=None):
        super().__init__(parent, style='Content.TFrame')
        self.app = app
        self.step_status = {'fix': STATUS_IDLE, 'group': STATUS_IDLE, 'meta': STATUS_IDLE}
        self._build_ui()

    def _build_ui(self):
        ttk.Label(self, text=PREP_TITLE, style='Title.TLabel').pack(
            anchor='w', padx=16, pady=(12, 8))

        body = ttk.Frame(self)
        body.pack(fill='both', expand=True, padx=16)

        steps = [
            ('fix', PREP_FIX, '置信度过滤 + 插值 + 空笼检测', self._run_fix),
            ('group', PREP_GROUP, '根据 metadata 标签将 CSV 分组到对应目录', self._run_group),
            ('meta', PREP_METADATA, '扫描 grouped/ 生成 metadata.xlsx', self._run_metadata),
        ]

        self.status_labels = {}
        self.step_buttons = {}

        for key, title, desc, cmd in steps:
            frame = ttk.LabelFrame(body, text=f"  {title}  ", padding=10)
            frame.pack(fill='x', pady=4)

            ttk.Label(frame, text=desc, style='Status.TLabel').pack(anchor='w')

            row = ttk.Frame(frame)
            row.pack(fill='x', pady=(6, 0))

            btn = ttk.Button(row, text="运行", style='Step.TButton', command=cmd)
            btn.pack(side='left')
            self.step_buttons[key] = btn

            status = ttk.Label(row, text=STATUS_IDLE, style='Status.TLabel', foreground='#888')
            status.pack(side='left', padx=(8, 0))
            self.status_labels[key] = status

        # 更新模式选项（元数据步骤）
        self.update_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(body, text=PREP_UPDATE_MODE,
                        variable=self.update_var).pack(anchor='w', pady=(8, 0))

        # 一键全流程
        ttk.Separator(body, orient='horizontal').pack(fill='x', pady=12)
        ttk.Button(body, text=PREP_RUN_ALL, style='Action.TButton',
                   command=self._run_all).pack(anchor='w')

    def _set_status(self, key, text, color='#888'):
        self.status_labels[key].configure(text=text, foreground=color)

    def _disable_all(self):
        for btn in self.step_buttons.values():
            btn.configure(state='disabled')

    def _enable_all(self):
        for btn in self.step_buttons.values():
            btn.configure(state='normal')

    def _run_fix(self):
        self._set_status('fix', STATUS_RUNNING, '#1a73e8')
        if self.app and self.app.worker:
            self.app.worker.run(
                self._fix_job,
                on_done=lambda ok: self._on_done('fix', ok),
            )

    def _run_group(self):
        self._set_status('group', STATUS_RUNNING, '#1a73e8')
        if self.app and self.app.worker:
            self.app.worker.run(
                self._group_job,
                on_done=lambda ok: self._on_done('group', ok),
            )

    def _run_metadata(self):
        self._set_status('meta', STATUS_RUNNING, '#1a73e8')
        update = self.update_var.get()
        if self.app and self.app.worker:
            self.app.worker.run(
                lambda: self._metadata_job(update),
                on_done=lambda ok: self._on_done('meta', ok),
            )

    def _run_all(self):
        self._set_status('fix', STATUS_RUNNING, '#1a73e8')
        self._set_status('group', STATUS_RUNNING, '#1a73e8')
        self._set_status('meta', STATUS_RUNNING, '#1a73e8')
        if self.app and self.app.worker:
            self.app.worker.run(
                self._all_job,
                on_done=lambda ok: (
                    self._on_done('fix', ok),
                    self._on_done('group', ok),
                    self._on_done('meta', ok),
                ),
            )

    def _on_done(self, key, success):
        if success:
            self._set_status(key, STATUS_DONE, '#27ae60')
        else:
            self._set_status(key, '出错', '#e74c3c')

    @staticmethod
    def _fix_job():
        from preprocessing.fix_csv import main
        main()

    @staticmethod
    def _group_job():
        from preprocessing.group_csv import group_by_metadata, main
        try:
            group_by_metadata()
        except Exception:
            main()

    @staticmethod
    def _metadata_job(update=False):
        from preprocessing.build_metadata import build_metadata
        build_metadata(update=update)

    def _all_job(self):
        self._fix_job()
        self._group_job()
        self._metadata_job(update=self.update_var.get())
