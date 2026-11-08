"""v3.3 — Quy tắc bàn tay có hình minh hoạ (SVG tự vẽ) + cách áng chừng khi ăn ngoài. v3.4: vẽ lại hình rõ hơn."""
from __future__ import annotations

import html

from core import an_ngoai as an

E = html.escape
# v3.4 — vẽ lại: bàn tay liền mạch (2 lớp viền + da) đặt CẠNH món ăn cùng cỡ, có vạch so kích thước.
DA, BONG, VIEN = "#F5CBA3", "#E3A97F", "#8F5B3A"
def _tay(id_, shapes, extra=""):
    # vẽ 2 lớp: viền dày rồi phủ da → hình liền mạch, không lộ đường nối giữa các ngón
    return (f'<defs><g id="{id_}">{shapes}</g></defs>'
            f'<use href="#{id_}" fill="{VIEN}" stroke="{VIEN}" stroke-width="5" stroke-linejoin="round"/>'
            f'<use href="#{id_}" fill="{DA}" stroke="none"/>{extra}')
GUIDE = 'stroke="#B8912F" stroke-width="1.6" stroke-dasharray="4 3" fill="none"'
def _svg_p():
    tay = _tay("btp", '<rect x="24" y="16" width="14" height="50" rx="7"/><rect x="39" y="8" width="14" height="58" rx="7"/>'
        '<rect x="54" y="12" width="14" height="54" rx="7"/><rect x="69" y="24" width="12" height="44" rx="6"/>'
        '<rect x="16" y="58" width="15" height="44" rx="7.5" transform="rotate(-32 24 100)"/>'
        '<rect x="22" y="52" width="60" height="56" rx="18"/><rect x="34" y="98" width="38" height="28" rx="6"/>',
        f'<path d="M30 74 Q50 84 74 70 M34 90 Q52 96 72 86" stroke="{BONG}" stroke-width="2.2" fill="none" stroke-linecap="round"/>'
        f'<path d="M45 19 v3 M60 15 v3" stroke="{BONG}" stroke-width="2" stroke-linecap="round"/>')
    thit = ('<ellipse cx="150" cy="112" rx="40" ry="9" fill="#EDE7DA" stroke="#CBBFA6" stroke-width="1.5"/>'
        '<path d="M124 64 Q150 52 176 62 Q184 84 172 104 Q150 112 128 104 Q116 84 124 64 Z" fill="#B85A3A" stroke="#7E3520" stroke-width="2.2"/>'
        '<path d="M130 72 Q150 64 170 72 M128 86 Q150 78 174 86 M132 98 Q150 92 168 98" stroke="#E7A486" stroke-width="2.4" fill="none" stroke-linecap="round"/>')
    g = f'<rect x="25" y="54" width="54" height="52" rx="14" {GUIDE}/><path d="M84 56 H118 M84 106 H118" {GUIDE}/>'
    return tay + g + thit
def _svg_rau():
    tay = _tay("btr", '<rect x="20" y="40" width="64" height="58" rx="16"/>'
        '<rect x="20" y="30" width="17" height="40" rx="8.5"/><rect x="36" y="26" width="17" height="44" rx="8.5"/>'
        '<rect x="52" y="27" width="17" height="43" rx="8.5"/><rect x="67" y="32" width="17" height="38" rx="8.5"/>'
        '<rect x="34" y="92" width="36" height="34" rx="6"/>',
        f'<path d="M36.5 36 v26 M52.5 34 v28 M68 37 v25" stroke="{BONG}" stroke-width="2.2" stroke-linecap="round"/>'
        f'<rect x="14" y="68" width="52" height="19" rx="9.5" fill="{DA}" stroke="{VIEN}" stroke-width="2.5"/>'
        f'<path d="M50 72 Q56 77 50 83" stroke="{BONG}" stroke-width="2" fill="none"/>')
    rau = ('<path d="M120 84 H182 Q180 112 151 114 Q122 112 120 84 Z" fill="#F4F1EA" stroke="#B9AE97" stroke-width="2"/>'
        '<g fill="#4E9A5B" stroke="#2E6A39" stroke-width="1.8"><circle cx="132" cy="70" r="12"/><circle cx="150" cy="60" r="14"/>'
        '<circle cx="168" cy="70" r="12"/><circle cx="141" cy="78" r="10"/><circle cx="160" cy="78" r="10"/></g>'
        '<g fill="#7CC08A"><circle cx="146" cy="56" r="3"/><circle cx="165" cy="66" r="2.5"/><circle cx="130" cy="67" r="2.5"/></g>'
        '<path d="M120 84 H182" stroke="#B9AE97" stroke-width="2"/>')
    g = f'<path d="M88 30 H118 M88 98 H118" {GUIDE}/>'
    return tay + g + rau
