"""
OF (Open Field) ROI 标注工具
- 拖拽画矩形区域
- 支持自动生成中心区（1/9 或 1/4 面积）
"""
import os
import sys
import json
import math
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from dataclasses import dataclass, asdict
from typing import List, Optional
import cv2
import numpy as np
from PIL import Image, ImageTk

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from config.paths import OF_ROI_JSON
from gui.roi_styles import (
    BG_DARK, BG_PANEL, BG_TOOLBAR, BG_INPUT, BG_CARD,
    FG_PRIMARY, FG_SECONDARY, FG_DIM,
    ACCENT_BLUE, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_YELLOW,
    make_btn, make_toolbar, make_info_label, make_side_panel,
    make_section, make_treeview, make_help_box, apply_dark_theme,
)

DEFAULT_FRAME_INDEX = 300


@dataclass
class ROIRegion:
    name: str
    x1: int
    y1: int
    x2: int
    y2: int

    def normalize(self):
        self.x1, self.x2 = sorted([self.x1, self.x2])
        self.y1, self.y2 = sorted([self.y1, self.y2])

    @property
    def w(self): return self.x2 - self.x1

    @property
    def h(self): return self.y2 - self.y1

    @property
    def cx(self): return (self.x1 + self.x2) / 2.0

    @property
    def cy(self): return (self.y1 + self.y2) / 2.0


def make_center_roi(base, area_fraction, name, img_w, img_h):
    scale = math.sqrt(area_fraction)
    new_w = max(2, int(round(base.w * scale)))
    new_h = max(2, int(round(base.h * scale)))
    x1 = int(round(base.cx - new_w / 2.0))
    x2 = int(round(base.cx + new_w / 2.0))
    y1 = int(round(base.cy - new_h / 2.0))
    y2 = int(round(base.cy + new_h / 2.0))
    x1, x2 = max(0, min(x1, img_w-1)), max(0, min(x2, img_w-1))
    y1, y2 = max(0, min(y1, img_h-1)), max(0, min(y2, img_h-1))
    r = ROIRegion(name=name, x1=x1, y1=y1, x2=x2, y2=y2)
    r.normalize()
    return r


