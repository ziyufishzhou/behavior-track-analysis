"""Catppuccin Mocha 深色主题 QSS"""
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

# ========== 色值 ==========
BG_BASE    = '#1E1E2E'
BG_MANTLE  = '#181825'
BG_CRUST   = '#11111B'
BG_SURFACE = '#313244'
BG_OVERLAY = '#45475A'
FG_TEXT    = '#CDD6F4'
FG_SUBTEXT = '#A6ADC8'
FG_DIM     = '#6C7086'

ACCENT_BLUE   = '#89B4FA'
ACCENT_GREEN  = '#A6E3A1'
ACCANT_RED    = '#F38BA8'
ACCENT_ORANGE = '#FAB387'
ACCENT_YELLOW = '#F9E2AF'
ACCENT_TEAL   = '#94E2D5'
ACCENT_PINK   = '#F5C2E7'

QSS = f"""
/* ─── 全局 ─── */
QWidget {{
    background: {BG_BASE};
    color: {FG_TEXT};
    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
    font-size: 13px;
}}
QFrame {{
    border: none;
}}

/* ─── 侧边栏 ─── */
#sidebar {{
    background: {BG_MANTLE};
    border-right: 1px solid {BG_OVERLAY};
}}
#sidebar QListWidget {{
    background: transparent;
    border: none;
    outline: none;
    padding: 8px 0;
}}
#sidebar QListWidget::item {{
    padding: 12px 20px;
    border-radius: 8px;
    margin: 2px 8px;
    color: {FG_SUBTEXT};
    font-size: 13px;
}}
#sidebar QListWidget::item:hover {{
    background: {BG_SURFACE};
    color: {FG_TEXT};
}}
#sidebar QListWidget::item:selected {{
    background: {ACCENT_BLUE};
    color: {BG_MANTLE};
    font-weight: bold;
}}

/* ─── 按钮 ─── */
QPushButton {{
    background: {BG_SURFACE};
    color: {FG_TEXT};
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
    min-height: 20px;
}}
QPushButton:hover {{
    background: {BG_OVERLAY};
}}
QPushButton:pressed {{
    background: {ACCENT_BLUE};
    color: {BG_MANTLE};
}}
QPushButton:disabled {{
    background: {BG_OVERLAY};
    color: {FG_DIM};
}}

/* ─── 强调按钮 ─── */
QPushButton[class="accent"] {{
    background: {ACCENT_BLUE};
    color: {BG_MANTLE};
    font-weight: bold;
}}
QPushButton[class="accent"]:hover {{
    background: #B4D0FB;
}}
QPushButton[class="success"] {{
    background: {ACCENT_GREEN};
    color: {BG_MANTLE};
    font-weight: bold;
}}
QPushButton[class="success"]:hover {{
    background: #C0EDBE;
}}
QPushButton[class="danger"] {{
    background: {ACCANT_RED};
    color: {BG_MANTLE};
    font-weight: bold;
}}
QPushButton[class="danger"]:hover {{
    background: #F5A5B8;
}}
QPushButton[class="warning"] {{
    background: {ACCENT_ORANGE};
    color: {BG_MANTLE};
    font-weight: bold;
}}

/* ─── 输入框 ─── */
QLineEdit, QSpinBox, QDoubleSpinBox {{
    background: {BG_SURFACE};
    color: {FG_TEXT};
    border: 1px solid {BG_OVERLAY};
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 20px;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {ACCENT_BLUE};
}}
QComboBox {{
    background: {BG_SURFACE};
    color: {FG_TEXT};
    border: 1px solid {BG_OVERLAY};
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 20px;
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background: {BG_SURFACE};
    color: {FG_TEXT};
    border: 1px solid {BG_OVERLAY};
    selection-background-color: {ACCENT_BLUE};
    selection-color: {BG_MANTLE};
}}

/* ─── 分组框 ─── */
QGroupBox {{
    border: 1px solid {BG_OVERLAY};
    border-radius: 8px;
    margin-top: 16px;
    padding: 16px 12px 8px;
    font-weight: bold;
    color: {FG_TEXT};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    color: {ACCENT_BLUE};
}}

/* ─── 复选框 ─── */
QCheckBox {{
    spacing: 8px;
    color: {FG_TEXT};
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {BG_OVERLAY};
    background: {BG_SURFACE};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT_BLUE};
    border-color: {ACCENT_BLUE};
}}

/* ─── 表格/树 ─── */
QTreeWidget, QTableWidget {{
    background: {BG_SURFACE};
    color: {FG_TEXT};
    border: 1px solid {BG_OVERLAY};
    border-radius: 6px;
    gridline-color: {BG_OVERLAY};
    selection-background-color: {ACCENT_BLUE};
    selection-color: {BG_MANTLE};
}}
QTreeWidget::item, QTableWidget::item {{
    padding: 4px;
}}
QHeaderView::section {{
    background: {BG_MANTLE};
    color: {FG_SUBTEXT};
    border: none;
    border-bottom: 1px solid {BG_OVERLAY};
    padding: 6px 10px;
    font-weight: bold;
}}

/* ─── 滚动条 ─── */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BG_OVERLAY};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {FG_DIM};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {BG_OVERLAY};
    border-radius: 5px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {FG_DIM};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ─── 日志终端 ─── */
#log_console {{
    background: {BG_CRUST};
    color: {ACCENT_GREEN};
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 12px;
    border: 1px solid {BG_OVERLAY};
    border-radius: 6px;
    padding: 8px;
}}

/* ─── 标签 ─── */
QLabel[class="title"] {{
    font-size: 20px;
    font-weight: bold;
    color: {FG_TEXT};
    padding: 8px 0;
}}
QLabel[class="section"] {{
    font-size: 13px;
    font-weight: bold;
    color: {ACCENT_BLUE};
}}
QLabel[class="status"] {{
    font-size: 12px;
    padding: 4px;
}}

/* ─── 分割线 ─── */
QSplitter::handle {{
    background: {BG_OVERLAY};
}}
QSplitter::handle:hover {{
    background: {ACCENT_BLUE};
}}

/* ─── 列表框 ─── */
QListWidget {{
    background: {BG_SURFACE};
    color: {FG_TEXT};
    border: 1px solid {BG_OVERLAY};
    border-radius: 6px;
    padding: 4px;
    outline: none;
}}
QListWidget::item {{
    padding: 6px 10px;
    border-radius: 4px;
}}
QListWidget::item:hover {{
    background: {BG_OVERLAY};
}}
QListWidget::item:selected {{
    background: {ACCENT_BLUE};
    color: {BG_MANTLE};
}}
"""


def apply_theme(app):
    """应用深色主题到 QApplication"""
    app.setStyleSheet(QSS)
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(BG_BASE))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(FG_TEXT))
    palette.setColor(QPalette.ColorRole.Base, QColor(BG_SURFACE))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(BG_MANTLE))
    palette.setColor(QPalette.ColorRole.Text, QColor(FG_TEXT))
    palette.setColor(QPalette.ColorRole.Button, QColor(BG_SURFACE))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(FG_TEXT))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT_BLUE))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(BG_MANTLE))
    app.setPalette(palette)