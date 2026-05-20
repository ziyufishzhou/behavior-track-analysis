"""命名配色方案 — CNS 论文预设"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Palette:
    name: str
    display_name: str
    colors: List[str]
    scatter: str = "#000000"
    connect: str = "#4D4D4D"
    edge: str = "#000000"
    fill_alpha: float = 0.7


PALETTES = [
    Palette("nature_classic", "Nature Classic",
            ["#D1D1D1", "#4682B4"], scatter="#000000", connect="#4D4D4D"),
    Palette("blue_coral", "Blue-Coral (Paul Tol)",
            ["#4477AA", "#EE6677"], scatter="#333333", connect="#888888"),
    Palette("prism_default", "Prism Default",
            ["#4259B0", "#C96442"], scatter="#222222", connect="#666666"),
    Palette("colorblind_safe", "Colorblind Safe (Okabe-Ito)",
            ["#0072B2", "#E69F00"], scatter="#000000", connect="#999999"),
    Palette("pastel", "Pastel",
            ["#A8D8EA", "#FFB6B9"], scatter="#555555", connect="#AAAAAA"),
    Palette("science_bright", "Science Bright",
            ["#0C5DA5", "#FF2C00"], scatter="#000000", connect="#555555"),
    Palette("deep_blue_orange", "Deep Blue-Orange",
            ["#0c74b9", "#d55427"], scatter="#333333", connect="#777777"),
    Palette("magenta_blue", "Magenta-Blue",
            ["#c30078", "#4370b4"], scatter="#222222", connect="#888888"),
]


def get_palette(name: str) -> Palette:
    for p in PALETTES:
        if p.name == name:
            return p
    return PALETTES[0]


def palette_list() -> list:
    return [{"name": p.name, "display_name": p.display_name,
             "colors": p.colors, "scatter": p.scatter,
             "connect": p.connect, "edge": p.edge} for p in PALETTES]
