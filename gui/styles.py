"""
ttk 样式配置
"""
import tkinter as tk
from tkinter import ttk


def configure_styles(root):
    style = ttk.Style(root)
    style.theme_use('clam')

    # 侧边栏按钮
    style.configure(
        'Nav.TButton',
        font=('Microsoft YaHei', 10),
        padding=(12, 8),
        anchor='w',
        width=14,
    )
    style.map(
        'Nav.TButton',
        background=[('active', '#e0e0e0'), ('!active', '#f5f5f5')],
        foreground=[('active', '#1a73e8')],
    )
    style.configure(
        'NavActive.TButton',
        font=('Microsoft YaHei', 10, 'bold'),
        padding=(12, 8),
        anchor='w',
        width=14,
        background='#1a73e8',
        foreground='white',
    )

    # 内容区标题
    style.configure(
        'Title.TLabel',
        font=('Microsoft YaHei', 14, 'bold'),
        foreground='#333333',
    )
    style.configure(
        'Section.TLabel',
        font=('Microsoft YaHei', 10, 'bold'),
        foreground='#555555',
    )

    # 操作按钮
    style.configure(
        'Action.TButton',
        font=('Microsoft YaHei', 9),
        padding=(8, 4),
    )

    # 状态标签
    style.configure(
        'Status.TLabel',
        font=('Microsoft YaHei', 9),
    )

    # 步骤按钮（预处理流水线）
    style.configure(
        'Step.TButton',
        font=('Microsoft YaHei', 9),
        padding=(6, 3),
    )

    # Frame 样式
    style.configure('Content.TFrame', background='#ffffff')
    style.configure('Sidebar.TFrame', background='#f5f5f5')
    style.configure('Log.TFrame', background='#1e1e1e')