class ROIAnnotator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OF 旷场 ROI 标注工具")
        self.geometry("1400x900")
        apply_dark_theme(self)

        self.video_path = None
        self.frame_index = DEFAULT_FRAME_INDEX
        self.pil_img = None
        self.tk_img = None
        self.regions: List[ROIRegion] = []
        self._scale = 1.0
        self._start_xy = None
        self._temp_rect_id = None

        self._setup_ui()

    def _setup_ui(self):
        toolbar = make_toolbar(self)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        make_btn(toolbar, "打开视频", self.choose_video, accent='blue', width=10).pack(side=tk.LEFT, padx=4)
        make_btn(toolbar, "加载帧", self.ask_frame_and_load, accent='teal', width=8).pack(side=tk.LEFT, padx=4)

        tk.Frame(toolbar, bg=FG_DIM, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=4)

        make_btn(toolbar, "保存 JSON", self.save_json, accent='green', width=10).pack(side=tk.LEFT, padx=4)
        make_btn(toolbar, "加载 JSON", self.load_json, accent='orange', width=10).pack(side=tk.LEFT, padx=4)
        make_btn(toolbar, "清 空", self.clear_rois, accent='red', width=8).pack(side=tk.LEFT, padx=4)

        self.info_label = make_info_label(toolbar, "请打开视频并加载帧")
        self.info_label.pack(side=tk.LEFT, padx=16)

        main = tk.Frame(self, bg=BG_DARK)
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main, bg='#11111B', cursor="cross", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        panel = make_side_panel(main, width=310)
        panel.pack(side=tk.RIGHT, fill=tk.Y)

        sec = make_section(panel, "自动生成中心区")
        sec.pack(fill=tk.X, pady=(0, 10))
        tk.Label(sec, text="先画全箱体 ROI，选中后点击生成：",
                 bg=BG_CARD, fg=FG_DIM, font=('微软雅黑', 8)).pack(anchor='w', pady=(0, 6))
        make_btn(sec, "生成中心区 (1/9)", lambda: self.generate_center(1/9),
                 accent='green', width=20).pack(fill=tk.X, pady=2)
        make_btn(sec, "生成中心区 (1/4)", lambda: self.generate_center(1/4),
                 accent='green', width=20).pack(fill=tk.X, pady=2)

        tk.Label(panel, text="ROI 区域列表", bg=BG_PANEL, fg=FG_PRIMARY,
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(4, 6))

        tree_frame, self.tree = make_treeview(
            panel, columns=('name', 'size'), headings=('名称', '尺寸'), height=14)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        btn_row = tk.Frame(panel, bg=BG_PANEL)
        btn_row.pack(fill=tk.X, pady=6)
        make_btn(btn_row, "删除选中", self.delete_selected, accent='red', width=10).pack(side=tk.LEFT, padx=(0, 4))
        make_btn(btn_row, "编辑名称", self.edit_selected, accent='blue', width=10).pack(side=tk.LEFT)

        make_help_box(panel,
            "1. 打开视频 → 加载帧\n"
            "2. 拖拽画矩形标注区域\n"
            "3. 先画全箱体(arena)，选中后\n"
            "   可自动生成中心区(1/9或1/4)\n"
            "4. 松开鼠标后输入区域名称")

        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.bind("<Configure>", lambda e: self.render())

    def choose_video(self):
        path = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=[("Video", "*.mp4 *.avi *.mkv *.mov"), ("All", "*.*")])
        if not path:
            return
        self.video_path = path
        self.info_label.config(text=f"视频: {os.path.basename(path)} | 请点击「加载帧」", fg=ACCENT_BLUE)

    def ask_frame_and_load(self):
        if not self.video_path:
            messagebox.showwarning("提示", "请先打开视频")
            return
        s = simpledialog.askstring("帧号", f"输入帧号(0-based)，默认 {DEFAULT_FRAME_INDEX}:")
        if not s or not s.strip():
            return
        try:
            idx = int(s.strip())
        except ValueError:
            messagebox.showerror("错误", "帧号必须是整数")
            return
        try:
            cap = cv2.VideoCapture(self.video_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            cap.release()
            if not ok:
                raise RuntimeError("读取失败")
            self.frame_index = idx
            self.pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            self.clear_rois(redraw=False)
            self.info_label.config(text=f"视频: {os.path.basename(self.video_path)} | 帧: {idx}", fg=ACCENT_GREEN)
            self.render()
        except Exception as e:
            messagebox.showerror("读取失败", str(e))

    def render(self):
        if self.pil_img is None:
            return
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cw < 10: cw, ch = 900, 650
        iw, ih = self.pil_img.size
        self._scale = min(cw / iw, ch / ih)
        nw, nh = int(iw * self._scale), int(ih * self._scale)
        self.tk_img = ImageTk.PhotoImage(self.pil_img.resize((nw, nh), Image.Resampling.LANCZOS))
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        for r in self.regions:
            is_center = 'center' in r.name.lower()
            color = ACCENT_GREEN if is_center else ACCENT_BLUE
            s = self._scale
            self.canvas.create_rectangle(r.x1*s, r.y1*s, r.x2*s, r.y2*s, outline=color, width=2)
            self.canvas.create_text((r.x1+5)*s, (r.y1+12)*s, text=r.name, fill=color, anchor="nw",
                                    font=('Segoe UI', 9, 'bold'))

    def on_mouse_down(self, event):
        if self.pil_img is None: return
        self._start_xy = (event.x, event.y)
        if self._temp_rect_id: self.canvas.delete(self._temp_rect_id)
        self._temp_rect_id = self.canvas.create_rectangle(event.x, event.y, event.x, event.y,
                                                           outline=ACCENT_YELLOW, width=2, dash=(4, 4))

    def on_mouse_drag(self, event):
        if self._start_xy and self._temp_rect_id:
            self.canvas.coords(self._temp_rect_id, self._start_xy[0], self._start_xy[1], event.x, event.y)

    def on_mouse_up(self, event):
        if self.pil_img is None or self._start_xy is None: return
        x0, y0 = self._start_xy
        x1, y1 = event.x, event.y
        if abs(x1-x0) < 5 or abs(y1-y0) < 5:
            self.canvas.delete(self._temp_rect_id)
            self._temp_rect_id = self._start_xy = None
            return
        name = simpledialog.askstring("ROI 命名", "输入区域名称 (如 arena, center, wall):")
        if not name:
            self.canvas.delete(self._temp_rect_id)
            self._temp_rect_id = self._start_xy = None
            return
        name = name.strip()
        existing = {r.name for r in self.regions}
        if name in existing:
            k = 2
            while f"{name}_{k}" in existing: k += 1
            name = f"{name}_{k}"
        s = self._scale
        r = ROIRegion(name=name,
                      x1=int(round(min(x0,x1)/s)), y1=int(round(min(y0,y1)/s)),
                      x2=int(round(max(x0,x1)/s)), y2=int(round(max(y0,y1)/s)))
        r.normalize()
        self.regions.append(r)
        self._sync_tree()
        self._temp_rect_id = self._start_xy = None
        self.render()

    def _sync_tree(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for r in self.regions:
            self.tree.insert('', 'end', values=(r.name, f"{r.w}×{r.h}"))

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel: return
        self.regions.pop(self.tree.index(sel[0]))
        self._sync_tree(); self.render()

    def edit_selected(self):
        sel = self.tree.selection()
        if not sel: return
        idx = self.tree.index(sel[0])
        name = simpledialog.askstring("编辑名称", "新名称:", initialvalue=self.regions[idx].name)
        if name and name.strip():
            self.regions[idx].name = name.strip()
            self._sync_tree(); self.render()

    def generate_center(self, area_fraction):
        if self.pil_img is None:
            messagebox.showwarning("提示", "请先加载帧"); return
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先在列表中选中一个基础 ROI"); return
        base = self.regions[self.tree.index(sel[0])]
        iw, ih = self.pil_img.size
        default = "center_1_9" if abs(area_fraction - 1/9) < 1e-9 else "center_1_4"
        name = simpledialog.askstring("中心区命名", "名称:", initialvalue=default)
        if not name: return
        name = name.strip()
        existing = {r.name for r in self.regions}
        if name in existing:
            k = 2
            while f"{name}_{k}" in existing: k += 1
            name = f"{name}_{k}"
        try:
            c = make_center_roi(base, area_fraction, name, iw, ih)
        except Exception as e:
            messagebox.showerror("生成失败", str(e)); return
        self.regions.append(c)
        self._sync_tree(); self.render()

    def clear_rois(self, redraw=True):
        self.regions = []
        self._sync_tree()
        if redraw: self.render()

    def save_json(self):
        if not self.regions:
            messagebox.showwarning("提示", "没有标注区域"); return
        default_path = str(OF_ROI_JSON)
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            initialfile=os.path.basename(default_path),
                                            initialdir=os.path.dirname(default_path))
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({"video": self.video_path or "", "regions": [asdict(r) for r in self.regions]},
                          f, indent=2, ensure_ascii=False)
            messagebox.showinfo("成功", f"已保存:\n{path}")

    def load_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")],
                                          initialdir=str(OF_ROI_JSON.parent) if OF_ROI_JSON.parent.exists() else ".")
        if not path: return
        try:
            with open(path, 'r', encoding='utf-8') as f: data = json.load(f)
            self.regions = []
            for r in data.get('regions', []):
                self.regions.append(ROIRegion(**{k: r[k] for k in ('name','x1','y1','x2','y2')}))
            self._sync_tree(); self.render()
            messagebox.showinfo("成功", f"已加载 {len(self.regions)} 个区域")
        except Exception as e:
            messagebox.showerror("错误", f"加载失败: {e}")


if __name__ == "__main__":
    ROIAnnotator().mainloop()
