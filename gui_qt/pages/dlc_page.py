"""DLC 分析页面"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSpinBox, QDoubleSpinBox, QGroupBox, QListWidget,
    QFileDialog,
)
from config.paths import MODELS_DIR, METADATA_FILE, VIDEO_DIR
import pandas as pd


class DLCPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        title = QLabel("DeepLabCut 视频分析")
        title.setProperty('class', 'title')
        layout.addWidget(title)

        # 模型路径
        model_group = QGroupBox("模型路径")
        model_layout = QHBoxLayout(model_group)
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("选择 DLC 模型目录 (含 config.yaml)")
        model_layout.addWidget(self.model_edit)
        btn_model = QPushButton("选择")
        btn_model.clicked.connect(self._select_model)
        model_layout.addWidget(btn_model)
        layout.addWidget(model_group)

        # 参数
        param_group = QGroupBox("参数")
        param_layout = QHBoxLayout(param_group)
        param_layout.addWidget(QLabel("Shuffle:"))
        self.shuffle_spin = QSpinBox()
        self.shuffle_spin.setRange(1, 100)
        self.shuffle_spin.setValue(1)
        param_layout.addWidget(self.shuffle_spin)
        param_layout.addWidget(QLabel("  置信度:"))
        self.conf_spin = QDoubleSpinBox()
        self.conf_spin.setRange(0.0, 1.0)
        self.conf_spin.setSingleStep(0.05)
        self.conf_spin.setValue(0.6)
        param_layout.addWidget(self.conf_spin)
        param_layout.addStretch()
        layout.addWidget(param_group)

        # 视频列表
        vid_group = QGroupBox("待分析视频")
        vid_layout = QVBoxLayout(vid_group)
        top_row = QHBoxLayout()
        btn_refresh = QPushButton("刷新列表")
        btn_refresh.clicked.connect(self._refresh_videos)
        top_row.addWidget(btn_refresh)
        top_row.addStretch()
        vid_layout.addLayout(top_row)
        self.video_lb = QListWidget()
        vid_layout.addWidget(self.video_lb)
        layout.addWidget(vid_group, stretch=1)

        # 运行
        btn_row = QHBoxLayout()
        btn_run = QPushButton("开始 DLC 分析")
        btn_run.setProperty('class', 'success')
        btn_run.clicked.connect(self._run_dlc)
        btn_row.addWidget(btn_run)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # 自动查找模型
        self._auto_find_model()

    def _auto_find_model(self):
        if not MODELS_DIR.exists():
            return
        for d in sorted(MODELS_DIR.iterdir()):
            if d.is_dir() and (d / 'config.yaml').exists():
                self.model_edit.setText(str(d))
                return

    def _select_model(self):
        d = QFileDialog.getExistingDirectory(self, "选择 DLC 模型目录", str(MODELS_DIR))
        if d:
            self.model_edit.setText(d)

    def _refresh_videos(self):
        self.video_lb.clear()
        if not METADATA_FILE.exists():
            return
        df = pd.read_excel(str(METADATA_FILE))
        for _, row in df.iterrows():
            fname = str(row.get('FileName', '')).strip()
            if not fname:
                continue
            video_name = fname.replace('_result.csv', '').replace('.csv', '')
            found = False
            if VIDEO_DIR.exists():
                for f in VIDEO_DIR.iterdir():
                    if f.stem == video_name and f.is_file():
                        self.video_lb.addItem(f"{video_name}  ({row.get('Experiment','')} / {row.get('Group','')})")
                        found = True
                        break
            if not found:
                self.video_lb.addItem(f"{video_name}  (视频未找到)")

    def _run_dlc(self):
        model_path = self.model_edit.text().strip()
        if not model_path or not os.path.exists(os.path.join(model_path, 'config.yaml')):
            if self.main.log_console:
                self.main.log_console.write("[错误] 请选择有效的 DLC 模型路径\n")
            return
        config_path = os.path.join(model_path, 'config.yaml')
        shuffle = self.shuffle_spin.value()

        def _job():
            import deeplabcut
            if not METADATA_FILE.exists():
                print("metadata.xlsx 不存在")
                return
            df = pd.read_excel(str(METADATA_FILE))
            videos = []
            if VIDEO_DIR.exists():
                for _, row in df.iterrows():
                    fname = str(row.get('FileName', '')).strip()
                    video_name = fname.replace('_result.csv', '').replace('.csv', '')
                    for f in VIDEO_DIR.iterdir():
                        if f.stem == video_name and f.is_file():
                            videos.append(str(f))
                            break
            if not videos:
                print("没有找到视频文件")
                return
            print(f"开始 DLC 分析: {len(videos)} 个视频")
            deeplabcut.analyze_videos(config_path, videos, shuffle=shuffle, save_as_csv=True)
            print("DLC 分析完成")

        self.main.worker.run(_job)