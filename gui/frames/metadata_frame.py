"""
元数据编辑 — Treeview 表格 + 双击编辑
"""
import tkinter as tk
from tkinter import ttk

import pandas as pd

from config.paths import METADATA_FILE
from gui.i18n import META_TITLE, META_RESCAN, META_SAVE, META_ADD_COL


class MetadataFrame(ttk.Frame):
    def __init__(self, parent, app=None):
        super().__init__(parent, style='Content.TFrame')
        self.app = app
        self.df = pd.DataFrame()
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        ttk.Label(self, text=META_TITLE, style='Title.TLabel').pack(
            anchor='w', padx=16, pady=(12, 8))

        # ---- 按钮栏 ----
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill='x', padx=16)

        ttk.Button(btn_frame, text=META_RESCAN, style='Action.TButton',
                   command=self._rescan).pack(side='left', padx=(0, 4))
        ttk.Button(btn_frame, text=META_SAVE, style='Action.TButton',
                   command=self._save).pack(side='left', padx=(0, 4))

        self.update_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(btn_frame, text="更新模式(保留手动列)",
                        variable=self.update_var).pack(side='left', padx=(8, 0))

        # 添加列
        add_frame = ttk.Frame(btn_frame)
        add_frame.pack(side='right')
        ttk.Label(add_frame, text="列名:").pack(side='left')
        self.new_col_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.new_col_var, width=10).pack(side='left', padx=(2, 4))
        ttk.Button(add_frame, text=META_ADD_COL, command=self._add_column).pack(side='left')

        # ---- Treeview ----
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill='both', expand=True, padx=16, pady=(8, 12))

        self.tree = ttk.Treeview(tree_frame, show='headings', height=20)
        tree_scroll_y = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set,
                            xscrollcommand=tree_scroll_x.set)

        tree_scroll_y.pack(side='right', fill='y')
        tree_scroll_x.pack(side='bottom', fill='x')
        self.tree.pack(fill='both', expand=True)

        # 双击编辑
        self.tree.bind('<Double-1>', self._on_double_click)

    def _load_data(self):
        if not METADATA_FILE.exists():
            return
        try:
            self.df = pd.read_excel(str(METADATA_FILE))
            self._refresh_tree()
        except Exception as e:
            if self.app and self.app.log_console:
                self.app.log_console.write(f"[错误] 加载元数据失败: {e}\n")

    def _refresh_tree(self):
        # 清空
        self.tree.delete(*self.tree.get_children())
        cols = list(self.df.columns)
        self.tree['columns'] = cols

        for col in cols:
            self.tree.heading(col, text=col)
            width = max(80, min(200, len(col) * 10 + 20))
            self.tree.column(col, width=width, minwidth=60)

        for _, row in self.df.iterrows():
            self.tree.insert('', 'end', values=list(row))

    def _on_double_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != 'cell':
            return

        col = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)
        if not row or not col:
            return

        col_idx = int(col.replace('#', '')) - 1
        col_name = self.df.columns[col_idx]

        # 获取单元格位置
        bbox = self.tree.bbox(row, col)
        if not bbox:
            return

        x, y, w, h = bbox
        current_val = self.tree.item(row, 'values')[col_idx]

        # 创建 Entry
        entry = tk.Entry(self.tree, font=('Consolas', 9))
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, current_val)
        entry.select_range(0, 'end')
        entry.focus_set()

        def _commit(event=None):
            new_val = entry.get()
            entry.destroy()
            # 更新 Treeview
            vals = list(self.tree.item(row, 'values'))
            vals[col_idx] = new_val
            self.tree.item(row, values=vals)
            # 更新 DataFrame
            row_idx = self.tree.index(row)
            self.df.iloc[row_idx, col_idx] = new_val

        def _cancel(event=None):
            entry.destroy()

        entry.bind('<Return>', _commit)
        entry.bind('<Escape>', _cancel)
        entry.bind('<FocusOut>', _commit)

    def _rescan(self):
        from preprocessing.build_metadata import build_metadata
        update = self.update_var.get()
        build_metadata(update=update)
        self._load_data()

    def _save(self):
        if self.df.empty:
            return
        METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.df.to_excel(str(METADATA_FILE), index=False)
        if self.app and self.app.log_console:
            self.app.log_console.write(f"元数据已保存: {METADATA_FILE}\n")

    def _add_column(self):
        name = self.new_col_var.get().strip()
        if not name:
            return
        if name in self.df.columns:
            if self.app and self.app.log_console:
                self.app.log_console.write(f"[提示] 列 '{name}' 已存在\n")
            return
        self.df[name] = ''
        self._refresh_tree()
        self.new_col_var.set('')
