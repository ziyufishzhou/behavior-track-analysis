"""预处理页面"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QCheckBox,
)


class PreprocessPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        title = QLabel("CSV 预处理流水线")
        title.setProperty('class', 'title')
        layout.addWidget(title)

        # 三步
        self.step_status = {}
        self.status_labels = {}

        steps = [
            ('fix', '修复 CSV', '修复 DLC 输出的 CSV 文件'),
            ('group', '按标签分组', '将 CSV 复制到 grouped/ 对应目录'),
            ('meta', '构建元数据', '扫描 grouped/ 生成 metadata.xlsx'),
        ]

        for key, name, desc in steps:
            group = QGroupBox(name)
            row = QHBoxLayout(group)
            lbl = QLabel(desc)
            lbl.setProperty('class', 'status')
            row.addWidget(lbl)
            row.addStretch()

            status = QLabel("就绪")
            status.setStyleSheet("color: #6C7086; font-weight: bold;")
            row.addWidget(status)
            self.status_labels[key] = status

            btn = QPushButton("运行")
            btn.setProperty('class', 'accent')
            btn.clicked.connect(lambda _, k=key: self._run_step(k))
            row.addWidget(btn)

            layout.addWidget(group)

        # 更新模式
        self.update_check = QCheckBox("更新模式 (保留手动列)")
        layout.addWidget(self.update_check)

        layout.addStretch()

        # 一键全流程
        btn_row = QHBoxLayout()
        btn_all = QPushButton("一键全流程")
        btn_all.setProperty('class', 'success')
        btn_all.clicked.connect(self._run_all)
        btn_row.addWidget(btn_all)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _run_step(self, key):
        jobs = {
            'fix': lambda: __import__('preprocessing.fix_csv', fromlist=['main']).main(),
            'group': lambda: self._group_job(),
            'meta': lambda: __import__('preprocessing.build_metadata', fromlist=['build_metadata']).build_metadata(update=self.update_check.isChecked()),
        }
        on_dones = {k: lambda ok, k=k: self._update_status(k, ok) for k in ['fix', 'group', 'meta']}
        self.main.worker.run(jobs[key], on_done=on_dones[key])

    def _group_job(self):
        try:
            from preprocessing.group_csv import group_by_metadata
            group_by_metadata()
        except Exception:
            from preprocessing.group_csv import main
            main()

    def _run_all(self):
        update = self.update_check.isChecked()

        def _job():
            from preprocessing.fix_csv import main as fix_main
            from preprocessing.group_csv import group_by_metadata
            from preprocessing.build_metadata import build_metadata
            print("=== 步骤 1: 修复 CSV ===")
            fix_main()
            print("=== 步骤 2: 按标签分组 ===")
            try:
                group_by_metadata()
            except Exception:
                from preprocessing.group_csv import main as group_main
                group_main()
            print("=== 步骤 3: 构建元数据 ===")
            build_metadata(update=update)
            print("=== 全流程完成 ===")

        self.main.worker.run(_job, on_done=lambda ok: [self._update_status(k, ok) for k in ['fix', 'group', 'meta']])

    def _update_status(self, key, success):
        colors = {True: '#A6E3A1', False: '#F38BA8'}
        texts = {True: '完成', False: '出错'}
        self.status_labels[key].setStyleSheet(f"color: {colors[success]}; font-weight: bold;")
        self.status_labels[key].setText(texts[success])