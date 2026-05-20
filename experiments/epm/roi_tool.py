"""
EPM ROI 标注工具 — 十字交叉版
- 点击 4 点画横矩形，点击 2 点画竖矩形（宽高自动匹配）
- 两矩形交叉 = 中心区，自动分割为 5 个区域
- 用户为每个区域命名 + 选 group
"""
import os
import sys
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from dataclasses import dataclass, asdict
from typing import List
import cv2
import numpy as np
from PIL import Image, ImageTk

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from config.paths import EPM_ROI_JSON
from gui.roi_styles import (
    BG_DARK, BG_PANEL, BG_TOOLBAR, BG_INPUT, BG_CARD,
    FG_PRIMARY, FG_SECONDARY, FG_DIM,
    ACCENT_BLUE, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_RED, ACCENT_TEAL, ACCENT_YELLOW,
    make_btn, make_toolbar, make_info_label, make_side_panel,
    make_section, make_param_row, make_treeview, make_help_box,
    apply_dark_theme, color_for_group,
)


@dataclass
class ROIPolygon:
    name: str
    points: list
    group: str

GROUP_LABELS = {'open': '开放臂', 'closed': '闭合臂', 'center': '中心区'}


class RegionNameDialog(tk.Toplevel):
    """为分割出的 5 个区域命名 + 选 group"""

    def __init__(self, parent, regions_info):
        super().__init__(parent)
        self.title("命名区域")
        self.configure(bg=BG_DARK)
        self.resizable(False, False)
        self.grab_set()
        self.result = None

        frame = tk.Frame(self, bg=BG_DARK, padx=20, pady=16)
        frame.pack()

        tk.Label(frame, text="为每个区域命名并选择分组",
                 bg=BG_DARK, fg=FG_PRIMARY,
                 font=('Segoe UI', 11, 'bold')).grid(row=0, column=0, columnspan=3, pady=(0, 12))

        self.vars = []
        for i, (default_name, default_group) in enumerate(regions_info):
            row = i + 1
            color = color_for_group(default_group)
            tk.Label(frame, text=f"区域 {i+1}", bg=BG_DARK, fg=color,
                     font=('Segoe UI', 9, 'bold'), width=5, anchor='e').grid(
                row=row, column=0, pady=4, padx=(0, 8))
            name_var = tk.StringVar(value=default_name)
            e = tk.Entry(frame, textvariable=name_var, width=14, bg=BG_INPUT, fg=FG_PRIMARY,
                         font=('Segoe UI', 9), relief='flat', bd=0, insertbackground=FG_PRIMARY)
            e.grid(row=row, column=1, padx=(0, 6), pady=4)
            group_var = tk.StringVar(value=default_group)
            cb = ttk.Combobox(frame, textvariable=group_var,
                              values=['open', 'closed', 'center'], state='readonly', width=8)
            cb.grid(row=row, column=2, pady=4)
            self.vars.append((name_var, group_var))

        btn_frame = tk.Frame(frame, bg=BG_DARK)
        btn_frame.grid(row=len(regions_info) + 1, column=0, columnspan=3, pady=(16, 0))
        make_btn(btn_frame, "确 定", self._ok, accent='green', width=10).pack(side=tk.LEFT, padx=6)
        make_btn(btn_frame, "取 消", self._cancel, accent='red', width=10).pack(side=tk.LEFT, padx=6)

        self.bind('<Return>', lambda e: self._ok())
        self.bind('<Escape>', lambda e: self._cancel())
        self.transient(parent)
        self.wait_visibility()
        x = parent.winfo_rootx() + parent.winfo_width() // 2 - self.winfo_width() // 2
        y = parent.winfo_rooty() + parent.winfo_height() // 2 - self.winfo_height() // 2
        self.geometry(f"+{x}+{y}")

    def _ok(self):
        arms = []
        for name_var, group_var in self.vars:
            name = name_var.get().strip()
            group = group_var.get()
            if not name:
                messagebox.showwarning("提示", "请填写所有区域名称", parent=self)
                return
            arms.append((name, group))
        self.result = arms
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


