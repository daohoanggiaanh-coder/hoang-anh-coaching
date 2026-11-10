# Atlas Academy v3.28 (2026-10-14) — bộ icon nét mảnh cho chỉ số cơ thể: 1 nguồn vẽ, dùng cho cả web (SVG) và báo cáo PDF
"""
Mỗi icon vẽ trên lưới 24×24, nét 1,8. Phần tử:
  ("p", "M x y L x y C x1 y1 x2 y2 x y Z")  — đường (chỉ lệnh tuyệt đối M L C Z)
  ("c", cx, cy, r[, "fill"])                — hình tròn
  ("r", x, y, w, h, bo_góc)                 — hình chữ nhật
  ("l", x1, y1, x2, y2)                     — đoạn thẳng
"""
from __future__ import annotations

import re

ICONS: dict[str, list] = {
    "can_nang": [("r", 3, 3.5, 18, 17, 4), ("p", "M7.5 10 C9 7.6 15 7.6 16.5 10"), ("l", 12, 10.5, 13.6, 7.8)],
    "chieu_cao": [("r", 8, 2.5, 8, 19, 1.6), ("l", 8, 7, 11, 7), ("l", 8, 11.5, 12.5, 11.5), ("l", 8, 16, 11, 16)],
    "co": [("l", 7, 12, 17, 12), ("r", 4, 7, 3, 10, 1), ("r", 17, 7, 3, 10, 1), ("l", 2.5, 10, 2.5, 14), ("l", 21.5, 10, 21.5, 14)],
    "khoi_mo": [("p", "M12 3 C9 7 5.5 10.8 5.5 15 C5.5 18.8 8.4 21.5 12 21.5 C15.6 21.5 18.5 18.8 18.5 15 C18.5 10.8 15 7 12 3 Z")],
    "pbf": [("c", 7, 7, 2.6), ("c", 17, 17, 2.6), ("l", 18.5, 5.5, 5.5, 18.5)],
    "noi_tang": [("c", 12, 12, 9), ("c", 12, 12, 5), ("c", 12, 12, 1.6, "fill")],
    "bmi": [("c", 12, 4.8, 2.4), ("p", "M12 8 L12 15 M7.5 10.5 L16.5 10.5 M12 15 L8.8 21 M12 15 L15.2 21")],
    "bmr": [("p", "M12 2.8 C13 7 17.2 9.2 17.2 14.2 C17.2 18.4 14.9 21.2 12 21.2 C9.1 21.2 6.8 19 6.8 15.6 "
                  "C6.8 13.2 8.2 11.6 9.4 10.4 C9.5 12.8 10.4 14 11.6 14.2 C10.9 10.2 11 6.2 12 2.8 Z")],
    "tuoi": [("p", "M6.5 3 L17.5 3 M6.5 21 L17.5 21 M7.6 3 C7.6 8.6 12 9.6 12 12 C12 14.4 7.6 15.4 7.6 21 "
                   "M16.4 3 C16.4 8.6 12 9.6 12 12 C12 14.4 16.4 15.4 16.4 21")],
    "diem": [("p", "M12 3 L14.6 8.6 L20.6 9.3 L16.1 13.4 L17.3 19.4 L12 16.4 L6.7 19.4 L7.9 13.4 L3.4 9.3 L9.4 8.6 Z")],
    "nuoc": [("p", "M6 4 L18 4 L16.4 20.5 L7.6 20.5 Z"), ("p", "M6.9 10 C9 11.2 15 8.8 17.1 10")],
    "huyet_ap": [("p", "M12 20 C6 15.6 3 12.6 3 9 C3 6.2 5.1 4.4 7.5 4.4 C9.4 4.4 11 5.5 12 7.2 C13 5.5 14.6 4.4 16.5 4.4 "
                       "C18.9 4.4 21 6.2 21 9 C21 12.6 18 15.6 12 20 Z"), ("p", "M6.5 11.5 L9.4 11.5 L10.7 9 L12.6 14 L13.9 11.5 L17.5 11.5")],
    "vong": [("c", 10, 11, 7), ("c", 10, 11, 2.2), ("p", "M10 18 L21 18 L21 14.5")],
    "protein": [("p", "M5 19 C5 11 9.5 5 19 5 C19 14.5 13 19 5 19 Z"), ("l", 5, 19, 13, 11)],
    "khoang_chat": [("p", "M6 3.5 L18 3.5 L21.5 9 L12 20.5 L2.5 9 Z"), ("l", 2.5, 9, 21.5, 9), ("p", "M9 3.5 L12 20.5 L15 3.5")],
}

_TOK = re.compile(r"[MLCZ]|-?\d*\.?\d+")


def _parse(d: str):
    toks = _TOK.findall(d)
    i, out, cmd = 0, [], None
    while i < len(toks):
        t = toks[i]
        if t in "MLCZ":
            cmd = t
            i += 1
            if t == "Z":
                out.append(("Z",))
            continue
        n = 6 if cmd == "C" else 2
        out.append((cmd, *map(float, toks[i:i + n])))
        i += n
        if cmd == "M":
            cmd = "L"
    return out


# ------------------------------------------------------------------ web
def svg(name: str, color: str = "#7A5B14", size: int = 22, stroke: float = 1.8) -> str:
    parts = []
    for el in ICONS.get(name, []):
        k = el[0]
        if k == "p":
            parts.append(f'<path d="{el[1]}"/>')
        elif k == "c":
            fill = f' fill="{color}"' if len(el) > 4 else ""
            parts.append(f'<circle cx="{el[1]}" cy="{el[2]}" r="{el[3]}"{fill}/>')
        elif k == "r":
            parts.append(f'<rect x="{el[1]}" y="{el[2]}" width="{el[3]}" height="{el[4]}" rx="{el[5]}"/>')
        elif k == "l":
            parts.append(f'<line x1="{el[1]}" y1="{el[2]}" x2="{el[3]}" y2="{el[4]}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">{"".join(parts)}</svg>')


# ------------------------------------------------------------------ PDF (reportlab)
def draw(c, name: str, x: float, y: float, size: float, color, stroke: float = 1.8):
    """Vẽ icon vào ô vuông góc dưới-trái (x, y) cạnh `size` trên canvas reportlab."""
    c.saveState()
    c.translate(x, y + size)
    c.scale(size / 24, -size / 24)
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(stroke)
    c.setLineCap(1)
    c.setLineJoin(1)
    for el in ICONS.get(name, []):
        k = el[0]
        if k == "p":
            p = c.beginPath()
            for seg in _parse(el[1]):
                if seg[0] == "M":
                    p.moveTo(*seg[1:])
                elif seg[0] == "L":
                    p.lineTo(*seg[1:])
                elif seg[0] == "C":
                    p.curveTo(*seg[1:])
                else:
                    p.close()
            c.drawPath(p, stroke=1, fill=0)
        elif k == "c":
            c.circle(el[1], el[2], el[3], stroke=1, fill=1 if len(el) > 4 else 0)
        elif k == "r":
            c.roundRect(el[1], el[2], el[3], el[4], el[5], stroke=1, fill=0)
        elif k == "l":
            c.line(el[1], el[2], el[3], el[4])
    c.restoreState()
