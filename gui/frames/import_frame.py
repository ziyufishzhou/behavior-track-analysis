"""
导入视频 + 打标签
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog
import pandas as pd

from config.paths import VIDEO_DIR, METADATA_FILE
from gui.i18n import (
    IMPORT_TITLE, IMPORT_SELECT_FILES, IMPORT_SELECT_DIR,
    IMPORT_VIDEO_LIST, IMPORT_LABEL_SECTION,
    IMPORT_EXPERIMENT, IMPORT_GROUP, IMPORT_CONDITION,
    IMPORT_MOUSEID, IMPORT_PHASE, IMPORT_APPLY, IMPORT_SAVE,
    IMPORT_PREVIEW,
)
from gui.utils import extract_mouse_id, is_video_file

EXPERIMENTS = ['OF', 'EPM', 'TCT']
GROUPS = ['hM4Di', 'mCherry']
CONDITIONS = ['CNO', 'Saline']
TCT_PHASES = ['S', 'N', 'H']


class ImportFrame(ttk.Frame):
    def __init__(self, parent, app=None):
        super().__init__(parent, style='Content.TFrame')
        self.app = app
        self.video_list = []  # [(display_name, full_path)]
        self._build_ui()
        self._load_existing_metadata()

    def _build_ui(self):
        # 标题
        ttk.Label(self, text=IMPORT_TITLE, style='Title.TLabel').pack(
            anchor='w', padx=16, pady=(12, 8))

        body = ttk.Frame(self)
        body.pack(fill='both', expand=True, padx=16)

        # ---- 左侧: 视频列表 ----
        left = ttk.Frame(body)
        left.pack(side='left', fill='both', expand=True)

        btn_row = ttk.Frame(left)
        btn_row.pack(fill='x', pady=(0, 4))
        ttk.Button(btn_row, text=IMPORT_SELECT_FILES, style='Action.TButton',
                   command=self._select_files).pack(side='left', padx=(0, 6))
        ttk.Button(btn_row, text=IMPORT_SELECT_DIR, style='Action.TButton',
                   command=self._select_dir).pack(side='left')
        ttk.Button(btn_row, text="清空列表", style='Action.TButton',
                   command=self._clear_list).pack(side='right')

        ttk.Label(left, text=IMPORT_VIDEO_LIST, style='Section.TLabel').pack(anchor='w')

        list_frame = ttk.Frame(left)
        list_frame.pack(fill='both', expand=True, pady=4)

        self.video_lb = tk.Listbox(list_frame, selectmode='extended', height=10,
                                   font=('Consolas', 9))
        lb_scroll = ttk.Scrollbar(list_frame, command=self.video_lb.yview)
        self.video_lb.configure(yscrollcommand=lb_scroll.set)
        lb_scroll.pack(side='right', fill='y')
        self.video_lb.pack(fill='both', expand=True)
        self.video_lb.bind('<<ListboxSelect>>', self._on_select)

        # ---- 右侧: 标签设置 ----
        right = ttk.LabelFrame(body, text=IMPORT_LABEL_SECTION, padding=10)
        right.pack(side='right', fill='y', padx=(12, 0))

        # Experiment
        ttk.Label(right, text=IMPORT_EXPERIMENT).pack(anchor='w', pady=(4, 0))
        self.exp_var = tk.StringVar()
        exp_combo = ttk.Combobox(right, textvariable=self.exp_var,
                                 values=EXPERIMENTS, state='readonly', width=14)
        exp_combo.pack(anchor='w', pady=2)
        exp_combo.bind('<<ComboboxSelected>>', self._on_experiment_change)

        # Group
        ttk.Label(right, text=IMPORT_GROUP).pack(anchor='w', pady=(8, 0))
        self.group_var = tk.StringVar()
        self.group_combo = ttk.Combobox(right, textvariable=self.group_var,
                                        values=GROUPS, width=14)
        self.group_combo.pack(anchor='w', pady=2)

        # Condition
        ttk.Label(right, text=IMPORT_CONDITION).pack(anchor='w', pady=(8, 0))
        self.cond_var = tk.StringVar()
        self.cond_combo = ttk.Combobox(right, textvariable=self.cond_var,
                                       values=CONDITIONS, width=14)
        self.cond_combo.pack(anchor='w', pady=2)

        # MouseID
        ttk.Label(right, text=IMPORT_MOUSEID).pack(anchor='w', pady=(8, 0))
        self.mouse_var = tk.StringVar()
        ttk.Entry(right, textvariable=self.mouse_var, width=16).pack(anchor='w', pady=2)

        # Phase (TCT only)
        self.phase_frame = ttk.Frame(right)
        self.phase_label = ttk.Label(self.phase_frame, text=IMPORT_PHASE)
        self.phase_label.pack(anchor='w')
        self.phase_var = tk.StringVar()
        self.phase_combo = ttk.Combobox(self.phase_frame, textvariable=self.phase_var,
                                        values=TCT_PHASES, state='readonly', width=14)
        self.phase_combo.pack(anchor='w', pady=2)

        # 按钮
        btn_frame = ttk.Frame(right)
        btn_frame.pack(fill='x', pady=(16, 0))
        ttk.Button(btn_frame, text=IMPORT_APPLY, style='Action.TButton',
                   command=self._apply_labels).pack(fill='x', pady=2)
        ttk.Button(btn_frame, text=IMPORT_SAVE, style='Action.TButton',
                   command=self._save_metadata).pack(fill='x', pady=2)

        # ---- 底部: 标签预览表 ----
        preview_frame = ttk.LabelFrame(self, text=IMPORT_PREVIEW, padding=6)
        preview_frame.pack(fill='both', expand=True, padx=16, pady=(8, 12))

        cols = ('filename', 'experiment', 'group', 'condition', 'mouseid', 'phase')
        self.preview_tree = ttk.Treeview(preview_frame, columns=cols,
                                         show='headings', height=6)
        self.preview_tree.heading('filename', text='文件名')
        self.preview_tree.heading('experiment', text='实验')
        self.preview_tree.heading('group', text='Group')
        self.preview_tree.heading('condition', text='Condition')
        self.preview_tree.heading('mouseid', text='MouseID')
        self.preview_tree.heading('phase', text='Phase')

        for col in cols:
            self.preview_tree.column(col, width=120, minwidth=80)
        self.preview_tree.column('filename', width=260, minwidth=160)
        self.preview_tree.column('phase', width=60, minwidth=40)

        tree_scroll = ttk.Scrollbar(preview_frame, command=self.preview_tree.yview)
        self.preview_tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side='right', fill='y')
        self.preview_tree.pack(fill='both', expand=True)

    def _select_files(self):
        files = filedialog.askopenfilenames(
            title=IMPORT_SELECT_FILES,
            initialdir=str(VIDEO_DIR) if VIDEO_DIR.exists() else '.',
            filetypes=[('视频文件', '*.mp4 *.avi *.mov *.mkv'), ('所有文件', '*.*')],
        )
        for f in files:
            name = os.path.basename(f)
            if (name, f) not in self.video_list:
                self.video_list.append((name, f))
        self._refresh_listbox()

    def _select_dir(self):
        d = filedialog.askdirectory(
            title=IMPORT_SELECT_DIR,
            initialdir=str(VIDEO_DIR) if VIDEO_DIR.exists() else '.',
        )
        if not d:
            return
        for f in sorted(os.listdir(d)):
            full = os.path.join(d, f)
            if os.path.isfile(full) and is_video_file(f):
                if (f, full) not in self.video_list:
                    self.video_list.append((f, full))
        self._refresh_listbox()

    def _clear_list(self):
        self.video_list.clear()
        self._refresh_listbox()
        self._refresh_preview()

    def _refresh_listbox(self):
        self.video_lb.delete(0, 'end')
        for name, _ in self.video_list:
            self.video_lb.insert('end', name)

    def _on_select(self, event):
        sel = self.video_lb.curselection()
        if not sel:
            return
        idx = sel[0]
        name, _ = self.video_list[idx]
        # 自动填充 MouseID
        mid = extract_mouse_id(name)
        if mid:
            self.mouse_var.set(mid)

    def _on_experiment_change(self, event=None):
        exp = self.exp_var.get()
        if exp == 'TCT':
            self.phase_frame.pack(anchor='w', pady=(8, 0), before=self.phase_frame.master.winfo_children()[-1])
        else:
            self.phase_frame.pack_forget()
            self.phase_var.set('')

    def _apply_labels(self):
        sel = self.video_lb.curselection()
        if not sel:
            return
        exp = self.exp_var.get()
        group = self.group_var.get()
        cond = self.cond_var.get()
        mouse = self.mouse_var.get()
        phase = self.phase_var.get() if exp == 'TCT' else ''

        if not exp:
            return

        for idx in sel:
            name, _ = self.video_list[idx]
            mid = mouse or extract_mouse_id(name)
            # 更新或插入预览表
            tags = (name, exp, group, cond, mid, phase)
            # 查找是否已存在
            existing = self.preview_tree.get_children()
            found = False
            for item in existing:
                if self.preview_tree.item(item, 'values')[0] == name:
                    self.preview_tree.item(item, values=tags)
                    found = True
                    break
            if not found:
                self.preview_tree.insert('', 'end', values=tags)

    def _save_metadata(self):
        items = self.preview_tree.get_children()
        if not items:
            return

        records = []
        for item in items:
            vals = self.preview_tree.item(item, 'values')
            records.append({
                'FileName': vals[0],
                'Experiment': vals[1],
                'Group': vals[2],
                'Condition': vals[3],
                'MouseID': vals[4],
                'Phase': vals[5] if vals[5] else '',
            })

        df_new = pd.DataFrame(records)

        # 合并已有 metadata（保留用户手动添加的列）
        if METADATA_FILE.exists():
            df_old = pd.read_excel(str(METADATA_FILE))
            user_cols = [c for c in df_old.columns if c not in df_new.columns]
            if user_cols:
                df_new = df_new.merge(df_old[['FileName'] + user_cols], on='FileName', how='left')

        METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        df_new.to_excel(str(METADATA_FILE), index=False)

        if self.app and self.app.log_console:
            self.app.log_console.write(f"元数据已保存到 {METADATA_FILE}（{len(records)} 条记录）\n")

    def _load_existing_metadata(self):
        """启动时加载已有的 metadata 记录到预览表"""
        if not METADATA_FILE.exists():
            return
        try:
            df = pd.read_excel(str(METADATA_FILE))
            for _, row in df.iterrows():
                self.preview_tree.insert('', 'end', values=(
                    row.get('FileName', ''),
                    row.get('Experiment', ''),
                    row.get('Group', ''),
                    row.get('Condition', ''),
                    row.get('MouseID', ''),
                    row.get('Phase', ''),
                ))
        except Exception:
            pass

    def _refresh_preview(self):
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