def cross_split(h_rect, v_rect):
    hx1, hy1, hx2, hy2 = h_rect
    vx1, vy1, vx2, vy2 = v_rect
    cx1, cy1 = max(hx1, vx1), max(hy1, vy1)
    cx2, cy2 = min(hx2, vx2), min(hy2, vy2)
    if cx1 >= cx2 or cy1 >= cy2:
        raise ValueError("两个矩形没有交叉区域，请重新标注")
    return [
        ('center', 'center', [[cx1, cy1], [cx2, cy1], [cx2, cy2], [cx1, cy2]]),
        ('top',    'open',   [[vx1, vy1], [vx2, vy1], [vx2, cy1], [vx1, cy1]]),
        ('bottom', 'open',   [[vx1, cy2], [vx2, cy2], [vx2, vy2], [vx1, vy2]]),
        ('left',   'closed', [[hx1, hy1], [cx1, hy1], [cx1, hy2], [hx1, hy2]]),
        ('right',  'closed', [[cx2, hy1], [hx2, hy1], [hx2, hy2], [cx2, hy2]]),
    ]


class EPMAnnotator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EPM ROI 标注工具")
        self.geometry("1400x900")
        apply_dark_theme(self)

        self.video_path = None
        self.pil_img = None
        self.tk_img = None
        self.regions: List[ROIPolygon] = []

        self._scale = 1.0
        self._draw_step = 0
        self._click_points = []
        self._point_ids = []
        self._line_ids = []
        self._h_rect = None
        self._v_rect = None
        self._h_size = None

        self.center_size_cm = tk.DoubleVar(value=5.0)
        self.open_arm_length_cm = tk.DoubleVar(value=30.0)
        self.closed_arm_length_cm = tk.DoubleVar(value=30.0)
        self.entry_depth_ratio = tk.DoubleVar(value=0.2)

        self._setup_ui()
        if EPM_ROI_JSON.exists():
            self._load_existing_json()

    def _setup_ui(self):
        # ---- 顶部工具栏 ----
        toolbar = make_toolbar(self)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        make_btn(toolbar, "打开视频", self.load_video, accent='blue', width=10).pack(side=tk.LEFT, padx=4)
        make_btn(toolbar, "画横矩形", lambda: self._start_draw(1), accent='teal', width=10).pack(side=tk.LEFT, padx=4)
        make_btn(toolbar, "画竖矩形", lambda: self._start_draw(2), accent='teal', width=10).pack(side=tk.LEFT, padx=4)

        tk.Frame(toolbar, bg=FG_DIM, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=4)

        make_btn(toolbar, "保存 JSON", self.save_json, accent='green', width=10).pack(side=tk.LEFT, padx=4)
        make_btn(toolbar, "加载 JSON", self.load_json, accent='orange', width=10).pack(side=tk.LEFT, padx=4)
        make_btn(toolbar, "清 空", self.clear_all, accent='red', width=8).pack(side=tk.LEFT, padx=4)

        self.info_label = make_info_label(toolbar, "请加载视频 → 画横矩形(4点) → 画竖矩形(2点)")
        self.info_label.pack(side=tk.LEFT, padx=16)

        # ---- 主区域 ----
        main = tk.Frame(self, bg=BG_DARK)
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main, bg='#11111B', cursor="cross", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ---- 右侧面板 ----
        panel = make_side_panel(main, width=310)
        panel.pack(side=tk.RIGHT, fill=tk.Y)

        # 物理尺寸参数
        sec = make_section(panel, "物理尺寸参数")
        sec.pack(fill=tk.X, pady=(0, 10))
        make_param_row(sec, "中心区边长", self.center_size_cm, "cm")
        make_param_row(sec, "开放臂长度", self.open_arm_length_cm, "cm")
        make_param_row(sec, "闭合臂长度", self.closed_arm_length_cm, "cm")
        make_param_row(sec, "入场深度比", self.entry_depth_ratio, "")

        # 区域列表
        tk.Label(panel, text="ROI 区域列表", bg=BG_PANEL, fg=FG_PRIMARY,
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(4, 6))

        tree_frame, self.tree = make_treeview(
            panel, columns=('name', 'group'), headings=('名称', '分组'), height=12)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview group 颜色 tag
        self.tree.tag_configure('open',   foreground=ACCENT_BLUE)
        self.tree.tag_configure('closed', foreground=ACCENT_ORANGE)
        self.tree.tag_configure('center', foreground=ACCENT_GREEN)

        btn_row = tk.Frame(panel, bg=BG_PANEL)
        btn_row.pack(fill=tk.X, pady=6)
        make_btn(btn_row, "编辑选中", self.edit_selected, accent='blue', width=10).pack(side=tk.LEFT, padx=(0, 4))
        make_btn(btn_row, "删除选中", self.delete_selected, accent='red', width=10).pack(side=tk.LEFT)

        # 帮助
        make_help_box(panel,
            "1. 打开视频\n"
            "2. 点击「画横矩形」→ 点击 4 个角点\n"
            "3. 点击「画竖矩形」→ 点击 2 个角点\n"
            "   (宽高自动匹配横矩形)\n"
            "4. 交叉区域自动识别为中心区\n"
            "5. 弹窗为每个区域命名 + 选分组\n"
            "6. 右键或 Esc 取消当前标注")

        # 画布事件
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", lambda e: self._cancel_draw())
        self.bind("<Escape>", lambda e: self._cancel_draw())
        self.bind("<Configure>", lambda e: self.redraw())

    # ============ 画布交互 ============

    def _start_draw(self, step):
        if self.pil_img is None:
            messagebox.showwarning("提示", "请先打开视频")
            return
        self._draw_step = step
        self._click_points = []
        self._clear_temp_marks()
        if step == 1:
            self.info_label.config(text="点击 4 个角点画横矩形...", fg=ACCENT_TEAL)
        elif step == 2:
            if self._h_rect is None:
                messagebox.showwarning("提示", "请先画横矩形")
                self._draw_step = 0
                return
            self.info_label.config(text="点击 2 个角点画竖矩形（宽高自动匹配）...", fg=ACCENT_TEAL)

    def _cancel_draw(self):
        self._draw_step = 0
        self._click_points = []
        self._clear_temp_marks()
        self.info_label.config(text="已取消", fg=FG_SECONDARY)
        self.redraw()

    def _clear_temp_marks(self):
        for pid in self._point_ids:
            self.canvas.delete(pid)
        for lid in self._line_ids:
            self.canvas.delete(lid)
        self._point_ids = []
        self._line_ids = []

    def on_canvas_click(self, event):
        if self._draw_step == 0 or self.pil_img is None:
            return

        ox, oy = event.x / self._scale, event.y / self._scale
        self._click_points.append((ox, oy))

        r = 5
        pid = self.canvas.create_oval(
            event.x - r, event.y - r, event.x + r, event.y + r,
            fill=ACCENT_YELLOW, outline='white', width=1)
        self._point_ids.append(pid)

        if len(self._click_points) >= 2:
            prev = self._click_points[-2]
            px, py = prev[0] * self._scale, prev[1] * self._scale
            lid = self.canvas.create_line(px, py, event.x, event.y,
                                          fill=ACCENT_YELLOW, width=2, dash=(4, 4))
            self._line_ids.append(lid)

        if self._draw_step == 1 and len(self._click_points) == 4:
            self._finish_h_rect()
        elif self._draw_step == 2 and len(self._click_points) == 2:
            self._finish_v_rect()

    def _finish_h_rect(self):
        pts = self._click_points[:4]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        self._h_rect = (min(xs), min(ys), max(xs), max(ys))
        self._h_size = (max(xs) - min(xs), max(ys) - min(ys))
        self._click_points = []
        self._clear_temp_marks()
        self.info_label.config(
            text=f"横矩形完成 ({self._h_size[0]:.0f}×{self._h_size[1]:.0f}px) → 画竖矩形",
            fg=ACCENT_BLUE)
        self.redraw()
        hx1, hy1, hx2, hy2 = self._h_rect
        self.canvas.create_rectangle(
            hx1 * self._scale, hy1 * self._scale,
            hx2 * self._scale, hy2 * self._scale,
            outline=ACCENT_TEAL, width=2)

    def _finish_v_rect(self):
        pts = self._click_points[:2]
        cx = (pts[0][0] + pts[1][0]) / 2
        cy = (pts[0][1] + pts[1][1]) / 2
        w, h = self._h_size
        self._v_rect = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
        self._click_points = []
        self._clear_temp_marks()

        try:
            regions_info = cross_split(self._h_rect, self._v_rect)
        except ValueError as ex:
            messagebox.showerror("错误", str(ex))
            self._v_rect = None
            self.redraw()
            return

        dlg = RegionNameDialog(self, [(n, g) for n, g, _ in regions_info])
        self.wait_window(dlg)
        if dlg.result is None:
            self._v_rect = None
            self.redraw()
            return

        self.regions = []
        for (name, group), (_, _, points) in zip(dlg.result, regions_info):
            self.regions.append(ROIPolygon(
                name=name,
                points=[[round(x, 1), round(y, 1)] for x, y in points],
                group=group
            ))
        self._sync_tree()
        self.info_label.config(text=f"已分割 {len(self.regions)} 个区域", fg=ACCENT_GREEN)
        self.redraw()

    # ============ 视频加载 / 绘图 ============

    def load_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mkv *.mov")])
        if not path:
            return
        cap = cv2.VideoCapture(path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
        success, frame = cap.read()
        cap.release()
        if success:
            self.video_path = path
            self.pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            self.info_label.config(text="视频已加载 → 画横矩形 → 画竖矩形", fg=ACCENT_BLUE)
            self.redraw()

    def redraw(self):
        if self.pil_img is None:
            return
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cw < 10:
            cw, ch = 900, 650
        iw, ih = self.pil_img.size
        self._scale = min(cw / iw, ch / ih)
        nw, nh = int(iw * self._scale), int(ih * self._scale)
        self.tk_img = ImageTk.PhotoImage(self.pil_img.resize((nw, nh), Image.Resampling.LANCZOS))
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

        for r in self.regions:
            color = color_for_group(r.group)
            scaled_pts = []
            for px, py in r.points:
                scaled_pts.extend([px * self._scale, py * self._scale])
            self.canvas.create_polygon(scaled_pts, outline=color, fill='', width=2)
            cx = sum(p[0] for p in r.points) / 4 * self._scale
            cy = min(p[1] for p in r.points) * self._scale - 8
            self.canvas.create_text(cx, cy, text=r.name, fill=color, anchor="s",
                                    font=('Segoe UI', 9, 'bold'))

    # ============ 区域管理 ============

    def _sync_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in self.regions:
            gl = GROUP_LABELS.get(r.group, r.group)
            self.tree.insert('', 'end', values=(r.name, gl), tags=(r.group,))

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        self.regions.pop(idx)
        self._sync_tree()
        self.redraw()

    def edit_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        r = self.regions[idx]

        dlg = tk.Toplevel(self)
        dlg.title("编辑区域")
        dlg.configure(bg=BG_DARK)
        dlg.grab_set()
        dlg.resizable(False, False)

        frame = tk.Frame(dlg, bg=BG_DARK, padx=20, pady=16)
        frame.pack()

        tk.Label(frame, text="名称:", bg=BG_DARK, fg=FG_SECONDARY,
                 font=('Segoe UI', 9)).grid(row=0, column=0, sticky='e', pady=6, padx=(0, 8))
        name_var = tk.StringVar(value=r.name)
        tk.Entry(frame, textvariable=name_var, width=16, bg=BG_INPUT, fg=FG_PRIMARY,
                 font=('Segoe UI', 9), relief='flat', insertbackground=FG_PRIMARY).grid(
            row=0, column=1, pady=6)

        tk.Label(frame, text="分组:", bg=BG_DARK, fg=FG_SECONDARY,
                 font=('Segoe UI', 9)).grid(row=1, column=0, sticky='e', pady=6, padx=(0, 8))
        group_var = tk.StringVar(value=r.group)
        ttk.Combobox(frame, textvariable=group_var,
                     values=['open', 'closed', 'center'], state='readonly', width=14).grid(
            row=1, column=1, pady=6)

        result = [None]
        def _ok():
            result[0] = (name_var.get().strip(), group_var.get())
            dlg.destroy()
        def _cancel():
            dlg.destroy()

        btn_f = tk.Frame(frame, bg=BG_DARK)
        btn_f.grid(row=2, column=0, columnspan=2, pady=(12, 0))
        make_btn(btn_f, "确 定", _ok, accent='green', width=8).pack(side=tk.LEFT, padx=6)
        make_btn(btn_f, "取 消", _cancel, accent='red', width=8).pack(side=tk.LEFT, padx=6)

        dlg.transient(self)
        dlg.wait_window()

        if result[0]:
            name, group = result[0]
            self.regions[idx] = ROIPolygon(name=name, points=r.points, group=group)
            self._sync_tree()
            self.redraw()

    def clear_all(self):
        if messagebox.askyesno("确认", "清空所有 ROI 吗？"):
            self.regions = []
            self._h_rect = self._v_rect = self._h_size = None
            self._sync_tree()
            self.redraw()
            self.info_label.config(text="请画横矩形 → 画竖矩形", fg=FG_SECONDARY)

    # ============ 保存 / 加载 JSON ============

    def save_json(self):
        if not self.regions:
            messagebox.showwarning("提示", "没有标注区域")
            return
        output = {
            "video": self.video_path or "",
            "h_rect": list(self._h_rect) if self._h_rect else None,
            "v_rect": list(self._v_rect) if self._v_rect else None,
            "center_size_cm": self.center_size_cm.get(),
            "open_arm_length_cm": self.open_arm_length_cm.get(),
            "closed_arm_length_cm": self.closed_arm_length_cm.get(),
            "entry_depth_ratio": self.entry_depth_ratio.get(),
            "regions": [asdict(r) for r in self.regions],
        }
        default_path = str(EPM_ROI_JSON)
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile=os.path.basename(default_path),
            initialdir=os.path.dirname(default_path),
        )
        if path:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("成功", f"JSON 已保存:\n{path}")

    def load_json(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json")],
            initialdir=str(EPM_ROI_JSON.parent) if EPM_ROI_JSON.parent.exists() else ".",
        )
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._apply_json_data(data)
            messagebox.showinfo("成功", f"已加载 {len(self.regions)} 个区域")
        except Exception as e:
            messagebox.showerror("错误", f"加载失败: {e}")

    def _load_existing_json(self):
        try:
            with open(str(EPM_ROI_JSON), 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._apply_json_data(data)
            self.info_label.config(
                text=f"已加载: {EPM_ROI_JSON.name} ({len(self.regions)} 区域)", fg=ACCENT_GREEN)
        except Exception:
            pass

    def _apply_json_data(self, data):
        self.regions = []
        for r in data.get('regions', []):
            if 'points' in r and 'group' in r:
                self.regions.append(ROIPolygon(name=r['name'], points=r['points'], group=r['group']))
            elif 'x1' in r:
                self.regions.append(ROIPolygon(
                    name=r['name'],
                    points=[[r['x1'], r['y1']], [r['x2'], r['y1']],
                            [r['x2'], r['y2']], [r['x1'], r['y2']]],
                    group='center' if 'center' in r['name'].lower()
                    else 'open' if 'open' in r['name'].lower() else 'closed'))
        if 'center_size_cm' in data: self.center_size_cm.set(data['center_size_cm'])
        if 'open_arm_length_cm' in data: self.open_arm_length_cm.set(data['open_arm_length_cm'])
        if 'closed_arm_length_cm' in data: self.closed_arm_length_cm.set(data['closed_arm_length_cm'])
        if 'entry_depth_ratio' in data: self.entry_depth_ratio.set(data['entry_depth_ratio'])
        if data.get('video'): self.video_path = data['video']
        if data.get('h_rect'): self._h_rect = tuple(data['h_rect'])
        if data.get('v_rect'): self._v_rect = tuple(data['v_rect'])
        if self._h_rect:
            self._h_size = (self._h_rect[2] - self._h_rect[0], self._h_rect[3] - self._h_rect[1])
        self._sync_tree()
        if self.pil_img: self.redraw()


if __name__ == "__main__":
    EPMAnnotator().mainloop()
