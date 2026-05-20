"""行为分析工作台 — PySide6 主窗口"""
import sys
import os

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QSplitter, QLabel,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

import matplotlib
matplotlib.use('Agg')

from gui_qt.log_console import LogConsole
from gui_qt.worker import ThreadWorker

NAV_ITEMS = [
    ("导入视频",  "📹"),
    ("DLC 分析",  "🔬"),
    ("预处理",    "⚙"),
    ("ROI 标注",  "📐"),
    ("数据分析",  "📊"),
    ("绘图设置",  "🎨"),
    ("元数据编辑", "📋"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("行为分析工作台")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 900)

        self.log_console = LogConsole()
        self.worker = ThreadWorker(self.log_console)

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 上部：侧边栏 + 内容
        top_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 侧边栏
        sidebar = QWidget()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # 标题
        title_label = QLabel("行为分析")
        title_label.setObjectName('sidebar_title')
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #89B4FA; "
            "padding: 20px 0 8px; background: transparent;")
        sidebar_layout.addWidget(title_label)

        subtitle = QLabel("Behavior Analysis")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(
            "font-size: 10px; color: #6C7086; "
            "padding: 0 0 16px; background: transparent;")
        sidebar_layout.addWidget(subtitle)

        self.nav_list = QListWidget()
        self.nav_list.setObjectName('nav_list')
        for text, icon in NAV_ITEMS:
            item = QListWidgetItem(f"  {icon}  {text}")
            self.nav_list.addItem(item)
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        sidebar_layout.addWidget(self.nav_list)

        top_splitter.addWidget(sidebar)

        # 内容区域
        self.stack = QStackedWidget()
        self._load_pages()
        top_splitter.addWidget(self.stack)

        top_splitter.setStretchFactor(0, 0)
        top_splitter.setStretchFactor(1, 1)
        top_splitter.setSizes([200, 1000])

        # 下部：日志控制台（可折叠）
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(self.log_console)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 0)
        main_splitter.setSizes([700, 180])

        main_layout.addWidget(main_splitter)

    def _load_pages(self):
        """延迟导入并实例化所有页面"""
        from gui_qt.pages.import_page import ImportPage
        from gui_qt.pages.dlc_page import DLCPage
        from gui_qt.pages.preprocess_page import PreprocessPage
        from gui_qt.pages.roi_page import ROIPage
        from gui_qt.pages.analyze_page import AnalyzePage
        from gui_qt.pages.plot_page import PlotPage
        from gui_qt.pages.metadata_page import MetadataPage

        self.pages = [
            ImportPage(self),
            DLCPage(self),
            PreprocessPage(self),
            ROIPage(self),
            AnalyzePage(self),
            PlotPage(self),
            MetadataPage(self),
        ]
        for page in self.pages:
            self.stack.addWidget(page)

    def _on_nav_changed(self, row):
        if 0 <= row < len(self.pages):
            self.stack.setCurrentIndex(row)


def run():
    app = QApplication(sys.argv)
    from gui_qt.theme import apply_theme
    apply_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()