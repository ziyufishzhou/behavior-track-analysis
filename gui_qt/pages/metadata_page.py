"""元数据编辑页面 — 表格 + 双击编辑"""
import pandas as pd
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog,
)
from PySide6.QtCore import Qt
from config.paths import METADATA_FILE


class MetadataPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self.df = pd.DataFrame()
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        title = QLabel("元数据编辑")
        title.setProperty('class', 'title')
        layout.addWidget(title)

        # 按钮栏
        btn_row = QHBoxLayout()

        btn_rescan = QPushButton("重新扫描")
        btn_rescan.setProperty('class', 'accent')
        btn_rescan.clicked.connect(self._rescan)
        btn_row.addWidget(btn_rescan)

        btn_save = QPushButton("保存")
        btn_save.setProperty('class', 'success')
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)

        self.update_check = QCheckBox("更新模式 (保留手动列)")
        self.update_check.setChecked(True)
        btn_row.addWidget(self.update_check)
        btn_row.addStretch()

        # 添加列
        btn_row.addWidget(QLabel("新列名:"))
        self.new_col_edit = QLineEdit()
        self.new_col_edit.setPlaceholderText("列名")
        self.new_col_edit.setFixedWidth(120)
        btn_row.addWidget(self.new_col_edit)
        btn_add = QPushButton("添加列")
        btn_add.clicked.connect(self._add_column)
        btn_row.addWidget(btn_add)

        layout.addLayout(btn_row)

        # 表格
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setDefaultSectionSize(28)
        layout.addWidget(self.table, stretch=1)

    def _load_data(self):
        if not METADATA_FILE.exists():
            return
        try:
            self.df = pd.read_excel(str(METADATA_FILE))
            self._refresh_table()
        except Exception as e:
            if self.main.log_console:
                self.main.log_console.write(f"[错误] 加载元数据失败: {e}\n")

    def _refresh_table(self):
        cols = list(self.df.columns)
        self.table.setColumnCount(len(cols))
        self.table.setRowCount(len(self.df))
        self.table.setHorizontalHeaderLabels(cols)

        for r, (_, row) in enumerate(self.df.iterrows()):
            for c, col in enumerate(cols):
                val = str(row[col]) if pd.notna(row[col]) else ''
                item = QTableWidgetItem(val)
                self.table.setItem(r, c, item)

        # auto-size columns
        for c in range(len(cols)):
            width = max(80, min(200, len(str(cols[c])) * 10 + 20))
            self.table.setColumnWidth(c, width)

    def _rescan(self):
        def _job():
            from preprocessing.build_metadata import build_metadata
            build_metadata(update=self.update_check.isChecked())

        def _on_done(success):
            if success:
                self._load_data()

        self.main.worker.run(_job, on_done=_on_done)

    def _save(self):
        if self.df.empty:
            return
        # 同步表格编辑回 DataFrame
        self._sync_table_to_df()
        METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.df.to_excel(str(METADATA_FILE), index=False)
        if self.main.log_console:
            self.main.log_console.write(f"元数据已保存: {METADATA_FILE}\n")

    def _sync_table_to_df(self):
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                if item is not None:
                    self.df.iloc[r, c] = item.text()

    def _add_column(self):
        name = self.new_col_edit.text().strip()
        if not name:
            return
        if name in self.df.columns:
            if self.main.log_console:
                self.main.log_console.write(f"[提示] 列 '{name}' 已存在\n")
            return
        self.df[name] = ''
        self._refresh_table()
        self.new_col_edit.setText('')
