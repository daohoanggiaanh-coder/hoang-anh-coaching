"""v3.9 — Hiển thị kế hoạch tăng tiến: thẻ cho khách (buổi tới cần tăng gì) và bảng nhắc cho HLV (kèm tin Zalo soạn sẵn)."""
from __future__ import annotations

import html
from datetime import date

import streamlit as st

from core import tang_tien as ttn

E = html.escape
CSS = """<style>
.tt-r{display:grid;grid-template-columns:1.1fr 2.2fr;gap:10px;padding:8px 10px;border-bottom:1px solid rgba(163,128,60,.18);font-size:.88rem}
.tt-r b{font-size:.92rem}.tt-r small{display:block;opacity:.7;font-size:.74rem;margin-top:2px}
.tt-c{border:1px solid rgba(200,162,74,.35);border-radius:14px;overflow:hidden;margin:6px 0 10px}
.tt-h{background:rgba(200,162,74,.12);padding:8px 12px;font-weight:700}
.tt-w{background:#FFF8E6;color:#5a4a1e;border-radius:10px;padding:6px 10px;margin:4px 0;font-size:.82rem}
@media (max-width:640px){.tt-r{grid-template-columns:1fr}}
</style>"""


def _md(s: str) -> str:
    """**đậm** → <b> (sau khi escape)."""
    out, mo = "", False
    for i, p in enumerate(E(s).split("**")):
        out += (("<b>" if not mo else "</b>") if i else "") + p
        mo = not mo if i else mo
    return out + ("</b>" if mo else "")


def _cho_khach(c: str) -> str:
    """Câu chú ý viết cho HLV → lời nói với khách."""
    for a, b in (("→ hỏi lại khách trước khi tập.", "→ nếu vẫn còn đau, báo HLV trước buổi nhé."),
                 ("→ hỏi ngủ / ăn / mệt; giữ tạ, chưa tăng.", "→ ngủ đủ, ăn đủ trước buổi; hôm đó giữ tạ, chưa tăng."),
                 ("→ hỏi giấc ngủ, ăn uống trước buổi.", "→ ngủ đủ, ăn nhẹ trước buổi 1–2 tiếng."),
                 ("Buổi trước khách chấm", "Buổi trước bạn chấm"), ("Buổi trước khách thấy", "Buổi trước bạn thấy")):
        c = c.replace(a, b)
    return c


def bang(kh: dict, ngay: date, tieu_de: str = "", hien_ls: bool = True, chi_doi: bool = False, khach: bool = False):
    """Bảng: bài · lịch sử các buổi trước · gợi ý hôm nay (+ chú ý)."""
    st.markdown(CSS, unsafe_allow_html=True)
    dong = []
    for b in kh["bai"]:
        p = b["pt"]
        if chi_doi and p["muc"] == "moi":
            continue
        ls = (" · ".join(E(ttn.mo_ta(y, b["giay"])) for y in b["ls"][:3]) or "chưa tập lần nào") if hien_ls else ""
        cy = "".join(f'<div class="tt-w">⚠️ {E(_cho_khach(c) if khach else c)}</div>' for c in p["chu_y"][:2])
        dong.append(f'<div class="tt-r"><div><b>{E(b["ten"])}</b><small>Mục tiêu {E(b["lieu"])}</small>'
                    + (f"<small>📜 {ls}</small>" if ls else "") + f'</div><div>{p["icon"]} {_md(p["ngan"])}{cy}</div></div>')
    tieu_de = tieu_de or f"Buổi {kh['buoi']['ma']} · {kh['buoi']['ten']} — {ngay:%d/%m} · tuần {kh['tuan']} ({kh['phase']})"
    st.markdown(f'<div class="tt-c"><div class="tt-h">{E(tieu_de)}</div>{"".join(dong)}</div>', unsafe_allow_html=True)
    for c in ([] if khach else kh["chung"]):
        st.markdown(f'<div class="tt-w">📌 {E(c)}</div>', unsafe_allow_html=True)


def the_khach(k: dict, ngay: date | None, buoi_ma: str | None = None):
    """Trang chủ khách: buổi tập tới cần tăng gì, chú ý gì."""
    try:
        kh = ttn.ke_hoach(k, ngay, buoi_ma)
    except Exception:  # noqa: BLE001 — giáo án lỗi / chưa có thì bỏ qua thẻ
        return
    if not kh or not any(b["ls"] for b in kh["bai"]):
        return
    d = kh["dem"]
    tom = " · ".join(x for x in (f"⬆️ {d['tang_ta']} bài tăng tạ" if d["tang_ta"] else "",
                                 f"➕ {d['tang_lan']} bài thêm lần" if d["tang_lan"] else "",
                                 f"🔁 {d['doi_bien']} bài đổi biến số" if d["doi_bien"] else "") if x)
    with st.expander(f"🎯 Buổi tới cần tăng tiến gì{' — ' + tom if tom else ''}", expanded=True):
        st.caption("Dựa trên số tạ và số lần các buổi trước của bạn. Hôm đó mệt / đau thì báo HLV để điều chỉnh.")
        bang(kh, ngay or date.today(), chi_doi=True, khach=True)


def nhac_hlv(k: dict, ngay: date, buoi_ma: str | None, key: str):
    """HLV: bảng tăng tiến + tin Zalo soạn sẵn cho 1 buổi."""
    kh = ttn.ke_hoach(k, ngay, buoi_ma)
    if not kh:
        st.caption("Khách chưa có giáo án — soạn ở 🏋️ Giáo án khách.")
        return
    bang(kh, ngay)
    if any(b["pt"]["muc"] != "moi" for b in kh["bai"]):
        st.caption("📋 Tin nhắc khách (bấm biểu tượng góc phải để chép, dán vào Zalo):")
        st.code(ttn.tin_zalo(k, kh, ngay), language=None, wrap_lines=True)