def _svg_c():
    gao = "".join(f'<ellipse cx="{x}" cy="{y}" rx="3.2" ry="1.8" transform="rotate({r} {x} {y})"/>' for x, y, r in
        [(34,56,20),(44,48,-30),(54,44,10),(64,46,40),(74,52,-15),(40,58,-40),(52,54,30),(62,55,-20),(72,58,15),(48,40,0),(58,38,-25),(68,42,35),(82,58,0),(28,60,0)])
    com = (f'<path d="M20 64 Q22 34 53 32 Q86 34 88 64 Z" fill="#FFFDF7" stroke="#C9BFA8" stroke-width="1.8"/>'
           f'<g fill="#EFE8D6">{gao}</g>')
    tay = com + _tay("btc", '<path d="M12 62 Q12 56 20 57 H88 Q96 56 95 62 Q92 104 53 110 Q16 104 12 62 Z"/>'
        '<rect x="40" y="100" width="28" height="26" rx="6"/><rect x="8" y="56" width="34" height="13" rx="6.5" transform="rotate(-8 25 62)"/>',
        f'<path d="M62 62 Q90 66 92 70 M60 74 Q86 80 89 82 M58 86 Q80 92 83 94" stroke="{BONG}" stroke-width="2.2" fill="none" stroke-linecap="round"/>')
    chen = ('<path d="M122 76 Q124 50 151 48 Q178 50 180 76 Z" fill="#FFFDF7" stroke="#C9BFA8" stroke-width="1.8"/>'
            '<path d="M116 76 H186 Q184 106 151 108 Q118 106 116 76 Z" fill="#DCEBF2" stroke="#7FA3B5" stroke-width="2"/>'
            '<path d="M126 88 Q151 96 176 88" stroke="#7FA3B5" stroke-width="1.6" fill="none"/>'
            '<rect x="138" y="106" width="26" height="7" rx="3" fill="#C5DCE7" stroke="#7FA3B5" stroke-width="1.6"/>'
            '<path d="M122 76 H180" stroke="#C9BFA8" stroke-width="1.2" stroke-dasharray="3 3"/>')
    return tay + chen
def _svg_f():
    tay = _tay("btf", '<rect x="30" y="56" width="50" height="50" rx="14"/>'
        '<rect x="58" y="56" width="28" height="14" rx="7"/><rect x="58" y="69" width="28" height="14" rx="7"/>'
        '<rect x="58" y="82" width="27" height="13" rx="6.5"/><rect x="58" y="94" width="24" height="12" rx="6"/>'
        '<rect x="30" y="14" width="19" height="54" rx="9.5"/><rect x="38" y="98" width="32" height="28" rx="6"/>',
        f'<rect x="33.5" y="18" width="12" height="13" rx="5" fill="#FBE3CC" stroke="{BONG}" stroke-width="1.5"/>'
        f'<path d="M60 70 H82 M60 83 H82 M60 95 H80" stroke="{BONG}" stroke-width="2" stroke-linecap="round"/>'
        f'<path d="M33 44 Q40 47 46 44" stroke="{BONG}" stroke-width="2" fill="none"/>')
    g = f'<rect x="26" y="10" width="27" height="60" rx="12" {GUIDE}/>'
    thia = ('<path d="M168 32 L192 14" stroke="#9AA3AB" stroke-width="5" stroke-linecap="round"/>'
            '<ellipse cx="146" cy="40" rx="26" ry="14" fill="#DDE2E6" stroke="#8D969E" stroke-width="2"/>'
            '<ellipse cx="146" cy="40" rx="19" ry="9" fill="#E9BE4E"/><ellipse cx="140" cy="37" rx="6" ry="2.5" fill="#F6DE95"/>'
            '<g fill="#D9B27A" stroke="#9C743F" stroke-width="1.5"><ellipse cx="130" cy="88" rx="9" ry="6" transform="rotate(-20 130 88)"/>'
            '<ellipse cx="150" cy="94" rx="9" ry="6" transform="rotate(15 150 94)"/><ellipse cx="168" cy="86" rx="9" ry="6" transform="rotate(-35 168 86)"/>'
            '<ellipse cx="146" cy="78" rx="9" ry="6" transform="rotate(30 146 78)"/></g>'
            '<text x="149" y="118" font-size="11" text-anchor="middle" fill="#8F7A55">hoặc</text>')
    return tay + g + thia


