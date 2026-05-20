"""绘图设置页面"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QRadioButton, QCheckBox,
    QGroupBox, QDoubleSpinBox, QSpinBox, QFileDialog, QColorDialog,
)
from PySide6.QtGui import QColor
from config.paths import (
    OF_SUMMARY, EPM_SUMMARY, TCT_SUMMARY,
    OF_FIGURES, EPM_FIGURES, TCT_FIGURES,
)
from gui.utils import find_latest_summary
import pandas as pd


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

COLOR_LABELS = [
    ('saline_bar', 'Saline 柱'),
    ('cno_bar', 'CNO 柱'),
    ('connect_line', '连接线'),
    ('scatter', '散点'),
    ('time_toy', 'Time (对照)'),
    ('time_live', 'Time (实验)'),
    ('pi_gray', 'PI (Saline)'),
    ('pi_blue', 'PI (CNO)'),
]


class PlotPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self.colors = dict(DEFAULT_COLORS)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        title = QLabel("绘图设置")
        title.setProperty('class', 'title')
        layout.addWidget(title)

        # 实验选择 + 数据源
        src_group = QGroupBox("数据源")
        src_layout = QVBoxLayout(src_group)

        exp_row = QHBoxLayout()
        exp_row.addWidget(QLabel("实验:"))
        self.exp_combo = QComboBox()
        self.exp_combo.addItems(['OF', 'EPM', 'TCT'])
        self.exp_combo.setCurrentText('EPM')
        self.exp_combo.currentTextChanged.connect(self._auto_find)
        exp_row.addWidget(self.exp_combo)
        exp_row.addStretch()
        src_layout.addLayout(exp_row)

        file_row = QHBoxLayout()
        file_row.addWidget(QLabel("数据文件:"))
        self.source_edit = QLineEdit()
        file_row.addWidget(self.source_edit)
        btn_browse = QPushButton("浏览")
        btn_browse.clicked.connect(self._browse_source)
        file_row.addWidget(btn_browse)
        btn_auto = QPushButton("自动查找")
        btn_auto.setProperty('class', 'accent')
        btn_auto.clicked.connect(self._auto_find)
        file_row.addWidget(btn_auto)
        src_layout.addLayout(file_row)

        layout.addWidget(src_group)

        # 图表类型
        type_group = QGroupBox("图表类型")
        type_layout = QHBoxLayout(type_group)
        self.bar_radio = QRadioButton("柱状图")
        self.bar_radio.setChecked(True)
        self.line_radio = QRadioButton("折线图")
        type_layout.addWidget(self.bar_radio)
        type_layout.addWidget(self.line_radio)
        type_layout.addStretch()
        layout.addWidget(type_group)

        # 颜色设置
        color_group = QGroupBox("颜色设置")
        color_grid = QVBoxLayout(color_group)

        self.color_labels = {}
        row_layout = None
        for i, (key, label) in enumerate(COLOR_LABELS):
            if i % 2 == 0:
                row_layout = QHBoxLayout()
                color_grid.addLayout(row_layout)

            row_layout.addWidget(QLabel(label))
            color_lbl = QLabel("  ")
            color_lbl.setFixedSize(40, 24)
            color_lbl.setStyleSheet(
                f"background: {self.colors[key]}; border: 1px solid #585B70; border-radius: 3px;")
            row_layout.addWidget(color_lbl)
            self.color_labels[key] = color_lbl

            btn_pick = QPushButton("选色")
            btn_pick.setFixedWidth(48)
            btn_pick.clicked.connect(lambda _, k=key: self._pick_color(k))
            row_layout.addWidget(btn_pick)

        # pad if odd
        if len(COLOR_LABELS) % 2 != 0:
            row_layout.addStretch()

        layout.addWidget(color_group)

        # 参数
        param_group = QGroupBox("参数")
        param_layout = QVBoxLayout(param_group)

        p1 = QHBoxLayout()
        p1.addWidget(QLabel("柱宽:"))
        self.bar_width_spin = QDoubleSpinBox()
        self.bar_width_spin.setRange(0.2, 1.0)
        self.bar_width_spin.setSingleStep(0.1)
        self.bar_width_spin.setValue(0.6)
        p1.addWidget(self.bar_width_spin)
        p1.addWidget(QLabel("  散点大小:"))
        self.point_size_spin = QSpinBox()
        self.point_size_spin.setRange(4, 40)
        self.point_size_spin.setValue(18)
        p1.addWidget(self.point_size_spin)
        p1.addStretch()
        param_layout.addLayout(p1)

        p2 = QHBoxLayout()
        p2.addWidget(QLabel("误差线:"))
        self.errorbar_combo = QComboBox()
        self.errorbar_combo.addItems(['SEM', 'SD'])
        p2.addWidget(self.errorbar_combo)
        p2.addWidget(QLabel("  显著性 α:"))
        self.alpha_spin = QDoubleSpinBox()
        self.alpha_spin.setRange(0.01, 0.10)
        self.alpha_spin.setSingleStep(0.01)
        self.alpha_spin.setValue(0.05)
        self.alpha_spin.setDecimals(2)
        p2.addWidget(self.alpha_spin)
        p2.addStretch()
        param_layout.addLayout(p2)

        p3 = QHBoxLayout()
        p3.addWidget(QLabel("输出:"))
        self.pdf_check = QCheckBox("PDF")
        self.pdf_check.setChecked(True)
        p3.addWidget(self.pdf_check)
        self.png_check = QCheckBox("PNG")
        p3.addWidget(self.png_check)
        p3.addWidget(QLabel("  DPI:"))
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setSingleStep(50)
        self.dpi_spin.setValue(300)
        p3.addWidget(self.dpi_spin)
        p3.addStretch()
        param_layout.addLayout(p3)

        layout.addWidget(param_group)

        # 按钮
        btn_row = QHBoxLayout()
        btn_gen = QPushButton("生成图表")
        btn_gen.setProperty('class', 'success')
        btn_gen.clicked.connect(self._generate)
        btn_row.addWidget(btn_gen)
        btn_open = QPushButton("打开输出目录")
        btn_open.setProperty('class', 'accent')
        btn_open.clicked.connect(self._open_output_dir)
        btn_row.addWidget(btn_open)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addStretch()

        # 自动查找
        self._auto_find()

    def _pick_color(self, key):
        initial = QColor(self.colors.get(key, '#ffffff'))
        color = QColorDialog.getColor(initial, self, "选择颜色")
        if color.isValid():
            self.colors[key] = color.name()
            self.color_labels[key].setStyleSheet(
                f"background: {color.name()}; border: 1px solid #585B70; border-radius: 3px;")

    def _browse_source(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择数据源", "", "Excel (*.xlsx);;所有文件 (*)")
        if path:
            self.source_edit.setText(path)

    def _auto_find(self):
        exp = self.exp_combo.currentText()
        summary_dirs = {'OF': OF_SUMMARY, 'EPM': EPM_SUMMARY, 'TCT': TCT_SUMMARY}
        patterns = {'OF': 'Summary', 'EPM': 'EPM_Summary', 'TCT': 'TCT_Complete_Data'}
        d = summary_dirs.get(exp)
        p = patterns.get(exp, '')
        if d:
            found = find_latest_summary(str(d), prefix=p)
            if found:
                self.source_edit.setText(found)
                return
        self.source_edit.setText('')

    def _generate(self):
        exp = self.exp_combo.currentText()
        source = self.source_edit.text().strip()

        if not source or not os.path.exists(source):
            if self.main.log_console:
                self.main.log_console.write("[错误] 请先选择有效的数据源文件\n")
            return

        colors = dict(self.colors)
        bar_width = self.bar_width_spin.value()
        point_size = self.point_size_spin.value()

        def _job():
            df = pd.read_excel(source)
            chart_type = 'bar' if self.bar_radio.isChecked() else 'paired'
            common = {
                'chart_type': chart_type,
                'colors': {
                    'color_0': colors['saline_bar'],
                    'color_1': colors['cno_bar'],
                    'scatter': colors['scatter'],
                    'connect': colors['connect_line'],
                    'edge': '#000000',
                },
                'bar_width': bar_width,
                'point_size': point_size,
                'errorbar': self.errorbar_combo.currentText().lower(),
                'alpha': self.alpha_spin.value(),
                'pdf': self.pdf_check.isChecked(),
                'png': self.png_check.isChecked(),
                'dpi': self.dpi_spin.value(),
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

        self.main.worker.run(_job)

    def _open_output_dir(self):
        exp = self.exp_combo.currentText()
        dirs = {'OF': OF_FIGURES, 'EPM': EPM_FIGURES, 'TCT': TCT_FIGURES}
        d = dirs.get(exp)
        if d and d.exists():
            os.startfile(str(d))
        elif self.main.log_console:
            self.main.log_console.write(f"[提示] 输出目录不存在: {d}\n")
