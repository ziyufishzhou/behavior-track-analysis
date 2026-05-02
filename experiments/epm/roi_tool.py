import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image, ImageTk

# ===================== 数据结构 =====================
@dataclass
class ROIRegion:
    name: str
    x1: int
    y1: int
    x2: int
    y2: int

    def normalize(self):
        """确保 x1 < x2 且 y1 < y2"""
        self.x1, self.x2 = sorted([self.x1, self.x2])
        self.y1, self.y2 = sorted([self.y1, self.y2])

# ===================== 主程序 =====================
class EPMAnnotator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EPM 智能标注工具 - 精准边界修正版")
        self.geometry("1300x850")
        
        self.video_path = None
        self.pil_img = None
        self.tk_img = None
        self.regions: List[ROIRegion] = []
        
        self._scale = 1.0
        self._start_xy = None
        self._temp_rect_id = None

        self._setup_ui()

    def _setup_ui(self):
        # 顶部控制栏
        top = tk.Frame(self, pady=5)
        top.pack(side=tk.TOP, fill=tk.X)

        tk.Button(top, text="1. 打开视频", command=self.load_video, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="2. 保存 JSON", command=self.save_json, bg="#c3e6cb", width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="清空所有", command=self.clear_all, width=10).pack(side=tk.LEFT, padx=5)
        
        self.info_label = tk.Label(top, text="状态: 请加载视频", fg="blue")
        self.info_label.pack(side=tk.LEFT, padx=20)

        # 主界面布局
        main_frame = tk.Frame(self)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main_frame, bg="#1a1a1a", cursor="cross")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_panel = tk.Frame(main_frame, width=280, padx=10)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(right_panel, text="[ ROI 管理列表 ]", font=('Arial', 10, 'bold')).pack(pady=10)
        self.listbox = tk.Listbox(right_panel, height=20)
        self.listbox.pack(fill=tk.X, pady=5)
        
        tk.Button(right_panel, text="删除选中 ROI", command=self.delete_selected).pack(fill=tk.X)

        tk.Frame(right_panel, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, pady=15)
        
        # 核心按钮
        btn_auto = tk.Button(right_panel, text="自动生成 Center Zone", 
                             command=self.auto_generate_center, 
                             bg="#ffeeba", font=('Arial', 10, 'bold'), pady=10)
        btn_auto.pack(fill=tk.X)

        help_text = (
            "【中心区计算逻辑】\n"
            "X = [左臂右边缘, 右臂左边缘]\n"
            "Y = [上臂下边缘, 下臂上边缘]\n"
            "\n*请确保每组有4个臂\n"
            "*命名需带前缀(如 M1_...)"
        )
        # 修正处：side=bottom 改为 side=tk.BOTTOM
        tk.Label(right_panel, text=help_text, justify="left", fg="#d9534f", font=('微软雅黑', 9)).pack(side=tk.BOTTOM, pady=20)

        self.canvas.bind("<Button-1>", self.on_mousedown)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouseup)
        self.bind("<Configure>", lambda e: self.redraw())

    def load_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mkv *.mov")])
        if not path: return
        cap = cv2.VideoCapture(path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
        success, frame = cap.read()
        cap.release()
        if success:
            self.video_path = path
            self.pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            self.info_label.config(text=f"当前视频: {os.path.basename(path)}", fg="black")
            self.redraw()

    def redraw(self):
        if self.pil_img is None: return
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cw < 10: cw, ch = 900, 650
        iw, ih = self.pil_img.size
        self._scale = min(cw/iw, ch/ih)
        nw, nh = int(iw * self._scale), int(ih * self._scale)
        self.tk_img = ImageTk.PhotoImage(self.pil_img.resize((nw, nh), Image.Resampling.LANCZOS))
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        for r in self.regions:
            color = "#00FFFF" if "center" in r.name.lower() else "#00FF00"
            self.canvas.create_rectangle(r.x1*self._scale, r.y1*self._scale, r.x2*self._scale, r.y2*self._scale, outline=color, width=2)
            self.canvas.create_text(r.x1*self._scale, r.y1*self._scale - 5, text=r.name, fill=color, anchor="sw")

    def auto_generate_center(self):
        """精准边界逻辑：基于四个臂的方位提取边界线"""
        if len(self.regions) < 4:
            messagebox.showwarning("提示", "区域不足 4 个臂。")
            return

        groups = {}
        for r in self.regions:
            prefix = r.name.split('_')[0] if '_' in r.name else "M1"
            if prefix not in groups: groups[prefix] = []
            groups[prefix].append(r)

        generated_count = 0
        for prefix, members in groups.items():
            arms = [m for m in members if "center" not in m.name.lower()]
            if len(arms) != 4: continue

            arm_data = []
            for a in arms:
                arm_data.append({
                    'obj': a,
                    'cx': (a.x1 + a.x2) / 2,
                    'cy': (a.y1 + a.y2) / 2
                })
            
            left_arm = min(arm_data, key=lambda p: p['cx'])['obj']
            right_arm = max(arm_data, key=lambda p: p['cx'])['obj']
            top_arm = min(arm_data, key=lambda p: p['cy'])['obj']
            bottom_arm = max(arm_data, key=lambda p: p['cy'])['obj']

            # X 轴：左臂右缘 -> 右臂左缘
            cx1 = left_arm.x2
            cx2 = right_arm.x1
            # Y 轴：上臂下缘 -> 下臂上缘
            cy1 = top_arm.y2
            cy2 = bottom_arm.y1

            center_name = f"{prefix}_center_zone"
            new_center = ROIRegion(name=center_name, x1=cx1, y1=cy1, x2=cx2, y2=cy2)
            new_center.normalize()

            self.regions = [r for r in self.regions if r.name != center_name]
            self.regions.append(new_center)
            generated_count += 1

        if generated_count > 0:
            self._sync_listbox()
            self.redraw()
            messagebox.showinfo("成功", f"已生成 {generated_count} 个精准中心区。")

    def on_mousedown(self, e):
        if self.pil_img is None: return
        self._start_xy = (e.x, e.y)
        self._temp_rect_id = self.canvas.create_rectangle(e.x, e.y, e.x, e.y, outline="yellow", dash=(4,4))

    def on_drag(self, e):
        if self._start_xy:
            self.canvas.coords(self._temp_rect_id, self._start_xy[0], self._start_xy[1], e.x, e.y)

    def on_mouseup(self, e):
        if not self._start_xy: return
        name = simpledialog.askstring("命名", "格式: 前缀_名称 (如 M1_Open1)")
        if name:
            x1, y1 = [int(v / self._scale) for v in self._start_xy]
            x2, y2 = [int(v / self._scale) for v in (e.x, e.y)]
            new_roi = ROIRegion(name=name.strip(), x1=x1, y1=y1, x2=x2, y2=y2)
            new_roi.normalize()
            self.regions.append(new_roi)
            self._sync_listbox()
        if self._temp_rect_id:
            self.canvas.delete(self._temp_rect_id)
        self._start_xy = None
        self.redraw()

    def _sync_listbox(self):
        self.listbox.delete(0, tk.END)
        for r in self.regions: self.listbox.insert(tk.END, r.name)

    def delete_selected(self):
        sel = self.listbox.curselection()
        if sel:
            self.regions.pop(sel[0]); self._sync_listbox(); self.redraw()

    def clear_all(self):
        if messagebox.askyesno("确认", "清空所有 ROI 吗？"):
            self.regions = []; self._sync_listbox(); self.redraw()

    def save_json(self):
        if not self.regions: return
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            output = {"video": self.video_path, "regions": [asdict(r) for r in self.regions]}
            with open(path, 'w', encoding='utf-8') as f: json.dump(output, f, indent=4)
            messagebox.showinfo("成功", "JSON 保存成功")

if __name__ == "__main__":
    EPMAnnotator().mainloop()