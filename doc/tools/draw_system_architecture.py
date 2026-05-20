from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "system_architecture.png"
FONT = Path(r"C:\Windows\Fonts\msyh.ttc")
BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(BOLD if bold else FONT), size)


def box(draw: ImageDraw.ImageDraw, xy, fill, outline, width=3, radius=12):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def centered(draw: ImageDraw.ImageDraw, xy, text: str, fnt, fill="#1f2937"):
    x1, y1, x2, y2 = xy
    bbox = draw.textbbox((0, 0), text, font=fnt)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text((x1 + (x2 - x1 - w) / 2, y1 + (y2 - y1 - h) / 2 - 2), text, font=fnt, fill=fill)


def arrow(draw: ImageDraw.ImageDraw, start, end, fill="#334155", width=4):
    draw.line([start, end], fill=fill, width=width)
    x1, y1 = start
    x2, y2 = end
    if y2 > y1:
        points = [(x2, y2), (x2 - 9, y2 - 16), (x2 + 9, y2 - 16)]
    else:
        points = [(x2, y2), (x2 - 9, y2 + 16), (x2 + 9, y2 + 16)]
    draw.polygon(points, fill=fill)


def draw_layer(draw, y, title, fill, outline, items):
    box(draw, (70, y, 1130, y + 105), fill, outline)
    draw.text((105, y + 35), title, font=font(25, True), fill="#111827")
    for item in items:
        x, w, main, sub = item
        box(draw, (x, y + 23, x + w, y + 83), "#ffffff", outline, width=2, radius=10)
        if sub:
            centered(draw, (x, y + 28, x + w, y + 56), main, font(19, True))
            centered(draw, (x, y + 53, x + w, y + 80), sub, font(16), fill="#475569")
        else:
            centered(draw, (x, y + 23, x + w, y + 83), main, font(20, True))


def main() -> None:
    image = Image.new("RGB", (1200, 760), "white")
    draw = ImageDraw.Draw(image)

    centered(
        draw,
        (0, 18, 1200, 78),
        "基于 DeepLabCut 的啮齿动物行为分析系统总体架构",
        font(32, True),
        fill="#111827",
    )

    draw_layer(
        draw,
        95,
        "交互层",
        "#eef6ff",
        "#2563eb",
        [
            (245, 220, "Flask Web 工作台", None),
            (500, 200, "Tkinter 桌面界面", None),
            (735, 200, "PyQt 辅助界面", None),
        ],
    )
    draw_layer(
        draw,
        230,
        "绘图层",
        "#f0fdf4",
        "#16a34a",
        [
            (245, 220, "统计绘图", None),
            (500, 200, "显著性标注", None),
            (735, 200, "论文图导出", None),
        ],
    )
    draw_layer(
        draw,
        365,
        "分析层",
        "#fff7ed",
        "#ea580c",
        [
            (245, 220, "OF 旷场实验", "距离、中心区时间"),
            (500, 220, "EPM 高架十字迷宫", "开放臂时间、进入次数"),
            (755, 220, "TCT 三箱社交实验", "探索时间、偏好指数"),
        ],
    )
    draw_layer(
        draw,
        515,
        "处理层",
        "#faf5ff",
        "#9333ea",
        [
            (220, 180, "collect_csv", None),
            (430, 160, "fix_csv", None),
            (620, 170, "group_csv", None),
            (820, 190, "metadata 管理", None),
        ],
    )

    box(draw, (70, 660, 1130, 730), "#f8fafc", "#64748b")
    draw.text((105, 684), "数据层", font=font(25, True), fill="#111827")
    for xy, text in [
        ((210, 676, 390, 716), "video 原始视频"),
        ((405, 676, 610, 716), "data CSV / ROI / metadata"),
        ((650, 676, 840, 716), "models DLC 模型"),
        ((875, 676, 1060, 716), "output 图表与结果"),
    ]:
        centered(draw, xy, text, font(18, True))

    arrow(draw, (600, 660), (600, 633))
    arrow(draw, (600, 515), (600, 488))
    arrow(draw, (600, 365), (600, 338))
    arrow(draw, (600, 230), (600, 203))

    OUT.parent.mkdir(exist_ok=True)
    image.save(OUT, dpi=(300, 300))
    print(OUT)


if __name__ == "__main__":
    main()