def _khung(noi_dung: str) -> str:
    return ('<svg viewBox="-8 0 208 130" width="100%" style="max-width:230px" role="img">' + noi_dung +
            '<text x="103" y="70" font-size="20" font-weight="700" text-anchor="middle" fill="#B8912F">≈</text></svg>')


SVG = {"p": _khung(_svg_p()), "c": _khung(_svg_c()), "f": _khung(_svg_f()), "rau": _khung(_svg_rau())}
TEN = {"p": ("Lòng bàn tay", "Đạm", "≈ 20–30 g đạm", "thịt, cá, trứng, đậu hũ — cỡ & độ dày lòng bàn tay (không tính ngón)"),
       "c": ("Vốc tay", "Tinh bột", "≈ 20–30 g tinh bột", "cơm, bún, phở, khoai, trái cây — lượng vừa 1 bàn tay khum"),
       "f": ("Ngón cái", "Chất béo", "≈ 7–12 g béo", "dầu, bơ, hạt, sốt, da / mỡ — cỡ cả ngón cái"),
       "rau": ("Nắm tay", "Rau", "≈ 1 chén rau", "rau luộc, xào ít dầu, rau sống — càng nhiều càng tốt")}
VD = {"p": "Ví dụ: ≈ 90–120 g thịt / cá chín · 1 miếng ức gà nhỏ · 3–4 quả trứng",
      "c": "Ví dụ: ≈ 90 g cơm chín (khoảng ⅔ chén nhỏ) · 1 củ khoai lang nhỏ · 1 trái chuối",
      "f": "Ví dụ: ≈ 2 thìa cà phê dầu · 1 thìa canh bơ đậu phộng · 1 nắm nhỏ hạt (~15 g)",
      "rau": "Ví dụ: 1 chén rau luộc · 1 đĩa nhỏ rau sống · ½ đĩa rau xào"}
GHI = ('<small style="opacity:.7">Số gram là ước lượng theo cỡ tay người trưởng thành trung bình — tay to / nhỏ thì phần ăn '
       'tự to / nhỏ theo. Muốn chính xác hơn: cân thử vài lần đầu để "luyện mắt".</small>')

CSS = """<style>
.bt-w{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:8px 0}
@media(max-width:700px){.bt-w{grid-template-columns:repeat(2,minmax(0,1fr))}}
.bt-c{border:1px solid #E6DCC6;border-radius:14px;padding:10px 8px;text-align:center;background:#FFFDF8}
.bt-c b{display:block;font-size:1.05rem}.bt-c .n{font-size:1.45rem;font-weight:800;color:#B8912F;line-height:1.1}
.bt-c .n2{font-size:.95rem}.bt-c .vd{margin-top:4px;opacity:.9;font-style:italic}.bt-c small{display:block;font-size:.72rem;opacity:.75;line-height:1.3}
html[data-hac-theme=dark] .bt-c{background:#1A1814;border-color:#3A342A}
</style>"""


# ------------------------------------------------------------------ v3.4: ảnh thật (HLV chụp / AI tạo) thay hình vẽ
KHOA_ANH = "ban_tay_anh"          # DinhDuong: {p: id ảnh, c: …, f: …, rau: …}
PROMPT = {  # mô tả cho AI tạo ảnh (tiếng Anh cho kết quả ổn định hơn)
    "p": "Realistic food photo, top-down view: an open adult Asian hand, palm up, on a light wooden table; next to the palm a "
         "grilled chicken breast fillet exactly the same size and thickness as the palm (not including fingers). Soft natural light, "
         "clean, no text, no logo.",
    "c": "Realistic food photo: an adult Asian hand cupped, holding a small mound of cooked white jasmine rice that fills the cupped "
         "palm, beside a small Vietnamese rice bowl, light wooden table, soft natural light, clean, no text, no logo.",
    "f": "Realistic food photo: an adult Asian hand making a thumbs-up, next to a tablespoon of peanut butter and a small pile of "
         "cashew nuts about the size of the thumb, light wooden table, soft natural light, clean, no text, no logo.",
    "rau": "Realistic food photo: an adult Asian hand closed in a fist, next to a small bowl of steamed broccoli and morning glory "
           "about the same size as the fist, light wooden table, soft natural light, clean, no text, no logo.",
}
_URI: dict[str, str] = {}


def anh_luu() -> dict:
    from core import db
    try:
        return {k: v for k, v in db.latest("DinhDuong").get(KHOA_ANH, {}).items() if k in TEN and v}
    except Exception:  # noqa: BLE001 — chưa có DB: dùng hình vẽ
        return {}


