"""
DLC 分析页面
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog

from config.paths import MODELS_DIR, VIDEO_DIR, METADATA_FILE
from gui.i18n import (
    DLC_TITLE, DLC_MODEL_PATH, DLC_SELECT_MODEL,
    DLC_VIDEO_LIST, DLC_PARAMS, DLC_SHUFFLE, DLC_CONFIDENCE,
    DLC_START, DLC_NO_VIDEOS,
)
import pandas as pd


class DLCFrame(ttk.Frame):
    def __init__(self, parent, app=None):
        super().__init__(parent, style='Content.TFrame')
        self.app = app
        self._build_ui()

    def _build_ui(self):
        ttk.Label(self, text=DLC_TITLE, style='Title.TLabel').pack(
            anchor='w', padx=16, pady=(12, 8))

        body = ttk.Frame(self)
        body.pack(fill='both', expand=True, padx=16)

        # ---- 模型选择 ----
        model_frame = ttk.LabelFrame(body, text=DLC_MODEL_PATH, padding=8)
        model_frame.pack(fill='x', pady=(0, 8))

        self.model_var = tk.StringVar()
        # 自动查找模型
        default_model = ''
        if MODELS_DIR.exists():
            for d in MODELS_DIR.iterdir():
                if d.is_dir() and (d / 'config.yaml').exists():
                    default_model = str(d)
                    break

        ttk.Entry(model_frame, textvariable=self.model_var, width=60).pack(
            side='left', fill='x', expand=True, padx=(0, 6))
        self.model_var.set(default_model)
        ttk.Button(model_frame, text=DLC_SELECT_MODEL,
                   command=self._select_model).pack(side='right')

        # ---- 视频列表 ----
        video_frame = ttk.LabelFrame(body, text=DLC_VIDEO_LIST, padding=8)
        video_frame.pack(fill='both', expand=True, pady=(0, 8))

        self.video_lb = tk.Listbox(video_frame, selectmode='extended',
                                   height=10, font=('Consolas', 9))
        lb_scroll = ttk.Scrollbar(video_frame, command=self.video_lb.yview)
        self.video_lb.configure(yscrollcommand=lb_scroll.set)
        lb_scroll.pack(side='right', fill='y')
        self.video_lb.pack(fill='both', expand=True)

        ttk.Button(video_frame, text="刷新", style='Action.TButton',
                   command=self._refresh_videos).pack(anchor='w', pady=(4, 0))

        # ---- 参数 ----
        param_frame = ttk.LabelFrame(body, text=DLC_PARAMS, padding=8)
        param_frame.pack(fill='x', pady=(0, 8))

        row = ttk.Frame(param_frame)
        row.pack(fill='x')
        ttk.Label(row, text=DLC_SHUFFLE).pack(side='left', padx=(0, 4))
        self.shuffle_var = tk.IntVar(value=1)
        ttk.Spinbox(row, from_=1, to=10, textvariable=self.shuffle_var,
                    width=5).pack(side='left', padx=(0, 16))
        ttk.Label(row, text=DLC_CONFIDENCE).pack(side='left', padx=(0, 4))
        self.conf_var = tk.DoubleVar(value=0.6)
        ttk.Spinbox(row, from_=0.0, to=1.0, increment=0.05,
                    textvariable=self.conf_var, width=6).pack(side='left')

        # ---- 开始按钮 ----
        ttk.Button(body, text=DLC_START, style='Action.TButton',
                   command=self._run_dlc).pack(anchor='w', pady=4)

        # 初始化视频列表
        self._refresh_videos()

    def _select_model(self):
        d = filedialog.askdirectory(
            title=DLC_SELECT_MODEL,
            initialdir=str(MODELS_DIR) if MODELS_DIR.exists() else '.',
        )
        if d:
            self.model_var.set(d)

    def _refresh_videos(self):
        self.video_lb.delete(0, 'end')
        if not METADATA_FILE.exists():
            self.video_lb.insert('end', DLC_NO_VIDEOS)
            return

        try:
            df = pd.read_excel(str(METADATA_FILE))
            # 查找 video/ 目录中对应的视频文件
            for _, row in df.iterrows():
                fname = row.get('FileName', '')
                # FileName 是 CSV 名，需要找对应的视频
                # 去掉 _result.csv 后缀，加上视频扩展名
                video_name = fname.replace('_result.csv', '')
                # 在 video/ 目录中搜索
                found = False
                if VIDEO_DIR.exists():
                    for root, dirs, files in os.walk(str(VIDEO_DIR)):
                        for f in files:
                            if f.startswith(video_name) and not f.endswith('.csv'):
                                label = f"{f}  ({row.get('Experiment', '')}, {row.get('Group', '')}, {row.get('Condition', '')})"
                                self.video_lb.insert('end', label)
                                found = True
                                break
                        if found:
                            break
                if not found:
                    self.video_lb.insert('end', f"{video_name}.*  (视频文件未找到)")

            if self.video_lb.size() == 0:
                self.video_lb.insert('end', DLC_NO_VIDEOS)

        except Exception as e:
            self.video_lb.insert('end', f"加载失败: {e}")

    def _run_dlc(self):
        model_path = self.model_var.get()
        if not model_path or not os.path.exists(model_path):
            if self.app and self.app.log_console:
                self.app.log_console.write("[错误] 请先选择有效的 DLC 模型目录\n")
            return

        if not self.app or not self.app.worker:
            return

        shuffle = self.shuffle_var.get()

        def _dlc_job():
            import deeplabcut
            config_path = os.path.join(model_path, 'config.yaml')

            # 从 metadata 获取视频列表
            if METADATA_FILE.exists():
                df = pd.read_excel(str(METADATA_FILE))
                videos = []
                for _, row in df.iterrows():
                    fname = row.get('FileName', '').replace('_result.csv', '')
                    if VIDEO_DIR.exists():
                        for root, dirs, files in os.walk(str(VIDEO_DIR)):
                            for f in files:
                                if f.startswith(fname) and not f.endswith('.csv'):
                                    videos.append(os.path.join(root, f))
                                    break

                if videos:
                    print(f"开始 DLC 分析 {len(videos)} 个视频...")
                    deeplabcut.analyze_videos(
                        config_path, videos,
                        shuffle=shuffle,
                        save_as_csv=True,
                    )
                    print("DLC 分析完成！")
                else:
                    print("没有找到视频文件")
            else:
                print("没有找到 metadata.xlsx")

        self.app.worker.run(_dlc_job)
