"""
ROI 标注 — 启动独立窗口
"""
import os
import tkinter as tk
from tkinter import ttk

from config.paths import OF_ROI_JSON, EPM_ROI_JSON, TCT_ROI_JSON
from gui.i18n import (
    ROI_TITLE, ROI_OF, ROI_EPM, ROI_TCT,
    ROI_STATUS, ROI_CONFIGURED, ROI_NOT_CONFIGURED,
)


class ROIFrame(ttk.Frame):
    def __init__(self, parent, app=None):
        super().__init__(parent, style='Content.TFrame')
        self.app = app
        self._build_ui()

    def _build_ui(self):
        ttk.Label(self, text=ROI_TITLE, style='Title.TLabel').pack(
            anchor='w', padx=16, pady=(12, 8))

        body = ttk.Frame(self)
        body.pack(fill='both', expand=True, padx=16)

        ttk.Label(body, text="点击下方按钮启动对应实验的 ROI 标注工具：",
                  style='Section.TLabel').pack(anchor='w', pady=(0, 12))

        tools = [
            (ROI_OF, self._launch_of, OF_ROI_JSON),
            (ROI_EPM, self._launch_epm, EPM_ROI_JSON),
            (ROI_TCT, self._launch_tct, TCT_ROI_JSON),
        ]

        for label, cmd, json_path in tools:
            frame = ttk.Frame(body)
            frame.pack(fill='x', pady=4)

            ttk.Button(frame, text=label, style='Action.TButton',
                       command=cmd).pack(side='left')

            if json_path.exists():
                ttk.Label(frame, text=f"  {ROI_CONFIGURED} ({json_path.name})",
                          foreground='#27ae60').pack(side='left', padx=8)
            else:
                ttk.Label(frame, text=f"  {ROI_NOT_CONFIGURED}",
                          foreground='#e74c3c').pack(side='left', padx=8)

    def _launch_of(self):
        self._launch_roi_tool('of')

    def _launch_epm(self):
        self._launch_roi_tool('epm')

    def _launch_tct(self):
        self._launch_roi_tool('tct')

    def _launch_roi_tool(self, experiment):
        """在独立窗口中启动 ROI 工具"""
        try:
            if experiment == 'of':
                from experiments.OF.roi_tool import ROIAnnotator
                ROIAnnotator()
            elif experiment == 'epm':
                from experiments.EPM.roi_tool import EPMAnnotator
                EPMAnnotator()
            elif experiment == 'tct':
                from experiments.TCT.roi_tool import TCTAnnotator
                TCTAnnotator()
        except Exception as e:
            if self.app and self.app.log_console:
                self.app.log_console.write(f"[错误] 启动 ROI 工具失败: {e}\n")
