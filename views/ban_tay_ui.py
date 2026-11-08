"""v3.3 — Quy tắc bàn tay có hình minh hoạ (SVG tự vẽ) + cách áng chừng khi ăn ngoài."""
from __future__ import annotations

import html

from core import an_ngoai as an

E = html.escape
DA, VIEN = "#F2CDA8", "#A9744A"

SVG = {
    # lòng bàn tay mở + miếng thịt / cá đặt trên lòng bàn tay
    "p": f"""<svg viewBox="0 0 120 130" width="92" height="100">
<g fill="{DA}" stroke="{VIEN}" stroke-width="2.5" stroke-linejoin="round">
<rect x="27" y="8" width="13" height="52" rx="6.5"/><rect x="42" y="3" width="13" height="56" rx="6.5"/>
<rect x="57" y="5" width="13" height="55" rx="6.5"/><rect x="72" y="12" width="12" height="48" rx="6"/>
<rect x="88" y="52" width="12" height="40" rx="6" transform="rotate(-38 94 72)"/>
<rect x="25" y="50" width="62" height="72" rx="20"/></g>
<ellipse cx="56" cy="86" rx="24" ry="20" fill="#C8653F" stroke="#8E3F22" stroke-width="2"/>
<path d="M40 82 Q56 74 72 82 M42 92 Q56 84 70 92" stroke="#E9A07F" stroke-width="2.5" fill="none" stroke-linecap="round"/></svg>""",
    # nắm tay = 1 phần rau
    "rau": f"""<svg viewBox="0 0 120 130" width="92" height="100">
<g fill="#4E9A5B" stroke="#2F6B3A" stroke-width="2"><circle cx="45" cy="26" r="14"/><circle cx="62" cy="18" r="15"/><circle cx="79" cy="27" r="13"/>
<rect x="56" y="30" width="10" height="22" rx="4" fill="#8BC08F"/></g>
<g fill="{DA}" stroke="{VIEN}" stroke-width="2.5" stroke-linejoin="round">
<rect x="26" y="50" width="70" height="66" rx="22"/>
<circle cx="38" cy="58" r="10"/><circle cx="55" cy="54" r="10"/><circle cx="72" cy="55" r="10"/><circle cx="87" cy="61" r="9"/>
<rect x="22" y="78" width="46" height="16" rx="8"/></g>
<path d="M45 62 v10 M62 60 v10 M78 62 v9" stroke="{VIEN}" stroke-width="2" stroke-linecap="round"/></svg>""",
    # vốc tay (bàn tay khum) đựng cơm
    "c": f"""<svg viewBox="0 0 120 130" width="92" height="100">
<g fill="#FFFDF6" stroke="#CFC6B4" stroke-width="1.5"><circle cx="40" cy="62" r="6"/><circle cx="52" cy="56" r="6"/><circle cx="64" cy="54" r="6"/>
<circle cx="76" cy="57" r="6"/><circle cx="86" cy="64" r="6"/><circle cx="47" cy="66" r="6"/><circle cx="60" cy="63" r="6"/><circle cx="73" cy="65" r="6"/>
<circle cx="56" cy="47" r="5.5"/><circle cx="68" cy="47" r="5.5"/></g>
<path d="M14 66 Q16 60 24 62 L98 62 Q106 60 108 66 Q104 112 61 116 Q18 112 14 66 Z" fill="{DA}" stroke="{VIEN}" stroke-width="2.5" stroke-linejoin="round"/>
<path d="M30 78 Q61 96 92 78" stroke="{VIEN}" stroke-width="2" fill="none" stroke-linecap="round" opacity=".7"/>
<path d="M24 92 Q61 108 98 92" stroke="{VIEN}" stroke-width="2" fill="none" stroke-linecap="round" opacity=".5"/></svg>""",
    # ngón cái = 1 phần chất béo (dầu, bơ, hạt)
    "f": f"""<svg viewBox="0 0 120 130" width="92" height="100">
<path d="M84 14 Q96 26 90 44 Q86 52 80 46 Q74 38 84 14 Z" fill="#E8C76A" stroke="#B08A2E" stroke-width="2"/>
<g fill="{DA}" stroke="{VIEN}" stroke-width="2.5" stroke-linejoin="round">
<rect x="46" y="14" width="22" height="58" rx="11"/>
<rect x="30" y="58" width="66" height="60" rx="20"/>
<rect x="24" y="66" width="20" height="13" rx="6.5"/><rect x="24" y="80" width="20" height="13" rx="6.5"/><rect x="24" y="94" width="20" height="13" rx="6.5"/></g>
<path d="M50 24 Q57 20 64 24" stroke="{VIEN}" stroke-width="2" fill="none"/></svg>""",
}
TEN = {"p": ("Lòng bàn tay", "Đạm", "≈ 20–30 g đạm", "thịt, cá, trứng, đậu hũ — cỡ & độ dày lòng bàn tay (không tính ngón)"),
       "c": ("Vốc tay", "Tinh bột", "≈ 20–30 g tinh bột", "cơm, bún, phở, khoai, trái cây — lượng vừa 1 bàn tay khum"),
       "f": ("Ngón cái", "Chất béo", "≈ 7–12 g béo", "dầu, bơ, hạt, sốt, da / mỡ — cỡ cả ngón cái"),
       "rau": ("Nắm tay", "Rau", "≈ 1 chén rau", "rau luộc, xào ít dầu, rau sống — càng nhiều càng tốt")}

