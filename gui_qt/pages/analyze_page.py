"""数据分析页面"""
import sys
import os
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QGroupBox, QSpinBox, QDoubleSpinBox,
)
from config.paths import OF_ROI_JSON, EPM_ROI_JSON, TCT_ROI_JSON

# 从顶层 config.py 读取参数（非 config/ 包）
import importlib.util
_cfg_path = os.path.join(_project_root, 'config.py')
_spec = importlib.util.spec_from_file_location('_project_config', _cfg_path)
_project_config = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_project_config)


class AnalyzePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        title = QLabel("数据分析")
        title.setProperty('class', 'title')
        layout.addWidget(title)

        # 实验选择
        exp_group = QGroupBox("实验选择")
        exp_layout = QVBoxLayout(exp_group)

        self.of_check = QCheckBox("OF 旷场")
        self.of_check.setChecked(True)
        self.epm_check = QCheckBox("EPM 高架十字")
        self.epm_check.setChecked(True)
        self.tct_check = QCheckBox("TCT 三箱")
        self.tct_check.setChecked(True)

        for check, json_path in [
            (self.of_check, OF_ROI_JSON),
            (self.epm_check, EPM_ROI_JSON),
            (self.tct_check, TCT_ROI_JSON),
        ]:
            row = QHBoxLayout()
            row.addWidget(check)
            if json_path.exists():
                status = QLabel("已配置 ROI")
                status.setStyleSheet("color: #A6E3A1; font-size: 11px;")
            else:
                status = QLabel("未配置 ROI")
                status.setStyleSheet("color: #F38BA8; font-size: 11px;")
            row.addWidget(status)
            row.addStretch()
            exp_layout.addLayout(row)

        layout.addWidget(exp_group)

        # 参数设置
        param_group = QGroupBox("参数设置")
        param_layout = QVBoxLayout(param_group)

        # FPS
        fps_row = QHBoxLayout()
        fps_row.addWidget(QLabel("FPS:"))
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(_project_config.FPS)
        fps_row.addWidget(self.fps_spin)
        fps_row.addStretch()
        param_layout.addLayout(fps_row)

        # 置信度
        like_row = QHBoxLayout()
        like_row.addWidget(QLabel("置信度阈值:"))
        self.like_spin = QDoubleSpinBox()
        self.like_spin.setRange(0.0, 1.0)
        self.like_spin.setSingleStep(0.05)
        self.like_spin.setValue(_project_config.LIKELIHOOD_THRESHOLD)
        like_row.addWidget(self.like_spin)
        like_row.addStretch()
        param_layout.addLayout(like_row)

        # 分析时长
        time_row = QHBoxLayout()
        time_row.addWidget(QLabel("分析时长 (分钟):"))
        time_row.addWidget(QLabel("OF"))
        self.of_time = QSpinBox()
        self.of_time.setRange(1, 60)
        self.of_time.setValue(_project_config.OF_ANALYSIS_MINUTES)
        time_row.addWidget(self.of_time)
        time_row.addWidget(QLabel("EPM"))
        self.epm_time = QSpinBox()
        self.epm_time.setRange(1, 60)
        self.epm_time.setValue(_project_config.EPM_ANALYSIS_MINUTES)
        time_row.addWidget(self.epm_time)
        time_row.addWidget(QLabel("TCT"))
        self.tct_time = QSpinBox()
        self.tct_time.setRange(1, 60)
        self.tct_time.setValue(_project_config.TCT_ANALYSIS_MINUTES)
        time_row.addWidget(self.tct_time)
        time_row.addStretch()
        param_layout.addLayout(time_row)

        layout.addWidget(param_group)

        # 运行
        btn_row = QHBoxLayout()
        btn_run = QPushButton("开始分析")
        btn_run.setProperty('class', 'success')
        btn_run.clicked.connect(self._run_analysis)
        btn_row.addWidget(btn_run)
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #6C7086; font-weight: bold;")
        btn_row.addWidget(self.status_label)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addStretch()

    def _run_analysis(self):
        run_of = self.of_check.isChecked()
        run_epm = self.epm_check.isChecked()
        run_tct = self.tct_check.isChecked()
        fps = self.fps_spin.value()
        likelihood = self.like_spin.value()
        of_time = self.of_time.value()
        epm_time = self.epm_time.value()
        tct_time = self.tct_time.value()

        self.status_label.setText("运行中...")
        self.status_label.setStyleSheet("color: #89B4FA; font-weight: bold;")

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
                self.status_label.setText("完成")
                self.status_label.setStyleSheet("color: #A6E3A1; font-weight: bold;")
            else:
                self.status_label.setText("出错")
                self.status_label.setStyleSheet("color: #F38BA8; font-weight: bold;")

        self.main.worker.run(_job, on_done=_on_done)
