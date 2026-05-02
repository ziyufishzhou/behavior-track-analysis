import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageTk


# ===================== 你可以改的默认值 =====================
DEFAULT_FRAME_INDEX = 300          # 默认读取第几帧（0-based）
DEFAULT_OUTPUT_NAME = "roi_regions.json"

# 自动生成 center zone 的默认命名
DEFAULT_CENTER_NAME_1_9 = "center_1_9"
DEFAULT_CENTER_NAME_1_4 = "center_1_4"
# =========================================================


@dataclass
class ROIRegion:
    name: str
    x1: int  # left
    y1: int  # top
    x2: int  # right
    y2: int  # bottom

    def normalize(self):
        lx, rx = sorted([self.x1, self.x2])
        ty, by = sorted([self.y1, self.y2])
        self.x1, self.x2, self.y1, self.y2 = lx, rx, ty, by

    @property
    def w(self) -> int:
        return int(self.x2 - self.x1)

    @property
    def h(self) -> int:
        return int(self.y2 - self.y1)

    @property
    def cx(self) -> float:
        return (self.x1 + self.x2) / 2.0

    @property
    def cy(self) -> float:
        return (self.y1 + self.y2) / 2.0


@dataclass
class ROIProject:
    video_path: str
    frame_index: int
    image_width: int
    image_height: int
    regions: List[ROIRegion]

    def to_dict(self):
        return {
            "video_path": self.video_path,
            "frame_index": int(self.frame_index),
            "image_width": int(self.image_width),
            "image_height": int(self.image_height),
            "regions": [asdict(r) for r in self.regions],
        }