CSS = """<style>
.bt-w{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:8px 0}
@media(max-width:700px){.bt-w{grid-template-columns:repeat(2,minmax(0,1fr))}}
.bt-c{border:1px solid #E6DCC6;border-radius:14px;padding:10px 8px;text-align:center;background:#FFFDF8}
.bt-c b{display:block;font-size:1.05rem}.bt-c .n{font-size:1.45rem;font-weight:800;color:#B8912F;line-height:1.1}
.bt-c .n2{font-size:.95rem}.bt-c small{display:block;font-size:.72rem;opacity:.75;line-height:1.3}
html[data-hac-theme=dark] .bt-c{background:#1A1814;border-color:#3A342A}
</style>"""


def the_ban_tay(phan: dict | None = None, nhan_nu_nam: bool = False) -> str:
    """4 thẻ hình: số phần cho 1 bữa (nếu có `phan`) hoặc chuẩn chung Nữ / Nam."""
    chuan = {k: "Nữ 1 · Nam 2 / bữa" for k in ("p", "c", "f", "rau")}
    out = ""
    for k in ("p", "c", "f", "rau"):
        t = TEN[k]
        so = (an.so_s(phan.get(k, 0)) + " " + t[0].lower()) if phan else chuan[k]
        out += (f'<div class="bt-c">{SVG[k]}<b>{E(t[1])}</b><div class="n{'' if phan else ' n2'}">{E(so)}</div>'
                f'<small>{E(t[0])} {E(t[2])}</small><small>{E(t[3])}</small></div>')
    return CSS + f'<div class="bt-w">{out}</div>'


def dong_ban_tay(m: dict, rau_g: float) -> str:
    s = an.so_phan(m, rau_g)
    phan = [f"✋ {an.so_s(s['p'])} lòng bàn tay đạm", f"🤲 {an.so_s(s['c'])} vốc tinh bột", f"👍 {an.so_s(s['f'])} ngón cái béo"]
    if s["rau"]:
        phan.append(f"✊ {an.so_s(s['rau'])} nắm tay rau")
    return " · ".join(x for x in phan if not x.split(" ")[1] == "0")


HUONG_DAN_AN_NGOAI = [
    "**Bước 1 — Nhìn thực đơn hôm nay** để biết bữa này cần mấy lòng bàn tay đạm, mấy vốc tinh bột, mấy ngón cái béo (ghi ngay dưới mỗi bữa).",
    "**Bước 2 — Đạm trước:** chọn món có đủ số lòng bàn tay thịt / cá / trứng. Thiếu thì gọi thêm (tô thêm thịt, 1–2 trứng luộc, thêm phần gà).",
    "**Bước 3 — Tinh bột vừa đủ:** cơm phần quán thường 2–3 vốc tay (≈ 1,5–2 chén) → ăn đúng số vốc của mình, phần dư để lại. "
    "Phở / bún: ăn hết thịt, để lại khoảng ⅓ bánh nếu tô lớn.",
    "**Bước 4 — Béo là chỗ dễ dư calo nhất:** món chiên, xào, sốt, nước béo, da, mỡ thường đã chiếm 2–4 ngón cái. "
    "Ưu tiên luộc / hấp / nướng; xin ít dầu, sốt để riêng; hớt bớt váng mỡ trên nước dùng.",
    "**Bước 5 — Rau ít nhất 1–2 nắm tay:** gọi thêm rau luộc / rau sống, ăn rau trước.",
    "**Bước 6 — Đồ uống:** nước lọc, trà đá, cà phê đen / ít sữa. Một ly trà sữa ≈ 300–500 kcal (ước lượng, tuỳ size và topping) — gần bằng 1 bữa.",
    "**Mẹo:** ăn chậm, dừng khi no khoảng 80 %; bữa trước lỡ ăn nhiều thì bữa sau bớt tinh bột / béo — không cần nhịn.",
]
