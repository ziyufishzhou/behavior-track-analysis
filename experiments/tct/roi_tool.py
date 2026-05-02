import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from dataclasses import dataclass, asdict
from typing import List
import cv2
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
        """确保坐标顺序正确"""
        self.x1, self.x2 = sorted([self.x1, self.x2])
        self.y1, self.y2 = sorted([self.y1, self.y2])

# ===================== 主程序 =====================
class TCTAnnotator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TCT 三箱社交实验标注工具 - 自动对齐版")
        self.geometry("1400x900")
        
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
        top = tk.Frame(self, pady=8, bg="#2c3e50")
        top.pack(side=tk.TOP, fill=tk.X)

        tk.Button(top, text="📂 加载视频", command=self.load_video, width=12, bg="#ecf0f1").pack(side=tk.LEFT, padx=10)
        tk.Button(top, text="⚡ 自动生成中间箱", command=self.auto_generate_center, bg="#f1c40f", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=10)
        tk.Button(top, text="💾 保存 JSON", command=self.save_json, bg="#2ecc71", fg="white", width=12).pack(side=tk.LEFT, padx=10)
        tk.Button(top, text="🗑️ 全部清空", command=self.clear_all, bg="#e74c3c", fg="white").pack(side=tk.LEFT, padx=10)
        
        self.info_label = tk.Label(top, text="状态: 请加载视频", fg="white", bg="#2c3e50", font=('Arial', 10))
        self.info_label.pack(side=tk.LEFT, padx=20)

        # 主界面布局
        main_frame = tk.Frame(self)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main_frame, bg="#1a1a1a", cursor="cross")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 右侧面板
        right_panel = tk.Frame(main_frame, width=300, padx=15, bg="#ffffff")
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(right_panel, text="[ 已标注区域 ]", font=('Arial', 11, 'bold'), bg="#ffffff").pack(pady=10)
        
        # 列表框
        self.listbox = tk.Listbox(right_panel, height=20, font=('Consolas', 10))
        self.listbox.pack(fill=tk.BOTH, expand=False, pady=5)
        
        tk.Button(right_panel, text="删除选中 ROI", command=self.delete_selected).pack(fill=tk.X)

        # 命名指南
        guide_box = tk.LabelFrame(right_panel, text=" 命名规则说明 ", padx=10, pady=10, bg="#ffffff", fg="#2980b9")
        guide_box.pack(fill=tk.X, pady=20)
        
        guide_text = (
            "1. 画左箱命名: 1_L\n"
            "2. 画右箱命名: 1_R\n"
            "3. 点击上方'自动生成'\n\n"
            "※ 支持 1_L, 2_L, 3_L...\n"
            "※ 生成后中间箱命名为 1_Center"
        )
        tk.Label(guide_box, text=guide_text, justify="left", bg="#ffffff", font=('微软雅黑', 9)).pack()

        # 事件绑定
        self.canvas.bind("<Button-1>", self.on_mousedown)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouseup)
        self.bind("<Configure>", lambda e: self.redraw())

    def load_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mkv *.mov")])
        if not path: return
        cap = cv2.VideoCapture(path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 50) # 跳过开头可能的不稳定帧
        success, frame = cap.read()
        cap.release()
        if success:
            self.video_path = path
            self.pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            self.info_label.config(text=f"当前视频: {os.path.basename(path)}", fg="#2ecc71")
            self.redraw()

    def redraw(self):
        if self.pil_img is None: return
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cw < 10: cw, ch = 1000, 700
        iw, ih = self.pil_img.size
        self._scale = min(cw/iw, ch/ih)
        nw, nh = int(iw * self._scale), int(ih * self._scale)
        
        resized = self.pil_img.resize((nw, nh), Image.Resampling.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(resized)
        
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        
        for r in self.regions:
            name_low = r.name.lower()
            # 颜色逻辑：左红，右绿，中蓝
            color = "#e74c3c" if "_l" in name_low else ("#2ecc71" if "_r" in name_low else "#3498db")
            
            x1, y1, x2, y2 = r.x1*self._scale, r.y1*self._scale, r.x2*self._scale, r.y2*self._scale
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=2)
            self.canvas.create_text(x1, y1-5, text=r.name, fill=color, anchor="sw", font=('Arial', 10, 'bold'))

    def auto_generate_center(self):
        """根据已有的 _L 和 _R 自动闭合中间区域"""
        groups = {}
        for r in self.regions:
            if "_" in r.name:
                prefix = r.name.split('_')[0]
                if prefix not in groups: groups[prefix] = []
                groups[prefix].append(r)

        new_centers = []
        for prefix, members in groups.items():
            l_roi = next((m for m in members if m.name.lower().endswith('_l')), None)
            r_roi = next((m for m in members if m.name.lower().endswith('_r')), None)

            if l_roi and r_roi:
                # 核心逻辑：取 L 的右边缘到 R 的左边缘
                cx1, cx2 = l_roi.x2, r_roi.x1
                # 纵向取平均值以对齐
                cy1 = (l_roi.y1 + r_roi.y1) // 2
                cy2 = (l_roi.y2 + r_roi.y2) // 2
                
                center_name = f"{prefix}_Center"
                # 移除旧的同名中心区
                self.regions = [r for r in self.regions if r.name != center_name]
                
                new_roi = ROIRegion(name=center_name, x1=cx1, y1=cy1, x2=cx2, y2=cy2)
                new_roi.normalize()
                new_centers.append(new_roi)

        if new_centers:
            self.regions.extend(new_centers)
            self._sync_listbox()
            self.redraw()
            messagebox.showinfo("完成", f"已成功生成 {len(new_centers)} 个中间箱区域。")
        else:
            messagebox.showwarning("失败", "未找到匹配的 L/R 命名对。请确保命名如 '1_L' 和 '1_R'。")

    def on_mousedown(self, e):
        if self.pil_img is None: return
        self._start_xy = (e.x, e.y)
        self._temp_rect_id = self.canvas.create_rectangle(e.x, e.y, e.x, e.y, outline="white", dash=(4,4))

    def on_drag(self, e):
        if self._start_xy:
            self.canvas.coords(self._temp_rect_id, self._start_xy[0], self._start_xy[1], e.x, e.y)

    def on_mouseup(self, e):
        if not self._start_xy: return
        name = simpledialog.askstring("区域命名", "格式: 序号_L 或 序号_R (如 1_L):")
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
        # 排序让列表更整齐
        self.regions.sort(key=lambda x: x.name)
        for r in self.regions:
            self.listbox.insert(tk.END, r.name)

    def delete_selected(self):
        sel = self.listbox.curselection()
        if sel:
            name_to_del = self.listbox.get(sel[0])
            self.regions = [r for r in self.regions if r.name != name_to_del]
            self._sync_listbox()
            self.redraw()

    def clear_all(self):
        if messagebox.askyesno("确认", "确定清空所有标注？"):
            self.regions = []
            self._sync_listbox()
            self.redraw()

    def save_json(self):
        if not self.regions: return
        path = filedialog.asksaveasfilename(defaultextension=".json", initialfile="TCT_ROI_Config.json")
        if path:
            output = {
                "video_source": self.video_path,
                "total_regions": len(self.regions),
                "regions": [asdict(r) for r in self.regions]
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("成功", "ROI 配置文件已保存。")

if __name__ == "__main__":
    TCTAnnotator().mainloop()