def read_frame_from_video(video_path: str, frame_index: int) -> np.ndarray:
    """读取指定帧（0-based），返回 BGR ndarray。"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频：{video_path}")

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        cap.release()
        raise RuntimeError("无法获取视频总帧数（可能是编码/解码问题）。")

    if frame_index < 0 or frame_index >= total:
        cap.release()
        raise ValueError(f"frame_index 越界：{frame_index}，视频总帧数为 {total}（合法范围 0~{total-1}）")

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ok, frame = cap.read()
    cap.release()

    if not ok or frame is None:
        raise RuntimeError(f"读取第 {frame_index} 帧失败。")

    return frame


def make_center_roi(base: ROIRegion, area_fraction: float, name: str, img_w: int, img_h: int) -> ROIRegion:
    """
    在 base ROI 中心生成一个矩形 center zone，使得其面积为 base 的 area_fraction。
    area_fraction = 1/9 -> 宽高各缩放 1/3
    area_fraction = 1/4 -> 宽高各缩放 1/2
    """
    if base.w <= 2 or base.h <= 2:
        raise ValueError("基础 ROI 太小，无法生成 center zone。")

    if area_fraction <= 0 or area_fraction >= 1:
        raise ValueError("area_fraction 必须在 (0,1) 内，例如 1/9 或 1/4。")

    # 面积比例 -> 边长比例
    scale = math.sqrt(area_fraction)

    new_w = max(2, int(round(base.w * scale)))
    new_h = max(2, int(round(base.h * scale)))

    cx, cy = base.cx, base.cy
    x1 = int(round(cx - new_w / 2.0))
    x2 = int(round(cx + new_w / 2.0))
    y1 = int(round(cy - new_h / 2.0))
    y2 = int(round(cy + new_h / 2.0))

    # clamp 到图像范围
    x1 = max(0, min(x1, img_w - 1))
    y1 = max(0, min(y1, img_h - 1))
    x2 = max(0, min(x2, img_w - 1))
    y2 = max(0, min(y2, img_h - 1))

    r = ROIRegion(name=name, x1=x1, y1=y1, x2=x2, y2=y2)
    r.normalize()
    return r


import math


class ROIAnnotator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ROI 标注（从视频指定帧读取）+ 自动生成 Center Zone")
        self.geometry("1300x780")

        # --- 状态 ---
        self.video_path: Optional[str] = None
        self.frame_index: int = DEFAULT_FRAME_INDEX

        self.pil_img: Optional[Image.Image] = None
        self.tk_img: Optional[ImageTk.PhotoImage] = None

        self.regions: List[ROIRegion] = []

        # 绘制交互状态
        self._scale = 1.0
        self._start_xy: Optional[Tuple[int, int]] = None
        self._temp_rect_id = None

        # --- UI ---
        top = tk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.X)

        btn_video = tk.Button(top, text="1) 选择视频", command=self.choose_video)
        btn_video.pack(side=tk.LEFT, padx=6, pady=6)

        btn_frame = tk.Button(top, text="2) 选择帧号并加载", command=self.ask_frame_and_load)
        btn_frame.pack(side=tk.LEFT, padx=6, pady=6)

        btn_save = tk.Button(top, text="3) 保存 ROI_JSON", command=self.save_json)
        btn_save.pack(side=tk.LEFT, padx=6, pady=6)

        btn_clear = tk.Button(top, text="清空 ROI", command=self.clear_rois)
        btn_clear.pack(side=tk.LEFT, padx=6, pady=6)

        self.info_label = tk.Label(top, text="未选择视频", anchor="w")
        self.info_label.pack(side=tk.LEFT, padx=12)

        main = tk.Frame(self)
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main, bg="#222")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right = tk.Frame(main, width=380)
        right.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(right, text="ROI 列表（选中可删除/生成中心区）").pack(anchor="w", padx=8, pady=(8, 2))
        self.listbox = tk.Listbox(right, height=18)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # ROI 操作按钮
        btn_del = tk.Button(right, text="删除选中 ROI", command=self.delete_selected)
        btn_del.pack(fill=tk.X, padx=8, pady=4)

        sep = tk.Frame(right, height=2, bd=1, relief=tk.SUNKEN)
        sep.pack(fill=tk.X, padx=8, pady=10)

        tk.Label(right, text="OF Center Zone（从选中 ROI 自动生成）").pack(anchor="w", padx=8, pady=(0, 4))

        btn_c19 = tk.Button(right, text="生成中心区 (1/9 面积)", command=lambda: self.generate_center(area_fraction=1/9))
        btn_c19.pack(fill=tk.X, padx=8, pady=4)

        btn_c14 = tk.Button(right, text="生成中心区 (1/4 面积)", command=lambda: self.generate_center(area_fraction=1/4))
        btn_c14.pack(fill=tk.X, padx=8, pady=4)

        tips = (
            "操作建议（OF）：\n"
            "1) 先画一个“全箱体”ROI（例如 arena / box）\n"
            "2) 在列表里选中它\n"
            "3) 点击生成中心区 1/9 或 1/4\n"
            "4) center ROI 会自动加入列表并显示\n"
        )
        tk.Label(right, text=tips, justify="left").pack(anchor="w", padx=8, pady=10)

        # --- 绑定鼠标事件 ---
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        # 窗口 resize 时重绘
        self.bind("<Configure>", lambda e: self.render_image_fit())

    # ---------------- UI actions ----------------
    def choose_video(self):
        path = filedialog.askopenfilename(
            title="选择一个视频文件",
            filetypes=[("Video", "*.mp4;*.avi;*.mkv;*.mov;*.wmv;*.mpg;*.mpeg"), ("All", "*.*")]
        )
        if not path:
            return
        self.video_path = path
        self.info_label.config(text=f"视频：{os.path.basename(path)} | 帧号：{self.frame_index}（未加载）")

    def ask_frame_and_load(self):
        if not self.video_path:
            messagebox.showwarning("提示", "请先选择视频。")
            return

        s = simpledialog.askstring("帧号", f"请输入要读取的帧号（0-based），例如 {DEFAULT_FRAME_INDEX}：")
        if s is None:
            return
        s = s.strip()
        if s == "":
            return
        try:
            idx = int(s)
        except Exception:
            messagebox.showerror("错误", "帧号必须是整数。")
            return

        try:
            frame_bgr = read_frame_from_video(self.video_path, idx)
        except Exception as e:
            messagebox.showerror("读取失败", str(e))
            return

        self.frame_index = idx

        # BGR -> RGB -> PIL
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        self.pil_img = Image.fromarray(frame_rgb)

        # 清空旧 ROI（不同帧避免混淆）
        self.clear_rois(redraw=False)
        self.listbox.delete(0, tk.END)

        self.info_label.config(
            text=f"视频：{os.path.basename(self.video_path)} | 帧号：{self.frame_index} | 尺寸：{self.pil_img.size[0]}x{self.pil_img.size[1]}"
        )
        self.render_image_fit()

    def save_json(self):
        if self.pil_img is None or not self.video_path:
            messagebox.showwarning("提示", "请先选择视频并加载一帧。")
            return

        iw, ih = self.pil_img.size
        proj = ROIProject(
            video_path=self.video_path,
            frame_index=self.frame_index,
            image_width=iw,
            image_height=ih,
            regions=self.regions
        )

        out_path = filedialog.asksaveasfilename(
            title="保存 ROI JSON",
            defaultextension=".json",
            initialfile=DEFAULT_OUTPUT_NAME,
            filetypes=[("JSON", "*.json")]
        )
        if not out_path:
            return

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(proj.to_dict(), f, ensure_ascii=False, indent=2)

        messagebox.showinfo("完成", f"已保存：\n{out_path}")

    def clear_rois(self, redraw=True):
        self.regions = []
        self.listbox.delete(0, tk.END)
        if redraw:
            self.render_image_fit()

    def delete_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        i = sel[0]
        self.listbox.delete(i)
        self.regions.pop(i)
        self.render_image_fit()

    def generate_center(self, area_fraction: float):
        if self.pil_img is None:
            messagebox.showwarning("提示", "请先加载一帧图像。")
            return
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("提示", "请先在 ROI 列表中选中一个基础 ROI（例如全箱体 arena）。")
            return

        base = self.regions[sel[0]]
        iw, ih = self.pil_img.size

        default_name = DEFAULT_CENTER_NAME_1_9 if abs(area_fraction - 1/9) < 1e-9 else DEFAULT_CENTER_NAME_1_4
        name = simpledialog.askstring("Center ROI 命名", f"请输入中心区 ROI 名称：", initialvalue=default_name)
        if not name:
            return
        name = name.strip()

        # 防止重名：重名则自动加后缀
        existing = set([r.name for r in self.regions])
        if name in existing:
            k = 2
            new_name = f"{name}_{k}"
            while new_name in existing:
                k += 1
                new_name = f"{name}_{k}"
            name = new_name

        try:
            center_roi = make_center_roi(base, area_fraction=area_fraction, name=name, img_w=iw, img_h=ih)
        except Exception as e:
            messagebox.showerror("生成失败", str(e))
            return

        self.regions.append(center_roi)
        self.listbox.insert(tk.END, f"{center_roi.name}: ({center_roi.x1},{center_roi.y1})-({center_roi.x2},{center_roi.y2})")
        self.render_image_fit()

    # ---------------- Rendering ----------------
    def render_image_fit(self):
        if self.pil_img is None:
            return

        self.canvas.update_idletasks()
        cw = max(1, self.canvas.winfo_width())
        ch = max(1, self.canvas.winfo_height())

        iw, ih = self.pil_img.size
        scale = min(cw / iw, ch / ih, 1.0)  # 不放大，只缩小
        self._scale = scale

        disp = self.pil_img.resize((int(iw * scale), int(ih * scale)), Image.BILINEAR)
        self.tk_img = ImageTk.PhotoImage(disp)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

        # 画 ROI
        for r in self.regions:
            self.canvas.create_rectangle(
                r.x1 * scale, r.y1 * scale, r.x2 * scale, r.y2 * scale,
                outline="lime", width=2
            )
            self.canvas.create_text(
                (r.x1 + 5) * scale, (r.y1 + 10) * scale,
                text=r.name, fill="lime", anchor="nw"
            )

    # ---------------- Mouse events ----------------
    def on_mouse_down(self, event):
        if self.pil_img is None:
            return
        self._start_xy = (event.x, event.y)
        if self._temp_rect_id is not None:
            self.canvas.delete(self._temp_rect_id)
        self._temp_rect_id = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="yellow", width=2
        )

    def on_mouse_drag(self, event):
        if self._start_xy is None or self._temp_rect_id is None:
            return
        x0, y0 = self._start_xy
        self.canvas.coords(self._temp_rect_id, x0, y0, event.x, event.y)

    def on_mouse_up(self, event):
        if self.pil_img is None or self._start_xy is None or self._temp_rect_id is None:
            return

        x0, y0 = self._start_xy
        x1, y1 = event.x, event.y

        # 太小的框忽略
        if abs(x1 - x0) < 5 or abs(y1 - y0) < 5:
            self.canvas.delete(self._temp_rect_id)
            self._temp_rect_id = None
            self._start_xy = None
            return

        name = simpledialog.askstring("ROI 命名", "请输入 ROI 名称（例如：arena / wall / arm1 / open）")
        if not name:
            self.canvas.delete(self._temp_rect_id)
            self._temp_rect_id = None
            self._start_xy = None
            return
        name = name.strip()

        # 防止重名：重名自动加后缀
        existing = set([r.name for r in self.regions])
        if name in existing:
            k = 2
            new_name = f"{name}_{k}"
            while new_name in existing:
                k += 1
                new_name = f"{name}_{k}"
            name = new_name

        # 转回原图像素坐标
        scale = self._scale
        rx0 = int(round(x0 / scale))
        ry0 = int(round(y0 / scale))
        rx1 = int(round(x1 / scale))
        ry1 = int(round(y1 / scale))

        r = ROIRegion(name=name, x1=rx0, y1=ry0, x2=rx1, y2=ry1)
        r.normalize()
        self.regions.append(r)

        self.listbox.insert(tk.END, f"{r.name}: ({r.x1},{r.y1})-({r.x2},{r.y2})")

        # 重画为绿色固定显示
        self._temp_rect_id = None
        self._start_xy = None
        self.render_image_fit()


def main():
    app = ROIAnnotator()
    messagebox.showinfo(
        "流程提示",
        "步骤：\n"
        "1) 选择视频\n"
        "2) 选择帧号并加载\n"
        "3) 先画一个全箱体 ROI（arena/box）\n"
        "4) 在列表选中该 ROI，生成 center zone (1/9 或 1/4)\n"
        "5) 保存 ROI_JSON\n"
    )
    app.mainloop()


if __name__ == "__main__":
    main()