"""
绘图设置 — 颜色/图表类型/参数
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, colorchooser
import pandas as pd

from config.paths import (
    OF_SUMMARY, EPM_SUMMARY, TCT_SUMMARY,
    OF_FIGURES, EPM_FIGURES, TCT_FIGURES,
)
from gui.i18n import (
    PLOT_TITLE, PLOT_EXPERIMENT, PLOT_DATA_SOURCE,
    PLOT_CHART_TYPE, PLOT_BAR, PLOT_LINE,
    PLOT_COLORS, PLOT_PARAMS, PLOT_GENERATE, PLOT_OPEN_DIR,
)
from gui.utils import find_latest_summary


EXPERIMENTS = ['OF', 'EPM', 'TCT']

# 默认颜色
DEFAULT_COLORS = {
    'saline_bar': '#D1D1D1',
    'cno_bar': '#4682B4',
    'connect_line': '#4D4D4D',
    'scatter': '#000000',
    'time_toy': '#48C9B0',
    'time_live': '#2E86C1',
    'pi_gray': '#D5D8DC',
    'pi_blue': '#5DADE2',
}


class PlotFrame(ttk.Frame):
    def __init__(self, parent, app=None):
        super().__init__(parent, style='Content.TFrame')
        self.app = app
        self.colors = dict(DEFAULT_COLORS)
        self._build_ui()

    def _build_ui(self):
        ttk.Label(self, text=PLOT_TITLE, style='Title.TLabel').pack(
            anchor='w', padx=16, pady=(12, 8))

        body = ttk.Frame(self)
        body.pack(fill='both', expand=True, padx=16)

        # ---- 实验选择 + 数据源 ----
        top = ttk.Frame(body)
        top.pack(fill='x', pady=(0, 8))

        ttk.Label(top, text=PLOT_EXPERIMENT).pack(side='left', padx=(0, 4))
        self.exp_var = tk.StringVar(value='EPM')
        ttk.Combobox(top, textvariable=self.exp_var, values=EXPERIMENTS,
                     state='readonly', width=8).pack(side='left', padx=(0, 16))

        ttk.Label(top, text=PLOT_DATA_SOURCE).pack(side='left', padx=(0, 4))
        self.source_var = tk.StringVar()
        self.source_entry = ttk.Entry(top, textvariable=self.source_var, width=40)
        self.source_entry.pack(side='left', fill='x', expand=True, padx=(0, 4))
        ttk.Button(top, text="浏览", command=self._browse_source).pack(side='left')
        ttk.Button(top, text="自动查找", command=self._auto_find).pack(side='left', padx=(4, 0))

        # ---- 图表类型 ----
        type_frame = ttk.LabelFrame(body, text=PLOT_CHART_TYPE, padding=8)
        type_frame.pack(fill='x', pady=(0, 8))

        self.chart_type_var = tk.StringVar(value='bar')
        ttk.Radiobutton(type_frame, text=PLOT_BAR, variable=self.chart_type_var,
                        value='bar').pack(side='left', padx=(0, 16))
        ttk.Radiobutton(type_frame, text=PLOT_LINE, variable=self.chart_type_var,
                        value='line').pack(side='left')

        # ---- 颜色设置 ----
        color_frame = ttk.LabelFrame(body, text=PLOT_COLORS, padding=8)
        color_frame.pack(fill='x', pady=(0, 8))

        self.color_labels = {}
        color_items = [
            ('saline_bar', 'Saline 柱'),
            ('cno_bar', 'CNO 柱'),
            ('connect_line', '连接线'),
            ('scatter', '散点'),
            ('time_toy', 'Time 图 (对照)'),
            ('time_live', 'Time 图 (实验)'),
            ('pi_gray', 'PI 图 (Saline)'),
            ('pi_blue', 'PI 图 (CNO)'),
        ]

        for i, (key, label) in enumerate(color_items):
            row = i // 2
            col = (i % 2) * 3
            ttk.Label(color_frame, text=label).grid(row=row, column=col, sticky='w', padx=(0, 4))
            color_lbl = tk.Label(color_frame, text='  ', bg=self.colors[key],
                                 relief='solid', width=4)
            color_lbl.grid(row=row, column=col+1, padx=(0, 4))
            self.color_labels[key] = color_lbl
            ttk.Button(color_frame, text="选色", width=4,
                       command=lambda k=key: self._pick_color(k)).grid(
                row=row, column=col+2, padx=(0, 12))

        # ---- 参数 ----
        param_frame = ttk.LabelFrame(body, text=PLOT_PARAMS, padding=8)
        param_frame.pack(fill='x', pady=(0, 8))

        row0 = ttk.Frame(param_frame)
        row0.pack(fill='x', pady=2)
        ttk.Label(row0, text="柱宽:").pack(side='left')
        self.bar_width_var = tk.DoubleVar(value=0.6)
        ttk.Scale(row0, from_=0.2, to=1.0, variable=self.bar_width_var,
                  orient='horizontal', length=120).pack(side='left', padx=(4, 16))
        ttk.Label(row0, text="散点大小:").pack(side='left')
        self.point_size_var = tk.IntVar(value=18)
        ttk.Scale(row0, from_=4, to=40, variable=self.point_size_var,
                  orient='horizontal', length=120).pack(side='left', padx=4)

        row1 = ttk.Frame(param_frame)
        row1.pack(fill='x', pady=2)
        ttk.Label(row1, text="误差线:").pack(side='left')
        self.errorbar_var = tk.StringVar(value='SEM')
        ttk.Combobox(row1, textvariable=self.errorbar_var,
                     values=['SEM', 'SD'], state='readonly', width=6).pack(
            side='left', padx=(4, 16))

        ttk.Label(row1, text="显著性 α:").pack(side='left')
        self.alpha_var = tk.DoubleVar(value=0.05)
        ttk.Spinbox(row1, from_=0.01, to=0.10, increment=0.01,
                    textvariable=self.alpha_var, width=5).pack(side='left', padx=4)

        row2 = ttk.Frame(param_frame)
        row2.pack(fill='x', pady=2)
        ttk.Label(row2, text="输出:").pack(side='left')
        self.pdf_var = tk.BooleanVar(value=True)
        self.png_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row2, text="PDF", variable=self.pdf_var).pack(side='left', padx=4)
        ttk.Checkbutton(row2, text="PNG", variable=self.png_var).pack(side='left', padx=4)
        ttk.Label(row2, text="  DPI:").pack(side='left')
        self.dpi_var = tk.IntVar(value=300)
        ttk.Spinbox(row2, from_=72, to=600, increment=50,
                    textvariable=self.dpi_var, width=5).pack(side='left', padx=4)

        # ---- 生成按钮 ----
        btn_frame = ttk.Frame(body)
        btn_frame.pack(fill='x', pady=8)
        ttk.Button(btn_frame, text=PLOT_GENERATE, style='Action.TButton',
                   command=self._generate).pack(side='left', padx=(0, 8))
        ttk.Button(btn_frame, text=PLOT_OPEN_DIR, style='Action.TButton',
                   command=self._open_output_dir).pack(side='left')

        # 自动查找数据源
        self._auto_find()

    def _pick_color(self, key):
        result = colorchooser.askcolor(
            initialcolor=self.colors.get(key, '#ffffff'),
            title="选择颜色",
        )
        if result[1]:
            self.colors[key] = result[1]
            self.color_labels[key].configure(bg=result[1])

    def _browse_source(self):
        path = filedialog.askopenfilename(
            title="选择数据源",
            filetypes=[('Excel', '*.xlsx'), ('所有文件', '*.*')],
        )
        if path:
            self.source_var.set(path)

    def _auto_find(self):
        exp = self.exp_var.get()
        summary_dirs = {'OF': OF_SUMMARY, 'EPM': EPM_SUMMARY, 'TCT': TCT_SUMMARY}
        patterns = {'OF': 'Summary', 'EPM': 'EPM_Summary', 'TCT': 'TCT_Complete_Data'}
        d = summary_dirs.get(exp)
        p = patterns.get(exp, '')
        if d:
            found = find_latest_summary(str(d), prefix=p)
            if found:
                self.source_var.set(found)
                return
        self.source_var.set('')

    def _generate(self):
        if not self.app or not self.app.worker:
            return
        exp = self.exp_var.get()
        source = self.source_var.get()

        if not source or not os.path.exists(source):
            if self.app.log_console:
                self.app.log_console.write("[错误] 请先选择有效的数据源文件\n")
            return

        colors = dict(self.colors)
        chart_type = self.chart_type_var.get()
        bar_width = self.bar_width_var.get()
        point_size = self.point_size_var.get()

        def _job():
            df = pd.read_excel(source)
            plot_type = 'paired' if chart_type == 'line' else chart_type
            common = {
                'chart_type': plot_type,
                'colors': {
                    'color_0': colors['saline_bar'],
                    'color_1': colors['cno_bar'],
                    'scatter': colors['scatter'],
                    'connect': colors['connect_line'],
                    'edge': '#000000',
                },
                'bar_width': bar_width,
                'point_size': point_size,
                'errorbar': self.errorbar_var.get().lower(),
                'alpha': self.alpha_var.get(),
                'pdf': self.pdf_var.get(),
                'png': self.png_var.get(),
                'dpi': self.dpi_var.get(),
            }

            if exp == 'EPM':
                import experiments.EPM.plot as epm_plot
                epm_plot.plot_epm(df, **common)

            elif exp == 'TCT':
                import experiments.TCT.plot as tct_plot
                tct_common = dict(common)
                tct_common['colors'] = {
                    'color_0': colors['time_toy'],
                    'color_1': colors['time_live'],
                    'scatter': colors['scatter'],
                    'connect': colors['connect_line'],
                    'edge': '#000000',
                }
                for phase in ['S', 'N']:
                    tct_plot.plot_tct(df, phase, **tct_common)

            elif exp == 'OF':
                import experiments.OF.plot as of_plot
                of_plot.plot_of(df, **common)

            print(f"绘图完成: {exp}")

        self.app.worker.run(_job)

    def _open_output_dir(self):
        exp = self.exp_var.get()
        dirs = {'OF': OF_FIGURES, 'EPM': EPM_FIGURES, 'TCT': TCT_FIGURES}
        d = dirs.get(exp)
        if d and d.exists():
            os.startfile(str(d))
        elif self.app and self.app.log_console:
            self.app.log_console.write(f"[提示] 输出目录不存在: {d}\n")
