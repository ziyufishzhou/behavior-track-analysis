"""
ROI 工具共享 UI 样式
- 深色主题配色
- 统一按钮 / 标签 / 面板风格
"""
import tkinter as tk
from tkinter import ttk

# ========== 配色 ==========
BG_DARK    = '#1E1E2E'     # 主背景
BG_PANEL   = '#2A2A3C'     # 侧边栏
BG_TOOLBAR = '#181825'     # 顶部工具栏
BG_INPUT   = '#313244'     # 输入框背景
BG_CARD    = '#2D2D42'     # 卡片/分组框

FG_PRIMARY   = '#CDD6F4'   # 主文字
FG_SECONDARY = '#A6ADC8'   # 次要文字
FG_DIM       = '#6C7086'   # 提示文字

ACCENT_BLUE   = '#89B4FA'  # 主按钮
ACCENT_GREEN  = '#A6E3A1'  # 确认/成功
ACCENT_ORANGE = '#FAB387'  # 警告
ACCENT_RED    = '#F38BA8'  # 危险/删除
ACCENT_YELLOW = '#F9E2AF'  # 标注临时
ACCENT_TEAL   = '#94E2D5'  # 辅助

ROI_COLORS = {
    'open':   ACCENT_BLUE,
    'closed': ACCENT_ORANGE,
    'center': ACCENT_GREEN,
    'left':   ACCENT_RED,
    'right':  ACCENT_TEAL,
    'default': '#FFFFFF',
}


# ========== 按钮工厂 ==========
def make_btn(parent, text, command, accent='blue', width=12, **kw):
    """创建统一风格按钮"""
    colors = {
        'blue':   (ACCENT_BLUE,   BG_DARK),
        'green':  (ACCENT_GREEN,  BG_DARK),
        'red':    (ACCENT_RED,    BG_DARK),
        'orange': (ACCENT_ORANGE, BG_DARK),
        'teal':   (ACCENT_TEAL,   BG_DARK),
    }
    fg, bg = colors.get(accent, colors['blue'])
    return tk.Button(parent, text=text, command=command, width=width,
                     bg=bg, fg=fg, activebackground=fg, activeforeground=bg,
                     font=('Segoe UI', 9, 'bold'), relief='flat', bd=0,
                     cursor='hand2', padx=8, pady=4, **kw)


def make_toolbar(parent):
    """创建顶部工具栏"""
    bar = tk.Frame(parent, bg=BG_TOOLBAR, pady=6, padx=8)
    return bar


def make_info_label(parent, text=""):
    """创建状态信息标签"""
    return tk.Label(parent, text=text, bg=BG_TOOLBAR, fg=FG_SECONDARY,
                    font=('Segoe UI', 9))


def make_side_panel(parent, width=300):
    """创建右侧面板"""
    panel = tk.Frame(parent, bg=BG_PANEL, width=width, padx=12, pady=8)
    panel.pack_propagate(False)
    return panel


def make_section(parent, title=""):
    """创建分组区域（卡片风格）"""
    frame = tk.LabelFrame(parent, text=title, bg=BG_CARD, fg=FG_PRIMARY,
                          font=('Segoe UI', 9, 'bold'), padx=10, pady=8,
                          relief='flat', bd=0, highlightbackground=BG_INPUT,
                          highlightthickness=1)
    return frame


def make_param_row(parent, label, var, unit="", from_=0.1, to=200, inc=0.5):
    """创建参数行"""
    row = tk.Frame(parent, bg=BG_CARD)
    row.pack(fill=tk.X, pady=3)
    tk.Label(row, text=label, bg=BG_CARD, fg=FG_SECONDARY,
             font=('Segoe UI', 9), width=10, anchor='e').pack(side=tk.LEFT)
    sb = tk.Spinbox(row, from_=from_, to=to, increment=inc,
                    textvariable=var, width=8, bg=BG_INPUT, fg=FG_PRIMARY,
                    font=('Consolas', 9), relief='flat', bd=0,
                    buttonbackground=BG_INPUT, insertbackground=FG_PRIMARY)
    sb.pack(side=tk.LEFT, padx=(8, 4))
    if unit:
        tk.Label(row, text=unit, bg=BG_CARD, fg=FG_DIM,
                 font=('Segoe UI', 8)).pack(side=tk.LEFT)
    return row


def make_treeview(parent, columns, headings, height=12):
    """创建统一风格 Treeview"""
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('ROI.Treeview',
                    background=BG_INPUT, foreground=FG_PRIMARY,
                    fieldbackground=BG_INPUT, font=('Segoe UI', 9),
                    rowheight=26)
    style.configure('ROI.Treeview.Heading',
                    background=BG_PANEL, foreground=FG_PRIMARY,
                    font=('Segoe UI', 9, 'bold'), relief='flat')
    style.map('ROI.Treeview', background=[('selected', ACCENT_BLUE)])
    style.map('ROI.Treeview', foreground=[('selected', BG_DARK)])

    frame = tk.Frame(parent, bg=BG_PANEL)
    tree = ttk.Treeview(frame, columns=columns, show='headings', height=height,
                        style='ROI.Treeview')
    for col, hd in zip(columns, headings):
        tree.heading(col, text=hd)
        tree.column(col, width=120, minwidth=60)

    scroll = ttk.Scrollbar(frame, command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    return frame, tree


def make_help_box(parent, text):
    """创建帮助提示"""
    frame = tk.Frame(parent, bg=BG_INPUT, padx=10, pady=8)
    frame.pack(fill=tk.X, pady=(8, 0), side=tk.BOTTOM)
    tk.Label(frame, text=text, justify='left', bg=BG_INPUT, fg=FG_DIM,
             font=('微软雅黑', 8)).pack(anchor='w')
    return frame


def apply_dark_theme(root):
    """给顶层窗口应用深色背景"""
    root.configure(bg=BG_DARK)


def color_for_group(group):
    """根据 group 返回颜色"""
    return ROI_COLORS.get(group, ROI_COLORS['default'])