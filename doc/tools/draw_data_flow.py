from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "data_flow.png"
FONT = Path(r"C:\Windows\Fonts\msyh.ttc")
BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(BOLD if bold else FONT), size)


def rounded(draw: ImageDraw.ImageDraw, xy, fill, outline, width=3, radius=12):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def centered(draw: ImageDraw.ImageDraw, xy, text: str, fnt, fill="#1f2937"):
    x1, y1, x2, y2 = xy
    bbox = draw.textbbox((0, 0), text, font=fnt)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text((x1 + (x2 - x1 - w) / 2, y1 + (y2 - y1 - h) / 2 - 2), text, font=fnt, fill=fill)


def multiline(draw: ImageDraw.ImageDraw, xy, lines, main_color="#111827"):
    x1, y1, x2, y2 = xy
    heights = []
    widths = []
    fonts = [font(22, True)] + [font(16) for _ in lines[1:]]
    for line, fnt in zip(lines, fonts):
        bbox = draw.textbbox((0, 0), line, font=fnt)
        widths.append(bbox[2] - bbox[0])
        heights.append(bbox[3] - bbox[1])
    total_h = sum(heights) + 8 * (len(lines) - 1)
    y = y1 + (y2 - y1 - total_h) / 2 - 2
    for idx, (line, fnt, w, h) in enumerate(zip(lines, fonts, widths, heights)):
        color = main_color if idx == 0 else "#475569"
        draw.text((x1 + (x2 - x1 - w) / 2, y), line, font=fnt, fill=color)
        y += h + 8


def arrow(draw: ImageDraw.ImageDraw, start, end, fill="#334155", width=4):
    draw.line([start, end], fill=fill, width=width)
    x1, y1 = start
    x2, y2 = end
    if abs(x2 - x1) >= abs(y2 - y1):
        if x2 >= x1:
            points = [(x2, y2), (x2 - 17, y2 - 9), (x2 - 17, y2 + 9)]
        else:
            points = [(x2, y2), (x2 + 17, y2 - 9), (x2 + 17, y2 + 9)]
    else:
        if y2 >= y1:
            points = [(x2, y2), (x2 - 9, y2 - 17), (x2 + 9, y2 - 17)]
        else:
            points = [(x2, y2), (x2 - 9, y2 + 17), (x2 + 9, y2 + 17)]
    draw.polygon(points, fill=fill)


def node(draw, x, y, title, subtitle, fill, outline):
    xy = (x, y, x + 185, y + 96)
    rounded(draw, xy, fill, outline)
    multiline(draw, xy, [title, subtitle])
    return xy


def main() -> None:
    image = Image.new("RGB", (1300, 720), "white")
    draw = ImageDraw.Draw(image)

    centered(draw, (0, 22, 1300, 78), "系统数据处理流程", font(34, True), fill="#111827")

    top_y = 135
    bottom_y = 435
    xs = [70, 315, 560, 805, 1050]
    colors = [
        ("#eef6ff", "#2563eb"),
        ("#f0fdf4", "#16a34a"),
        ("#fff7ed", "#ea580c"),
        ("#faf5ff", "#9333ea"),
        ("#f8fafc", "#64748b"),
    ]

    top_nodes = [
        node(draw, xs[0], top_y, "视频导入", "video 原始视频", *colors[0]),
        node(draw, xs[1], top_y, "姿态估计", "DeepLabCut 输出坐标", *colors[1]),
        node(draw, xs[2], top_y, "CSV 收集", "data/raw_csv", *colors[2]),
        node(draw, xs[3], top_y, "CSV 修复", "低置信度过滤与插值", *colors[3]),
        node(draw, xs[4], top_y, "按标签分组", "metadata -> grouped", *colors[4]),
    ]

    bottom_nodes = [
        node(draw, xs[0], bottom_y, "ROI 标注", "保存 ROI JSON", *colors[0]),
        node(draw, xs[1], bottom_y, "行为指标计算", "OF / EPM / TCT", *colors[1]),
        node(draw, xs[2], bottom_y, "统计绘图", "统计检验与显著性", *colors[2]),
        node(draw, xs[3], bottom_y, "结果导出", "图表、汇总表、报告", *colors[3]),
    ]

    for left, right in zip(top_nodes, top_nodes[1:]):
        arrow(draw, (left[2] + 18, (left[1] + left[3]) // 2), (right[0] - 18, (right[1] + right[3]) // 2))

    arrow(draw, ((top_nodes[-1][0] + top_nodes[-1][2]) // 2, top_nodes[-1][3] + 16), (1180, 330))
    draw.line([(1180, 330), (162, 330)], fill="#334155", width=4)
    arrow(draw, (162, 330), ((bottom_nodes[0][0] + bottom_nodes[0][2]) // 2, bottom_nodes[0][1] - 16))

    for left, right in zip(bottom_nodes, bottom_nodes[1:]):
        arrow(draw, (left[2] + 18, (left[1] + left[3]) // 2), (right[0] - 18, (right[1] + right[3]) // 2))

    rounded(draw, (1015, bottom_y, 1235, bottom_y + 96), "#ecfeff", "#0891b2")
    multiline(draw, (1015, bottom_y, 1235, bottom_y + 96), ["用户查看与复核", "Web / Word / 输出目录"])
    arrow(draw, (990, bottom_y + 48), (1015 - 18, bottom_y + 48), fill="#334155")

    draw.text((84, 620), "说明：视频标签和 ROI 配置由用户在交互层维护，CSV 坐标数据经过预处理后进入各实验分析模块，最终生成可用于论文撰写的统计图和汇总结果。", font=font(18), fill="#475569")

    OUT.parent.mkdir(exist_ok=True)
    image.save(OUT, dpi=(300, 300))
    print(OUT)


if __name__ == "__main__":
    main()
