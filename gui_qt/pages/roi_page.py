"""ROI 标注页面"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox,
)
from PySide6.QtCore import Qt
from config.paths import OF_ROI_JSON, EPM_ROI_JSON, TCT_ROI_JSON


class ROIPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        title = QLabel("ROI 区域标注")
        title.setProperty('class', 'title')
        layout.addWidget(title)

        desc = QLabel("点击下方按钮启动对应实验的 ROI 标注工具（独立窗口）")
        desc.setProperty('class', 'status')
        layout.addWidget(desc)

        tools = [
            ("OF 旷场 ROI 标注", self._launch_of, OF_ROI_JSON),
            ("EPM 高架十字 ROI", self._launch_epm, EPM_ROI_JSON),
            ("TCT 三箱 ROI 标注", self._launch_tct, TCT_ROI_JSON),
        ]

        for label, cmd, json_path in tools:
            group = QGroupBox(label)
            row = QHBoxLayout(group)

            btn = QPushButton("启动标注工具")
            btn.setProperty('class', 'accent')
            btn.clicked.connect(cmd)
            row.addWidget(btn)

            if json_path.exists():
                status = QLabel("已配置")
                status.setStyleSheet("color: #A6E3A1; font-weight: bold;")
            else:
                status = QLabel("未配置")
                status.setStyleSheet("color: #F38BA8; font-weight: bold;")
            row.addWidget(status)
            row.addStretch()

            layout.addWidget(group)

        layout.addStretch()

    def _launch_of(self):
        self._launch_tool('of')

    def _launch_epm(self):
        self._launch_tool('epm')

    def _launch_tct(self):
        self._launch_tool('tct')

    def _launch_tool(self, experiment):
        # 用子进程启动，避免 Qt/tkinter 冲突
        scripts = {
            'of': 'experiments/OF/roi_tool.py',
            'epm': 'experiments/EPM/roi_tool.py',
            'tct': 'experiments/TCT/roi_tool.py',
        }
        script = scripts.get(experiment)
        if script:
            import subprocess
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            full_path = os.path.join(project_root, script)
            subprocess.Popen(['python', full_path], cwd=project_root)
            if self.main.log_console:
                self.main.log_console.write(f"[提示] 已启动 {experiment.upper()} ROI 标注工具\n")
