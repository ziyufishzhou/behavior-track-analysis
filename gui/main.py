"""
行为分析工作台 — 主窗口
"""
import tkinter as tk
from tkinter import ttk

import matplotlib
matplotlib.use('Agg')

from gui.i18n import APP_TITLE, NAV_LIST
from gui.styles import configure_styles
from gui.widgets.log_console import LogConsole
from gui.workers import ThreadWorker


class BehaviorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry('1100x720')
        self.minsize(900, 600)

        configure_styles(self)

        self.worker = None
        self.log_console = None
        self.frames = {}
        self.current_nav = None

        self._build_ui()

    def _build_ui(self):
        # 主容器
        main = ttk.PanedWindow(self, orient='horizontal')
        main.pack(fill='both', expand=True)

        # 侧边栏
        sidebar = ttk.Frame(main, style='Sidebar.TFrame', width=160)
        main.add(sidebar, weight=0)

        for name in NAV_LIST:
            btn = ttk.Button(
                sidebar, text=name, style='Nav.TButton',
                command=lambda n=name: self._switch(n),
            )
            btn.pack(fill='x', padx=6, pady=3)
            setattr(self, f'_nav_{id(btn)}', btn)

        # 右侧区域
        right = ttk.Frame(main)
        main.add(right, weight=1)

        # 内容区
        self.content = ttk.Frame(right, style='Content.TFrame')
        self.content.pack(fill='both', expand=True)

        # 日志控制台
        log_frame = ttk.Frame(right)
        log_frame.pack(fill='x', side='bottom')
        self.log_console = LogConsole(log_frame)
        log_scroll = ttk.Scrollbar(log_frame, command=self.log_console.yview)
        self.log_console.configure(yscrollcommand=log_scroll.set)
        log_scroll.pack(side='right', fill='y')
        self.log_console.pack(fill='x')

        self.worker = ThreadWorker(self.log_console)

        # 延迟导入 frame 类，避免循环依赖
        self._frame_classes = self._load_frame_classes()

        # 默认显示第一个页面
        self._switch(NAV_LIST[0])

    def _load_frame_classes(self):
        from gui.frames.import_frame import ImportFrame
        from gui.frames.dlc_frame import DLCFrame
        from gui.frames.preprocess_frame import PreprocessFrame
        from gui.frames.roi_frame import ROIFrame
        from gui.frames.analyze_frame import AnalyzeFrame
        from gui.frames.plot_frame import PlotFrame
        return {
            NAV_LIST[0]: ImportFrame,
            NAV_LIST[1]: DLCFrame,
            NAV_LIST[2]: PreprocessFrame,
            NAV_LIST[3]: ROIFrame,
            NAV_LIST[4]: AnalyzeFrame,
            NAV_LIST[5]: PlotFrame,
        }

    def _switch(self, name):
        if name == self.current_nav:
            return

        # 销毁当前内容
        for widget in self.content.winfo_children():
            widget.destroy()

        # 创建新 frame
        cls = self._frame_classes.get(name)
        if cls:
            frame = cls(self.content, app=self)
            frame.pack(fill='both', expand=True)
            self.current_nav = name


def main():
    app = BehaviorApp()
    app.mainloop()


if __name__ == '__main__':
    main()
