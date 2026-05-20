"""
数据分析
"""
import os
import tkinter as tk
from tkinter import ttk

import sys
import os
# 确保顶层 config.py 优先于 config/ 包
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import config as cfg

from config.paths import OF_ROI_JSON, EPM_ROI_JSON, TCT_ROI_JSON
from gui.i18n import (
    ANALYZE_TITLE, ANALYZE_EXPERIMENTS, ANALYZE_PARAMS,
    ANALYZE_RUN, ANALYZE_TIME, ANALYZE_LIKELIHOOD, ANALYZE_FPS,
    ROI_CONFIGURED, ROI_NOT_CONFIGURED, STATUS_IDLE,
)


EXPERIMENTS = ['OF', 'EPM', 'TCT']


class AnalyzeFrame(ttk.Frame):
    def __init__(self, parent, app=None):
        super().__init__(parent, style='Content.TFrame')
        self.app = app
        self._build_ui()

    def _build_ui(self):
        ttk.Label(self, text=ANALYZE_TITLE, style='Title.TLabel').pack(
            anchor='w', padx=16, pady=(12, 8))

        body = ttk.Frame(self)
        body.pack(fill='both', expand=True, padx=16)

        # ---- 实验选择 ----
        exp_frame = ttk.LabelFrame(body, text=ANALYZE_EXPERIMENTS, padding=8)
        exp_frame.pack(fill='x', pady=(0, 8))

        self.of_var = tk.BooleanVar(value=True)
        self.epm_var = tk.BooleanVar(value=True)
        self.tct_var = tk.BooleanVar(value=True)

        for var, name, json_path in [
            (self.of_var, 'OF 旷场', OF_ROI_JSON),
            (self.epm_var, 'EPM 高架十字', EPM_ROI_JSON),
            (self.tct_var, 'TCT 三箱', TCT_ROI_JSON),
        ]:
            row = ttk.Frame(exp_frame)
            row.pack(fill='x', pady=2)
            ttk.Checkbutton(row, text=name, variable=var).pack(side='left')
            if json_path.exists():
                ttk.Label(row, text=f"  ({ROI_CONFIGURED})",
                          foreground='#27ae60').pack(side='left')
            else:
                ttk.Label(row, text=f"  ({ROI_NOT_CONFIGURED})",
                          foreground='#e74c3c').pack(side='left')

        # ---- 参数设置 ----
        param_frame = ttk.LabelFrame(body, text=ANALYZE_PARAMS, padding=8)
        param_frame.pack(fill='x', pady=(0, 8))

        # FPS
        row1 = ttk.Frame(param_frame)
        row1.pack(fill='x', pady=2)
        ttk.Label(row1, text=ANALYZE_FPS, width=16, anchor='e').pack(side='left')
        self.fps_var = tk.IntVar(value=cfg.FPS)
        ttk.Spinbox(row1, from_=1, to=120, textvariable=self.fps_var,
                    width=8).pack(side='left', padx=(8, 0))

        # 置信度
        row2 = ttk.Frame(param_frame)
        row2.pack(fill='x', pady=2)
        ttk.Label(row2, text=ANALYZE_LIKELIHOOD, width=16, anchor='e').pack(side='left')
        self.likelihood_var = tk.DoubleVar(value=cfg.LIKELIHOOD_THRESHOLD)
        ttk.Spinbox(row2, from_=0.0, to=1.0, increment=0.05,
                    textvariable=self.likelihood_var, width=8).pack(side='left', padx=(8, 0))

        # 分析时长
        time_frame = ttk.Frame(param_frame)
        time_frame.pack(fill='x', pady=2)
        ttk.Label(time_frame, text=ANALYZE_TIME, width=16, anchor='e').pack(side='left')

        self.of_time_var = tk.IntVar(value=cfg.OF_ANALYSIS_MINUTES)
        self.epm_time_var = tk.IntVar(value=cfg.EPM_ANALYSIS_MINUTES)
        self.tct_time_var = tk.IntVar(value=cfg.TCT_ANALYSIS_MINUTES)

        ttk.Label(time_frame, text="OF:").pack(side='left', padx=(8, 2))
        ttk.Spinbox(time_frame, from_=1, to=60, textvariable=self.of_time_var,
                    width=4).pack(side='left')
        ttk.Label(time_frame, text="EPM:").pack(side='left', padx=(8, 2))
        ttk.Spinbox(time_frame, from_=1, to=60, textvariable=self.epm_time_var,
                    width=4).pack(side='left')
        ttk.Label(time_frame, text="TCT:").pack(side='left', padx=(8, 2))
        ttk.Spinbox(time_frame, from_=1, to=60, textvariable=self.tct_time_var,
                    width=4).pack(side='left')

        # ---- 运行按钮 ----
        btn_frame = ttk.Frame(body)
        btn_frame.pack(fill='x', pady=8)
        ttk.Button(btn_frame, text=ANALYZE_RUN, style='Action.TButton',
                   command=self._run_analysis).pack(side='left')

        self.status_label = ttk.Label(btn_frame, text=STATUS_IDLE, style='Status.TLabel')
        self.status_label.pack(side='left', padx=(12, 0))

    def _run_analysis(self):
        if not self.app or not self.app.worker:
            return
        self.status_label.configure(text="运行中...", foreground='#1a73e8')

        run_of = self.of_var.get()
        run_epm = self.epm_var.get()
        run_tct = self.tct_var.get()
        fps = self.fps_var.get()
        likelihood = self.likelihood_var.get()
        of_time = self.of_time_var.get()
        epm_time = self.epm_time_var.get()
        tct_time = self.tct_time_var.get()

        def _job():
            from gui.utils import temp_patch

            if run_of:
                import experiments.OF.analyze as of_mod
                with temp_patch(of_mod, ANALYSIS_MINUTES=of_time, FPS=fps,
                                LIKELIHOOD_THRESHOLD=likelihood):
                    of_mod.process_all()

            if run_epm:
                import experiments.EPM.analyze as epm_mod
                with temp_patch(epm_mod, ANALYSIS_MINUTES=epm_time, FPS=fps,
                                LIKELIHOOD_THRESHOLD=likelihood):
                    epm_mod.process_all()

            if run_tct:
                import experiments.TCT.analyze as tct_mod
                with temp_patch(tct_mod, ANALYSIS_MINUTES=tct_time, FPS=fps,
                                LIKELIHOOD_THRESHOLD=likelihood):
                    tct_mod.process_tct_full_visual()

        def _on_done(success):
            if success:
                self.status_label.configure(text="完成", foreground='#27ae60')
            else:
                self.status_label.configure(text="出错", foreground='#e74c3c')

        self.app.worker.run(_job, on_done=_on_done)
