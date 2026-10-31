# Hoàng Anh Coaching v1.0 (2026-10-31) — font + màu dùng chung cho PDF (đen – vàng đồng)
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from core import config

PAPER, INK, MUTE, RULE = HexColor("#FBF8F1"), HexColor("#1C1B19"), HexColor("#6C6860"), HexColor("#DDD4C0")
BRONZE, BRONZE_D, SOFT = HexColor("#A3803C"), HexColor("#7A5B14"), HexColor("#F3ECDC")
DARK, GOLD, GREEN, RED = HexColor("#1C1B19"), HexColor("#C8A24A"), HexColor("#2E7D4F"), HexColor("#B4442F")
_REG = False


def fonts():
    global _REG
    if _REG:
        return
    for name, f in (("R", "BeVietnamPro-Regular"), ("S", "BeVietnamPro-SemiBold"), ("B", "BeVietnamPro-Bold")):
        pdfmetrics.registerFont(TTFont(name, str(config.FONTS / f"{f}.ttf")))
    _REG = True
