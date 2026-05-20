"""导入视频页面"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QListWidget, QTreeWidget, QTreeWidgetItem,
    QGroupBox, QListWidgetItem, QFileDialog,
)
from PySide6.QtCore import Qt
from config.paths import METADATA_FILE, VIDEO_DIR
from gui.utils import extract_mouse_id, is_video_file
import pandas as pd


class ImportPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self.video_list = []
        self._build_ui()
        self._load_existing_metadata()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        title = QLabel("导入视频并设置标签")
        title.setProperty('class', 'title')
        layout.addWidget(title)

        # 顶部：选择文件
        top = QHBoxLayout()
        btn_select = QPushButton("选择视频文件")
        btn_select.setProperty('class', 'accent')
        btn_select.clicked.connect(self._select_files)
        top.addWidget(btn_select)

        btn_dir = QPushButton("选择视频目录")
        btn_dir.setProperty('class', 'accent')
        btn_dir.clicked.connect(self._select_dir)
        top.addWidget(btn_dir)

        btn_clear = QPushButton("清空列表")
        btn_clear.setProperty('class', 'danger')
        btn_clear.clicked.connect(self._clear_list)
        top.addWidget(btn_clear)
        top.addStretch()
        layout.addLayout(top)

        # 中部：视频列表 + 标签设置
        mid = QHBoxLayout()

        # 左：视频列表
        left_group = QGroupBox("已导入视频")
        left_layout = QVBoxLayout(left_group)
        self.video_lb = QListWidget()
        self.video_lb.itemSelectionChanged.connect(self._on_select)
        left_layout.addWidget(self.video_lb)
        mid.addWidget(left_group, stretch=3)

        # 右：标签设置
        right_group = QGroupBox("标签设置")
        right_layout = QVBoxLayout(right_group)

        form = QHBoxLayout()
        form.addWidget(QLabel("实验:"))
        self.exp_combo = QComboBox()
        self.exp_combo.addItems(['OF', 'EPM', 'TCT'])
        self.exp_combo.currentTextChanged.connect(self._on_exp_changed)
        form.addWidget(self.exp_combo)
        right_layout.addLayout(form)

        form2 = QHBoxLayout()
        form2.addWidget(QLabel("组别:"))
        self.group_combo = QComboBox()
        self.group_combo.setEditable(True)
        self.group_combo.addItems(['hM4Di', 'mCherry'])
        form2.addWidget(self.group_combo)
        right_layout.addLayout(form2)

        form3 = QHBoxLayout()
        form3.addWidget(QLabel("条件:"))
        self.cond_combo = QComboBox()
        self.cond_combo.setEditable(True)
        self.cond_combo.addItems(['CNO', 'Saline'])
        form3.addWidget(self.cond_combo)
        right_layout.addLayout(form3)

        form4 = QHBoxLayout()
        form4.addWidget(QLabel("小鼠:"))
        self.mouse_edit = QLineEdit()
        self.mouse_edit.setPlaceholderText("自动从文件名提取")
        form4.addWidget(self.mouse_edit)
        right_layout.addLayout(form4)

        # 阶段（TCT 专用）
        self.phase_row = QHBoxLayout()
        self.phase_label = QLabel("阶段:")
        self.phase_row.addWidget(self.phase_label)
        self.phase_combo = QComboBox()
        self.phase_combo.addItems(['S', 'N', 'H'])
        self.phase_row.addWidget(self.phase_combo)
        right_layout.addLayout(self.phase_row)
        self.phase_label.setVisible(False)
        self.phase_combo.setVisible(False)

        btn_apply = QPushButton("应用标签到选中")
        btn_apply.setProperty('class', 'success')
        btn_apply.clicked.connect(self._apply_labels)
        right_layout.addWidget(btn_apply)

        btn_save = QPushButton("保存元数据")
        btn_save.setProperty('class', 'accent')
        btn_save.clicked.connect(self._save_metadata)
        right_layout.addWidget(btn_save)

        right_layout.addStretch()
        mid.addWidget(right_group, stretch=2)

        layout.addLayout(mid, stretch=1)

        # 底部：预览表
        self.preview_tree = QTreeWidget()
        self.preview_tree.setHeaderLabels(['文件名', '实验', '组别', '条件', '小鼠', '阶段'])
        self.preview_tree.setAlternatingRowColors(True)
        layout.addWidget(self.preview_tree, stretch=1)

    def _on_exp_changed(self, text):
        is_tct = text == 'TCT'
        self.phase_label.setVisible(is_tct)
        self.phase_combo.setVisible(is_tct)

    def _select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择视频文件", str(VIDEO_DIR),
            "视频 (*.mp4 *.avi *.mov *.mkv);;所有 (*)")
        for f in files:
            name = os.path.basename(f)
            if (name, f) not in self.video_list:
                self.video_list.append((name, f))
                self.video_lb.addItem(name)

    def _select_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择视频目录", str(VIDEO_DIR))
        if not d:
            return
        for f in os.listdir(d):
            full = os.path.join(d, f)
            if os.path.isfile(full) and is_video_file(full):
                if (f, full) not in self.video_list:
                    self.video_list.append((f, full))
                    self.video_lb.addItem(f)

    def _clear_list(self):
        self.video_list.clear()
        self.video_lb.clear()

    def _on_select(self):
        rows = self.video_lb.selectedItems()
        if rows:
            name = rows[0].text()
            mid = extract_mouse_id(name)
            if mid:
                self.mouse_edit.setText(mid)

    def _apply_labels(self):
        rows = self.video_lb.selectedItems()
        if not rows:
            return
        exp = self.exp_combo.currentText()
        group = self.group_combo.currentText()
        cond = self.cond_combo.currentText()
        mouse = self.mouse_edit.text().strip()
        phase = self.phase_combo.currentText() if self.exp_combo.currentText() == 'TCT' else ''

        for row_item in rows:
            name = row_item.text()
            # 更新或插入预览
            existing = self.preview_tree.findItems(name, Qt.MatchFlag.MatchExactly, 0)
            if existing:
                item = existing[0]
            else:
                item = QTreeWidgetItem([name, '', '', '', '', ''])
                self.preview_tree.addTopLevelItem(item)
            item.setText(1, exp)
            item.setText(2, group)
            item.setText(3, cond)
            item.setText(4, mouse or extract_mouse_id(name))
            item.setText(5, phase)

    def _save_metadata(self):
        cols = ['FileName', 'Experiment', 'Group', 'Condition', 'MouseID', 'Phase']
        rows = []
        for i in range(self.preview_tree.topLevelItemCount()):
            item = self.preview_tree.topLevelItem(i)
            rows.append([item.text(j) for j in range(6)])
        new_df = pd.DataFrame(rows, columns=cols)

        if METADATA_FILE.exists():
            old_df = pd.read_excel(str(METADATA_FILE))
            extra_cols = [c for c in old_df.columns if c not in cols]
            if extra_cols:
                new_df = new_df.merge(old_df[extra_cols + ['FileName']], on='FileName', how='left')
        METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        new_df.to_excel(str(METADATA_FILE), index=False)
        if self.main.log_console:
            self.main.log_console.write(f"元数据已保存: {METADATA_FILE} ({len(new_df)} 条)\n")

    def _load_existing_metadata(self):
        if not METADATA_FILE.exists():
            return
        try:
            df = pd.read_excel(str(METADATA_FILE))
            for _, row in df.iterrows():
                item = QTreeWidgetItem([
                    str(row.get('FileName', '')),
                    str(row.get('Experiment', '')),
                    str(row.get('Group', '')),
                    str(row.get('Condition', '')),
                    str(row.get('MouseID', '')),
                    str(row.get('Phase', '')),
                ])
                self.preview_tree.addTopLevelItem(item)
        except Exception:
            pass