def _uri(anh_id: str) -> str | None:
    if anh_id not in _URI:
        import base64

        from core import anh as A, db
        b = db.get_images([anh_id]).get(anh_id)
        if not b:
            return None
        _URI[anh_id] = "data:image/jpeg;base64," + base64.b64encode(A.shrink(b, 520)).decode()
    return _URI[anh_id]


def _hinh(k: str, ANH: dict) -> str:
    u = _uri(ANH[k]) if ANH.get(k) else None
    return (f'<img src="{u}" alt="{E(TEN[k][0])}" style="width:100%;max-width:240px;aspect-ratio:4/3;object-fit:cover;'
            f'border-radius:10px;margin-bottom:6px">') if u else SVG[k]


def the_ban_tay(phan: dict | None = None, nhan_nu_nam: bool = False) -> str:
    """4 thẻ hình: số phần cho 1 bữa (nếu có `phan`) hoặc chuẩn chung Nữ / Nam."""
    chuan = {k: "Nữ 1 · Nam 2 / bữa" for k in ("p", "c", "f", "rau")}
    out, ANH = "", anh_luu()
    for k in ("p", "c", "f", "rau"):
        t = TEN[k]
        so = (an.so_s(phan.get(k, 0)) + " " + t[0].lower()) if phan else chuan[k]
        out += (f'<div class="bt-c">{_hinh(k, ANH)}<b>{E(t[1])}</b><div class="n{'' if phan else ' n2'}">{E(so)}</div>'
                f'<small>{E(t[0])} {E(t[2])}</small><small>{E(t[3])}</small><small class="vd">{E(VD[k])}</small></div>')
    return CSS + f'<div class="bt-w">{out}</div>' + GHI


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


def quan_ly_anh(nguoi: str):
    """HLV: thay 4 hình bằng ảnh thật — tự chụp tay mình cạnh món ăn (rõ nhất) hoặc bấm AI tạo."""
    import streamlit as st

    from core import anh as A, db, llm
    S = st.session_state
    ANH = anh_luu()
    st.caption("Ảnh tốt nhất là **chính tay anh chụp cạnh món ăn thật** (khách nhìn là hiểu ngay). Hoặc bấm 🎨 để AI tạo ảnh. "
               "Ảnh lưu trong kho ảnh của app (Google Drive), không đưa lên GitHub.")

    def ghi(moi: dict):
        db.append("DinhDuong", KHOA_ANH, moi, nguoi, "")
        st.rerun()
    cs = st.columns(4)
    for i, k in enumerate(("p", "c", "f", "rau")):
        with cs[i]:
            st.markdown(f"**{TEN[k][0]}** · {TEN[k][1]}")
            st.markdown(_hinh(k, ANH), unsafe_allow_html=True)
            f = st.file_uploader("Tải ảnh", type=["jpg", "jpeg", "png", "webp"], key=f"bta_{k}_{S.get('bta_v', 0)}",
                                 label_visibility="collapsed")
            if f is not None and st.button("💾 Dùng ảnh này", key=f"btl_{k}", use_container_width=True):
                up = db.upload_images({k: A.shrink(f.getvalue(), 1200)}, "HAC_bantay_")
                if not up:
                    st.error("Chưa tải lên được — thử lại.")
                else:
                    S["bta_v"] = S.get("bta_v", 0) + 1
                    ghi({**ANH, k: up[k]})
            if llm.provider() == "gemini" and st.button("🎨 AI tạo ảnh", key=f"btg_{k}", use_container_width=True):
                with st.spinner("AI đang vẽ (20–60 giây)…"):
                    try:
                        b = llm.tao_anh(PROMPT[k])
                    except llm.LLMError as e:
                        st.error(f"{e} — anh có thể tự tạo ở app Gemini / ChatGPT với mô tả bên dưới rồi tải lên.")
                        b = None
                if b:
                    up = db.upload_images({k: A.shrink(b, 1200)}, "HAC_bantay_")
                    if up:
                        ghi({**ANH, k: up[k]})
            if ANH.get(k) and st.button("↩️ Về hình vẽ", key=f"btx_{k}", use_container_width=True):
                ghi({x: y for x, y in ANH.items() if x != k})
    with st.expander("Mô tả để tự tạo ảnh ở app AI (Gemini / ChatGPT) — chép từng đoạn"):
        for k in ("p", "c", "f", "rau"):
            st.markdown(f"**{TEN[k][0]}**")
            st.code(PROMPT[k], language=None)
